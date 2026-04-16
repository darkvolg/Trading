"""Tests for TrendRider scripts — business logic, formatting, calculations.

Covers: daily_digest, export_trades, export_to_sheets, oi_funding_alerts,
        monday_context, friday_recap, monthly_report, equity_curve, shared_utils.

External deps (gspread, google.oauth2, ccxt, talib) are mocked at import time.
"""

import sqlite3
import sys
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add scripts directory to sys.path so we can import modules
SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

# ── Mock heavy external deps before importing scripts ──────────────────

# gspread + google.oauth2 (for export_to_sheets, setup_sheets)
if "gspread" not in sys.modules:
    _gspread = types.ModuleType("gspread")
    _gspread.Client = MagicMock
    _gspread.Spreadsheet = MagicMock
    _gspread.Worksheet = MagicMock
    _gspread.authorize = MagicMock()
    _gspread_exc = types.ModuleType("gspread.exceptions")
    _gspread_exc.WorksheetNotFound = type("WorksheetNotFound", (Exception,), {})
    _gspread.exceptions = _gspread_exc
    sys.modules["gspread"] = _gspread
    sys.modules["gspread.exceptions"] = _gspread_exc

if "google" not in sys.modules:
    _google = types.ModuleType("google")
    sys.modules["google"] = _google
if "google.oauth2" not in sys.modules:
    _google_oauth2 = types.ModuleType("google.oauth2")
    sys.modules["google.oauth2"] = _google_oauth2
if "google.oauth2.service_account" not in sys.modules:
    _sa = types.ModuleType("google.oauth2.service_account")
    _sa.Credentials = MagicMock()
    sys.modules["google.oauth2.service_account"] = _sa


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_trades():
    """List of trade dicts resembling Freqtrade SQLite rows.

    Uses relative dates (within the last 10 days) so the trades always fall
    inside the 30-day rolling window used by query_stats.
    """
    now = datetime.now(timezone.utc)
    day1 = (now - timedelta(days=10)).strftime("%Y-%m-%d")
    day2 = (now - timedelta(days=8)).strftime("%Y-%m-%d")
    day3 = (now - timedelta(days=5)).strftime("%Y-%m-%d")

    return [
        {
            "id": 1,
            "pair": "BTC/USDT:USDT",
            "open_date": f"{day1} 10:00:00",
            "close_date": f"{day1} 14:30:00",
            "open_rate": 64000.0,
            "close_rate": 65920.0,
            "profit_ratio": 0.03,
            "profit_abs": 6.0,
            "exit_reason": "roi",
            "leverage": 3,
            "stake_amount": 200.0,
            "strategy": "TrendRider",
            "close_profit": 0.03,
            "close_profit_abs": 6.0,
        },
        {
            "id": 2,
            "pair": "ETH/USDT:USDT",
            "open_date": f"{day2} 08:00:00",
            "close_date": f"{day2} 20:00:00",
            "open_rate": 3500.0,
            "close_rate": 3430.0,
            "profit_ratio": -0.02,
            "profit_abs": -4.0,
            "exit_reason": "stop_loss",
            "leverage": 3,
            "stake_amount": 200.0,
            "strategy": "TrendRider",
            "close_profit": -0.02,
            "close_profit_abs": -4.0,
        },
        {
            "id": 3,
            "pair": "SOL/USDT:USDT",
            "open_date": f"{day3} 12:00:00",
            "close_date": f"{day3} 18:00:00",
            "open_rate": 140.0,
            "close_rate": 147.0,
            "profit_ratio": 0.05,
            "profit_abs": 10.0,
            "exit_reason": "trailing_stop_loss",
            "leverage": 3,
            "stake_amount": 200.0,
            "strategy": "TrendRider",
            "close_profit": 0.05,
            "close_profit_abs": 10.0,
        },
    ]


