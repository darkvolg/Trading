"""Cash-and-carry portfolio simulator with proper concurrent-position tracking.

Replaces the "sum/N_SLOTS" approximation in carry_backtest.py. At every 8h
funding tick, we know which pairs are eligible to be in position; we pick
the top N_SLOTS by current funding rate and stay in those, paying fees only
on actual opens/closes (not on every flip).

Outputs monthly PnL distribution so we can see deployment-relevant metrics:
- Worst month (tail risk)
- % positive months (consistency)
- Sharpe-like ratio on monthly returns
- Drawdown over the period
"""
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path("/opt/freqtrade/user_data/data/bybit/futures")
WHITELIST = [
    "BTC", "ETH", "SOL", "DOGE", "XRP", "ADA", "AVAX", "DOT",
    "POL", "NEAR", "ATOM", "SUI", "LINK", "OP", "BNB",
]

ENTRY_THRESHOLD = 0.0001
EXIT_THRESHOLD = -0.00005
ENTRY_PERSISTENCE = 3
EXIT_PERSISTENCE = 3
N_SLOTS = 8

FEE_SPOT_TAKER = 0.0010
FEE_PERP_TAKER = 0.0006
SLIPPAGE_PER_SIDE = 0.0005
COST_PER_CYCLE = 2 * (FEE_SPOT_TAKER + FEE_PERP_TAKER + SLIPPAGE_PER_SIDE)


def load_funding(sym):
    p = DATA_DIR / f"{sym}_USDT_USDT-8h-funding_rate.feather"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_feather(p)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df = df[["date", "open"]].rename(columns={"open": "rate"})
    return df.sort_values("date").reset_index(drop=True)


def build_funding_matrix(start, end, syms):
    """Returns DataFrame indexed by 8h timestamp, columns = pair symbols, values = funding rate."""
    frames = []
    for sym in syms:
        f = load_funding(sym)
        if f.empty:
            continue
        f = f[(f["date"] >= start) & (f["date"] <= end)].copy()
        f = f.set_index("date").rename(columns={"rate": sym})
        frames.append(f)
    if not frames:
        return pd.DataFrame()
    matrix = pd.concat(frames, axis=1)
    matrix = matrix.sort_index()
    return matrix


def simulate_portfolio(matrix: pd.DataFrame,
                       entry_thr=ENTRY_THRESHOLD, exit_thr=EXIT_THRESHOLD,
                       entry_pers=ENTRY_PERSISTENCE, exit_pers=EXIT_PERSISTENCE,
                       n_slots=N_SLOTS, cost_per_cycle=COST_PER_CYCLE):
    """For each 8h tick: determine eligible pairs, pick top n_slots by recent
    funding signal, hold until exit rule fires. Return per-tick PnL series."""
    syms = list(matrix.columns)
    n_ticks = len(matrix)

    # State per pair: 'flat' / 'in'
    state = {s: "flat" for s in syms}
    bars_in_pos = {s: 0 for s in syms}
    bars_below = {s: 0 for s in syms}  # consecutive ticks rate < exit_thr while flat
    bars_above = {s: 0 for s in syms}  # consecutive ticks rate > entry_thr while flat

    # Per-tick PnL contributions: funding minus fees on entry/exit
    per_tick = []
    open_fee_per_pos = (FEE_SPOT_TAKER + FEE_PERP_TAKER + SLIPPAGE_PER_SIDE)
    close_fee_per_pos = open_fee_per_pos

    n_opens = 0
    n_closes = 0

    for i, ts in enumerate(matrix.index):
        rates = matrix.iloc[i]

        # 1. Update persistence counters for flat pairs
        for s in syms:
            r = rates[s]
            if pd.isna(r):
                continue
            if state[s] == "flat":
                if r > entry_thr:
                    bars_above[s] += 1
                else:
                    bars_above[s] = 0

        # 2. Determine candidates eligible to enter (flat AND persistence met)
        candidates = []
        for s in syms:
            if state[s] == "flat" and bars_above[s] >= entry_pers and not pd.isna(rates[s]):
                candidates.append((s, rates[s]))

        # 3. Compute current open count
        open_pairs = [s for s in syms if state[s] == "in"]
        free_slots = n_slots - len(open_pairs)

        # 4. Open positions in free slots, prioritizing highest funding
        candidates.sort(key=lambda x: -x[1])
        opens_this_tick = 0
        for s, _ in candidates[:max(0, free_slots)]:
            state[s] = "in"
            bars_in_pos[s] = 0
            bars_below[s] = 0
            n_opens += 1
            opens_this_tick += 1

        # 5. For pairs in position: accumulate funding, check exit
        funding_received = 0.0
        closes_this_tick = 0
        for s in list(syms):
            if state[s] != "in":
                continue
            r = rates[s]
            if pd.isna(r):
                # treat NaN as zero funding (no movement)
                continue
            funding_received += r  # short-perp earns positive funding
            bars_in_pos[s] += 1
            # exit persistence
            if r < exit_thr:
                bars_below[s] += 1
            else:
                bars_below[s] = 0
            if bars_below[s] >= exit_pers:
                state[s] = "flat"
                bars_above[s] = 0
                bars_below[s] = 0
                bars_in_pos[s] = 0
                n_closes += 1
                closes_this_tick += 1

        # 6. Net PnL for this tick:
        #    funding earned across all active positions
        #    minus fees on opens (per new position)
        #    minus fees on closes (per closed position)
        # Each position is sized to (capital / n_slots) of total notional, so
        # per-pair contribution scales as (1 / n_slots) of full notional.
        # Total return is funding_received / n_slots * 1 (since each held
        # position is using 1 slot's worth of capital).
        per_position_funding = funding_received  # already per-pair
        # PnL as fraction of total portfolio capital:
        # if we have N positions out of n_slots, each uses capital of 1/n_slots.
        # funding_received already sums per-pair rates. As fraction of total:
        # sum_rates / n_slots (if we had n_slots positions and each is 1/n_slots of cap).
        portfolio_funding_pct = funding_received / n_slots
        portfolio_fee_pct = (
            (opens_this_tick * open_fee_per_pos
             + closes_this_tick * close_fee_per_pos)
            / n_slots
        )
        net_pct = portfolio_funding_pct - portfolio_fee_pct

        per_tick.append({
            "date": ts,
            "n_open": len(open_pairs) + opens_this_tick - closes_this_tick,
            "opens": opens_this_tick,
            "closes": closes_this_tick,
            "funding_pct": portfolio_funding_pct * 100,
            "fees_pct": portfolio_fee_pct * 100,
            "net_pct": net_pct * 100,
        })

    df = pd.DataFrame(per_tick)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df["cum_pct"] = df["net_pct"].cumsum()
    return df, {"opens": n_opens, "closes": n_closes}


