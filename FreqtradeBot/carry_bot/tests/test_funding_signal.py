"""Unit tests for funding_signal: persistence rules + slot ranking."""
import sys
import os

# Make sibling package importable when run from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from carry_bot.funding_signal import PairSignal, SignalBook


def test_enter_after_persistence():
    s = PairSignal(base="BTC")
    # First two ticks above threshold: still wait
    assert s.observe(0.0002, 0, 0.0001, -0.00005, 3, 3) == "wait"
    assert s.observe(0.0002, 1, 0.0001, -0.00005, 3, 3) == "wait"
    # Third: enter
    assert s.observe(0.0002, 2, 0.0001, -0.00005, 3, 3) == "enter"


def test_persistence_resets_on_low_tick():
    s = PairSignal(base="BTC")
    s.observe(0.0002, 0, 0.0001, -0.00005, 3, 3)
    s.observe(0.0002, 1, 0.0001, -0.00005, 3, 3)
    # Drop below threshold
    s.observe(0.00005, 2, 0.0001, -0.00005, 3, 3)
    # Counter reset → next two highs not yet enough
    assert s.observe(0.0002, 3, 0.0001, -0.00005, 3, 3) == "wait"
    assert s.observe(0.0002, 4, 0.0001, -0.00005, 3, 3) == "wait"
    assert s.observe(0.0002, 5, 0.0001, -0.00005, 3, 3) == "enter"


def test_exit_after_persistence():
    s = PairSignal(base="ETH")
    s.in_position = True
    assert s.observe(-0.0001, 0, 0.0001, -0.00005, 3, 3) == "hold"
    assert s.observe(-0.0001, 1, 0.0001, -0.00005, 3, 3) == "hold"
    assert s.observe(-0.0001, 2, 0.0001, -0.00005, 3, 3) == "exit"


def test_hold_when_funding_neutral():
    s = PairSignal(base="ETH")
    s.in_position = True
    # Funding hovering at zero — neither below exit threshold nor strongly positive
    for i in range(5):
        v = s.observe(0.00001, i, 0.0001, -0.00005, 3, 3)
        assert v == "hold", f"tick {i} expected hold, got {v}"


def test_signalbook_ranking():
    book = SignalBook(whitelist=("BTC", "ETH", "SOL"))
    # Feed ETH the highest mean of last 3
    for i, (b, rate) in enumerate([
        ("BTC", 0.0001), ("ETH", 0.0003), ("SOL", 0.0002),
        ("BTC", 0.0001), ("ETH", 0.0003), ("SOL", 0.0002),
        ("BTC", 0.0001), ("ETH", 0.0003), ("SOL", 0.0002),
    ]):
        book.observe(b, rate, i, 0.0001, -0.00005, 3, 3)
    ranking = book.rank_by_recent_rate(periods=3)
    assert [b for b, _ in ranking] == ["ETH", "SOL", "BTC"]


def test_signalbook_serialize_roundtrip():
    book1 = SignalBook(whitelist=("BTC", "ETH"))
    book1.observe("BTC", 0.0002, 0, 0.0001, -0.00005, 3, 3)
    book1.observe("BTC", 0.0002, 1, 0.0001, -0.00005, 3, 3)
    state = book1.serialize()

    book2 = SignalBook(whitelist=("BTC", "ETH"))
    book2.restore(state)
    assert book2.signal("BTC").bars_above == 2
    assert book2.signal("BTC").last_rate == 0.0002


def test_mark_opened_resets_counters():
    s = PairSignal(base="BTC")
    s.bars_above = 5
    s.mark_opened()
    assert s.in_position
    assert s.bars_above == 0
    assert s.bars_below == 0


if __name__ == "__main__":
    # Run all tests when invoked directly (no pytest dep).
    import inspect
    g = globals()
    for name, fn in list(g.items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"PASS  {name}")
            except AssertionError as e:
                print(f"FAIL  {name}: {e}")
                raise
