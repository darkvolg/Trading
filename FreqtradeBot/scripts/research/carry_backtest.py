"""Cash-and-carry realistic backtest — go/no-go decision.

Models a delta-neutral carry strategy on Bybit USDT-perps:

  - When funding rate stays POSITIVE for N consecutive 8h periods on a pair,
    OPEN: buy spot + sell perp same notional (delta-neutral).
  - While position open, COLLECT funding from short perp leg.
  - When funding crosses NEGATIVE for M consecutive periods, CLOSE.
  - Cap concurrent positions to N_SLOTS (capital constraint).

Fees (Bybit, taker — conservative):
  - Spot taker:  0.10%
  - Perp taker:  0.06%
  - Round trip (open+close): 0.10+0.06 + 0.10+0.06 = 0.32% per position cycle

Slippage assumption:
  - 0.05% per side on liquid USDT-perp alts (top-15 by volume) — total 0.10% per cycle.

Total transaction cost per cycle: ~0.42% of notional.

Spot ≈ perp price approximation: Bybit spot↔perp basis on USDT pairs is
typically <0.1% during normal market. For go/no-go decision (1-2% precision
needed), perp-as-spot proxy is acceptable.

What this validates:
  1. NET APR after realistic fees (gross funding minus all costs)
  2. Average hold period (drives fee drag)
  3. Per-pair contribution (which alts to focus on)
  4. Capacity / capital efficiency
"""
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("/opt/freqtrade/user_data/data/bybit/futures")
WHITELIST = [
    "BTC", "ETH", "SOL", "DOGE", "XRP", "ADA", "AVAX", "DOT",
    "POL", "NEAR", "ATOM", "SUI", "LINK", "OP", "BNB",
]

# Strategy parameters (conservative defaults; will sweep)
ENTRY_THRESHOLD = 0.0001   # 0.01% / 8h ≈ 11% APR — minimum funding to bother
EXIT_THRESHOLD = -0.00005  # exit if funding <-0.005%/8h (close to zero or negative)
ENTRY_PERSISTENCE = 3      # need 3 consecutive periods above threshold
EXIT_PERSISTENCE = 3       # need 3 below before closing

FEE_SPOT_TAKER = 0.0010
FEE_PERP_TAKER = 0.0006
SLIPPAGE_PER_SIDE = 0.0005
COST_PER_CYCLE = 2 * (FEE_SPOT_TAKER + FEE_PERP_TAKER + SLIPPAGE_PER_SIDE)

N_SLOTS = 8  # max concurrent positions (capital cap)


def load_funding(sym):
    p = DATA_DIR / f"{sym}_USDT_USDT-8h-funding_rate.feather"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_feather(p)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df[["date", "open"]].rename(columns={"open": "rate"})
    return df.sort_values("date").reset_index(drop=True)


def simulate_pair(funding: pd.DataFrame, start, end,
                  entry_thr=ENTRY_THRESHOLD, exit_thr=EXIT_THRESHOLD,
                  entry_pers=ENTRY_PERSISTENCE, exit_pers=EXIT_PERSISTENCE,
                  cost=COST_PER_CYCLE):
    """Single-pair simulation. Returns trade list and aggregate stats."""
    f = funding[(funding["date"] >= start) & (funding["date"] <= end)].copy()
    if len(f) < entry_pers + exit_pers + 5:
        return [], {"net_pct": 0.0, "n_cycles": 0, "avg_hold_periods": 0,
                    "total_funding": 0.0, "total_cost": 0.0}

    rates = f["rate"].values
    dates = f["date"].values

    trades = []
    in_pos = False
    open_idx = None
    cum_funding = 0.0

    for i in range(len(rates)):
        if not in_pos:
            # need ENTRY_PERSISTENCE recent periods all > entry_thr
            if i < entry_pers:
                continue
            window = rates[i - entry_pers + 1:i + 1]
            if (window > entry_thr).all():
                in_pos = True
                open_idx = i
                cum_funding = 0.0
        else:
            cum_funding += rates[i]  # short perp earns positive funding
            # check exit: EXIT_PERSISTENCE periods all < exit_thr
            if i < open_idx + exit_pers:
                continue
            window = rates[i - exit_pers + 1:i + 1]
            if (window < exit_thr).all():
                # close
                trades.append({
                    "open_date": dates[open_idx],
                    "close_date": dates[i],
                    "hold_periods": i - open_idx,
                    "funding_pct": cum_funding * 100,
                    "cost_pct": cost * 100,
                    "net_pct": (cum_funding - cost) * 100,
                })
                in_pos = False

    if in_pos:
        trades.append({
            "open_date": dates[open_idx],
            "close_date": dates[-1],
            "hold_periods": len(rates) - 1 - open_idx,
            "funding_pct": cum_funding * 100,
            "cost_pct": cost * 100,
            "net_pct": (cum_funding - cost) * 100,
            "still_open": True,
        })

    if not trades:
        return [], {"net_pct": 0.0, "n_cycles": 0, "avg_hold_periods": 0,
                    "total_funding": 0.0, "total_cost": 0.0}
    total_net = sum(t["net_pct"] for t in trades)
    total_funding = sum(t["funding_pct"] for t in trades)
    total_cost = sum(t["cost_pct"] for t in trades)
    avg_hold = sum(t["hold_periods"] for t in trades) / len(trades)
    return trades, {
        "net_pct": total_net,
        "n_cycles": len(trades),
        "avg_hold_periods": avg_hold,
        "total_funding": total_funding,
        "total_cost": total_cost,
    }


