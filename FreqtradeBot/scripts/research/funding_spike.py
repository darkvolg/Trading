"""Funding-rate carry spike — does Bybit perp funding offer exploitable alpha?

Three strategies tested on each alt:

  1. PASSIVE LONG: hold perp long forever, accumulate funding payments.
     If funding < 0 (shorts pay longs), longs profit.

  2. SHORT-EXTREME: when funding > 0.05%/8h (annualized ~55%), short the
     perp. Idea: extreme positive funding signals over-leveraged longs;
     mean reversion + carry = double payoff.

  3. DIRECTION-FOLLOW: long when funding < 0, short when funding > 0.
     Always on the side that GETS PAID by funding.

For each strategy on each alt, compute:
  - Cumulative funding payment over the period (% of notional, annualized)
  - Price PnL component (entry vs exit, holding the position)
  - Total = funding + price PnL
  - Sharpe-ish on daily returns

Funding paid 3x per day (every 8h) on Bybit.
Convention: funding RATE positive => longs pay shorts. funding payment for
long = -rate * notional. For short = +rate * notional.

Decision rule for the YES/NO verdict:
  - YES (build): at least 5 alts show >5% annualized total return on
    the best of {passive-long, short-extreme, direction-follow},
    AND total return > raw price PnL for at least one strategy
    (proving funding contributes alpha beyond price drift).
  - NO: funding is noise, can't beat HODL or accept-the-ceiling.
"""
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("/opt/freqtrade/user_data/data/bybit/futures")

WHITELIST = [
    "BTC", "ETH", "SOL", "DOGE", "XRP", "ADA", "AVAX", "DOT",
    "POL", "NEAR", "ATOM", "SUI", "LINK", "OP", "BNB",
]

EXTREME_THRESHOLD = 0.0005  # 0.05% per 8h (annualized ~55%)


def load_funding(sym: str) -> pd.DataFrame:
    p = DATA_DIR / f"{sym}_USDT_USDT-8h-funding_rate.feather"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_feather(p)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    # freqtrade stores funding_rate in 'open' column; drop OHLC zeros to avoid
    # name collisions when joining with price data later.
    df = df[["date", "open"]].rename(columns={"open": "rate"})
    return df


def load_price_1d(sym: str) -> pd.DataFrame:
    p = DATA_DIR / f"{sym}_USDT_USDT-1d-futures.feather"
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_feather(p)
    df["date"] = pd.to_datetime(df["date"], utc=True)
    df["date_d"] = df["date"].dt.normalize()
    return df


def passive_long_pnl(funding: pd.DataFrame, price: pd.DataFrame, start: str, end: str) -> dict:
    """Hold long perp forever. PnL = price change + cumulative funding (long pays positive funding)."""
    f = funding[(funding["date"] >= start) & (funding["date"] <= end)].copy()
    p = price[(price["date"] >= start) & (price["date"] <= end)].copy()
    if f.empty or p.empty:
        return {"funding_pct": np.nan, "price_pct": np.nan, "total_pct": np.nan, "n_periods": 0}
    funding_total = -f["rate"].sum()  # long PAYS positive funding -> negative for long
    price_pct = (p["close"].iloc[-1] / p["close"].iloc[0]) - 1
    days = (p["date"].iloc[-1] - p["date"].iloc[0]).days or 1
    annualizer = 365 / days
    return {
        "funding_pct": funding_total * 100,
        "funding_apr": funding_total * 100 * annualizer,
        "price_pct": price_pct * 100,
        "price_apr": price_pct * 100 * annualizer,
        "total_pct": (funding_total + price_pct) * 100,
        "total_apr": (funding_total + price_pct) * 100 * annualizer,
        "n_periods": len(f),
        "days": days,
    }


