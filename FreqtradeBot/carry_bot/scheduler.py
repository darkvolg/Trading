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
    rebalances: list[str] = None   # bases that were rebalanced

    def __post_init__(self):
        if self.rebalances is None:
            self.rebalances = []


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

        # 4. Risk evaluation (incl. liquidation distance + reconciliation)
        open_positions = self.store.list_open()
        last_rates_map = {b: r for b, r in rates.items()}
        exchange_positions = self._fetch_exchange_positions()
        self._reconcile(open_positions, exchange_positions, report)
        risk_verdict = self.risk.evaluate(
            open_positions, last_rates_map, now_ms,
            exchange_positions=exchange_positions,
        )
        report.alarms.extend(risk_verdict.alarm_messages)

        # 4b. Delta-rebalance any drifted positions BEFORE we make new entries.
        if not dry_run_signals_only:
            self._rebalance_drift(open_positions, report)

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
        # Idempotency guard: never double-open. Catches crash-after-fill /
        # restart-replay where signal state is stale but DB has the position.
        if self.store.get(base) is not None:
            logger.warning("open_pair %s: position already in DB; skipping", base)
            return False, 0.0
        try:
            notional = self._notional_per_slot()
            if notional <= 0:
                return False, 0.0
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
        """USDT notional to deploy per new position.

        Live path: fetch free USDT, multiply by cfg.position_size_pct.
        Fallback: cfg.fallback_notional_usdt (testnet / no creds).
        Refuses to open if computed notional below cfg.small_capital_floor_usdt
        (avoids dust orders that get rejected by Bybit min-notional rules).
        """
        # Test fakes or no-creds clients: skip balance fetch
        if not getattr(self.exchange, "has_credentials", False):
            return self.cfg.fallback_notional_usdt
        try:
            free_usdt = self.exchange.fetch_unified_usdt()
        except Exception as e:
            logger.warning(
                "balance fetch failed (%s); falling back to %.2f",
                e, self.cfg.fallback_notional_usdt,
            )
            return self.cfg.fallback_notional_usdt
        notional = free_usdt * self.cfg.position_size_pct
        if notional < self.cfg.small_capital_floor_usdt:
            logger.warning(
                "notional %.2f below floor %.2f (free=%.2f, pct=%.2f); "
                "refusing to open",
                notional, self.cfg.small_capital_floor_usdt,
                free_usdt, self.cfg.position_size_pct,
            )
            return 0.0
        return notional

    # ---------- Risk integration ----------

    def _fetch_exchange_positions(self) -> dict:
        """Pull current perp positions from exchange. Empty dict if no creds
        or call fails — risk monitor degrades gracefully."""
        if not self.exchange.has_credentials:
            return {}
        try:
            return self.exchange.fetch_open_positions()
        except Exception as e:
            logger.warning("fetch_open_positions failed: %s; risk monitor degraded", e)
            return {}

    def _reconcile(self, local_positions, exchange_positions: dict,
                   report) -> None:
        """Compare local position book to exchange-reported state.

        Mismatches we care about:
            - In local book but not on exchange  → exchange closed it (liquidation? manual?)
            - On exchange but not in local book  → manual position bypassing the bot
            - Qty mismatch >5%                   → drift since last rebalance
        Logs alarms; does not auto-correct (humans decide).
        """
        local_bases = {p.base for p in local_positions}
        ex_bases = set(exchange_positions.keys())

        for base in local_bases - ex_bases:
            report.alarms.append(
                f"reconcile: {base} in local book but no exchange perp position — "
                f"exchange may have liquidated/closed it. Investigate."
            )
        for base in ex_bases - local_bases:
            report.alarms.append(
                f"reconcile: {base} perp open on exchange but not in local book — "
                f"manual position or stale state."
            )
        for base in local_bases & ex_bases:
            local_p = next(p for p in local_positions if p.base == base)
            ex_p = exchange_positions[base]
            ex_qty = float(ex_p.get("qty", 0) or 0)
            if abs(ex_qty - local_p.perp_qty) / max(local_p.perp_qty, 1e-9) > 0.05:
                report.alarms.append(
                    f"reconcile: {base} perp qty drift — local={local_p.perp_qty} "
                    f"exchange={ex_qty} (>5%). Investigate."
                )

    def _rebalance_drift(self, positions, report) -> None:
        """For each open position whose delta drift exceeds the threshold,
        place a corrective trade to re-equalise spot and perp legs."""
        threshold = self.cfg.delta_drift_pct
        for p in positions:
            if p.delta_drift_pct < threshold:
                continue
            try:
                fill = self.exchange.rebalance_pair(p.base, p.spot_qty, p.perp_qty)
                if fill is None:
                    continue
                # Update position with new qtys + accumulated rebalance fee
                if p.spot_qty > p.perp_qty:
                    new_perp = p.perp_qty + fill.qty
                    new_spot = p.spot_qty
                else:
                    new_perp = p.perp_qty
                    new_spot = p.spot_qty + fill.qty
                self.store.update_qtys(
                    p.base, new_spot, new_perp,
                    rebalance_fee=fill.fee_quote,
                    ts_ms=int(time.time() * 1000),
                )
                report.rebalances.append(p.base)
                report.fees_paid += fill.fee_quote
                logger.info(
                    "rebalanced %s: spot=%.6f→%.6f perp=%.6f→%.6f fee=%.4f",
                    p.base, p.spot_qty, new_spot, p.perp_qty, new_perp,
                    fill.fee_quote,
                )
            except Exception as e:
                report.alarms.append(
                    f"rebalance {p.base} failed: {e}. Drift {p.delta_drift_pct*100:.2f}%."
                )
