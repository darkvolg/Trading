"""Unit tests for RiskGate: kill switch, stale force-close, daily PnL alarm."""
import os
import sys
import tempfile
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from carry_bot.risk import RiskGate


@dataclass
class FakePos:
    base: str
    open_ts_ms: int


def test_kill_switch_active():
    fd, path = tempfile.mkstemp()
    os.close(fd)  # file exists
    try:
        gate = RiskGate(kill_switch_path=path)
        positions = [FakePos("BTC", 0), FakePos("ETH", 0)]
        v = gate.evaluate(positions, {"BTC": 0.0001, "ETH": 0.0002}, now_ms=10_000)
        assert v.pause_new_entries is True
        assert set(v.force_close_pairs) == {"BTC", "ETH"}
        assert any("kill-switch" in m for m in v.alarm_messages)
    finally:
        os.unlink(path)


def test_kill_switch_inactive():
    gate = RiskGate(kill_switch_path="/nonexistent/path/nope")
    v = gate.evaluate([FakePos("BTC", 0)], {"BTC": 0.0001}, now_ms=10_000)
    assert v.pause_new_entries is False
    assert v.force_close_pairs == []


def test_stale_force_close():
    gate = RiskGate(kill_switch_path="/nope", stale_force_close_hours=24)
    now = 1_000_000_000
    old_open = now - 25 * 3600 * 1000  # 25h ago, exceeds 24h threshold
    fresh_open = now - 1 * 3600 * 1000  # 1h ago
    pos_old_negative = FakePos("BTC", old_open)
    pos_old_positive = FakePos("ETH", old_open)
    pos_fresh = FakePos("SOL", fresh_open)
    rates = {"BTC": -0.0001, "ETH": 0.0001, "SOL": -0.001}
    v = gate.evaluate([pos_old_negative, pos_old_positive, pos_fresh],
                      rates, now_ms=now)
    # Only BTC should be force-closed (old + negative funding)
    assert v.force_close_pairs == ["BTC"]


def test_daily_pnl_alarm_fires():
    gate = RiskGate(kill_switch_path="/nope", daily_loss_alarm_pct=0.01)
    v = gate.evaluate(
        positions=[],
        last_rates={},
        now_ms=10_000,
        capital_quote=1000.0,
        realized_24h=-15.0,  # -1.5% of capital, beyond 1% threshold
        unrealized=0.0,
    )
    assert any("daily-pnl-alarm" in m for m in v.alarm_messages)


def test_daily_pnl_alarm_silent_within_threshold():
    gate = RiskGate(kill_switch_path="/nope", daily_loss_alarm_pct=0.01)
    v = gate.evaluate(
        positions=[],
        last_rates={},
        now_ms=10_000,
        capital_quote=1000.0,
        realized_24h=-5.0,  # -0.5%, within threshold
        unrealized=0.0,
    )
    assert all("daily-pnl-alarm" not in m for m in v.alarm_messages)


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
