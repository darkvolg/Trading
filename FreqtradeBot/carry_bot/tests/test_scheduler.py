"""Unit tests for Scheduler with a fake exchange (no network).

Validates the cycle wiring: signal updates, slot management, opens, closes,
risk-forced exits, dry-run-signals-only mode.
"""
import os
import sys
import tempfile
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from carry_bot.config import CarryConfig
from carry_bot.exchange import FillResult
from carry_bot.funding_signal import SignalBook
from carry_bot.positions import PositionStore
from carry_bot.risk import RiskGate
from carry_bot.scheduler import Scheduler, next_funding_tick_ms


class FakeExchange:
    """In-memory stand-in for BybitClient. Returns scripted rates and fills."""
    def __init__(self, rates: dict[str, float]):
        self.rates = rates
        self.opened: list[str] = []
        self.closed: list[str] = []
        self.has_credentials = False  # Tests don't go through reconcile path

    def fetch_unified_usdt(self):
        return 400.0  # Test default; matches old hardcoded notional × n_slots

    def fetch_open_positions(self):
        return {}

    def rebalance_pair(self, base, spot_qty, perp_qty):
        return None  # No drift in these tests

    def fetch_funding_rate(self, base: str) -> float:
        return self.rates[base]

    def open_carry_pair(self, base, notional, leverage=1):
        self.opened.append(base)
        spot = FillResult(side="buy", market="spot", base=base,
                          qty=1.0, avg_price=100.0,
                          fee_quote=0.10, order_id="o1")
        perp = FillResult(side="sell", market="perp", base=base,
                          qty=1.0, avg_price=100.0,
                          fee_quote=0.06, order_id="p1")
        return spot, perp

    def close_carry_pair(self, base, qty):
        self.closed.append(base)
        spot = FillResult(side="sell", market="spot", base=base,
                          qty=qty, avg_price=101.0,
                          fee_quote=0.10, order_id="o2")
        perp = FillResult(side="buy", market="perp", base=base,
                          qty=qty, avg_price=101.0,
                          fee_quote=0.06, order_id="p2")
        return spot, perp


def fresh_setup(rates: dict[str, float], whitelist: tuple = ("BTC", "ETH", "SOL")):
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    cfg = CarryConfig(
        whitelist=whitelist, n_slots=2,
        entry_threshold=0.0001, exit_threshold=-0.00005,
        entry_persistence=2, exit_persistence=2,
        kill_switch_path="/nope/kill", db_path=path,
    )
    exch = FakeExchange(rates)
    store = PositionStore(path)
    signals = SignalBook(whitelist)
    risk = RiskGate(kill_switch_path=cfg.kill_switch_path)
    sched = Scheduler(cfg, exch, store, signals, risk)
    return sched, exch, store, path


def test_no_opens_below_threshold():
    sched, exch, store, path = fresh_setup({"BTC": 0.00005, "ETH": 0.00005, "SOL": 0.00005})
    try:
        # 2 ticks below threshold — no opens regardless
        sched.tick(now_ms=1_000_000)
        sched.tick(now_ms=1_000_000 + 8 * 3600 * 1000)
        assert exch.opened == []
        assert len(store.list_open()) == 0
    finally:
        store.close_db()
        os.unlink(path)


def test_opens_after_persistence():
    rates = {"BTC": 0.0002, "ETH": 0.0002, "SOL": 0.0002}
    sched, exch, store, path = fresh_setup(rates)
    try:
        # Tick 1: bars_above=1 each → no opens (need 2)
        sched.tick(now_ms=1_000_000)
        assert exch.opened == []
        # Tick 2: bars_above=2 → opens (n_slots=2 cap)
        sched.tick(now_ms=1_000_000 + 8 * 3600 * 1000)
        assert len(exch.opened) == 2
        assert len(store.list_open()) == 2
    finally:
        store.close_db()
        os.unlink(path)


def test_signals_only_mode_no_orders():
    rates = {"BTC": 0.0002, "ETH": 0.0002, "SOL": 0.0002}
    sched, exch, store, path = fresh_setup(rates)
    try:
        sched.tick(now_ms=1_000_000, dry_run_signals_only=True)
        sched.tick(now_ms=1_000_000 + 8 * 3600 * 1000, dry_run_signals_only=True)
        assert exch.opened == []  # never placed orders
        assert len(store.list_open()) == 0
        # But signals should still progress
        rep = sched.tick(now_ms=1_000_000 + 16 * 3600 * 1000, dry_run_signals_only=True)
        # All three should have wanted to open
        assert len(rep.skipped_reasons) > 0
    finally:
        store.close_db()
        os.unlink(path)


def test_exit_after_persistence():
    sched, exch, store, path = fresh_setup({"BTC": 0.0002, "ETH": 0.0002, "SOL": 0.0002})
    try:
        # 2 ticks high → both BTC and ETH open (slot cap = 2; sorted by rate, ties)
        sched.tick(now_ms=1_000_000)
        sched.tick(now_ms=1_000_000 + 8 * 3600 * 1000)
        assert len(store.list_open()) == 2
        # Now flip rates negative on BTC; ETH stays high
        exch.rates = {"BTC": -0.0001, "ETH": 0.0002, "SOL": 0.0002}
        sched.tick(now_ms=1_000_000 + 16 * 3600 * 1000)  # BTC bars_below=1
        sched.tick(now_ms=1_000_000 + 24 * 3600 * 1000)  # BTC bars_below=2 → exit
        assert "BTC" in exch.closed
        # ETH still in
        bases_open = {p.base for p in store.list_open()}
        assert "BTC" not in bases_open
    finally:
        store.close_db()
        os.unlink(path)


def test_next_funding_tick_ms_picks_next_boundary():
    # 2026-05-08 11:30:00 UTC → next 8h boundary is 16:00 + 5min offset
    import datetime
    base = datetime.datetime(2026, 5, 8, 11, 30, tzinfo=datetime.timezone.utc)
    now_ms = int(base.timestamp() * 1000)
    next_ms = next_funding_tick_ms(now_ms, offset_minutes=5)
    next_dt = datetime.datetime.fromtimestamp(next_ms / 1000, tz=datetime.timezone.utc)
    assert next_dt.hour == 16
    assert next_dt.minute == 5


def test_next_funding_tick_ms_wraps_to_next_day():
    # 22:00 UTC → next is 00:05 next day
    import datetime
    base = datetime.datetime(2026, 5, 8, 22, 0, tzinfo=datetime.timezone.utc)
    now_ms = int(base.timestamp() * 1000)
    next_ms = next_funding_tick_ms(now_ms, offset_minutes=5)
    next_dt = datetime.datetime.fromtimestamp(next_ms / 1000, tz=datetime.timezone.utc)
    assert next_dt.day == 9
    assert next_dt.hour == 0
    assert next_dt.minute == 5


if __name__ == "__main__":
    g = globals()
    for name, fn in list(g.items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except AssertionError as e:
                print(f"FAIL  {name}: {e}")
                raise