@pytest.fixture
def tmp_sqlite(tmp_path, sample_trades):
    """Create a temporary SQLite DB with sample trades."""
    db_path = str(tmp_path / "tradesv3.dryrun.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE trades (
            id INTEGER PRIMARY KEY,
            pair TEXT, open_date TEXT, close_date TEXT,
            open_rate REAL, close_rate REAL,
            close_profit REAL, close_profit_abs REAL,
            profit_ratio REAL,
            exit_reason TEXT, leverage REAL, stake_amount REAL,
            strategy TEXT, is_open INTEGER DEFAULT 0
        )
    """)
    for t in sample_trades:
        conn.execute(
            """INSERT INTO trades
               (id, pair, open_date, close_date, open_rate, close_rate,
                close_profit, close_profit_abs, profit_ratio,
                exit_reason, leverage, stake_amount, strategy, is_open)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,0)""",
            (
                t["id"], t["pair"], t["open_date"], t["close_date"],
                t["open_rate"], t["close_rate"],
                t["close_profit"], t["close_profit_abs"], t["profit_ratio"],
                t["exit_reason"], t["leverage"], t["stake_amount"],
                t["strategy"],
            ),
        )
    conn.commit()
    conn.close()
    return db_path


# ═══════════════════════════════════════════════════════════════════════
# daily_digest.py
# ═══════════════════════════════════════════════════════════════════════

class TestDailyDigestFormatPrice:
    def test_large_price(self):
        from daily_digest import format_price
        assert format_price(64250.0) == "$64,250"

    def test_medium_price(self):
        from daily_digest import format_price
        assert format_price(3.45) == "$3.45"

    def test_small_price(self):
        from daily_digest import format_price
        assert format_price(0.00012) == "$0.0001"

    def test_boundary_100(self):
        from daily_digest import format_price
        assert format_price(100.0) == "$100"

    def test_boundary_1(self):
        from daily_digest import format_price
        assert format_price(1.0) == "$1.00"


class TestDailyDigestClassifyFunding:
    def test_none_returns_na(self):
        from daily_digest import classify_funding
        assert classify_funding(None) == "N/A"

    def test_negative_is_bullish(self):
        from daily_digest import classify_funding
        assert classify_funding(-0.0005) == "bullish"

    def test_high_positive_is_bearish(self):
        from daily_digest import classify_funding
        assert classify_funding(0.0005) == "bearish"

    def test_near_zero_is_neutral(self):
        from daily_digest import classify_funding
        assert classify_funding(0.0001) == "neutral"

    def test_boundary_neutral_negative(self):
        from daily_digest import classify_funding
        assert classify_funding(-0.0001) == "neutral"


class TestDailyDigestPortfolioHeat:
    def test_zero_cold(self):
        from daily_digest import portfolio_heat
        assert portfolio_heat(0) == "COLD"

    def test_one_moderate(self):
        from daily_digest import portfolio_heat
        assert portfolio_heat(1) == "MODERATE"

    def test_two_moderate(self):
        from daily_digest import portfolio_heat
        assert portfolio_heat(2) == "MODERATE"

    def test_three_hot(self):
        from daily_digest import portfolio_heat
        assert portfolio_heat(3) == "HOT"


class TestDailyDigestPairToBybit:
    def test_standard(self):
        from daily_digest import pair_to_bybit
        assert pair_to_bybit("BTC/USDT") == "BTCUSDT"

    def test_with_colon(self):
        from daily_digest import pair_to_bybit
        assert pair_to_bybit("BTC/USDT:USDT") == "BTCUSDT"


def _make_safe_datetime():
    """Create a datetime subclass that handles %-d on Windows."""
    class SafeDatetime(datetime):
        def strftime(self, fmt):
            fmt = fmt.replace("%-d", "%d")
            return super().strftime(fmt)

        @classmethod
        def now(cls, tz=None):
            real_now = datetime.now(tz)
            return cls(
                real_now.year, real_now.month, real_now.day,
                real_now.hour, real_now.minute, real_now.second,
                real_now.microsecond, real_now.tzinfo,
            )
    return SafeDatetime


class TestDailyDigestBuildMessage:
    """Test build_message with platform-safe date formatting."""

    def _call_build_message(self, results, fng, open_pos, oi_changes):
        import daily_digest as dd
        from daily_digest import build_message
        SafeDatetime = _make_safe_datetime()
        original_dt = dd.datetime
        dd.datetime = SafeDatetime
        try:
            return build_message(results, fng, open_pos, oi_changes)
        finally:
            dd.datetime = original_dt

    def test_contains_sections(self):
        results = [
            {
                "symbol": "BTC/USDT", "error": False,
                "price": 64000.0, "change_pct": 2.5, "rsi": 55.0,
                "trend": "Uptrend", "status": "Neutral",
                "ema50": 62000.0, "ema200": 58000.0, "adx": 30.0,
                "funding": 0.0001,
            },
        ]
        fng = {"value": 55, "label": "Greed"}
        msg = self._call_build_message(results, fng, 2, {"BTCUSDT": 3.5})
        assert "MORNING BRIEF" in msg
        assert "MARKET PULSE" in msg
        assert "Fear & Greed: 55" in msg
        assert "BTC/USDT" in msg
        assert "OI CHANGES" in msg
        assert "TrendRider AI" in msg

    def test_error_pair_shows_unavailable(self):
        results = [{"symbol": "SOL/USDT", "error": True}]
        fng = {"value": 50, "label": "Neutral"}
        msg = self._call_build_message(results, fng, 0, {})
        assert "data unavailable" in msg

    def test_portfolio_heat_in_message(self):
        results = []
        fng = {"value": 50, "label": "Neutral"}
        msg = self._call_build_message(results, fng, 0, {})
        assert "COLD" in msg

    def test_trending_regime(self):
        results = [
            {
                "symbol": "BTC/USDT", "error": False,
                "price": 64000, "change_pct": 1.0, "rsi": 50,
                "trend": "Uptrend", "status": "Neutral",
                "ema50": 62000, "ema200": 58000, "adx": 30.0,
                "funding": None,
            },
        ]
        fng = {"value": 50, "label": "Neutral"}
        msg = self._call_build_message(results, fng, 0, {})
        assert "Trending" in msg


# ═══════════════════════════════════════════════════════════════════════
# export_trades.py
# ═══════════════════════════════════════════════════════════════════════

class TestExportTradesFmtDt:
    def test_normal(self):
        from export_trades import fmt_dt
        assert fmt_dt("2026-03-01 10:00:00") == "2026-03-01T10:00:00"

    def test_none(self):
        from export_trades import fmt_dt
        assert fmt_dt(None) == ""

    def test_empty(self):
        from export_trades import fmt_dt
        assert fmt_dt("") == ""

    def test_truncates_to_19(self):
        from export_trades import fmt_dt
        result = fmt_dt("2026-03-01 10:00:00.123456")
        assert len(result) == 19


class TestExportTradesCalcDuration:
    def test_hours(self):
        from export_trades import calc_duration
        assert calc_duration("2026-03-01 10:00:00", "2026-03-01 14:30:00") == "4.5h"

    def test_minutes(self):
        from export_trades import calc_duration
        assert calc_duration("2026-03-01 10:00:00", "2026-03-01 10:30:00") == "30m"

    def test_empty_dates(self):
        from export_trades import calc_duration
        assert calc_duration("", "") == "0h"

    def test_none_dates(self):
        from export_trades import calc_duration
        assert calc_duration(None, None) == "0h"

    def test_invalid_dates(self):
        from export_trades import calc_duration
        assert calc_duration("bad", "data") == "N/A"


class TestExportTradesBuildSummary:
    def test_empty_trades(self):
        from export_trades import build_summary
        s = build_summary([])
        assert s["total_trades"] == 0
        assert s["win_rate"] == 0

    def test_with_trades(self, sample_trades):
        from export_trades import build_summary
        s = build_summary(sample_trades)
        assert s["total_trades"] == 3
        assert s["win_rate"] == pytest.approx(66.7, abs=0.1)
        assert s["total_profit_pct"] == pytest.approx(6.0, abs=0.01)
        assert s["total_profit_usd"] == pytest.approx(12.0, abs=0.01)

    def test_best_worst_trade(self, sample_trades):
        from export_trades import build_summary
        s = build_summary(sample_trades)
        assert s["best_trade"]["pair"] == "SOL/USDT:USDT"
        assert s["worst_trade"]["pair"] == "ETH/USDT:USDT"

    def test_by_pair_present(self, sample_trades):
        from export_trades import build_summary
        s = build_summary(sample_trades)
        assert "BTC/USDT:USDT" in s["by_pair"]
        assert s["by_pair"]["BTC/USDT:USDT"]["trades"] == 1


# ═══════════════════════════════════════════════════════════════════════
# export_to_sheets.py
# ═══════════════════════════════════════════════════════════════════════

class TestExportToSheetsCalcDuration:
    def test_hours(self):
        from export_to_sheets import calc_duration
        assert calc_duration("2026-03-01 10:00:00", "2026-03-01 14:30:00") == "4.5h"

    def test_minutes(self):
        from export_to_sheets import calc_duration
        assert calc_duration("2026-03-01 10:00:00", "2026-03-01 10:20:00") == "20m"

    def test_empty(self):
        from export_to_sheets import calc_duration
        assert calc_duration("", "") == "0h"


class TestExportToSheetsCalcDurationHours:
    def test_numeric(self):
        from export_to_sheets import calc_duration_hours
        assert calc_duration_hours("2026-03-01 10:00:00", "2026-03-01 14:30:00") == pytest.approx(4.5)

    def test_empty(self):
        from export_to_sheets import calc_duration_hours
        assert calc_duration_hours("", "") == 0.0


class TestExportToSheetsTradeToRow:
    def test_row_length(self, sample_trades):
        from export_to_sheets import trade_to_row
        row = trade_to_row(sample_trades[0])
        assert len(row) == 11

    def test_direction_long(self, sample_trades):
        from export_to_sheets import trade_to_row
        row = trade_to_row(sample_trades[0])
        assert row[2] == "long"

    def test_direction_short(self):
        from export_to_sheets import trade_to_row
        trade = {
            "close_date": "2026-03-01 14:00:00",
            "pair": "BTC/USDT",
            "open_rate": 64000.0,
            "close_rate": 62000.0,
            "stake_amount": 200.0,
            "profit_abs": 8.0,
            "profit_ratio": 0.04,
            "open_date": "2026-03-01 10:00:00",
            "strategy": "TrendRider",
            "exit_reason": "roi",
            "leverage": -3,
        }
        row = trade_to_row(trade)
        assert row[2] == "short"


class TestExportToSheetsTracker:
    def test_read_write_last_id(self, tmp_path):
        from export_to_sheets import read_last_id, write_last_id
        tracker = str(tmp_path / ".tracker")
        assert read_last_id(tracker) == 0
        write_last_id(tracker, 42)
        assert read_last_id(tracker) == 42

    def test_read_missing_file(self, tmp_path):
        from export_to_sheets import read_last_id
        assert read_last_id(str(tmp_path / "nonexistent")) == 0


class TestExportToSheetsCalculateMetrics:
    def test_empty(self):
        from export_to_sheets import calculate_metrics
        assert calculate_metrics([]) == {}

    def test_with_trades(self, sample_trades):
        from export_to_sheets import calculate_metrics
        m = calculate_metrics(sample_trades)
        assert m["total_trades"] == 3
        assert m["win_rate"] == pytest.approx(66.7, abs=0.1)
        assert m["total_pnl_usdt"] == pytest.approx(12.0, abs=0.01)

    def test_max_drawdown(self):
        from export_to_sheets import calculate_metrics
        trades = [
            {"pair": "BTC/USDT", "profit_abs": 10, "profit_ratio": 0.05,
             "open_date": "2026-01-01 00:00:00", "close_date": "2026-01-01 04:00:00"},
            {"pair": "BTC/USDT", "profit_abs": -15, "profit_ratio": -0.075,
             "open_date": "2026-01-02 00:00:00", "close_date": "2026-01-02 04:00:00"},
            {"pair": "BTC/USDT", "profit_abs": 5, "profit_ratio": 0.025,
             "open_date": "2026-01-03 00:00:00", "close_date": "2026-01-03 04:00:00"},
        ]
        m = calculate_metrics(trades)
        assert m["max_drawdown_pct"] > 0

    def test_profit_factor(self):
        from export_to_sheets import calculate_metrics
        trades = [
            {"pair": "A", "profit_abs": 10, "profit_ratio": 0.05,
             "open_date": "2026-01-01 00:00:00", "close_date": "2026-01-01 04:00:00"},
            {"pair": "A", "profit_abs": -5, "profit_ratio": -0.025,
             "open_date": "2026-01-02 00:00:00", "close_date": "2026-01-02 04:00:00"},
        ]
        m = calculate_metrics(trades)
        assert m["profit_factor"] == 2.0

    def test_sqn_calculation(self):
        from export_to_sheets import calculate_metrics
        trades = [
            {"pair": "A", "profit_abs": 10, "profit_ratio": 0.05,
             "open_date": "2026-01-01 00:00:00", "close_date": "2026-01-01 04:00:00"},
            {"pair": "A", "profit_abs": 8, "profit_ratio": 0.04,
             "open_date": "2026-01-02 00:00:00", "close_date": "2026-01-02 04:00:00"},
            {"pair": "A", "profit_abs": -2, "profit_ratio": -0.01,
             "open_date": "2026-01-03 00:00:00", "close_date": "2026-01-03 04:00:00"},
        ]
        m = calculate_metrics(trades)
        assert isinstance(m["sqn"], float)

    def test_no_losses_profit_factor(self):
        from export_to_sheets import calculate_metrics
        trades = [
            {"pair": "A", "profit_abs": 10, "profit_ratio": 0.05,
             "open_date": "2026-01-01 00:00:00", "close_date": "2026-01-01 04:00:00"},
        ]
        m = calculate_metrics(trades)
        assert m["profit_factor"] == "N/A (no losses)"


class TestExportToSheetsCalculateMonthly:
    def test_single_month(self, sample_trades):
        from export_to_sheets import calculate_monthly
        rows = calculate_monthly(sample_trades)
        assert len(rows) == 1
        # sample_trades uses relative dates (now - 10/8/5 days), so month depends on current date
        expected_month = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m")
        assert rows[0][0] == expected_month
        assert rows[0][1] == "3"

    def test_multiple_months(self):
        from export_to_sheets import calculate_monthly
        trades = [
            {"close_date": "2026-01-15 10:00:00", "profit_abs": 5, "profit_ratio": 0.025},
            {"close_date": "2026-02-15 10:00:00", "profit_abs": -3, "profit_ratio": -0.015},
        ]
        rows = calculate_monthly(trades)
        assert len(rows) == 2
        assert rows[0][0] == "2026-01"
        assert rows[1][0] == "2026-02"

    def test_empty(self):
        from export_to_sheets import calculate_monthly
        assert calculate_monthly([]) == []


class TestExportToSheetsFmtDt:
    def test_normal(self):
        from export_to_sheets import fmt_dt
        assert fmt_dt("2026-03-01 10:00:00") == "2026-03-01T10:00:00"

    def test_none(self):
        from export_to_sheets import fmt_dt
        assert fmt_dt(None) == ""


# ═══════════════════════════════════════════════════════════════════════
# oi_funding_alerts.py
# ═══════════════════════════════════════════════════════════════════════

class TestOiAlertToSymbol:
    def test_standard(self):
        from oi_funding_alerts import to_symbol
        assert to_symbol("BTC/USDT") == "BTCUSDT"

    def test_with_colon(self):
        from oi_funding_alerts import to_symbol
        assert to_symbol("ETH/USDT:USDT") == "ETHUSDT"


class TestOiAlertFormatOi:
    def test_billions(self):
        from oi_funding_alerts import format_oi
        assert format_oi(2_500_000_000) == "$2.5B"

    def test_millions(self):
        from oi_funding_alerts import format_oi
        assert format_oi(150_000_000) == "$150.0M"

    def test_thousands(self):
        from oi_funding_alerts import format_oi
        assert format_oi(50_000) == "$50,000"


class TestOiAlertBuildOiAlert:
    def test_surge(self):
        from oi_funding_alerts import build_oi_alert
        msg = build_oi_alert("BTC/USDT", 1_000_000_000, 7.5)
        assert "surged" in msg
        assert "+7.5%" in msg
        assert "$1.0B" in msg
        assert "MARKET ALERT" in msg

    def test_drop(self):
        from oi_funding_alerts import build_oi_alert
        msg = build_oi_alert("ETH/USDT", 500_000_000, -6.0)
        assert "dropped" in msg
        assert "-6.0%" in msg


class TestOiAlertBuildFundingAlert:
    def test_positive_funding(self):
        from oi_funding_alerts import build_funding_alert
        msg = build_funding_alert("BTC/USDT", 0.0004, extreme=False)
        assert "HIGH FUNDING" in msg
        assert "longs paying shorts" in msg
        assert "overleveraged longs" in msg
        assert "Elevated" in msg

    def test_negative_extreme(self):
        from oi_funding_alerts import build_funding_alert
        msg = build_funding_alert("ETH/USDT", -0.0006, extreme=True)
        assert "EXTREME FUNDING" in msg
        assert "shorts paying longs" in msg
        assert "Extremely high" in msg


class TestOiAlertCooldown:
    def test_not_on_cooldown_empty(self):
        from oi_funding_alerts import is_on_cooldown
        assert is_on_cooldown({}, "test_key") is False

    def test_on_cooldown_recent(self):
        from oi_funding_alerts import is_on_cooldown
        now = datetime.now(timezone.utc)
        cooldowns = {"test_key": now.isoformat(timespec="seconds")}
        assert is_on_cooldown(cooldowns, "test_key") is True

    def test_expired_cooldown(self):
        from oi_funding_alerts import is_on_cooldown
        old = datetime.now(timezone.utc) - timedelta(hours=5)
        cooldowns = {"test_key": old.isoformat(timespec="seconds")}
        assert is_on_cooldown(cooldowns, "test_key") is False

    def test_set_cooldown(self):
        from oi_funding_alerts import set_cooldown, is_on_cooldown
        cooldowns = {}
        set_cooldown(cooldowns, "new_key")
        assert "new_key" in cooldowns
        assert is_on_cooldown(cooldowns, "new_key") is True

    def test_invalid_timestamp(self):
        from oi_funding_alerts import is_on_cooldown
        cooldowns = {"bad": "not-a-date"}
        assert is_on_cooldown(cooldowns, "bad") is False


class TestOiAlertCooldownFile:
    def test_load_save_roundtrip(self, tmp_path):
        import oi_funding_alerts as oia
        cooldown_file = str(tmp_path / "cooldowns.json")
        original = oia.COOLDOWN_FILE
        oia.COOLDOWN_FILE = cooldown_file
        try:
            # Initially empty
            c = oia.load_cooldowns()
            assert c == {}

            # Save and reload
            oia.set_cooldown(c, "test")
            oia.save_cooldowns(c)
            c2 = oia.load_cooldowns()
            assert "test" in c2
        finally:
            oia.COOLDOWN_FILE = original


# ═══════════════════════════════════════════════════════════════════════
# monday_context.py
# ═══════════════════════════════════════════════════════════════════════

class TestMondayContextFormatPrice:
    def test_large(self):
        from monday_context import format_price
        assert format_price(64000) == "$64,000"

    def test_medium(self):
        from monday_context import format_price
        assert format_price(3.50) == "$3.50"

    def test_small(self):
        from monday_context import format_price
        assert format_price(0.0001) == "$0.0001"


class TestMondayContextBuildObservations:
    def test_bullish_btc(self):
        from monday_context import _build_observations
        btc = {"error": False, "trend": "Uptrend", "rsi": 55.0, "adx": 30.0}
        obs = _build_observations(btc, 50, "Neutral")
        assert any("bullish" in o.lower() for o in obs)

    def test_bearish_btc(self):
        from monday_context import _build_observations
        btc = {"error": False, "trend": "Downtrend", "rsi": 25.0, "adx": 15.0}
        obs = _build_observations(btc, 20, "Extreme Fear")
        assert any("caution" in o.lower() for o in obs)
        assert any("oversold" in o.lower() for o in obs)

    def test_extreme_fear(self):
        from monday_context import _build_observations
        obs = _build_observations(None, 15, "Extreme Fear")
        assert any("Extreme Fear" in o for o in obs)

    def test_extreme_greed(self):
        from monday_context import _build_observations
        obs = _build_observations(None, 80, "Extreme Greed")
        assert any("Extreme Greed" in o for o in obs)

    def test_no_btc_fallback(self):
        from monday_context import _build_observations
        obs = _build_observations(None, -1, "N/A")
        assert len(obs) >= 1

    def test_overbought_rsi(self):
        from monday_context import _build_observations
        btc = {"error": False, "trend": "Uptrend", "rsi": 75.0, "adx": 25.0}
        obs = _build_observations(btc, 60, "Greed")
        assert any("overbought" in o.lower() for o in obs)

    def test_rsi_leaning_bullish(self):
        from monday_context import _build_observations
        btc = {"error": False, "trend": "Uptrend", "rsi": 65.0, "adx": 20.0}
        obs = _build_observations(btc, 50, "Neutral")
        assert any("bullish" in o.lower() for o in obs)


class TestMondayContextBuildMessage:
    """Test build_message with platform-safe date format."""

    def _call_build_message(self, results, fng_value, fng_label):
        import monday_context as mc
        from monday_context import build_message
        SafeDatetime = _make_safe_datetime()
        original_dt = mc.datetime
        mc.datetime = SafeDatetime
        try:
            return build_message(results, fng_value, fng_label)
        finally:
            mc.datetime = original_dt

    def test_structure(self):
        results = [
            {
                "symbol": "BTC/USDT", "error": False,
                "price": 64000, "change_7d": 5.0, "rsi": 55.0,
                "trend": "Uptrend", "ema50": 62000, "ema200": 58000,
                "adx": 30.0,
            },
        ]
        msg = self._call_build_message(results, 55, "Greed")
        assert "WEEKLY MARKET CONTEXT" in msg
        assert "MACRO OVERVIEW" in msg
        assert "WATCHLIST" in msg
        assert "WHAT WE'RE WATCHING" in msg
        assert "TrendRider" in msg

    def test_error_pair(self):
        results = [{"symbol": "SOL/USDT", "error": True}]
        msg = self._call_build_message(results, 50, "Neutral")
        assert "data unavailable" in msg


# ═══════════════════════════════════════════════════════════════════════
# friday_recap.py
# ═══════════════════════════════════════════════════════════════════════

class TestFridayRecapSign:
    def test_positive(self):
        from friday_recap import _sign
        assert _sign(5.0) == "+"

    def test_negative(self):
        from friday_recap import _sign
        assert _sign(-3.0) == ""

    def test_zero(self):
        from friday_recap import _sign
        assert _sign(0.0) == "+"


class TestFridayRecapComputeStats:
    def test_empty(self):
        from friday_recap import compute_stats
        s = compute_stats([])
        assert s["total"] == 0

    def test_with_trades(self, sample_trades):
        from friday_recap import compute_stats
        s = compute_stats(sample_trades)
        assert s["total"] == 3
        assert s["wins"] == 2
        assert s["losses"] == 1
        assert s["win_rate"] == pytest.approx(66.67, abs=0.1)
        assert s["total_profit_pct"] == pytest.approx(6.0, abs=0.01)

    def test_pair_stats(self, sample_trades):
        from friday_recap import compute_stats
        s = compute_stats(sample_trades)
        pairs = dict(s["pair_stats"])
        assert "BTC/USDT:USDT" in pairs


class TestFridayRecapBuildWeeklyMessage:
    def test_contains_sections(self, sample_trades):
        from friday_recap import compute_stats, build_weekly_message
        week = compute_stats(sample_trades)
        running = compute_stats(sample_trades)
        msg = build_weekly_message(week, running)
        assert "WEEKLY RECAP" in msg
        assert "PERFORMANCE" in msg
        assert "HIGHLIGHTS" in msg
        assert "BY PAIR" in msg
        assert "RUNNING (30 DAYS)" in msg
        assert "TrendRider" in msg


class TestFridayRecapBuildQuietMessage:
    def test_no_trades_this_week(self, sample_trades):
        from friday_recap import compute_stats, build_quiet_message
        running = compute_stats(sample_trades)
        msg = build_quiet_message(running)
        assert "No trades closed this week" in msg
        assert "RUNNING (30 DAYS)" in msg

    def test_no_trades_at_all(self):
        from friday_recap import compute_stats, build_quiet_message
        running = compute_stats([])
        msg = build_quiet_message(running)
        assert "No trades in the last 30 days" in msg


class TestFridayRecapFormatDateRange:
    def test_returns_string(self):
        import friday_recap as fr
        SafeDatetime = _make_safe_datetime()
        original_dt = fr.datetime
        fr.datetime = SafeDatetime
        try:
            result = fr.format_date_range()
            assert isinstance(result, str)
            assert len(result) > 0
        finally:
            fr.datetime = original_dt


# ═══════════════════════════════════════════════════════════════════════
# monthly_report.py
# ═══════════════════════════════════════════════════════════════════════

class TestMonthlyReportComputeStreaks:
    def test_all_wins(self):
        from monthly_report import compute_streaks
        wins, losses = compute_streaks([0.05, 0.03, 0.01])
        assert wins == 3
        assert losses == 0

    def test_all_losses(self):
        from monthly_report import compute_streaks
        wins, losses = compute_streaks([-0.02, -0.01, -0.03])
        assert wins == 0
        assert losses == 3

    def test_mixed(self):
        from monthly_report import compute_streaks
        wins, losses = compute_streaks([0.05, 0.03, -0.02, -0.01, 0.04])
        assert wins == 2
        assert losses == 2

    def test_empty(self):
        from monthly_report import compute_streaks
        wins, losses = compute_streaks([])
        assert wins == 0
        assert losses == 0


class TestMonthlyReportFormatDuration:
    def test_hours_minutes(self):
        from monthly_report import format_duration
        assert format_duration(3600 * 5 + 1800) == "5h 30m"

    def test_days(self):
        from monthly_report import format_duration
        assert format_duration(3600 * 50) == "2d 2h"

    def test_zero(self):
        from monthly_report import format_duration
        assert format_duration(0) == "N/A"

    def test_negative(self):
        from monthly_report import format_duration
        assert format_duration(-100) == "N/A"


class TestMonthlyReportGetPreviousMonth:
    def test_march(self):
        from monthly_report import get_previous_month
        today = datetime(2026, 3, 15, tzinfo=timezone.utc)
        start, end, name, year = get_previous_month(today)
        assert name == "February"
        assert year == 2026
        assert start.month == 2
        assert end.month == 3

    def test_january_wraps_to_december(self):
        from monthly_report import get_previous_month
        today = datetime(2026, 1, 10, tzinfo=timezone.utc)
        start, end, name, year = get_previous_month(today)
        assert name == "December"
        assert year == 2025
        assert start.month == 12


class TestMonthlyReportParseMonthArg:
    def test_valid(self):
        from monthly_report import parse_month_arg
        start, end, name, year = parse_month_arg("2026-03")
        assert name == "March"
        assert year == 2026
        assert start.month == 3
        assert end.month == 4

    def test_december(self):
        from monthly_report import parse_month_arg
        start, end, name, year = parse_month_arg("2026-12")
        assert name == "December"
        assert end.year == 2027
        assert end.month == 1

    def test_invalid_exits(self):
        from monthly_report import parse_month_arg
        with pytest.raises(SystemExit):
            parse_month_arg("bad-format")


class TestMonthlyReportComputeStats:
    def test_empty(self):
        from monthly_report import compute_stats
        s = compute_stats([])
        assert s["total"] == 0

    def test_with_trades(self):
        from monthly_report import compute_stats
        trades = [
            {
                "pair": "BTC/USDT", "profit_ratio": 0.03,
                "close_profit_abs": 6.0, "close_date": "2026-03-01 14:00:00",
                "open_date": "2026-03-01 10:00:00", "stake_amount": 200,
                "exit_reason": "roi",
            },
            {
                "pair": "ETH/USDT", "profit_ratio": -0.02,
                "close_profit_abs": -4.0, "close_date": "2026-03-02 20:00:00",
                "open_date": "2026-03-02 08:00:00", "stake_amount": 200,
                "exit_reason": "stop_loss",
            },
        ]
        s = compute_stats(trades)
        assert s["total"] == 2
        assert s["wins"] == 1
        assert s["losses"] == 1
        assert s["win_rate"] == 50.0
        assert s["win_streak"] == 1
        assert s["loss_streak"] == 1

    def test_avg_duration(self):
        from monthly_report import compute_stats
        trades = [
            {
                "pair": "BTC/USDT", "profit_ratio": 0.03,
                "close_profit_abs": 6.0,
                "close_date": "2026-03-01 14:00:00",
                "open_date": "2026-03-01 10:00:00",
                "stake_amount": 200, "exit_reason": "roi",
            },
        ]
        s = compute_stats(trades)
        assert s["avg_duration_secs"] == pytest.approx(4 * 3600, abs=1)


class TestMonthlyReportBuildMessage:
    def test_monthly_message_structure(self):
        from monthly_report import compute_stats, build_monthly_message
        trades = [
            {
                "pair": "BTC/USDT", "profit_ratio": 0.03,
                "close_profit_abs": 6.0, "close_date": "2026-03-01 14:00:00",
                "open_date": "2026-03-01 10:00:00", "stake_amount": 200,
                "exit_reason": "roi",
            },
        ]
        s = compute_stats(trades)
        msg = build_monthly_message(s, "March", 2026)
        assert "March 2026" in msg
        assert "Performance" in msg
        assert "By Pair" in msg
        assert "Streaks" in msg

    def test_no_trades_message(self):
        from monthly_report import build_no_trades_message
        msg = build_no_trades_message("February", 2026)
        assert "February 2026" in msg
        assert "No trades closed this month" in msg


# ═══════════════════════════════════════════════════════════════════════
# shared_utils.py
# ═══════════════════════════════════════════════════════════════════════

class TestSharedUtilsQueryStats:
    def setup_method(self):
        """Ensure real shared_utils is loaded, not a mock from other test files.

        test_subscription_menu.py installs a mock shared_utils into sys.modules
        at import time. If that runs first, 'from shared_utils import query_stats'
        returns the mock. Fix: detect mock and force reimport of the real module.
        """
        mod = sys.modules.get("shared_utils")
        if mod is not None and not hasattr(mod, '__file__'):
            # It's a mock — remove it so the real module gets imported
            sys.modules.pop("shared_utils", None)
        elif mod is not None and mod.__file__ is not None:
            # Real module already loaded — reload to clear any patches
            import importlib
            importlib.reload(mod)

    def test_no_database(self, tmp_path):
        from shared_utils import query_stats
        result = query_stats(str(tmp_path / "nonexistent.db"))
        assert "No database found" in result

    def test_no_trades(self, tmp_path):
        from shared_utils import query_stats
        db_path = str(tmp_path / "empty.db")
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY, pair TEXT, open_date TEXT,
                close_date TEXT, open_rate REAL, close_rate REAL,
                close_profit_abs REAL, close_profit REAL,
                stake_amount REAL, is_open INTEGER
            )
        """)
        conn.commit()
        conn.close()
        result = query_stats(db_path)
        assert "No trades yet" in result

    def test_with_trades(self, tmp_sqlite):
        from shared_utils import query_stats
        result = query_stats(tmp_sqlite)
        assert "TRENDRIDER STATS" in result
        assert "Win Rate" in result
        assert "By Pair" in result
        assert "BTC" in result

    def test_stats_numbers(self, tmp_sqlite):
        from shared_utils import query_stats
        result = query_stats(tmp_sqlite)
        assert "Win: 2" in result
        assert "Loss: 1" in result


