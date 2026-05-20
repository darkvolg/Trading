"""Tests for Phase 2.5.3 safety: retry, rebalance, liquidation monitor, reconcile."""
import os
import sys
import tempfile
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from carry_bot.config import CarryConfig
from carry_bot.exchange import FillResult, with_retry
from carry_bot.funding_signal import SignalBook
from carry_bot.positions import Position, PositionStore
from carry_bot.risk import RiskGate
from carry_bot.scheduler import Scheduler


# ---------- Retry ----------

class FakeNetworkError(Exception):
    pass


class FakeRateLimitExceeded(Exception):
    pass


def test_retry_succeeds_after_transient():
    calls = {"n": 0}

    @with_retry(retries=3, base_delay=0.001)
    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise FakeNetworkError("connection reset")
        return "ok"

    assert flaky() == "ok"
    assert calls["n"] == 3


def test_retry_gives_up_after_max():
    calls = {"n": 0}

    @with_retry(retries=2, base_delay=0.001)
    def always_fails():
        calls["n"] += 1
        raise FakeNetworkError("nope")

    try:
        always_fails()
        raise AssertionError("expected FakeNetworkError")
    except FakeNetworkError:
        pass
    assert calls["n"] == 3  # initial + 2 retries


def test_retry_does_not_retry_on_unknown():
    calls = {"n": 0}

    @with_retry(retries=3, base_delay=0.001)
    def bad_input():
        calls["n"] += 1
        raise ValueError("logic error, do not retry")

    try:
        bad_input()
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    assert calls["n"] == 1


def test_retry_handles_rate_limit():
    calls = {"n": 0}

    @with_retry(retries=2, base_delay=0.001)
    def rate_limited():
        calls["n"] += 1
        if calls["n"] < 2:
            raise FakeRateLimitExceeded("429")
        return "ok"

    assert rate_limited() == "ok"


# ---------- Liquidation monitor ----------

def test_liquidation_alarm_fires_when_close():
    gate = RiskGate(kill_switch_path="/nope", liq_alarm_distance_pct=0.10)
    # Short with mark=100, liq=105 → distance = 5% — alarm
    ex_pos = {"BTC": {"side": "short", "mark_price": 100, "liquidation_price": 105}}
    alarms = gate.check_liquidation_distance(ex_pos)
    assert len(alarms) == 1
    assert "BTC" in alarms[0]
    assert "5.00%" in alarms[0] or "5.0" in alarms[0]


def test_liquidation_alarm_silent_when_far():
    gate = RiskGate(kill_switch_path="/nope", liq_alarm_distance_pct=0.10)
    # Short with mark=100, liq=200 → distance = 100% — silent
    ex_pos = {"BTC": {"side": "short", "mark_price": 100, "liquidation_price": 200}}
    alarms = gate.check_liquidation_distance(ex_pos)
    assert alarms == []


def test_liquidation_alarm_handles_long_side():
    gate = RiskGate(kill_switch_path="/nope", liq_alarm_distance_pct=0.10)
    # Long with mark=100, liq=92 → distance = 8% — alarm
    ex_pos = {"ETH": {"side": "long", "mark_price": 100, "liquidation_price": 92}}
    alarms = gate.check_liquidation_distance(ex_pos)
    assert len(alarms) == 1


def test_liquidation_alarm_skips_zero_liq_price():
    gate = RiskGate(kill_switch_path="/nope")
    ex_pos = {"BTC": {"side": "short", "mark_price": 100, "liquidation_price": 0}}
    alarms = gate.check_liquidation_distance(ex_pos)
    assert alarms == []


# ---------- Rebalance + reconcile (via Scheduler) ----------

