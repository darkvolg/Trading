"""Tests for trendrider_database — SQLite operations for alerts, signals, queue."""

import sqlite3
from datetime import datetime, timezone

from trendrider_database import AlertsDB


class TestAlertsDBCreation:
    def test_db_file_created(self, tmp_db, tmp_path):
        AlertsDB(tmp_db)
        assert (tmp_path / "price_alerts.db").exists()

    def test_tables_exist(self, tmp_db, tmp_path):
        AlertsDB(tmp_db)
        conn = sqlite3.connect(str(tmp_path / "price_alerts.db"))
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        assert "price_alerts" in tables
        assert "signal_counter" in tables
        assert "signal_queue" in tables

    def test_string_config_path(self, tmp_path):
        """Config with string path should also work."""
        config = {"user_data_dir": str(tmp_path)}
        AlertsDB(config)
        assert (tmp_path / "price_alerts.db").exists()


class TestNextSignalNumber:
    def test_starts_at_one(self, tmp_db):
        db = AlertsDB(tmp_db)
        assert db.next_signal_number() == 1

    def test_increments(self, tmp_db):
        db = AlertsDB(tmp_db)
        n1 = db.next_signal_number()
        n2 = db.next_signal_number()
        n3 = db.next_signal_number()
        assert n1 == 1
        assert n2 == 2
        assert n3 == 3

    def test_persists_across_instances(self, tmp_db):
        db1 = AlertsDB(tmp_db)
        db1.next_signal_number()  # 1
        db1.next_signal_number()  # 2

        db2 = AlertsDB(tmp_db)
        assert db2.next_signal_number() == 3


class TestQueueSignal:
    def test_queue_and_read_back(self, tmp_db, tmp_path):
        db = AlertsDB(tmp_db)
        db.queue_signal(
            signal_num=1, pair="ETH/USDT:USDT", side="long", leverage=5,
            setup_name="Trend Pullback", entry_low=1994.0, entry_high=2006.0,
            sl_price=1880.0, sl_pct=-0.06,
            tp1=2060.0, tp2=2100.0, tp3=2200.0,
            rr_ratio=1.7, regime="Trending Bull",
        )

        conn = sqlite3.connect(str(tmp_path / "price_alerts.db"))
        cursor = conn.execute("SELECT pair, side, leverage, setup_name FROM signal_queue")
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "ETH/USDT:USDT"
        assert row[1] == "long"
        assert row[2] == 5
        assert row[3] == "Trend Pullback"

    def test_multiple_signals_queued(self, tmp_db, tmp_path):
        db = AlertsDB(tmp_db)
        for i in range(3):
            db.queue_signal(
                signal_num=i + 1, pair=f"PAIR{i}/USDT:USDT", side="long",
                leverage=5, setup_name="Test", entry_low=100.0, entry_high=101.0,
                sl_price=95.0, sl_pct=-0.05,
                tp1=103.0, tp2=105.0, tp3=110.0,
                rr_ratio=1.5, regime="Trending Bull",
            )

        conn = sqlite3.connect(str(tmp_path / "price_alerts.db"))
        cursor = conn.execute("SELECT COUNT(*) FROM signal_queue")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 3


class TestGetLastAlert:
    def test_returns_none_initially(self, tmp_db):
        db = AlertsDB(tmp_db)
        assert db.get_last_alert("ETH/USDT:USDT") is None

    def test_returns_none_for_unknown_pair(self, tmp_db):
        db = AlertsDB(tmp_db)
        db.set_last_alert("BTC/USDT:USDT", datetime(2026, 3, 23, tzinfo=timezone.utc))
        assert db.get_last_alert("ETH/USDT:USDT") is None


class TestSetLastAlert:
    def test_stores_and_retrieves(self, tmp_db):
        db = AlertsDB(tmp_db)
        alert_time = datetime(2026, 3, 23, 12, 30, 0, tzinfo=timezone.utc)
        db.set_last_alert("ETH/USDT:USDT", alert_time)

        result = db.get_last_alert("ETH/USDT:USDT")
        assert result is not None
        assert result.year == 2026
        assert result.month == 3
        assert result.day == 23
        assert result.hour == 12
        assert result.minute == 30

    def test_updates_existing_alert(self, tmp_db):
        db = AlertsDB(tmp_db)
        time1 = datetime(2026, 3, 23, 10, 0, 0, tzinfo=timezone.utc)
        time2 = datetime(2026, 3, 23, 14, 0, 0, tzinfo=timezone.utc)

        db.set_last_alert("ETH/USDT:USDT", time1)
        db.set_last_alert("ETH/USDT:USDT", time2)

        result = db.get_last_alert("ETH/USDT:USDT")
        assert result.hour == 14

    def test_different_pairs_independent(self, tmp_db):
        db = AlertsDB(tmp_db)
        time1 = datetime(2026, 3, 23, 10, 0, 0, tzinfo=timezone.utc)
        time2 = datetime(2026, 3, 23, 14, 0, 0, tzinfo=timezone.utc)

        db.set_last_alert("ETH/USDT:USDT", time1)
        db.set_last_alert("BTC/USDT:USDT", time2)

        eth_alert = db.get_last_alert("ETH/USDT:USDT")
        btc_alert = db.get_last_alert("BTC/USDT:USDT")
        assert eth_alert.hour == 10
        assert btc_alert.hour == 14
