"""Position tracker for delta-neutral cash-and-carry pairs.

Persists open positions to SQLite so the bot survives restarts. Each
position is a paired (spot_long, perp_short) tuple on the same base asset.

Tracks:
    - entry timestamps and prices for both legs
    - current qty on each leg (should remain ~equal)
    - cumulative funding received (in quote, USDT)
    - cumulative fees paid (open + close + rebalance)
    - delta drift (|spot_qty - perp_qty| / spot_qty)

Does NOT execute trades — only books them. Execution happens in scheduler
which calls into exchange.BybitClient.
"""
from __future__ import annotations
import logging
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator

logger = logging.getLogger(__name__)


SCHEMA = """
CREATE TABLE IF NOT EXISTS positions (
    base TEXT PRIMARY KEY,
    open_ts_ms INTEGER NOT NULL,
    spot_qty REAL NOT NULL,
    perp_qty REAL NOT NULL,           -- always positive; side is implicit short
    entry_spot_px REAL NOT NULL,
    entry_perp_px REAL NOT NULL,
    open_fee_quote REAL NOT NULL,
    funding_received_quote REAL NOT NULL DEFAULT 0,
    rebalance_fees_quote REAL NOT NULL DEFAULT 0,
    last_update_ts_ms INTEGER NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS closed_positions (
    base TEXT NOT NULL,
    open_ts_ms INTEGER NOT NULL,
    close_ts_ms INTEGER NOT NULL,
    spot_qty REAL NOT NULL,
    perp_qty REAL NOT NULL,
    entry_spot_px REAL NOT NULL,
    entry_perp_px REAL NOT NULL,
    exit_spot_px REAL NOT NULL,
    exit_perp_px REAL NOT NULL,
    open_fee_quote REAL NOT NULL,
    close_fee_quote REAL NOT NULL,
    rebalance_fees_quote REAL NOT NULL,
    funding_received_quote REAL NOT NULL,
    net_pnl_quote REAL NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS funding_history (
    base TEXT NOT NULL,
    ts_ms INTEGER NOT NULL,
    rate REAL NOT NULL,
    PRIMARY KEY (base, ts_ms)
);

CREATE TABLE IF NOT EXISTS signal_state (
    base TEXT PRIMARY KEY,
    in_position INTEGER NOT NULL,
    bars_above INTEGER NOT NULL,
    bars_below INTEGER NOT NULL,
    last_rate REAL,
    last_observed_ms INTEGER NOT NULL
);
"""


@dataclass
class Position:
    base: str
    open_ts_ms: int
    spot_qty: float
    perp_qty: float
    entry_spot_px: float
    entry_perp_px: float
    open_fee_quote: float
    funding_received_quote: float = 0.0
    rebalance_fees_quote: float = 0.0
    last_update_ts_ms: int = 0
    notes: str = ""

    @property
    def notional(self) -> float:
        return self.spot_qty * self.entry_spot_px

    @property
    def delta_drift_abs(self) -> float:
        return abs(self.spot_qty - self.perp_qty)

    @property
    def delta_drift_pct(self) -> float:
        ref = max(self.spot_qty, 1e-12)
        return self.delta_drift_abs / ref