class RecordingExchange:
    """Fake exchange that records all calls for assertions."""
    def __init__(self, rates=None, ex_positions=None):
        self.rates = rates or {}
        self.ex_positions = ex_positions or {}
        self.has_credentials = True
        self.opened = []
        self.closed = []
        self.rebalanced = []

    def fetch_unified_usdt(self):
        return 400.0

    def fetch_funding_rate(self, base):
        return self.rates[base]

    def fetch_open_positions(self):
        return self.ex_positions

    def open_carry_pair(self, base, notional, leverage=1):
        self.opened.append(base)
        return (
            FillResult("buy", "spot", base, 1.0, 100, 0.10, "o"),
            FillResult("sell", "perp", base, 1.0, 100, 0.06, "p"),
        )

    def close_carry_pair(self, base, qty):
        self.closed.append(base)
        return (
            FillResult("sell", "spot", base, qty, 101, 0.10, "o"),
            FillResult("buy", "perp", base, qty, 101, 0.06, "p"),
        )

    def rebalance_pair(self, base, spot_qty, perp_qty):
        self.rebalanced.append((base, spot_qty, perp_qty))
        # Simulate topping up the smaller leg
        if spot_qty > perp_qty:
            return FillResult("sell", "perp", base, spot_qty - perp_qty, 100, 0.05, "rb")
        return FillResult("buy", "spot", base, perp_qty - spot_qty, 100, 0.05, "rb")


def fresh_scheduler(rates, ex_positions=None):
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    cfg = CarryConfig(
        whitelist=("BTC", "ETH"), n_slots=2,
        entry_threshold=0.0001, exit_threshold=-0.00005,
        entry_persistence=2, exit_persistence=2,
        delta_drift_pct=0.005,  # 0.5%
        kill_switch_path="/nope", db_path=path,
    )
    exch = RecordingExchange(rates, ex_positions or {})
    store = PositionStore(path)
    signals = SignalBook(("BTC", "ETH"))
    risk = RiskGate(kill_switch_path="/nope")
    return Scheduler(cfg, exch, store, signals, risk), exch, store, path


def test_rebalance_fires_when_drift_above_threshold():
    sched, exch, store, path = fresh_scheduler({"BTC": 0.0002, "ETH": 0.0002})
    try:
        # Pre-insert a position with 1% drift (above 0.5% threshold)
        store.insert(Position(
            base="BTC", open_ts_ms=1_000_000,
            spot_qty=1.00, perp_qty=0.99,  # 1% drift
            entry_spot_px=100, entry_perp_px=100,
            open_fee_quote=0.16,
        ))
        rep = sched.tick(now_ms=1_001_000)
        assert "BTC" in rep.rebalances
        # Position should now have spot_qty == perp_qty
        p = store.get("BTC")
        assert abs(p.spot_qty - p.perp_qty) < 1e-6
    finally:
        store.close_db()
        os.unlink(path)


def test_rebalance_skipped_when_within_threshold():
    sched, exch, store, path = fresh_scheduler({"BTC": 0.0002, "ETH": 0.0002})
    try:
        store.insert(Position(
            base="BTC", open_ts_ms=1_000_000,
            spot_qty=1.000, perp_qty=0.998,  # 0.2% drift
            entry_spot_px=100, entry_perp_px=100,
            open_fee_quote=0.16,
        ))
        rep = sched.tick(now_ms=1_001_000)
        assert rep.rebalances == []
    finally:
        store.close_db()
        os.unlink(path)


def test_reconcile_alarms_on_missing_exchange_position():
    rates = {"BTC": 0.0002, "ETH": 0.0002}
    # We have BTC in local book, exchange reports nothing
    sched, exch, store, path = fresh_scheduler(rates, ex_positions={})
    try:
        store.insert(Position(
            base="BTC", open_ts_ms=1_000_000,
            spot_qty=1.0, perp_qty=1.0,
            entry_spot_px=100, entry_perp_px=100,
            open_fee_quote=0.16,
        ))
        rep = sched.tick(now_ms=1_001_000)
        assert any("local book but no exchange" in a for a in rep.alarms)
    finally:
        store.close_db()
        os.unlink(path)


def test_reconcile_alarms_on_unknown_exchange_position():
    rates = {"BTC": 0.0002, "ETH": 0.0002}
    # Exchange reports position bot didn't open
    ex_pos = {"DOGE": {"side": "short", "qty": 100,
                       "mark_price": 0.1, "liquidation_price": 0.5}}
    sched, exch, store, path = fresh_scheduler(rates, ex_positions=ex_pos)
    try:
        rep = sched.tick(now_ms=1_001_000)
        assert any("manual position" in a for a in rep.alarms)
    finally:
        store.close_db()
        os.unlink(path)


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
