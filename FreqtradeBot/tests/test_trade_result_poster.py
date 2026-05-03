"""Tests for the Trade Result Poster script."""

import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

# Ensure scripts/ is importable
SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import trade_result_poster  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────

def _create_test_db(db_path: Path, trades: list[dict]) -> None:
    """Create a minimal Freqtrade-like trades table with test data."""
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY,
            pair TEXT,
            trade_direction TEXT,
            is_short INTEGER DEFAULT 0,
            open_date TEXT,
            close_date TEXT,
            stake_amount REAL,
            open_rate REAL,
            close_rate REAL,
            close_profit REAL,
            close_profit_abs REAL,
            exit_reason TEXT,
            sell_reason TEXT,
            enter_tag TEXT,
            leverage REAL DEFAULT 1,
            is_open INTEGER DEFAULT 0
        )
        """
    )
    for t in trades:
        conn.execute(
            """
            INSERT INTO trades (id, pair, trade_direction, is_short, open_date,
                                close_date, stake_amount, open_rate, close_rate,
                                close_profit, close_profit_abs, exit_reason,
                                sell_reason, enter_tag, leverage, is_open)
            VALUES (:id, :pair, :trade_direction, :is_short, :open_date,
                    :close_date, :stake_amount, :open_rate, :close_rate,
                    :close_profit, :close_profit_abs, :exit_reason,
                    :sell_reason, :enter_tag, :leverage, :is_open)
            """,
            {
                "id": t.get("id", 1),
                "pair": t.get("pair", "BTC/USDT:USDT"),
                "trade_direction": t.get("trade_direction", "long"),
                "is_short": t.get("is_short", 0),
                "open_date": t.get("open_date", "2026-03-25 10:00:00"),
                "close_date": t.get("close_date", "2026-03-25 14:32:00"),
                "stake_amount": t.get("stake_amount", 100.0),
                "open_rate": t.get("open_rate", 67234.50),
                "close_rate": t.get("close_rate", 68891.20),
                "close_profit": t.get("close_profit", 0.0246),
                "close_profit_abs": t.get("close_profit_abs", 2.46),
                "exit_reason": t.get("exit_reason", "roi"),
                "sell_reason": t.get("sell_reason"),
                "enter_tag": t.get("enter_tag", "trend_pullback"),
                "leverage": t.get("leverage", 3),
                "is_open": t.get("is_open", 0),
            },
        )
    conn.commit()
    conn.close()


SAMPLE_WINNING_TRADE = {
    "id": 1,
    "pair": "BTC/USDT:USDT",
    "trade_direction": "long",
    "is_short": 0,
    "open_date": "2026-03-25 10:00:00",
    "close_date": "2026-03-25 14:32:00",
    "stake_amount": 100.0,
    "open_rate": 67234.50,
    "close_rate": 68891.20,
    "close_profit": 0.0246,
    "close_profit_abs": 2.46,
    "exit_reason": "roi",
    "enter_tag": "trend_pullback",
    "leverage": 3,
    "is_open": 0,
}

SAMPLE_LOSING_TRADE = {
    "id": 2,
    "pair": "ETH/USDT:USDT",
    "trade_direction": "long",
    "is_short": 0,
    "open_date": "2026-03-25 08:00:00",
    "close_date": "2026-03-25 09:15:00",
    "stake_amount": 50.0,
    "open_rate": 3500.0,
    "close_rate": 3290.0,
    "close_profit": -0.06,
    "close_profit_abs": -3.0,
    "exit_reason": "stop_loss",
    "enter_tag": "ema50_bounce",
    "leverage": 3,
    "is_open": 0,
}

SAMPLE_SHORT_TRADE = {
    "id": 3,
    "pair": "SOL/USDT:USDT",
    "trade_direction": "short",
    "is_short": 1,
    "open_date": "2026-03-24 20:00:00",
    "close_date": "2026-03-25 08:45:00",
    "stake_amount": 75.0,
    "open_rate": 145.30,
    "close_rate": 138.50,
    "close_profit": 0.0468,
    "close_profit_abs": 3.51,
    "exit_reason": "trailing_stop_loss",
    "enter_tag": "",
    "leverage": 3,
    "is_open": 0,
}

SAMPLE_STATS = {
    "wins": 26,
    "losses": 12,
    "total_trades": 38,
    "win_rate": 68.4,
    "total_profit_pct": 18.7,
}

EMPTY_STATS = {
    "wins": 0,
    "losses": 0,
    "total_trades": 0,
    "win_rate": 0.0,
    "total_profit_pct": 0.0,
}


# ─────────────────────────────────────────────────────────────────────────
# 1. State management
# ─────────────────────────────────────────────────────────────────────────

class TestStateManagement:
    """Test load/save of the state file."""

    def test_load_state_missing_file(self, tmp_path):
        with patch.object(trade_result_poster, "STATE_FILE", tmp_path / "missing.json"):
            state = trade_result_poster.load_state()
        assert state == {"last_posted_trade_id": 0, "trade_counter": 0}

    def test_load_state_valid(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_posted_trade_id": 42, "trade_counter": 15}))
        with patch.object(trade_result_poster, "STATE_FILE", state_file):
            state = trade_result_poster.load_state()
        assert state["last_posted_trade_id"] == 42
        assert state["trade_counter"] == 15

    def test_save_state(self, tmp_path):
        state_file = tmp_path / "sub" / "state.json"
        with patch.object(trade_result_poster, "STATE_FILE", state_file):
            trade_result_poster.save_state({"last_posted_trade_id": 7, "trade_counter": 3})
        assert state_file.exists()
        data = json.loads(state_file.read_text())
        assert data["last_posted_trade_id"] == 7
        assert data["trade_counter"] == 3

    def test_load_state_corrupt_json(self, tmp_path):
        state_file = tmp_path / "corrupt.json"
        state_file.write_text("{bad json")
        with patch.object(trade_result_poster, "STATE_FILE", state_file):
            state = trade_result_poster.load_state()
        assert state == {"last_posted_trade_id": 0, "trade_counter": 0}


# ─────────────────────────────────────────────────────────────────────────
# 2. Database queries
# ─────────────────────────────────────────────────────────────────────────

class TestFetchClosedTrades:
    """Test fetching closed trades from SQLite."""

    def test_fetch_returns_closed_trades(self, tmp_path):
        db = tmp_path / "trades.sqlite"
        _create_test_db(db, [
            SAMPLE_WINNING_TRADE,
            SAMPLE_LOSING_TRADE,
            {**SAMPLE_SHORT_TRADE, "id": 3, "is_open": 1, "close_date": None},  # open — skip
        ])
        trades = trade_result_poster.fetch_closed_trades(db, last_id=0)
        assert len(trades) == 2
        assert trades[0]["pair"] == "BTC/USDT:USDT"
        assert trades[1]["pair"] == "ETH/USDT:USDT"

    def test_fetch_skips_already_posted(self, tmp_path):
        db = tmp_path / "trades.sqlite"
        _create_test_db(db, [SAMPLE_WINNING_TRADE, SAMPLE_LOSING_TRADE])
        trades = trade_result_poster.fetch_closed_trades(db, last_id=1)
        assert len(trades) == 1
        assert trades[0]["id"] == 2

    def test_fetch_no_new_trades(self, tmp_path):
        db = tmp_path / "trades.sqlite"
        _create_test_db(db, [SAMPLE_WINNING_TRADE])
        trades = trade_result_poster.fetch_closed_trades(db, last_id=1)
        assert trades == []

    def test_fetch_missing_db(self, tmp_path):
        db = tmp_path / "nonexistent.sqlite"
        trades = trade_result_poster.fetch_closed_trades(db, last_id=0)
        assert trades == []

    def test_fetch_excludes_open_trades(self, tmp_path):
        db = tmp_path / "trades.sqlite"
        open_trade = {**SAMPLE_WINNING_TRADE, "is_open": 1, "close_date": None}
        _create_test_db(db, [open_trade])
        trades = trade_result_poster.fetch_closed_trades(db, last_id=0)
        assert trades == []


class TestFetchRunningStats:
    """Test running stats query."""

    def test_stats_with_trades(self, tmp_path):
        # Use a recent close_date so the 30-day window in fetch_running_stats
        # always captures these fixtures regardless of when CI runs.
        from datetime import datetime, timedelta, timezone

        recent = (datetime.now(timezone.utc) - timedelta(days=1)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        db = tmp_path / "trades.sqlite"
        _create_test_db(db, [
            {**SAMPLE_WINNING_TRADE, "id": 1, "close_profit": 0.03, "close_date": recent},
            {**SAMPLE_LOSING_TRADE, "id": 2, "close_profit": -0.02, "close_date": recent},
            {**SAMPLE_WINNING_TRADE, "id": 3, "close_profit": 0.05, "close_date": recent},
        ])
        stats = trade_result_poster.fetch_running_stats(db)
        assert stats["wins"] == 2
        assert stats["losses"] == 1
        assert stats["total_trades"] == 3
        assert abs(stats["win_rate"] - 66.7) < 0.1
        assert abs(stats["total_profit_pct"] - 6.0) < 0.01

    def test_stats_missing_db(self, tmp_path):
        db = tmp_path / "nonexistent.sqlite"
        stats = trade_result_poster.fetch_running_stats(db)
        assert stats["total_trades"] == 0

    def test_stats_no_closed_trades(self, tmp_path):
        db = tmp_path / "trades.sqlite"
        open_trade = {**SAMPLE_WINNING_TRADE, "is_open": 1, "close_date": None}
        _create_test_db(db, [open_trade])
        stats = trade_result_poster.fetch_running_stats(db)
        assert stats["total_trades"] == 0


# ─────────────────────────────────────────────────────────────────────────
# 3. Duration formatting
# ─────────────────────────────────────────────────────────────────────────

class TestFormatDuration:
    """Test duration string formatting."""

    def test_hours_and_minutes(self):
        result = trade_result_poster.format_duration(
            "2026-03-25 10:00:00", "2026-03-25 14:32:00"
        )
        assert result == "4h 32m"

    def test_minutes_only(self):
        result = trade_result_poster.format_duration(
            "2026-03-25 10:00:00", "2026-03-25 10:45:00"
        )
        assert result == "45m"

    def test_days_and_hours(self):
        result = trade_result_poster.format_duration(
            "2026-03-23 10:00:00", "2026-03-25 14:00:00"
        )
        assert result == "2d 4h"

    def test_with_microseconds(self):
        result = trade_result_poster.format_duration(
            "2026-03-25 10:00:00.123456", "2026-03-25 12:30:00.654321"
        )
        assert result == "2h 30m"

    def test_invalid_dates(self):
        result = trade_result_poster.format_duration("bad", "dates")
        assert result == "N/A"

    def test_with_timezone_suffix(self):
        result = trade_result_poster.format_duration(
            "2026-03-25 10:00:00+00:00", "2026-03-25 13:00:00+00:00"
        )
        assert result == "3h 0m"


# ─────────────────────────────────────────────────────────────────────────
# 4. Direction detection
# ─────────────────────────────────────────────────────────────────────────

class TestGetDirection:
    """Test trade direction detection."""

    def test_long_from_trade_direction(self):
        assert trade_result_poster.get_direction({"trade_direction": "long"}) == "LONG"

    def test_short_from_trade_direction(self):
        assert trade_result_poster.get_direction({"trade_direction": "short"}) == "SHORT"

    def test_short_from_is_short_bool(self):
        assert trade_result_poster.get_direction({"is_short": True}) == "SHORT"

    def test_long_from_is_short_false(self):
        assert trade_result_poster.get_direction({"is_short": False}) == "LONG"

    def test_short_from_is_short_int(self):
        assert trade_result_poster.get_direction({"is_short": 1}) == "SHORT"

    def test_default_long(self):
        assert trade_result_poster.get_direction({}) == "LONG"


# ─────────────────────────────────────────────────────────────────────────
# 5. Price formatting
# ─────────────────────────────────────────────────────────────────────────

class TestFormatPrice:
    """Test price formatting."""

    def test_large_price(self):
        assert trade_result_poster.format_price(67234.50) == "$67,234.50"

    def test_medium_price(self):
        assert trade_result_poster.format_price(145.3) == "$145.3000"

    def test_small_price(self):
        assert trade_result_poster.format_price(0.00123) == "$0.001230"

    def test_none_price(self):
        assert trade_result_poster.format_price(None) == "N/A"

    def test_zero_price(self):
        assert trade_result_poster.format_price(0) == "N/A"


# ─────────────────────────────────────────────────────────────────────────
# 6. Trade result card formatting
# ─────────────────────────────────────────────────────────────────────────

class TestFormatTradeResult:
    """Test the main trade result card formatting."""

    def test_winning_trade_card(self):
        msg = trade_result_poster.format_trade_result(
            SAMPLE_WINNING_TRADE, trade_number=42, stats=SAMPLE_STATS
        )
        assert "Trade Result #042" in msg
        assert "LONG" in msg
        assert "BTC/USDT:USDT" in msg
        assert "+2.46%" in msg
        assert "\u2705" in msg  # checkmark
        assert "4h 32m" in msg
        assert "ROI target reached" in msg
        assert "Trend Pullback" in msg
        assert "3x" in msg
        # Stats section
        assert "68.4%" in msg
        assert "26W" in msg
        assert "12L" in msg
        assert "+18.7%" in msg
        # CTA
        assert "@TrendRiderSignals" in msg
        assert "bybit.com" in msg

    def test_losing_trade_card(self):
        msg = trade_result_poster.format_trade_result(
            SAMPLE_LOSING_TRADE, trade_number=43, stats=SAMPLE_STATS
        )
        assert "Trade Result #043" in msg
        assert "LONG" in msg
        assert "ETH/USDT:USDT" in msg
        assert "-6.00%" in msg
        assert "\u274c" in msg  # red X
        assert "Stop Loss hit" in msg
        assert "EMA50 Bounce" in msg

    def test_short_trade_card(self):
        msg = trade_result_poster.format_trade_result(
            SAMPLE_SHORT_TRADE, trade_number=44, stats=SAMPLE_STATS
        )
        assert "SHORT" in msg
        assert "SOL/USDT:USDT" in msg
        assert "+4.68%" in msg
        assert "Trailing Stop" in msg

    def test_no_stats(self):
        msg = trade_result_poster.format_trade_result(
            SAMPLE_WINNING_TRADE, trade_number=1, stats=EMPTY_STATS
        )
        assert "Running Stats" not in msg
        # CTA should still be there
        assert "@TrendRiderSignals" in msg

    def test_no_leverage_display_for_1x(self):
        trade = {**SAMPLE_WINNING_TRADE, "leverage": 1}
        msg = trade_result_poster.format_trade_result(
            trade, trade_number=1, stats=EMPTY_STATS
        )
        assert "1x" not in msg

    def test_no_enter_tag(self):
        trade = {**SAMPLE_WINNING_TRADE, "enter_tag": None}
        msg = trade_result_poster.format_trade_result(
            trade, trade_number=1, stats=EMPTY_STATS
        )
        assert "Setup:" not in msg

    def test_sell_reason_fallback(self):
        trade = {**SAMPLE_WINNING_TRADE, "exit_reason": None, "sell_reason": "roi"}
        msg = trade_result_poster.format_trade_result(
            trade, trade_number=1, stats=EMPTY_STATS
        )
        assert "ROI target reached" in msg


# ─────────────────────────────────────────────────────────────────────────
# 7. Telegram sending
# ─────────────────────────────────────────────────────────────────────────

class TestSendTelegram:
    """Test Telegram notification dispatch."""

    @patch("trade_result_poster.requests.post")
    def test_send_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        result = trade_result_poster.send_telegram("fake-token", "-100123", "Hello")
        assert result is True
        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
        assert payload["chat_id"] == "-100123"
        assert payload["parse_mode"] == "Markdown"

    def test_send_missing_credentials(self):
        result = trade_result_poster.send_telegram("", "", "Hello")
        assert result is False

    @patch("trade_result_poster.requests.post", side_effect=requests.RequestException("timeout"))
    def test_send_network_error(self, _mock):
        result = trade_result_poster.send_telegram("tok", "-100123", "Hello")
        assert result is False

    @patch("trade_result_poster.requests.post")
    def test_send_api_error(self, mock_post):
        mock_post.return_value = MagicMock(status_code=403, text="Forbidden")
        result = trade_result_poster.send_telegram("tok", "-100123", "Hello")
        assert result is False


# ─────────────────────────────────────────────────────────────────────────
# 8. Config helpers
# ─────────────────────────────────────────────────────────────────────────

class TestConfigHelpers:
    """Test config loading and credential resolution."""

    def test_is_dry_run_default(self):
        assert trade_result_poster.is_dry_run({}) is True

    def test_is_dry_run_false(self):
        assert trade_result_poster.is_dry_run({"dry_run": False}) is False

    def test_get_db_path_dry_run(self):
        with patch.object(trade_result_poster, "FT_HOME", Path("/opt/freqtrade")):
            db = trade_result_poster.get_db_path({"dry_run": True})
        assert db == Path("/opt/freqtrade/tradesv3.dryrun.sqlite")

    def test_get_db_path_live(self):
        with patch.object(trade_result_poster, "FT_HOME", Path("/opt/freqtrade")):
            db = trade_result_poster.get_db_path({"dry_run": False})
        assert db == Path("/opt/freqtrade/tradesv3.sqlite")

    def test_get_tg_token_from_env(self):
        with patch.dict("os.environ", {"TG_TOKEN": "my-token"}, clear=False):
            token = trade_result_poster.get_tg_token({})
        assert token == "my-token"

    def test_get_tg_token_from_config(self):
        config = {"telegram": {"token": "cfg-tok"}}
        with patch.dict("os.environ", {}, clear=True):
            token = trade_result_poster.get_tg_token(config)
        assert token == "cfg-tok"

    def test_get_tg_token_missing_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(RuntimeError, match="TG_TOKEN"):
                trade_result_poster.get_tg_token({})

    def test_get_free_channel_id_from_env(self):
        with patch.dict("os.environ", {"FREE_CHANNEL_ID": "-100999"}, clear=False):
            cid = trade_result_poster.get_free_channel_id()
        assert cid == "-100999"

    def test_get_free_channel_id_missing_raises(self):
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(RuntimeError, match="FREE_CHANNEL_ID"):
                trade_result_poster.get_free_channel_id()


# ─────────────────────────────────────────────────────────────────────────
# 9. Integration: main flow
# ─────────────────────────────────────────────────────────────────────────

class TestMainFlow:
    """Test the main() function end-to-end with mocks."""

    @patch("trade_result_poster.send_telegram", return_value=True)
    @patch("trade_result_poster.save_state")
    @patch("trade_result_poster.load_state", return_value={"last_posted_trade_id": 0, "trade_counter": 0})
    @patch("trade_result_poster.get_free_channel_id", return_value="-100123")
    @patch("trade_result_poster.get_tg_token", return_value="test-token")
    @patch("trade_result_poster.load_config", return_value={"dry_run": True})
    def test_main_sends_for_closed_trades(
        self, _cfg, _tok, _ch, _state, mock_save, mock_send, tmp_path
    ):
        db = tmp_path / "tradesv3.dryrun.sqlite"
        _create_test_db(db, [SAMPLE_WINNING_TRADE, SAMPLE_LOSING_TRADE])
        with patch.object(trade_result_poster, "get_db_path", return_value=db):
            trade_result_poster.main()
        assert mock_send.call_count == 2
        mock_save.assert_called_once()
        saved = mock_save.call_args[0][0]
        assert saved["last_posted_trade_id"] == 2
        assert saved["trade_counter"] == 2

    @patch("trade_result_poster.send_telegram")
    @patch("trade_result_poster.save_state")
    @patch("trade_result_poster.load_state", return_value={"last_posted_trade_id": 5, "trade_counter": 10})
    @patch("trade_result_poster.get_free_channel_id", return_value="-100123")
    @patch("trade_result_poster.get_tg_token", return_value="test-token")
    @patch("trade_result_poster.load_config", return_value={"dry_run": True})
    def test_main_no_new_trades(
        self, _cfg, _tok, _ch, _state, mock_save, mock_send, tmp_path
    ):
        db = tmp_path / "tradesv3.dryrun.sqlite"
        _create_test_db(db, [SAMPLE_WINNING_TRADE])
        with patch.object(trade_result_poster, "get_db_path", return_value=db):
            trade_result_poster.main()
        mock_send.assert_not_called()
        mock_save.assert_not_called()

    @patch("trade_result_poster.send_telegram", return_value=True)
    @patch("trade_result_poster.save_state")
    @patch("trade_result_poster.load_state", return_value={"last_posted_trade_id": 0, "trade_counter": 40})
    @patch("trade_result_poster.get_free_channel_id", return_value="-100123")
    @patch("trade_result_poster.get_tg_token", return_value="test-token")
    @patch("trade_result_poster.load_config", return_value={"dry_run": True})
    def test_main_continues_trade_counter(
        self, _cfg, _tok, _ch, _state, mock_save, mock_send, tmp_path
    ):
        db = tmp_path / "tradesv3.dryrun.sqlite"
        _create_test_db(db, [SAMPLE_WINNING_TRADE])
        with patch.object(trade_result_poster, "get_db_path", return_value=db):
            trade_result_poster.main()
        assert mock_send.call_count == 1
        # The message should contain #041 (counter was 40, incremented to 41)
        sent_msg = mock_send.call_args[0][2]
        assert "#041" in sent_msg
        saved = mock_save.call_args[0][0]
        assert saved["trade_counter"] == 41

    @patch("trade_result_poster.send_telegram", return_value=False)
    @patch("trade_result_poster.save_state")
    @patch("trade_result_poster.load_state", return_value={"last_posted_trade_id": 0, "trade_counter": 0})
    @patch("trade_result_poster.get_free_channel_id", return_value="-100123")
    @patch("trade_result_poster.get_tg_token", return_value="test-token")
    @patch("trade_result_poster.load_config", return_value={"dry_run": True})
    def test_main_updates_state_even_on_send_failure(
        self, _cfg, _tok, _ch, _state, mock_save, mock_send, tmp_path
    ):
        """State should update even if Telegram send fails to avoid duplicate spam."""
        db = tmp_path / "tradesv3.dryrun.sqlite"
        _create_test_db(db, [SAMPLE_WINNING_TRADE])
        with patch.object(trade_result_poster, "get_db_path", return_value=db):
            trade_result_poster.main()
        mock_save.assert_called_once()
        saved = mock_save.call_args[0][0]
        assert saved["last_posted_trade_id"] == 1