def direction_follow_pnl(funding: pd.DataFrame, price: pd.DataFrame, start: str, end: str) -> dict:
    """At each 8h bar, take the side that GETS PAID by funding (long if rate<0, short if rate>0).
    For price PnL: track 8h-resolution direction changes. Approximation: assume we exit/re-enter
    each 8h costlessly (which is optimistic — real fees apply). Spike answers 'is there alpha
    in the funding signal?', not 'is it net of fees?'."""
    f = funding[(funding["date"] >= start) & (funding["date"] <= end)].copy()
    if f.empty:
        return {"funding_pct": np.nan, "price_pct": np.nan, "total_pct": np.nan}
    # Funding component: always on the receiving side, so |rate| * notional per period.
    funding_received = f["rate"].abs().sum()
    # Price component: need 8h price; we only have 1d. Approximate using daily close and
    # mapping each funding period to its day's close. Direction: long if rate<0 else short.
    p = price[(price["date"] >= start) & (price["date"] <= end)].copy()
    if p.empty:
        return {"funding_pct": funding_received * 100, "price_pct": np.nan, "total_pct": np.nan}
    p = p.set_index("date_d")[["close"]]
    f["date_d"] = f["date"].dt.normalize()
    f = f.join(p, on="date_d")
    f["direction"] = np.where(f["rate"] > 0, -1, 1)  # short if positive funding
    f["next_close"] = f["close"].shift(-1)
    f["price_ret"] = (f["next_close"] / f["close"] - 1) * f["direction"]
    price_total = f["price_ret"].sum(skipna=True)
    days = (f["date"].iloc[-1] - f["date"].iloc[0]).days or 1
    annualizer = 365 / days
    return {
        "funding_pct": funding_received * 100,
        "funding_apr": funding_received * 100 * annualizer,
        "price_pct": price_total * 100,
        "price_apr": price_total * 100 * annualizer,
        "total_pct": (funding_received + price_total) * 100,
        "total_apr": (funding_received + price_total) * 100 * annualizer,
    }


def extreme_short_pnl(funding: pd.DataFrame, price: pd.DataFrame, start: str, end: str,
                      threshold: float = EXTREME_THRESHOLD) -> dict:
    """When funding > threshold (over-leveraged longs), short the perp until funding normalizes.
    Receive funding + capture mean-reversion in price."""
    f = funding[(funding["date"] >= start) & (funding["date"] <= end)].copy()
    if f.empty:
        return {"hits": 0, "funding_pct": np.nan, "price_pct": np.nan, "total_pct": np.nan}
    f["short_active"] = (f["rate"] > threshold).astype(int)
    n_hits = f["short_active"].sum()
    if n_hits == 0:
        return {"hits": 0, "funding_pct": 0.0, "price_pct": 0.0, "total_pct": 0.0}
    # Funding received while short = +rate * notional per period.
    funding_received = (f["rate"] * f["short_active"]).sum()
    # Price PnL: when short, profit if price drops. Use next-period 8h close approximated by daily.
    p = price[(price["date"] >= start) & (price["date"] <= end)].copy()
    if p.empty:
        return {"hits": int(n_hits), "funding_pct": funding_received * 100,
                "price_pct": np.nan, "total_pct": np.nan}
    p = p.set_index("date_d")[["close"]]
    f["date_d"] = f["date"].dt.normalize()
    f = f.join(p, on="date_d")
    f["next_close"] = f["close"].shift(-1)
    f["price_ret_if_short"] = -(f["next_close"] / f["close"] - 1) * f["short_active"]
    price_total = f["price_ret_if_short"].sum(skipna=True)
    days = (f["date"].iloc[-1] - f["date"].iloc[0]).days or 1
    annualizer = 365 / days
    return {
        "hits": int(n_hits),
        "funding_pct": funding_received * 100,
        "funding_apr": funding_received * 100 * annualizer,
        "price_pct": price_total * 100,
        "price_apr": price_total * 100 * annualizer,
        "total_pct": (funding_received + price_total) * 100,
        "total_apr": (funding_received + price_total) * 100 * annualizer,
    }


