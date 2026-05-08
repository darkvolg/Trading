"""Funding-rate signal: tracks recent rates and emits enter/exit verdicts.

Persistence-based rules (same as `carry_portfolio_sim.py`):
    enter when funding > entry_threshold for entry_persistence consecutive periods
    exit  when funding < exit_threshold  for exit_persistence  consecutive periods

Designed to be fed one funding observation per pair per 8h tick.
Stateful per-pair counters live in this module, persisted via SQLite by
the scheduler.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, field
from typing import Literal


Verdict = Literal["enter", "exit", "hold", "wait"]


@dataclass
class PairSignal:
    """Per-pair signal state. Update via `observe()` once per 8h tick."""
    base: str
    in_position: bool = False
    bars_above: int = 0     # consecutive bars > entry_threshold while flat
    bars_below: int = 0     # consecutive bars < exit_threshold while in position
    last_rate: float | None = None
    last_observed_ms: int = 0
    history: deque = field(default_factory=lambda: deque(maxlen=20))

    def observe(self, rate: float, ts_ms: int,
                entry_threshold: float, exit_threshold: float,
                entry_persistence: int, exit_persistence: int) -> Verdict:
        """Append observation, advance state, return action verdict.

        Returns:
            "enter" — flat → should open
            "exit"  — in position → should close
            "hold"  — in position, keep holding
            "wait"  — flat, signal not strong enough yet
        """
        self.last_rate = rate
        self.last_observed_ms = ts_ms
        self.history.append((ts_ms, rate))

        if not self.in_position:
            if rate > entry_threshold:
                self.bars_above += 1
            else:
                self.bars_above = 0
            self.bars_below = 0
            if self.bars_above >= entry_persistence:
                return "enter"
            return "wait"

        # In position
        if rate < exit_threshold:
            self.bars_below += 1
        else:
            self.bars_below = 0
        self.bars_above = 0
        if self.bars_below >= exit_persistence:
            return "exit"
        return "hold"

    def mark_opened(self) -> None:
        self.in_position = True
        self.bars_above = 0
        self.bars_below = 0

    def mark_closed(self) -> None:
        self.in_position = False
        self.bars_above = 0
        self.bars_below = 0


class SignalBook:
    """Container for all per-pair signals + scoring helper."""

    def __init__(self, whitelist: tuple[str, ...]):
        self._signals: dict[str, PairSignal] = {
            base: PairSignal(base=base) for base in whitelist
        }

    def observe(self, base: str, rate: float, ts_ms: int,
                entry_threshold: float, exit_threshold: float,
                entry_persistence: int, exit_persistence: int) -> Verdict:
        sig = self._signals[base]
        return sig.observe(rate, ts_ms, entry_threshold, exit_threshold,
                           entry_persistence, exit_persistence)

    def signal(self, base: str) -> PairSignal:
        return self._signals[base]

    def rank_by_recent_rate(self, periods: int = 3) -> list[tuple[str, float]]:
        """Mean of last N rates per pair, sorted descending. Used by slot
        manager to pick which pairs to fill into free slots."""
        scores = []
        for base, sig in self._signals.items():
            if not sig.history:
                continue
            recent = [r for _, r in list(sig.history)[-periods:]]
            if recent:
                scores.append((base, sum(recent) / len(recent)))
        scores.sort(key=lambda x: -x[1])
        return scores

    def open_pairs(self) -> list[str]:
        return [b for b, s in self._signals.items() if s.in_position]

    def free_pairs(self) -> list[str]:
        return [b for b, s in self._signals.items() if not s.in_position]

    def serialize(self) -> dict:
        """Snapshot for persistence. Keys are pair bases."""
        return {
            base: {
                "in_position": s.in_position,
                "bars_above": s.bars_above,
                "bars_below": s.bars_below,
                "last_rate": s.last_rate,
                "last_observed_ms": s.last_observed_ms,
            }
            for base, s in self._signals.items()
        }

    def restore(self, state: dict) -> None:
        """Restore from a dict produced by serialize()."""
        for base, snap in state.items():
            if base not in self._signals:
                continue
            s = self._signals[base]
            s.in_position = bool(snap.get("in_position", False))
            s.bars_above = int(snap.get("bars_above", 0))
            s.bars_below = int(snap.get("bars_below", 0))
            s.last_rate = snap.get("last_rate")
            s.last_observed_ms = int(snap.get("last_observed_ms", 0))
