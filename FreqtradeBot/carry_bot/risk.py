"""Risk gates for the cash-and-carry bot.

Three guards run before any new entry and once per scheduler tick:

  1. Kill switch — file-based pause. Touch /tmp/carry_bot_kill to block
     new entries and force-close everything on next tick.

  2. Stale funding force-close — if a position has been held for more
     than `stale_force_close_hours` AND the last observed funding rate
     is negative, exit even if exit_persistence not yet hit. Catches
     regime flips that the persistence rule lags.

  3. Daily PnL alarm — if the last 24h realized + unrealized PnL drops
     below `-daily_loss_alarm_pct * capital`, log a loud warning. Doesn't
     auto-pause (delta-neutral PnL drift is usually fee/basis noise, not
     a real loss; a human should look).

This module is pure logic; it doesn't touch the exchange or the
position store directly. Scheduler queries it for verdicts.
"""
from __future__ import annotations
import logging
import os
import time
from dataclasses import dataclass
from typing import Iterable

logger = logging.getLogger(__name__)


@dataclass
class RiskVerdict:
    pause_new_entries: bool
    force_close_pairs: list[str]
    alarm_messages: list[str]

    @classmethod
    def empty(cls) -> "RiskVerdict":
        return cls(False, [], [])


# Distance from liquidation below which we sound the alarm. With 1x leverage
# and delta-neutral spot collateral via UTA, liquidation distance should be
# very large (>50%). If it drops below this, something is structurally wrong
# (e.g. Bybit migrated us off UTA, or someone moved spot collateral out).
LIQUIDATION_ALARM_DISTANCE_PCT = 0.10  # 10%


class RiskGate:
    def __init__(self, kill_switch_path: str,
                 stale_force_close_hours: int = 24,
                 daily_loss_alarm_pct: float = 0.01,
                 liq_alarm_distance_pct: float = LIQUIDATION_ALARM_DISTANCE_PCT):
        self.kill_switch_path = kill_switch_path
        self.stale_hours = stale_force_close_hours
        self.daily_loss_alarm_pct = daily_loss_alarm_pct
        self.liq_alarm_distance_pct = liq_alarm_distance_pct

    def check_kill_switch(self) -> bool:
        return os.path.exists(self.kill_switch_path)

    def check_stale_force_close(self, positions: Iterable, now_ms: int,
                                last_rates: dict) -> list[str]:
        """positions: iterable of objects with .base, .open_ts_ms.
        last_rates: {base: latest funding rate or None}.
        Returns: list of bases to force-close.
        """
        force = []
        threshold_ms = now_ms - self.stale_hours * 3600 * 1000
        for p in positions:
            if p.open_ts_ms > threshold_ms:
                continue
            rate = last_rates.get(p.base)
            if rate is None:
                continue
            if rate < 0:
                logger.warning(
                    "stale-force-close: %s held %dh, last rate %.5f < 0",
                    p.base, (now_ms - p.open_ts_ms) // 3_600_000, rate,
                )
                force.append(p.base)
        return force

    def check_liquidation_distance(self, exchange_positions: dict) -> list[str]:
        """Inspect each open perp position. Return list of "ALARM: BASE x.x%"
        messages for positions whose mark→liquidation distance is below
        threshold.

        With 1x leverage + UTA spot collateral the distance should be >50%
        in normal conditions; alarm fires if a position is somehow at higher
        effective leverage (config drift, collateral movement, etc).
        """
        alarms = []
        for base, p in exchange_positions.items():
            mark = p.get("mark_price") or p.get("entry") or 0
            liq = p.get("liquidation_price") or 0
            if mark <= 0 or liq <= 0:
                continue
            # For shorts: liquidation is ABOVE entry. Distance = (liq - mark)/mark.
            # For longs:  liquidation is BELOW entry. Distance = (mark - liq)/mark.
            if p.get("side") == "short":
                dist_pct = (liq - mark) / mark
            else:
                dist_pct = (mark - liq) / mark
            if 0 < dist_pct < self.liq_alarm_distance_pct:
                alarms.append(
                    f"liquidation-alarm: {base} {p.get('side')} mark={mark:.4f} "
                    f"liq={liq:.4f} distance={dist_pct*100:.2f}% "
                    f"(threshold {self.liq_alarm_distance_pct*100:.0f}%)"
                )
        return alarms

    def check_daily_pnl(self, capital_quote: float,
                        realized_24h: float, unrealized: float) -> str | None:
        total = realized_24h + unrealized
        if capital_quote <= 0:
            return None
        ratio = total / capital_quote
        if ratio < -self.daily_loss_alarm_pct:
            return (
                f"daily-pnl-alarm: 24h PnL {total:+.2f} USDT "
                f"({ratio*100:+.2f}% of {capital_quote:.0f} capital). "
                f"Threshold {-self.daily_loss_alarm_pct*100:.2f}%. "
                f"Investigate: basis blow-out, funding flip, or fee leak."
            )
        return None

    def evaluate(self, positions: Iterable, last_rates: dict,
                 now_ms: int, capital_quote: float = 0.0,
                 realized_24h: float = 0.0,
                 unrealized: float = 0.0,
                 exchange_positions: dict | None = None) -> RiskVerdict:
        v = RiskVerdict.empty()
        if self.check_kill_switch():
            v.pause_new_entries = True
            v.alarm_messages.append(
                f"kill-switch active (file {self.kill_switch_path}); "
                f"force-closing all positions and pausing new entries"
            )
            v.force_close_pairs.extend(p.base for p in positions)
            return v

        v.force_close_pairs.extend(
            self.check_stale_force_close(positions, now_ms, last_rates)
        )

        if exchange_positions:
            v.alarm_messages.extend(
                self.check_liquidation_distance(exchange_positions)
            )

        msg = self.check_daily_pnl(capital_quote, realized_24h, unrealized)
        if msg:
            v.alarm_messages.append(msg)

        return v
