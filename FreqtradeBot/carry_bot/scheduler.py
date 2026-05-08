"""8h tick driver — wakes after each Bybit funding payment, runs one cycle.

Cycle steps (idempotent — safe to re-run on crash recovery):
    1. Fetch latest funding rate per pair (REST)
    2. Update SignalBook + persist state
    3. Accrue funding on open positions (latest rate × notional)
    4. Run RiskGate; pause/force-close if needed
    5. For each open position with verdict 'exit', call exchange.close_carry_pair
    6. Pick top-K candidates from SignalBook, fill free slots via exchange.open_carry_pair
    7. Update positions store

Public API:
    Scheduler(...).tick(now_ms)  — run one cycle synchronously
    Scheduler(...).next_wake_ms(now_ms)  — when to wake next

The actual sleeping is left to a wrapper (cron, systemd timer, or asyncio
loop in main.py).
"""
from __future__ import annotations
import logging
import time
from dataclasses import dataclass

from .config import CarryConfig
from .exchange import BybitClient
from .funding_signal import SignalBook
from .positions import Position, PositionStore
from .risk import RiskGate

logger = logging.getLogger(__name__)


# Bybit funding payments at 00:00, 08:00, 16:00 UTC
FUNDING_HOURS_UTC = (0, 8, 16)
SECONDS_PER_HOUR = 3600


def next_funding_tick_ms(now_ms: int, offset_minutes: int = 5) -> int:
    """Next 8h boundary + offset, in epoch ms."""
    now_s = now_ms // 1000
    # Find next 8h-aligned UTC hour
    secs_in_day = now_s % 86400
    next_offset_s = None
    for h in FUNDING_HOURS_UTC:
        boundary = h * SECONDS_PER_HOUR + offset_minutes * 60
        if boundary > secs_in_day:
            next_offset_s = boundary
            break
    if next_offset_s is None:
        next_offset_s = FUNDING_HOURS_UTC[0] * SECONDS_PER_HOUR + offset_minutes * 60 + 86400
    next_s = now_s - secs_in_day + next_offset_s
    return next_s * 1000


@dataclass
class TickReport:
    now_ms: int
    opens: list[str]
    closes: list[str]
    funding_accrued: float        # in quote (USDT)
    fees_paid: float
    skipped_reasons: dict          # {base: reason} for entries blocked
    alarms: list[str]


