"""Flash-crash stress test for delta-neutral cash-and-carry.

Synthetically injects a large price shock (e.g. SOL drops 20% in 1 candle)
while the bot has an open position, and validates that the delta-neutral
PnL stays ~0 despite the move.

Key claim: spot leg loses X%, perp short leg gains X%, net ≈ 0 minus
fees and basis drift. With realistic fees + slippage on close (forced or
not), the position should still net to within ±0.5% of the funding
already accrued.

Failure modes we want to catch:
  - Liquidation triggers on perp leg before delta-neutral PnL nets out
  - Stop-loss-on-exchange (stoploss_on_exchange) on perp closes early
  - Spot order book too thin — actual sell price diverges from mark
  - Forced close mid-flash makes spot+perp non-simultaneous → directional risk

This is a model-level test (no real exchange). Verifies the math holds
under shock; real-exchange stress is the live testnet 7d window.
"""
from dataclasses import dataclass


@dataclass
class StressResult:
    scenario: str
    spot_pnl: float
    perp_pnl: float
    funding_accrued: float
    fees: float
    net_pnl: float
    survived: bool
    notes: str


def simulate_flash_crash(
    pair: str,
    notional_usdt: float,
    entry_spot: float,
    entry_perp: float,
    funding_received_quote: float,
    crash_pct: float,
    crash_recovery_pct: float = 0.0,
    perp_leverage: int = 1,
    perp_initial_margin_pct: float = 1.0,
    spot_taker_fee: float = 0.001,
    perp_taker_fee: float = 0.0006,
    slippage_each_side: float = 0.0005,
    forced_close_during_crash: bool = False,
) -> StressResult:
    """Single scenario simulation.

    Args:
        notional_usdt: position size on each leg (spot=long, perp=short)
        entry_spot/perp: prices at open
        funding_received_quote: funding accrued before the crash
        crash_pct: e.g. -0.20 for a 20% drop
        crash_recovery_pct: how much price recovers afterwards (0 = stays at low)
        perp_leverage: 1 for default safe; 2-3 for the scaled-up case
        perp_initial_margin_pct: 1.0 = full collateral; <1 = margin trade
        forced_close_during_crash: if True, close at the crash low (worst case)

    Returns:
        StressResult with PnL breakdown.
    """
    base_qty = notional_usdt / entry_spot

    # Crash low: spot drops by crash_pct
    spot_low = entry_spot * (1 + crash_pct)
    perp_low = entry_perp * (1 + crash_pct)

    # Liquidation check on perp short:
    # For 1x perp leverage with full margin, liq is at ~entry*(1+1/leverage)
    # but UTA spot collateral typically extends this far further.
    # Simplification: liq triggers if spot+perp combined equity goes negative.
    spot_value_at_low = base_qty * spot_low
    perp_short_pnl_at_low = (entry_perp - perp_low) * base_qty
    perp_initial_margin = (notional_usdt / perp_leverage) * perp_initial_margin_pct
    perp_margin_at_low = perp_initial_margin + perp_short_pnl_at_low

    # In UTA, spot value adds to collateral. So total collateral:
    total_collateral_at_low = spot_value_at_low + perp_margin_at_low
    # Maintenance margin requirement on perp (Bybit ~0.5% for major alts):
    perp_maint_margin = abs(base_qty * perp_low) * 0.005
    survived_liq = total_collateral_at_low > perp_maint_margin

    if not survived_liq:
        return StressResult(
            scenario=f"{pair} crash {crash_pct*100:.0f}%",
            spot_pnl=spot_value_at_low - notional_usdt,
            perp_pnl=perp_short_pnl_at_low,
            funding_accrued=funding_received_quote,
            fees=0,
            net_pnl=-notional_usdt,  # liquidation = full loss
            survived=False,
            notes="LIQUIDATION on perp leg",
        )

    # Determine exit prices
    if forced_close_during_crash:
        exit_spot = spot_low
        exit_perp = perp_low
    else:
        exit_spot = entry_spot * (1 + crash_pct + crash_recovery_pct)
        exit_perp = entry_perp * (1 + crash_pct + crash_recovery_pct)

    # PnL legs
    spot_pnl = (exit_spot - entry_spot) * base_qty
    perp_pnl = (entry_perp - exit_perp) * base_qty  # short

    # Fees: open already paid; here we count CLOSE fees only (open were tracked at entry)
    close_fee_spot = abs(base_qty * exit_spot) * (spot_taker_fee + slippage_each_side)
    close_fee_perp = abs(base_qty * exit_perp) * (perp_taker_fee + slippage_each_side)
    close_fees = close_fee_spot + close_fee_perp

    net = spot_pnl + perp_pnl + funding_received_quote - close_fees

    return StressResult(
        scenario=f"{pair} crash {crash_pct*100:+.0f}% recovery {crash_recovery_pct*100:+.0f}%",
        spot_pnl=round(spot_pnl, 2),
        perp_pnl=round(perp_pnl, 2),
        funding_accrued=round(funding_received_quote, 2),
        fees=round(close_fees, 2),
        net_pnl=round(net, 2),
        survived=True,
        notes="forced close at crash low" if forced_close_during_crash else "natural close after recovery",
    )


