"""
TrendRider Database — SQLite operations for price alerts, signal counter, signal queue.
"""

import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class AlertsDB:
    """Manages SQLite database for price alerts, signal counter, and signal queue."""

    def __init__(self, config: dict):
        data_dir = config.get('user_data_dir', Path('.'))
        if isinstance(data_dir, str):
            data_dir = Path(data_dir)
        self.db_path = str(data_dir / 'price_alerts.db')
        self._init_tables()

    @contextmanager
    def _connect(self):
        """Context manager for safe SQLite connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_tables(self):
        """Create tables if they don't exist."""
        try:
            with self._connect() as conn:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS price_alerts "
                    "(pair TEXT PRIMARY KEY, last_alert_time TEXT)"
                )
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS signal_counter "
                    "(id INTEGER PRIMARY KEY CHECK (id = 1), count INTEGER DEFAULT 0)"
                )
                conn.execute(
                    "INSERT OR IGNORE INTO signal_counter (id, count) VALUES (1, 0)"
                )
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS signal_queue ("
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                    "signal_num INTEGER, pair TEXT, side TEXT, leverage INTEGER, "
                    "setup_name TEXT, entry_low REAL, entry_high REAL, "
                    "sl_price REAL, sl_pct REAL, "
                    "tp1 REAL, tp2 REAL, tp3 REAL, rr_ratio REAL, "
                    "regime TEXT, created_at TEXT, sent_free INTEGER DEFAULT 0)"
                )
        except Exception as e:
            logger.warning(f"Failed to init alerts DB: {e}")

    def get_last_alert(self, pair: str):
        """Get last alert time for a pair. Returns datetime or None."""
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "SELECT last_alert_time FROM price_alerts WHERE pair = ?", (pair,)
                )
                row = cursor.fetchone()
                if row and row[0]:
                    return datetime.fromisoformat(row[0])
                return None
        except Exception:
            return None

    def set_last_alert(self, pair: str, alert_time: datetime):
        """Save last alert time for a pair."""
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO price_alerts (pair, last_alert_time) VALUES (?, ?)",
                    (pair, alert_time.isoformat())
                )
        except Exception as e:
            logger.warning(f"Failed to save alert: {e}")

    def next_signal_number(self) -> int:
        """Increment and return the next signal number (atomic)."""
        try:
            with self._connect() as conn:
                conn.execute("BEGIN EXCLUSIVE")
                conn.execute("UPDATE signal_counter SET count = count + 1 WHERE id = 1")
                cursor = conn.execute("SELECT count FROM signal_counter WHERE id = 1")
                num = cursor.fetchone()[0]
                return num
        except Exception:
            return 0

    def queue_signal(self, signal_num: int, pair: str, side: str, leverage: int,
                     setup_name: str, entry_low: float, entry_high: float,
                     sl_price: float, sl_pct: float,
                     tp1: float, tp2: float, tp3: float,
                     rr_ratio: float, regime: str):
        """Queue a signal for delayed free channel delivery."""
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO signal_queue "
                    "(signal_num, pair, side, leverage, setup_name, "
                    "entry_low, entry_high, sl_price, sl_pct, "
                    "tp1, tp2, tp3, rr_ratio, regime, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (signal_num, pair, side, leverage, setup_name,
                     entry_low, entry_high, sl_price, sl_pct,
                     tp1, tp2, tp3, rr_ratio,
                     regime, datetime.now(timezone.utc).isoformat())
                )
        except Exception as e:
            logger.warning(f"Failed to queue signal for free channel: {e}")