def run_window(start: str, end: str, label: str):
    print(f"\n=== {label} ({start} -> {end}) ===")
    rows = []
    for sym in WHITELIST:
        f = load_funding(sym)
        p = load_price_1d(sym)
        if f.empty or p.empty:
            print(f"  {sym}: NO DATA")
            continue
        passive = passive_long_pnl(f, p, start, end)
        direction = direction_follow_pnl(f, p, start, end)
        extreme = extreme_short_pnl(f, p, start, end)
        rows.append({
            "sym": sym,
            "n_periods": passive["n_periods"],
            # passive long
            "passive_funding%": round(passive["funding_pct"], 2),
            "passive_price%": round(passive["price_pct"], 2),
            "passive_total%": round(passive["total_pct"], 2),
            "passive_apr%": round(passive["total_apr"], 1),
            # direction follow (always on paying side)
            "dir_funding%": round(direction["funding_pct"], 2),
            "dir_total%": round(direction["total_pct"], 2),
            "dir_apr%": round(direction["total_apr"], 1),
            # extreme short
            "ext_hits": extreme["hits"],
            "ext_funding%": round(extreme["funding_pct"], 2),
            "ext_total%": round(extreme["total_pct"], 2),
            "ext_apr%": round(extreme.get("total_apr", 0), 1),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        print("No data found.")
        return

    print("PASSIVE LONG (hold long, collect/pay funding):")
    print(df[["sym", "passive_funding%", "passive_price%", "passive_total%", "passive_apr%"]].to_string(index=False))
    print()

    print("DIRECTION-FOLLOW (always on the paying side, 8h flips):")
    print(df[["sym", "dir_funding%", "dir_total%", "dir_apr%"]].to_string(index=False))
    print()

    print(f"EXTREME-SHORT (short when funding>{EXTREME_THRESHOLD*100}% per 8h):")
    print(df[["sym", "ext_hits", "ext_funding%", "ext_total%", "ext_apr%"]].to_string(index=False))
    print()

    # Verdict
    print("=== VERDICT ===")
    pl_winners = (df["passive_apr%"] > 5).sum()
    dir_winners = (df["dir_apr%"] > 5).sum()
    ext_winners = (df["ext_apr%"] > 5).sum()
    print(f"  Passive long >5% APR: {pl_winners}/{len(df)}")
    print(f"  Direction-follow >5% APR: {dir_winners}/{len(df)}")
    print(f"  Extreme-short >5% APR: {ext_winners}/{len(df)}")
    days = (pd.Timestamp(end, tz="UTC") - pd.Timestamp(start, tz="UTC")).days
    funding_apr_avg = df["passive_funding%"].mean() * (365 / days)
    funding_apr_median = df["passive_funding%"].median() * (365 / days)
    print(f"  Period {days}d. Avg passive-funding APR: {funding_apr_avg:.2f}% / Median: {funding_apr_median:.2f}%")
    print(f"  Median direction-follow APR: {df['dir_apr%'].median():.2f}%")
    print(f"  Median direction-follow FUNDING-only APR: "
          f"{(df['dir_funding%'].median() * (365 / days)):.2f}%")
    return df


def main():
    # Bear-leaning (matches our backtest comparator)
    bear_df = run_window("2025-01-15", "2026-04-30", "BEAR-LEANING 480d")
    # Bull-leaning OOS
    bull_df = run_window("2024-01-01", "2025-01-14", "BULL-LEANING 379d")
    # Multi-year sanity
    full_df = run_window("2022-01-01", "2026-04-30", "FULL 4y+")

    print("\n=== FINAL VERDICT ===")
    print("Pure funding carry alpha (passive-long funding component, NOT including price):")
    for label, df in [("bear 480d", bear_df), ("bull 379d", bull_df), ("full 4y", full_df)]:
        if df is None or df.empty:
            continue
        med = df["passive_funding%"].median()
        days = 480 if "480" in label else 379 if "379" in label else 1581
        print(f"  {label}: median {med:.2f}% over period -> {med * 365 / days:.2f}% APR")
    print("\nDirection-follow funding-only (per-period |rate|):")
    for label, df in [("bear 480d", bear_df), ("bull 379d", bull_df), ("full 4y", full_df)]:
        if df is None or df.empty:
            continue
        med = df["dir_funding%"].median()
        days = 480 if "480" in label else 379 if "379" in label else 1581
        print(f"  {label}: median {med:.2f}% / {med * 365 / days:.2f}% APR")


if __name__ == "__main__":
    main()
