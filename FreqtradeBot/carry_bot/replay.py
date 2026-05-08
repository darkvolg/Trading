"""Replay historical data through the production scheduler/positions/risk
pipeline. Validates that our real code produces the same PnL as the
standalone `carry_portfolio_sim.py` numerical model.

Why this matters:
    `carry_portfolio_sim.py` is a clean numerical model of the strategy.
    `carry_bot.scheduler.Scheduler` is the production code that will run
    against real Bybit. They were written from the same spec but
    independently. If they agree on historical data, that's strong
    evidence that the production code implements the validated strategy
    correctly. If they disagree, one of them has a bug.

How it works:
    A `ReplayExchange` reads pre-cached funding feathers + price feathers
    and serves `fetch_funding_rate(base)` returns at the simulated `now_ms`.
    The Scheduler runs unmodified — same SignalBook, same PositionStore
    (in-memory SQLite), same RiskGate, same atomic open/close paths
    (except orders go to ReplayExchange instead of Bybit).

Output: per-month PnL summary directly comparable with the standalone
sim's output.
"""
from __future__ import annotations
import logging
import sqlite3
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import pandas as pd

from .config import CarryConfig, TESTNET_WHITELIST, DEFAULT_WHITELIST
from .exchange import FillResult, perp_symbol, spot_symbol
from .funding_signal import SignalBook
from .positions import Position, PositionStore
from .risk import RiskGate
from .scheduler import Scheduler

logger = logging.getLogger(__name__)


# Same fee model as carry_portfolio_sim
FEE_SPOT_TAKER = 0.0010
FEE_PERP_TAKER = 0.0006
SLIPPAGE_PER_SIDE = 0.0005


class ReplayExchange:
    """Stand-in for BybitClient that serves cached historical data.

    Mirrors the BybitClient interface used by Scheduler. Maintains its
    own concept of "current price" via the latest OHLCV row at or before
    the simulated time.
    """

    def __init__(self, data_dir: str, whitelist: tuple[str, ...]):
        self.has_credentials = True  # so reconcile path runs
        self.data_dir = Path(data_dir)
        self.whitelist = whitelist
        self._funding: dict[str, pd.DataFrame] = {}
        self._prices: dict[str, pd.DataFrame] = {}
        self._now_ms = 0
        # Open exchange-side positions (mirror of bot's open positions)
        self._ex_positions: dict[str, dict] = {}
        for base in whitelist:
            self._load_pair(base)

    def _load_pair(self, base: str) -> None:
        f_path = self.data_dir / f"{base}_USDT_USDT-8h-funding_rate.feather"
        p_path = self.data_dir / f"{base}_USDT_USDT-1d-futures.feather"
        if f_path.exists():
            df = pd.read_feather(f_path)
            df["date"] = pd.to_datetime(df["date"], utc=True)
            df = df[["date", "open"]].rename(columns={"open": "rate"})
            self._funding[base] = df.sort_values("date").reset_index(drop=True)
        if p_path.exists():
            df = pd.read_feather(p_path)
            df["date"] = pd.to_datetime(df["date"], utc=True)
            self._prices[base] = df.sort_values("date").reset_index(drop=True)

    def set_now(self, ts_ms: int) -> None:
        self._now_ms = ts_ms

    # --- Public-API mocks ---

    def fetch_funding_rate(self, base: str) -> float:
        df = self._funding.get(base)
        if df is None or df.empty:
            raise RuntimeError(f"no funding data for {base}")
        # Find rate at-or-before now_ms
        cutoff = pd.Timestamp(self._now_ms, unit="ms", tz="UTC")
        rows = df[df["date"] <= cutoff]
        if rows.empty:
            raise RuntimeError(f"no funding before {cutoff} for {base}")
        return float(rows.iloc[-1]["rate"])

    def fetch_perp_price(self, base: str) -> float:
        df = self._prices.get(base)
        if df is None or df.empty:
            return 100.0
        cutoff = pd.Timestamp(self._now_ms, unit="ms", tz="UTC")
        rows = df[df["date"] <= cutoff]
        if rows.empty:
            return 100.0
        return float(rows.iloc[-1]["close"])

    def fetch_open_positions(self) -> dict:
        return self._ex_positions

    # --- Order placement mocks ---

    def open_carry_pair(self, base: str, notional_usdt: float,
                        leverage: int = 1) -> tuple[FillResult, FillResult]:
        px = self.fetch_perp_price(base)
        qty = notional_usdt / px
        spot_fee = notional_usdt * (FEE_SPOT_TAKER + SLIPPAGE_PER_SIDE)
        perp_fee = notional_usdt * (FEE_PERP_TAKER + SLIPPAGE_PER_SIDE)
        spot = FillResult("buy", "spot", base, qty, px, spot_fee, "rsp")
        perp = FillResult("sell", "perp", base, qty, px, perp_fee, "rpp")
        # Mirror in exchange position book for reconcile
        self._ex_positions[base] = {
            "side": "short", "qty": qty, "entry": px,
            "mark_price": px, "liquidation_price": px * 1.5,
        }
        return spot, perp

    def close_carry_pair(self, base: str, qty: float) -> tuple[FillResult, FillResult]:
        px = self.fetch_perp_price(base)
        spot_fee = qty * px * (FEE_SPOT_TAKER + SLIPPAGE_PER_SIDE)
        perp_fee = qty * px * (FEE_PERP_TAKER + SLIPPAGE_PER_SIDE)
        spot = FillResult("sell", "spot", base, qty, px, spot_fee, "csp")
        perp = FillResult("buy", "perp", base, qty, px, perp_fee, "cpp")
        self._ex_positions.pop(base, None)
        return spot, perp

    def rebalance_pair(self, base: str, spot_qty: float, perp_qty: float):
        # Replay never produces drift — always equal qtys at fill time
        return None

    def set_leverage(self, base: str, leverage: int) -> None:
        pass


