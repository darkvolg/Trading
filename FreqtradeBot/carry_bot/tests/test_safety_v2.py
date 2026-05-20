"""P0 fix tests: capital-aware sizing, idempotency, mainnet guard."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from carry_bot.config import CarryConfig
from carry_bot.exchange import FillResult
from carry_bot.funding_signal import SignalBook
from carry_bot.main import main as main_entry
from carry_bot.positions import Position, PositionStore
from carry_bot.risk import RiskGate
from carry_bot.scheduler import Scheduler


class BalanceExchange:
    """Fake exchange exposing fetch_unified_usdt for sizing tests."""
    def __init__(self, rates, balance, fail_balance=False):
        self.rates = rates
        self.balance = balance
        self.fail_balance = fail_balance
        self.has_credentials = True
        self.opened = []
        self.last_notional = None

    def fetch_funding_rate(self, base):
        return self.rates[base]

    def fetch_open_positions(self):
        return {}

    def fetch_unified_usdt(self):
        if self.fail_balance:
            raise RuntimeError("network down")
        return self.balance

    def rebalance_pair(self, base, spot_qty, perp_qty):
        return None

    def open_carry_pair(self, base, notional, leverage=1):
        self.last_notional = notional
        self.opened.append(base)
        # Use realistic price; qty derived from notional
        px = 100.0
        qty = notional / px
        return (
            FillResult("buy", "spot", base, qty, px, 0.10, "o"),
            FillResult("sell", "perp", base, qty, px, 0.06, "p"),
        )

    def close_carry_pair(self, base, qty):
        return (
            FillResult("sell", "spot", base, qty, 100, 0.10, "o"),
            FillResult("buy", "perp", base, qty, 100, 0.06, "p"),
        )


def _sched(rates, balance=400.0, fail=False, **cfg_overrides):
    fd, path = tempfile.mkstemp(suffix=".sqlite")
    os.close(fd)
    cfg_kwargs = dict(
        whitelist=("BTC", "ETH"), n_slots=2,
        entry_threshold=0.0001, exit_threshold=-0.00005,
        entry_persistence=2, exit_persistence=2,
        position_size_pct=0.25,
        fallback_notional_usdt=100.0,
        small_capital_floor_usdt=25.0,
        kill_switch_path="/nope", db_path=path,
    )
    cfg_kwargs.update(cfg_overrides)
    cfg = CarryConfig(**cfg_kwargs)
    exch = BalanceExchange(rates, balance, fail_balance=fail)
    store = PositionStore(path)
    signals = SignalBook(cfg.whitelist)
    risk = RiskGate(kill_switch_path="/nope")
    return Scheduler(cfg, exch, store, signals, risk), exch, store, path


# ---------- capital-aware sizing ----------

def test_notional_scales_with_balance():
    # 400 USDT × 25% = 100 per slot
    sched, exch, store, path = _sched({"BTC": 0.0002, "ETH": 0.0002}, balance=400.0)
    try:
        sched.tick(now_ms=1_000_000)
        sched.tick(now_ms=1_000_000 + 8 * 3600 * 1000)
        assert exch.last_notional == 100.0, f"expected 100, got {exch.last_notional}"
    finally:
        store.close_db()
        os.unlink(path)


def test_notional_scales_with_larger_balance():
    # 4000 USDT × 25% = 1000 per slot
    sched, exch, store, path = _sched({"BTC": 0.0002, "ETH": 0.0002}, balance=4000.0)
    try:
        sched.tick(now_ms=1_000_000)
        sched.tick(now_ms=1_000_000 + 8 * 3600 * 1000)
        assert exch.last_notional == 1000.0
    finally:
        store.close_db()
        os.unlink(path)


def test_refuses_open_when_below_floor():
    # 80 USDT × 25% = 20 → below 25 floor → no opens
    sched, exch, store, path = _sched({"BTC": 0.0002, "ETH": 0.0002}, balance=80.0)
    try:
        sched.tick(now_ms=1_000_000)
        sched.tick(now_ms=1_000_000 + 8 * 3600 * 1000)
        assert exch.opened == []
        assert len(store.list_open()) == 0
    finally:
        store.close_db()
        os.unlink(path)


def test_fallback_notional_on_balance_failure():
    sched, exch, store, path = _sched({"BTC": 0.0002, "ETH": 0.0002}, fail=True)
    try:
        sched.tick(now_ms=1_000_000)
        sched.tick(now_ms=1_000_000 + 8 * 3600 * 1000)
        assert exch.last_notional == 100.0  # fallback default
    finally:
        store.close_db()
        os.unlink(path)


# ---------- idempotency ----------

def test_open_skipped_if_position_in_db():
    sched, exch, store, path = _sched({"BTC": 0.0002, "ETH": 0.0002}, balance=400.0)
    try:
        # Pre-insert position; simulates crash-recovery state
        store.insert(Position(
            base="BTC", open_ts_ms=1_000_000,
            spot_qty=1.0, perp_qty=1.0,
            entry_spot_px=100, entry_perp_px=100,
            open_fee_quote=0.16,
        ))
        # Force signal to "enter" verdict by direct manipulation
        sched.tick(now_ms=1_000_000)
        sched.tick(now_ms=1_000_000 + 8 * 3600 * 1000)
        # ETH should be opened; BTC must NOT be re-opened despite signal
        assert "BTC" not in exch.opened or exch.opened.count("BTC") == 0
        # Only one BTC row in DB
        btc_rows = [p for p in store.list_open() if p.base == "BTC"]
        assert len(btc_rows) == 1
    finally:
        store.close_db()
        os.unlink(path)


# ---------- mainnet safety gate ----------

def test_mainnet_refuses_without_confirm():
    rc = main_entry(["--once", "--mainnet"])
    assert rc == 2, f"expected exit 2, got {rc}"


def test_mainnet_refuses_with_empty_keys(monkeypatch=None):
    # Ensure env vars absent
    for k in ("CARRY_API_KEY", "CARRY_API_SECRET"):
        os.environ.pop(k, None)
    rc = main_entry(["--once", "--mainnet", "--confirm-mainnet"])
    assert rc == 2


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