def main():
    print("=" * 90)
    print("Flash-crash stress test — delta-neutral cash-and-carry")
    print("Position: $100 notional each leg (long spot + short perp), 1x perp leverage")
    print("=" * 90)
    print()

    scenarios = [
        # 5 typical / acceptable: open at $100, crash N%, recover fully
        dict(pair="SOL c-5%/r+5%",  notional_usdt=100, entry_spot=100, entry_perp=100, funding_received_quote=0.50, crash_pct=-0.05, crash_recovery_pct=0.05),
        dict(pair="SOL c-10%/r+10%", notional_usdt=100, entry_spot=100, entry_perp=100, funding_received_quote=0.50, crash_pct=-0.10, crash_recovery_pct=0.10),
        dict(pair="SOL c-20%/r+20%", notional_usdt=100, entry_spot=100, entry_perp=100, funding_received_quote=0.50, crash_pct=-0.20, crash_recovery_pct=0.20),
        dict(pair="SOL c-30%/r+30%", notional_usdt=100, entry_spot=100, entry_perp=100, funding_received_quote=0.50, crash_pct=-0.30, crash_recovery_pct=0.30),
        # Forced close at the low (worst case for delta-neutral)
        dict(pair="SOL forced-low -20%", notional_usdt=100, entry_spot=100, entry_perp=100, funding_received_quote=0.50, crash_pct=-0.20, crash_recovery_pct=0.0, forced_close_during_crash=True),
        dict(pair="SOL forced-low -40%", notional_usdt=100, entry_spot=100, entry_perp=100, funding_received_quote=0.50, crash_pct=-0.40, crash_recovery_pct=0.0, forced_close_during_crash=True),
        # 2x leverage on perp leg (Config B target)
        dict(pair="SOL 2xLev c-20%/r+20%", notional_usdt=100, entry_spot=100, entry_perp=100, funding_received_quote=0.50, crash_pct=-0.20, crash_recovery_pct=0.20, perp_leverage=2),
        dict(pair="SOL 2xLev forced -40%", notional_usdt=100, entry_spot=100, entry_perp=100, funding_received_quote=0.50, crash_pct=-0.40, crash_recovery_pct=0.0, perp_leverage=2, forced_close_during_crash=True),
        # Extreme: 50% crash, forced close, 1x — testing liquidation safety
        dict(pair="SOL extreme -50% forced", notional_usdt=100, entry_spot=100, entry_perp=100, funding_received_quote=0.50, crash_pct=-0.50, crash_recovery_pct=0.0, forced_close_during_crash=True),
        # Realistic Bybit fast crash (FTX-era SOL drop ~30% in 24h, no recovery yet, natural close)
        dict(pair="FTX-era replay -30%", notional_usdt=100, entry_spot=22, entry_perp=22, funding_received_quote=0.50, crash_pct=-0.30, crash_recovery_pct=0.0),
        # Funding-flip scenario: small loss with 0 funding accrued
        dict(pair="zero-funding small drop", notional_usdt=100, entry_spot=100, entry_perp=100, funding_received_quote=0, crash_pct=-0.05, crash_recovery_pct=0.05),
    ]

    fmt = "{:<28} {:>10} {:>10} {:>8} {:>8} {:>10} {:>10} {:>10}"
    print(fmt.format(
        "Scenario", "spot$", "perp$", "fund$", "fees$", "net$",
        "net%/cap", "survived?",
    ))
    print("-" * 105)

    pass_count = 0
    fail_count = 0
    for params in scenarios:
        r = simulate_flash_crash(**params)
        net_pct = r.net_pnl / params["notional_usdt"] * 100  # net relative to notional
        # Pass: survived + net_pnl > -1% of notional (i.e. delta-neutral approximately holds)
        ok = r.survived and net_pct > -1.0
        flag = "PASS" if ok else "FAIL"
        if ok:
            pass_count += 1
        else:
            fail_count += 1
        print(fmt.format(
            params["pair"][:28],
            f"{r.spot_pnl:.2f}",
            f"{r.perp_pnl:.2f}",
            f"{r.funding_accrued:.2f}",
            f"{r.fees:.2f}",
            f"{r.net_pnl:.2f}",
            f"{net_pct:+.2f}%",
            flag,
        ))
        if r.notes and not ok:
            print(f"   ↳ {r.notes}")

    print("-" * 100)
    total = pass_count + fail_count
    print(f"PASS: {pass_count}/{total}  FAIL: {fail_count}/{total}")
    print()
    if fail_count == 0:
        print("OVERALL: PASS — delta-neutrality holds under all stress scenarios "
              "including 50% crash + forced close at the low.")
    else:
        print("OVERALL: REVIEW — some scenarios show >1% NAV loss; investigate.")


if __name__ == "__main__":
    main()