# ═══════════════════════════════════════════════════════════════════════
# equity_curve.py
# ═══════════════════════════════════════════════════════════════════════

class TestEquityCurveFetchTrades:
    def test_fetch_trades_from_db(self, tmp_sqlite):
        import equity_curve
        trades = equity_curve.fetch_trades(tmp_sqlite)
        assert len(trades) == 3
        assert all("close_date" in t for t in trades)


class TestEquityCurveBuildChart:
    def test_returns_png_bytes(self):
        """Test that build_chart produces valid PNG bytes."""
        import equity_curve
        trades = [
            {"close_date": "2026-03-01 10:00:00", "close_profit_abs": 5.0, "profit_ratio": 0.025, "pair": "BTC/USDT"},
            {"close_date": "2026-03-02 10:00:00", "close_profit_abs": -2.0, "profit_ratio": -0.01, "pair": "ETH/USDT"},
            {"close_date": "2026-03-03 10:00:00", "close_profit_abs": 8.0, "profit_ratio": 0.04, "pair": "SOL/USDT"},
        ]
        result = equity_curve.build_chart(trades, 1000.0)
        assert isinstance(result, bytes)
        assert len(result) > 1000
        # PNG magic bytes
        assert result[:8] == b'\x89PNG\r\n\x1a\n'


# ═══════════════════════════════════════════════════════════════════════
# Cross-script consistency tests
# ═══════════════════════════════════════════════════════════════════════

class TestCrossScriptConsistency:
    def test_sheet_columns_match(self):
        """export_to_sheets and setup_sheets must have matching column lists."""
        from export_to_sheets import SHEET_COLUMNS as cols1
        from setup_sheets import SHEET_COLUMNS as cols2
        assert cols1 == cols2

    def test_dashboard_labels_match(self):
        """export_to_sheets and setup_sheets must have matching dashboard labels."""
        from export_to_sheets import DASHBOARD_METRIC_LABELS as labels1
        from setup_sheets import DASHBOARD_METRIC_LABELS as labels2
        assert labels1 == labels2

    def test_monthly_headers_match(self):
        """export_to_sheets and setup_sheets must have matching monthly headers."""
        from export_to_sheets import MONTHLY_HEADERS as h1
        from setup_sheets import MONTHLY_HEADERS as h2
        assert h1 == h2
