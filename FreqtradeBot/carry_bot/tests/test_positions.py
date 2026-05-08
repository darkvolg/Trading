"""Unit tests for PositionStore: open/close lifecycle, accrual, persistence."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from carry_bot.positions import Position, PositionStore


def fresh_store():
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    return PositionStore(path), path


def test_insert_and_get():
    store, path = fresh_store()
    try:
        p = Position(
            base="BTC", open_ts_ms=1_000_000, spot_qty=0.01, perp_qty=0.01,
            entry_spot_px=80_000, entry_perp_px=79_990, open_fee_quote=0.16,
        )
        store.insert(p)
        got = store.get("BTC")
        assert got is not None
        assert got.base == "BTC"
        assert got.spot_qty == 0.01
        assert got.entry_spot_px == 80_000
        assert got.last_update_ts_ms == 1_000_000  # auto-populated from open_ts_ms
    finally:
        store.close_db()
        os.unlink(path)


def test_accrue_funding():
    store, path = fresh_store()
    try:
        store.insert(Position(
            base="ETH", open_ts_ms=1_000_000, spot_qty=1.0, perp_qty=1.0,
            entry_spot_px=2_300, entry_perp_px=2_299, open_fee_quote=0.46,
        ))
        store.accrue_funding("ETH", 0.5, 1_001_000)
        store.accrue_funding("ETH", 0.3, 1_002_000)
        p = store.get("ETH")
        assert abs(p.funding_received_quote - 0.8) < 1e-9
        assert p.last_update_ts_ms == 1_002_000
    finally:
        store.close_db()
        os.unlink(path)


def test_close_computes_pnl():
    store, path = fresh_store()
    try:
        store.insert(Position(
            base="DOGE", open_ts_ms=1_000_000, spot_qty=1000.0, perp_qty=1000.0,
            entry_spot_px=0.10, entry_perp_px=0.10, open_fee_quote=0.16,
            funding_received_quote=0.5,
        ))
        # Price moved up 5% on both legs (ideal delta-neutral case): PnL = 0
        # spot: (0.105-0.10)*1000 = +5
        # perp: (0.10-0.105)*1000 = -5
        # net price PnL = 0; net = funding(0.5) - close_fee(0.16) - open_fee(0.16) = 0.18
        store.close("DOGE", 0.105, 0.105, 0.16, 1_005_000)
        agg = store.realized_pnl()
        assert agg["n_closed"] == 1
        assert abs(agg["funding_received"] - 0.5) < 1e-9
        assert abs(agg["fees_paid"] - 0.32) < 1e-9
        assert abs(agg["net_pnl"] - 0.18) < 1e-9
        # Position should be removed from open table
        assert store.get("DOGE") is None
    finally:
        store.close_db()
        os.unlink(path)


def test_signal_state_persistence():
    store, path = fresh_store()
    try:
        state = {
            "BTC": {"in_position": False, "bars_above": 2, "bars_below": 0,
                    "last_rate": 0.0001, "last_observed_ms": 1_000_000},
            "ETH": {"in_position": True, "bars_above": 0, "bars_below": 1,
                    "last_rate": -0.00002, "last_observed_ms": 1_000_000},
        }
        store.save_signal_state(state)
        loaded = store.load_signal_state()
        assert loaded["BTC"]["bars_above"] == 2
        assert loaded["ETH"]["in_position"] is True
        assert abs(loaded["ETH"]["last_rate"] + 0.00002) < 1e-9
    finally:
        store.close_db()
        os.unlink(path)


def test_funding_history_dedup():
    store, path = fresh_store()
    try:
        store.record_funding("BTC", 1_000_000, 0.0001)
        store.record_funding("BTC", 1_000_000, 0.0001)  # duplicate, should silently skip
        store.record_funding("BTC", 1_000_001, 0.0002)
        rows = store._conn.execute(
            "SELECT COUNT(*) FROM funding_history WHERE base='BTC'"
        ).fetchone()
        assert rows[0] == 2
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
