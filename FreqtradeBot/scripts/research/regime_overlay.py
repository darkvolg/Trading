"""Regime-overlay analysis for ensemble validation.

Question: do V6A trade outcomes cluster by BTC regime (chop/bear vs bull),
and do SuperTrend backtest outcomes cluster the opposite way?
If yes -> regime-gated ensemble has alpha worth building.
If no  -> ensemble thesis fails, pick different direction.

Run on senko:
    source /opt/freqtrade/venv/bin/activate
    python3 /tmp/regime_overlay.py
"""
import sqlite3
import pandas as pd
import numpy as np
import zipfile
import json
import sys
from pathlib import Path

BTC = "/opt/freqtrade/user_data/data/bybit/futures/BTC_USDT_USDT-1d-futures.feather"
V6A_DB = "/opt/freqtrade/tradesv3.dryrun.sqlite"
ST_BT = "/opt/freqtrade/user_data/backtest_results/backtest-result-2026-05-08_10-16-15.zip"
V6A_BT = "/opt/freqtrade/user_data/backtest_results/backtest-result-2026-05-08_10-17-25.zip"

SMA_PERIOD = 200
ADX_PERIOD = 14
ADX_TREND = 25  # > 25 = trending; < 20 = chop


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Wilder ADX without external deps."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    tr = pd.concat(
        [(high - low), (high - close.shift()).abs(), (low - close.shift()).abs()],
        axis=1,
    ).max(axis=1)
    plus_dm = (high.diff()).where((high.diff() > low.shift().sub(low)) & (high.diff() > 0), 0.0)
    minus_dm = (low.shift() - low).where((low.shift().sub(low) > high.diff()) & (low.shift().sub(low) > 0), 0.0)
    atr = tr.ewm(alpha=1 / period, adjust=False).mean()
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False).mean() / atr
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di) * 100
    return dx.ewm(alpha=1 / period, adjust=False).mean()


def classify_regime(btc: pd.DataFrame) -> pd.DataFrame:
    """Add 'regime' column: bull / bear / chop."""
    btc = btc.copy()
    btc["sma200"] = btc["close"].rolling(SMA_PERIOD).mean()
    btc["adx"] = adx(btc, ADX_PERIOD)
    above_sma = btc["close"] > btc["sma200"]
    trending = btc["adx"] > ADX_TREND
    chopping = btc["adx"] < 20

    regime = pd.Series("chop", index=btc.index)
    regime = regime.where(~(trending & above_sma), "bull")
    regime = regime.where(~(trending & ~above_sma), "bear")
    regime = regime.where(~chopping, "chop")
    btc["regime"] = regime
    return btc[["date", "regime", "close", "sma200", "adx"]]


def load_v6a_trades(db_path: str) -> pd.DataFrame:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query(
        "SELECT pair, open_date, close_date, close_profit, close_profit_abs, exit_reason "
        "FROM trades WHERE close_date IS NOT NULL",
        conn,
    )
    conn.close()
    df["close_date"] = pd.to_datetime(df["close_date"], utc=True)
    df["open_date"] = pd.to_datetime(df["open_date"], utc=True)
    df["date"] = df["open_date"].dt.normalize()
    return df


def load_st_trades(zip_path: str) -> pd.DataFrame:
    """Pull trades json out of freqtrade backtest zip."""
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        cand = [n for n in names if n.endswith(".json") and "meta" not in n]
        if not cand:
            return pd.DataFrame()
        with zf.open(cand[0]) as f:
            data = json.load(f)
    # freqtrade backtest result: data['strategy'][<name>]['trades']
    strats = data.get("strategy", {})
    if not strats:
        return pd.DataFrame()
    trades = list(strats.values())[0].get("trades", [])
    if not trades:
        return pd.DataFrame()
    df = pd.DataFrame(trades)
    if "close_date" not in df:
        return pd.DataFrame()
    df["close_date"] = pd.to_datetime(df["close_date"], utc=True)
    df["open_date"] = pd.to_datetime(df["open_date"], utc=True)
    df["date"] = df["open_date"].dt.normalize()  # entry-date classification
    df["close_profit"] = df["profit_ratio"]
    df["close_profit_abs"] = df["profit_abs"]
    return df[["pair", "open_date", "close_date", "date", "close_profit", "close_profit_abs", "exit_reason"]]


def per_regime_summary(trades: pd.DataFrame, regimes: pd.DataFrame, label: str) -> None:
    if trades.empty:
        print(f"\n=== {label} === NO TRADES")
        return
    regimes_d = regimes.copy()
    regimes_d["date"] = pd.to_datetime(regimes_d["date"], utc=True).dt.normalize()
    merged = trades.merge(regimes_d[["date", "regime"]], on="date", how="left")
    print(f"\n=== {label} ===")
    print(f"Period: {merged['close_date'].min().date()} -> {merged['close_date'].max().date()}")
    print(f"Total trades: {len(merged)}, missing regime: {merged['regime'].isna().sum()}")
    print()
    grp = merged.groupby("regime").agg(
        n=("close_profit", "size"),
        avg_pct=("close_profit", lambda s: s.mean() * 100),
        sum_usd=("close_profit_abs", "sum"),
        wr=("close_profit", lambda s: (s > 0).mean() * 100),
    )
    grp = grp.reindex(["bull", "chop", "bear"]).round(2)
    print(grp.to_string())
    print()
    # also distribution of regime days for context
    rd = regimes_d[regimes_d["date"] >= merged["close_date"].min().normalize()].copy()
    rd_max = merged["close_date"].max().normalize()
    rd = rd[rd["date"] <= rd_max]
    days_dist = rd["regime"].value_counts().reindex(["bull", "chop", "bear"]).fillna(0).astype(int)
    total_days = days_dist.sum()
    print(f"Regime distribution over period ({total_days} days):")
    for r in ["bull", "chop", "bear"]:
        pct = (days_dist[r] / total_days * 100) if total_days else 0
        print(f"  {r:5}: {days_dist[r]:4d} days ({pct:5.1f}%)")


def main() -> int:
    btc = pd.read_feather(BTC)
    btc["date"] = pd.to_datetime(btc["date"], utc=True).dt.normalize()
    regimes = classify_regime(btc)
    print(f"Loaded BTC: {len(btc)} daily candles, "
          f"{regimes['date'].min().date()} -> {regimes['date'].max().date()}")
    print(f"All-time regime distribution:")
    for r in ["bull", "chop", "bear"]:
        n = (regimes["regime"] == r).sum()
        pct = n / len(regimes) * 100
        print(f"  {r:5}: {n:4d} days ({pct:5.1f}%)")

    v6a_live = load_v6a_trades(V6A_DB)
    per_regime_summary(v6a_live, regimes, "V6A LIVE (entry-date)")

    v6a_bt = load_st_trades(V6A_BT)
    per_regime_summary(v6a_bt, regimes, "V6A BACKTEST 480d (entry-date)")

    st = load_st_trades(ST_BT)
    per_regime_summary(st, regimes, "SuperTrend BACKTEST 480d (entry-date)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