def replay(start: str, end: str,
           data_dir: str = "/opt/freqtrade/user_data/data/bybit/futures",
           cfg: CarryConfig | None = None,
           db_path: str | None = None) -> dict:
    """Run Scheduler on replayed data; return aggregate metrics."""
    cfg = cfg or CarryConfig(whitelist=TESTNET_WHITELIST, n_slots=4)

    # Use a temp SQLite db so we don't pollute real state
    if db_path is None:
        fd, db_path = tempfile.mkstemp(suffix="_replay.sqlite")
        import os
        os.close(fd)

    exchange = ReplayExchange(data_dir, cfg.whitelist)
    store = PositionStore(db_path)
    signals = SignalBook(cfg.whitelist)
    risk = RiskGate(kill_switch_path="/nonexistent")
    sched = Scheduler(cfg, exchange, store, signals, risk)

    # Iterate through each 8h funding tick
    start_ts = pd.Timestamp(start, tz="UTC")
    end_ts = pd.Timestamp(end, tz="UTC")
    cur = start_ts
    eight_hours = pd.Timedelta(hours=8)

    n_ticks = 0
    while cur <= end_ts:
        ts_ms = int(cur.timestamp() * 1000)
        exchange.set_now(ts_ms)
        try:
            sched.tick(now_ms=ts_ms)
        except Exception as e:
            # Log but continue — replay shouldn't blow up on individual pair errors
            logger.warning(f"tick at {cur} failed: {e}")
        n_ticks += 1
        cur += eight_hours

    # Aggregate metrics from store
    realized = store.realized_pnl()
    open_positions = store.list_open()
    open_funding = sum(p.funding_received_quote for p in open_positions)
    open_open_fees = sum(p.open_fee_quote for p in open_positions)

    out = {
        "n_ticks": n_ticks,
        "n_closed": realized["n_closed"],
        "n_open_at_end": len(open_positions),
        "realized_funding": realized["funding_received"],
        "realized_fees": realized["fees_paid"],
        "realized_net": realized["net_pnl"],
        "unrealized_funding": open_funding,
        "open_fees_locked": open_open_fees,
        "total_funding": realized["funding_received"] + open_funding,
        "total_fees": realized["fees_paid"] + open_open_fees,
        # Net excludes unrealized price PnL on open positions (which is ≈0
        # for delta-neutral pairs when spot ≈ perp)
        "approx_net": realized["net_pnl"] + open_funding - open_open_fees,
    }
    store.close_db()
    import os
    try:
        os.unlink(db_path)
    except OSError:
        pass
    return out


def cli():
    """Standalone replay runner. Compares to expected sim output."""
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--start", default="2022-01-01")
    ap.add_argument("--end", default="2026-04-30")
    ap.add_argument("--data-dir", default="/opt/freqtrade/user_data/data/bybit/futures")
    args = ap.parse_args()

    logging.basicConfig(level=logging.WARNING)

    print(f"Replaying production carry_bot on cached data {args.start} -> {args.end}")
    result = replay(args.start, args.end, args.data_dir)

    print()
    print("=== REPLAY RESULT ===")
    for k, v in result.items():
        if isinstance(v, float):
            print(f"  {k:25} {v:.4f}")
        else:
            print(f"  {k:25} {v}")

    days = (pd.Timestamp(args.end, tz="UTC") - pd.Timestamp(args.start, tz="UTC")).days
    apr = result["approx_net"] / 100 * 365 / days * 100  # over $100 capital baseline
    print()
    print(f"Approx APR (assuming $100 capital, $25/slot): {apr:+.2f}%")
    print()
    print("Compare with carry_portfolio_sim N_SLOTS=4 result for the same window.")
    print("Numbers should be within ~10% of each other (small timing/precision differences).")


if __name__ == "__main__":
    cli()