class PositionStore:
    """Sqlite-backed position book. Single connection, one process."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        try:
            self._conn.execute("BEGIN")
            yield self._conn
            self._conn.execute("COMMIT")
        except Exception:
            self._conn.execute("ROLLBACK")
            raise

    # ---------- Open positions ----------

    def insert(self, p: Position) -> None:
        if p.last_update_ts_ms == 0:
            p.last_update_ts_ms = p.open_ts_ms
        self._conn.execute(
            """INSERT INTO positions (base, open_ts_ms, spot_qty, perp_qty,
               entry_spot_px, entry_perp_px, open_fee_quote,
               funding_received_quote, rebalance_fees_quote,
               last_update_ts_ms, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (p.base, p.open_ts_ms, p.spot_qty, p.perp_qty,
             p.entry_spot_px, p.entry_perp_px, p.open_fee_quote,
             p.funding_received_quote, p.rebalance_fees_quote,
             p.last_update_ts_ms, p.notes),
        )

    def get(self, base: str) -> Position | None:
        row = self._conn.execute(
            "SELECT * FROM positions WHERE base = ?", (base,)
        ).fetchone()
        if not row:
            return None
        return Position(
            base=row["base"],
            open_ts_ms=row["open_ts_ms"],
            spot_qty=row["spot_qty"],
            perp_qty=row["perp_qty"],
            entry_spot_px=row["entry_spot_px"],
            entry_perp_px=row["entry_perp_px"],
            open_fee_quote=row["open_fee_quote"],
            funding_received_quote=row["funding_received_quote"],
            rebalance_fees_quote=row["rebalance_fees_quote"],
            last_update_ts_ms=row["last_update_ts_ms"],
            notes=row["notes"] or "",
        )

    def list_open(self) -> list[Position]:
        rows = self._conn.execute(
            "SELECT base FROM positions ORDER BY open_ts_ms"
        ).fetchall()
        out = []
        for r in rows:
            p = self.get(r["base"])
            if p:
                out.append(p)
        return out

    def accrue_funding(self, base: str, funding_quote: float, ts_ms: int) -> None:
        """Add a funding payment in quote currency to an open position."""
        self._conn.execute(
            """UPDATE positions
                  SET funding_received_quote = funding_received_quote + ?,
                      last_update_ts_ms = ?
                WHERE base = ?""",
            (funding_quote, ts_ms, base),
        )

    def update_qtys(self, base: str, spot_qty: float, perp_qty: float,
                    rebalance_fee: float, ts_ms: int) -> None:
        """Adjust position quantities after a delta-rebalance."""
        self._conn.execute(
            """UPDATE positions
                  SET spot_qty = ?, perp_qty = ?,
                      rebalance_fees_quote = rebalance_fees_quote + ?,
                      last_update_ts_ms = ?
                WHERE base = ?""",
            (spot_qty, perp_qty, rebalance_fee, ts_ms, base),
        )

    def close(self, base: str, exit_spot_px: float, exit_perp_px: float,
              close_fee_quote: float, close_ts_ms: int,
              notes: str = "") -> Position | None:
        """Move position from open → closed table. Compute net PnL."""
        p = self.get(base)
        if not p:
            return None
        # PnL legs:
        # spot:  (exit_spot - entry_spot) * spot_qty   (long, profit if up)
        # perp:  (entry_perp - exit_perp) * perp_qty   (short, profit if down)
        # If spot ≈ perp price moves, these cancel → near-zero price PnL.
        spot_pnl = (exit_spot_px - p.entry_spot_px) * p.spot_qty
        perp_pnl = (p.entry_perp_px - exit_perp_px) * p.perp_qty
        price_pnl = spot_pnl + perp_pnl
        total_fees = p.open_fee_quote + close_fee_quote + p.rebalance_fees_quote
        net = price_pnl + p.funding_received_quote - total_fees

        with self.transaction():
            self._conn.execute(
                """INSERT INTO closed_positions
                   (base, open_ts_ms, close_ts_ms, spot_qty, perp_qty,
                    entry_spot_px, entry_perp_px, exit_spot_px, exit_perp_px,
                    open_fee_quote, close_fee_quote, rebalance_fees_quote,
                    funding_received_quote, net_pnl_quote, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (p.base, p.open_ts_ms, close_ts_ms, p.spot_qty, p.perp_qty,
                 p.entry_spot_px, p.entry_perp_px, exit_spot_px, exit_perp_px,
                 p.open_fee_quote, close_fee_quote, p.rebalance_fees_quote,
                 p.funding_received_quote, net, notes),
            )
            self._conn.execute("DELETE FROM positions WHERE base = ?", (base,))
        return p

    # ---------- Funding history (audit trail) ----------

    def record_funding(self, base: str, ts_ms: int, rate: float) -> None:
        try:
            self._conn.execute(
                "INSERT INTO funding_history (base, ts_ms, rate) VALUES (?, ?, ?)",
                (base, ts_ms, rate),
            )
        except sqlite3.IntegrityError:
            # Already recorded for this (base, ts_ms)
            pass

    # ---------- Signal state ----------

    def save_signal_state(self, state: dict) -> None:
        with self.transaction():
            for base, snap in state.items():
                self._conn.execute(
                    """INSERT OR REPLACE INTO signal_state
                       (base, in_position, bars_above, bars_below,
                        last_rate, last_observed_ms)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (base, int(bool(snap["in_position"])),
                     int(snap["bars_above"]), int(snap["bars_below"]),
                     snap["last_rate"], int(snap["last_observed_ms"])),
                )

    def load_signal_state(self) -> dict:
        rows = self._conn.execute("SELECT * FROM signal_state").fetchall()
        return {
            r["base"]: {
                "in_position": bool(r["in_position"]),
                "bars_above": r["bars_above"],
                "bars_below": r["bars_below"],
                "last_rate": r["last_rate"],
                "last_observed_ms": r["last_observed_ms"],
            }
            for r in rows
        }

    # ---------- Reporting ----------

    def realized_pnl(self) -> dict:
        """Aggregate realized PnL across all closed positions."""
        row = self._conn.execute(
            """SELECT
                 COUNT(*) AS n,
                 COALESCE(SUM(funding_received_quote), 0) AS funding,
                 COALESCE(SUM(open_fee_quote + close_fee_quote + rebalance_fees_quote), 0) AS fees,
                 COALESCE(SUM(net_pnl_quote), 0) AS net
               FROM closed_positions"""
        ).fetchone()
        return {
            "n_closed": int(row["n"]),
            "funding_received": float(row["funding"]),
            "fees_paid": float(row["fees"]),
            "net_pnl": float(row["net"]),
        }

    def close_db(self) -> None:
        self._conn.close()