def monthly_summary(per_tick: pd.DataFrame, label: str):
    df = per_tick.copy()
    df["month"] = df["date"].dt.to_period("M")
    monthly = df.groupby("month").agg(
        net_pct=("net_pct", "sum"),
        funding_pct=("funding_pct", "sum"),
        fees_pct=("fees_pct", "sum"),
        avg_open=("n_open", "mean"),
        opens=("opens", "sum"),
        closes=("closes", "sum"),
    ).round(3)
    pos_months = (monthly["net_pct"] > 0).sum()
    n = len(monthly)
    total = monthly["net_pct"].sum()
    days = (per_tick["date"].iloc[-1] - per_tick["date"].iloc[0]).days
    apr = total * 365 / days if days else 0
    sharpe = (
        monthly["net_pct"].mean() / monthly["net_pct"].std() * np.sqrt(12)
        if monthly["net_pct"].std() > 0 else 0
    )
    # drawdown on cumulative monthly
    cum = monthly["net_pct"].cumsum()
    dd = (cum - cum.cummax()).min()
    print(f"\n=== {label} ===")
    print(f"Period: {per_tick['date'].iloc[0].date()} -> {per_tick['date'].iloc[-1].date()}  ({days}d, {n} months)")
    print(f"Total net: {total:.2f}% / APR: {apr:.2f}%")
    print(f"Positive months: {pos_months}/{n} ({pos_months*100/n:.0f}%)")
    print(f"Best month: {monthly['net_pct'].max():.2f}% / Worst: {monthly['net_pct'].min():.2f}%")
    print(f"Sharpe (annualized from monthly): {sharpe:.2f}")
    print(f"Max drawdown over the run: {dd:.2f}%")
    print(f"Avg concurrent positions: {monthly['avg_open'].mean():.1f} / N_SLOTS")
    print(f"Total opens/closes: {monthly['opens'].sum()} / {monthly['closes'].sum()}")
    print()
    print("Monthly PnL distribution (top 5 best / worst):")
    print("  Top 5 best:")
    print(monthly.nlargest(5, "net_pct")[["net_pct", "funding_pct", "fees_pct", "avg_open"]].to_string())
    print("  Top 5 worst:")
    print(monthly.nsmallest(5, "net_pct")[["net_pct", "funding_pct", "fees_pct", "avg_open"]].to_string())
    return monthly


def run_full(matrix, n_slots, label):
    print(f"\n>>>>> N_SLOTS = {n_slots} <<<<<")
    per_tick, info = simulate_portfolio(matrix, n_slots=n_slots)
    print(f"Total opens/closes: {info['opens']} / {info['closes']}")
    return monthly_summary(per_tick, f"FULL 4y+ (N_SLOTS={n_slots})"), per_tick


def main():
    full_start = "2022-01-01"
    full_end = "2026-04-30"
    print(f"Cost per cycle: {COST_PER_CYCLE*100:.3f}%")
    print(f"Strategy: enter when funding > {ENTRY_THRESHOLD*100}%/8h for {ENTRY_PERSISTENCE} periods, "
          f"exit when funding < {EXIT_THRESHOLD*100}%/8h for {EXIT_PERSISTENCE} periods. "
          f"Top-N_SLOTS by funding signal. Capital evenly split across active slots.")

    matrix = build_funding_matrix(full_start, full_end, WHITELIST)
    print(f"Loaded funding matrix: {matrix.shape[0]} ticks × {matrix.shape[1]} pairs")

    # Compare 8 vs 4 vs 2 slot allocations to find capital-efficient sweet spot
    for slots in [8, 6, 4, 2]:
        m, per_tick = run_full(matrix, n_slots=slots, label=f"N_SLOTS={slots}")

    # Sub-windows
    for label, start, end in [
        ("BEAR 480d", "2025-01-15", "2026-04-30"),
        ("BULL 379d", "2024-01-01", "2025-01-14"),
    ]:
        sub = per_tick[
            (per_tick["date"] >= pd.Timestamp(start, tz="UTC"))
            & (per_tick["date"] <= pd.Timestamp(end, tz="UTC"))
        ].reset_index(drop=True)
        if not sub.empty:
            monthly_summary(sub, label)


if __name__ == "__main__":
    main()