class Scheduler:
    def __init__(self, cfg: CarryConfig, exchange: BybitClient,
                 store: PositionStore, signals: SignalBook,
                 risk: RiskGate):
        self.cfg = cfg
        self.exchange = exchange
        self.store = store
        self.signals = signals
        self.risk = risk

    # ---------- Public entry point ----------

    def tick(self, now_ms: int | None = None,
             dry_run_signals_only: bool = False) -> TickReport:
        """Run one full cycle. dry_run_signals_only skips actual order
        placement — useful for testing signal logic on testnet without
        moving capital."""
        now_ms = now_ms or int(time.time() * 1000)
        report = TickReport(
            now_ms=now_ms, opens=[], closes=[],
            funding_accrued=0.0, fees_paid=0.0,
            skipped_reasons={}, alarms=[],
        )

        # 1. Fetch latest funding rates per pair
        rates = self._fetch_rates(report)
        if not rates:
            report.alarms.append("no funding rates fetched; skipping cycle")
            return report

        # 2. Update SignalBook
        verdicts = self._update_signals(rates, now_ms)

        # 3. Accrue funding on open positions
        funding_accrued = self._accrue_funding(rates, now_ms)
        report.funding_accrued = funding_accrued

        # 4. Risk evaluation
        open_positions = self.store.list_open()
        last_rates_map = {b: r for b, r in rates.items()}
        risk_verdict = self.risk.evaluate(
            open_positions, last_rates_map, now_ms,
        )
        report.alarms.extend(risk_verdict.alarm_messages)

        # 5. Closes (exit-verdict OR risk-forced)
        force_close = set(risk_verdict.force_close_pairs)
        exit_bases = {b for b, v in verdicts.items() if v == "exit"} | force_close
        for base in exit_bases:
            if dry_run_signals_only:
                report.skipped_reasons[base] = "dry_run_signals_only"
                continue
            success, fee = self._close_pair(base, now_ms,
                                            forced=(base in force_close))
            if success:
                report.closes.append(base)
                report.fees_paid += fee

        # 6. Opens (only if not paused)
        if risk_verdict.pause_new_entries:
            return report

        opens_needed = self._slot_capacity()
        if opens_needed <= 0:
            return report

        candidates = self._candidate_opens(verdicts, rates)
        for base in candidates[:opens_needed]:
            if dry_run_signals_only:
                report.skipped_reasons[base] = "dry_run_signals_only"
                continue
            success, fee = self._open_pair(base, now_ms)
            if success:
                report.opens.append(base)
                report.fees_paid += fee

        return report

    def next_wake_ms(self, now_ms: int | None = None) -> int:
        return next_funding_tick_ms(
            now_ms or int(time.time() * 1000),
            self.cfg.tick_offset_minutes,
        )

    # ---------- Internals ----------

    def _fetch_rates(self, report: TickReport) -> dict[str, float]:
        out = {}
        for base in self.cfg.whitelist:
            try:
                rate = self.exchange.fetch_funding_rate(base)
                out[base] = rate
                self.store.record_funding(base, report.now_ms, rate)
            except Exception as e:
                logger.warning("fetch_funding_rate %s failed: %s", base, e)
        return out

    def _update_signals(self, rates: dict[str, float],
                        now_ms: int) -> dict[str, str]:
        verdicts = {}
        for base, rate in rates.items():
            v = self.signals.observe(
                base, rate, now_ms,
                self.cfg.entry_threshold, self.cfg.exit_threshold,
                self.cfg.entry_persistence, self.cfg.exit_persistence,
            )
            verdicts[base] = v
        # Persist signal state
        self.store.save_signal_state(self.signals.serialize())
        return verdicts

    def _accrue_funding(self, rates: dict[str, float], now_ms: int) -> float:
        """For each open position, add (rate × perp_notional) to funding."""
        total = 0.0
        for p in self.store.list_open():
            r = rates.get(p.base)
            if r is None:
                continue
            # Short perp earns positive funding; payment in quote = rate × notional.
            notional = p.perp_qty * p.entry_perp_px
            payment = r * notional
            self.store.accrue_funding(p.base, payment, now_ms)
            total += payment
        return total

    def _slot_capacity(self) -> int:
        return max(0, self.cfg.n_slots - len(self.store.list_open()))

    def _candidate_opens(self, verdicts: dict[str, str],
                         rates: dict[str, float]) -> list[str]:
        """Pairs eligible to open NOW: signal verdict 'enter', not already
        in position. Sort by current rate descending (highest funding first)."""
        cands = [b for b, v in verdicts.items() if v == "enter"]
        cands.sort(key=lambda b: -rates.get(b, 0))
        return cands

    def _open_pair(self, base: str, now_ms: int) -> tuple[bool, float]:
        try:
            notional = self._notional_per_slot()
            spot_fill, perp_fill = self.exchange.open_carry_pair(
                base, notional, leverage=self.cfg.perp_leverage,
            )
            self.signals.signal(base).mark_opened()
            self.store.insert(Position(
                base=base,
                open_ts_ms=now_ms,
                spot_qty=spot_fill.qty,
                perp_qty=perp_fill.qty,
                entry_spot_px=spot_fill.avg_price,
                entry_perp_px=perp_fill.avg_price,
                open_fee_quote=spot_fill.fee_quote + perp_fill.fee_quote,
                last_update_ts_ms=now_ms,
            ))
            fee = spot_fill.fee_quote + perp_fill.fee_quote
            return True, fee
        except Exception as e:
            logger.error("open_pair %s failed: %s", base, e)
            return False, 0.0

    def _close_pair(self, base: str, now_ms: int,
                    forced: bool = False) -> tuple[bool, float]:
        p = self.store.get(base)
        if not p:
            logger.warning("close_pair %s: no open position", base)
            return False, 0.0
        try:
            spot_fill, perp_fill = self.exchange.close_carry_pair(base, p.spot_qty)
            self.signals.signal(base).mark_closed()
            self.store.close(
                base,
                exit_spot_px=spot_fill.avg_price,
                exit_perp_px=perp_fill.avg_price,
                close_fee_quote=spot_fill.fee_quote + perp_fill.fee_quote,
                close_ts_ms=now_ms,
                notes="forced" if forced else "signal_exit",
            )
            return True, spot_fill.fee_quote + perp_fill.fee_quote
        except Exception as e:
            logger.error("close_pair %s failed: %s", base, e)
            return False, 0.0

    def _notional_per_slot(self) -> float:
        """USDT notional to deploy per new position. Placeholder: read from
        exchange wallet balance × position_size_pct in production."""
        # For now, return a sensible default; real impl should fetch
        # available balance and divide by free-slot count.
        return 100.0  # $100 testnet default