def run_window(start, end, label, params=None):
    p = params or {}
    print(f"\n=== {label} ({start} -> {end}) ===")
    print(f"params: entry_thr={p.get('entry_thr', ENTRY_THRESHOLD)}, exit_thr={p.get('exit_thr', EXIT_THRESHOLD)}, "
          f"entry_pers={p.get('entry_pers', ENTRY_PERSISTENCE)}, exit_pers={p.get('exit_pers', EXIT_PERSISTENCE)}, "
          f"cost/cycle={COST_PER_CYCLE*100:.3f}%")
    rows = []
    all_trades = []
    days = (pd.Timestamp(end, tz="UTC") - pd.Timestamp(start, tz="UTC")).days
    for sym in WHITELIST:
        f = load_funding(sym)
        if f.empty:
            continue
        trades, stats = simulate_pair(
            f, start, end,
            entry_thr=p.get("entry_thr", ENTRY_THRESHOLD),
            exit_thr=p.get("exit_thr", EXIT_THRESHOLD),
            entry_pers=p.get("entry_pers", ENTRY_PERSISTENCE),
            exit_pers=p.get("exit_pers", EXIT_PERSISTENCE),
        )
        for t in trades:
            t["sym"] = sym
        all_trades.extend(trades)
        apr = stats["net_pct"] * 365 / days if days else 0
        gross_apr = stats["total_funding"] * 365 / days if days else 0
        rows.append({
            "sym": sym,
            "n_cycles": stats["n_cycles"],
            "avg_hold_d": round(stats["avg_hold_periods"] / 3, 1),  # 8h periods → days
            "gross_funding%": round(stats["total_funding"], 2),
            "total_cost%": round(stats["total_cost"], 2),
            "net%": round(stats["net_pct"], 2),
            "net_apr%": round(apr, 1),
            "gross_apr%": round(gross_apr, 1),
        })
    df = pd.DataFrame(rows)
    print(df.to_string(index=False))

    if not df.empty:
        # portfolio: assume even allocation across active pairs at each moment
        # simplistic: sum all per-pair net% then divide by N_SLOTS (caps capital)
        total_net = df["net%"].sum()
        portfolio_apr_unsliced = total_net * 365 / days
        portfolio_apr_capped = portfolio_apr_unsliced / N_SLOTS  # capital constraint
        print(f"\n  Sum-of-pairs net: {total_net:.2f}% over {days}d -> {portfolio_apr_unsliced:.2f}% APR if all simultaneous (impossible)")
        print(f"  Portfolio APR with {N_SLOTS} concurrent slots cap: {portfolio_apr_capped:.2f}% net of fees")
        print(f"  Median per-pair net APR: {df['net_apr%'].median():.2f}%")
        print(f"  Median hold: {df['avg_hold_d'].median():.1f} days")
        print(f"  Pairs with positive net: {(df['net%'] > 0).sum()}/{len(df)}")
    return df, all_trades


def main():
    print(f"Cost per cycle: {COST_PER_CYCLE*100:.3f}% (spot 2×{FEE_SPOT_TAKER*100}% + perp 2×{FEE_PERP_TAKER*100}% + slippage 2×{SLIPPAGE_PER_SIDE*100}%)")

    # Default params, 3 windows
    run_window("2025-01-15", "2026-04-30", "BEAR-LEANING 480d (default params)")
    run_window("2024-01-01", "2025-01-14", "BULL-LEANING 379d (default params)")
    run_window("2022-01-01", "2026-04-30", "FULL 4y (default params)")

    # Param sweep on full 4y
    print("\n\n=== PARAM SWEEP on FULL 4y ===")
    for entry_thr in [0.00005, 0.0001, 0.0002, 0.0003]:
        for exit_persistence in [2, 3, 5]:
            df, _ = run_window("2022-01-01", "2026-04-30",
                f"entry_thr={entry_thr*100:.3f}% / exit_pers={exit_persistence}",
                params={"entry_thr": entry_thr, "exit_pers": exit_persistence})


if __name__ == "__main__":
    main()
