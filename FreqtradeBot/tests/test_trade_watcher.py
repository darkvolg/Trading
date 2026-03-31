"""Tests for the Trade Watcher script."""

import json
import sqlite3
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

# Ensure scripts/ is importable
SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import trade_watcher  # noqa: E402


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
            close_profit REAL,
            profit_ratio REAL,
            exit_reason TEXT,
            sell_reason TEXT
        )
        """
    )
    for t in trades:
        conn.execute(
            """
            INSERT INTO trades (id, pair, trade_direction, is_short, open_date,
                                close_date, stake_amount, open_rate, close_profit,
                                profit_ratio, exit_reason, sell_reason)
            VALUES (:id, :pair, :trade_direction, :is_short, :open_date,
                    :close_date, :stake_amount, :open_rate, :close_profit,
                    :profit_ratio, :exit_reason, :sell_reason)
            """,
            {
                "id": t.get("id", 1),
                "pair": t.get("pair", "BTC/USDT"),
                "trade_direction": t.get("trade_direction", "long"),
                "is_short": t.get("is_short", 0),
                "open_date": t.get("open_date", "2026-03-25 10:00:00"),
                "close_date": t.get("close_date"),
                "stake_amount": t.get("stake_amount", 100.0),
                "open_rate": t.get("open_rate", 65000.0),
                "close_profit": t.get("close_profit"),
                "profit_ratio": t.get("profit_ratio"),
                "exit_reason": t.get("exit_reason"),
                "sell_reason": t.get("sell_reason"),
            },
        )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────
# 1. State management
# ─────────────────────────────────────────────────────────────────────────

class TestStateManagement:
    """Test load/save of the state file."""

    def test_load_state_missing_file(self, tmp_path):
        with patch.object(trade_watcher, "STATE_FILE", tmp_path / "missing.json"):
            state = trade_watcher.load_state()
        assert state == {"last_notified_trade_id": 0}

    def test_load_state_valid(self, tmp_path):
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({"last_notified_trade_id": 42}))
        with patch.object(trade_watcher, "STATE_FILE", state_file):
            state = trade_watcher.load_state()
        assert state["last_notified_trade_id"] == 42

    def test_save_state(self, tmp_path):
        state_file = tmp_path / "sub" / "state.json"
        with patch.object(trade_watcher, "STATE_FILE", state_file):
            trade_watcher.save_state({"last_notified_trade_id": 7})
        assert state_file.exists()
        data = json.loads(state_file.read_text())
        assert data["last_notified_trade_id"] == 7

    def test_load_state_corrupt_json(self, tmp_path):
        state_file = tmp_path / "corrupt.json"
        state_file.write_text("{bad json")
        with patch.object(trade_watcher, "STATE_FILE", state_file):
            state = trade_watcher.load_state()
        assert state == {"last_notified_trade_id": 0}


# ─────────────────────────────────────────────────────────────────────────
# 2. Database queries
# ─────────────────────────────────────────────────────────────────────────

class TestFetchNewTrades:
    """Test fetching trades from SQLite."""

    def test_fetch_returns_new_trades(self, tmp_path):
        db = tmp_path / "trades.sqlite"
        _create_test_db(db, [
            {"id": 1, "pair": "BTC/USDT"},
            {"id": 2, "pair": "ETH/USDT"},
            {"id": 3, "pair": "SOL/USDT"},
        ])
        trades = trade_watcher.fetch_new_trades(db, last_id=1)
        assert len(trades) == 2
        assert trades[0]["pair"] == "ETH/USDT"
        assert trades[1]["pair"] == "SOL/USDT"

    def test_fetch_no_new_trades(self, tmp_path):
        db = tmp_path / "trades.sqlite"
        _create_test_db(db, [{"id": 1, "pair": "BTC/USDT"}])
        trades = trade_watcher.fetch_new_trades(db, last_id=1)
        assert trades == []

    def test_fetch_missing_db(self, tmp_path):
        db = tmp_path / "nonexistent.sqlite"
        trades = trade_watcher.fetch_new_trades(db, last_id=0)
        assert trades == []


# ─────────────────────────────────────────────────────────────────────────
# 3. Message formatting
# ─────────────────────────────────────────────────────────────────────────

class TestFormatTradeMessage:
    """Test trade notification formatting."""

    def test_open_trade_dry_run(self):
        trade = {
            "pair": "BTC/USDT",
            "trade_direction": "long",
            "open_date": "2026-03-25 10:00:00",
            "stake_amount": 100.0,
            "open_rate": 65000.0,
            "close_date": None,
        }
        msg = trade_watcher.format_trade_message(trade, dry_run=True)
        assert "BTC/USDT" in msg
        assert "LONG" in msg
        assert "100.0 USDT" in msg
        assert "65000.0" in msg
        assert "DRY RUN" in msg
        assert "P&L" not in msg

    def test_closed_trade_live(self):
        trade = {
            "pair": "ETH/USDT",
            "trade_direction": "short",
            "open_date": "2026-03-25 10:00:00",
            "close_date": "2026-03-25 12:00:00",
            "stake_amount": 50.0,
            "open_rate": 3500.0,
            "close_profit": 0.05,
            "exit_reason": "tp1",
        }
        msg = trade_watcher.format_trade_message(trade, dry_run=False)
        assert "ETH/USDT" in msg
        assert "SHORT" in msg
        assert "LIVE" in msg
        assert "P&L" in msg
        assert "+5.00%" in msg
        assert "tp1" in msg

    def test_short_via_is_short_flag(self):
        trade = {
            "pair": "DOGE/USDT",
            "is_short": True,
            "open_date": "2026-03-25 10:00:00",
            "stake_amount": 20.0,
            "open_rate": 0.15,
            "close_date": None,
        }
        msg = trade_watcher.format_trade_message(trade, dry_run=True)
        assert "SHORT" in msg


# ─────────────────────────────────────────────────────────────────────────
# 4. Telegram sending
# ─────────────────────────────────────────────────────────────────────────

class TestSendTelegram:
    """Test Telegram notification dispatch."""

    @patch("trade_watcher.requests.post")
    def test_send_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        result = trade_watcher.send_telegram("fake-token", "12345", "Hello")
        assert result is True
        mock_post.assert_called_once()
        payload = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1]["json"]
        assert payload["chat_id"] == "12345"
        assert payload["parse_mode"] == "HTML"

    def test_send_missing_credentials(self):
        result = trade_watcher.send_telegram("", "", "Hello")
        assert result is False

    @patch("trade_watcher.requests.post", side_effect=requests.RequestException("timeout"))
    def test_send_network_error(self, _mock):
        result = trade_watcher.send_telegram("tok", "123", "Hello")
        assert result is False

    @patch("trade_watcher.requests.post")
    def test_send_api_error(self, mock_post):
        mock_post.return_value = MagicMock(status_code=403, text="Forbidden")
        result = trade_watcher.send_telegram("tok", "123", "Hello")
        assert result is False


# ─────────────────────────────────────────────────────────────────────────
# 5. Config helpers
# ─────────────────────────────────────────────────────────────────────────

class TestConfigHelpers:
    """Test config loading and DB path resolution."""

    def test_is_dry_run_default(self):
        assert trade_watcher.is_dry_run({}) is True

    def test_is_dry_run_false(self):
        assert trade_watcher.is_dry_run({"dry_run": False}) is False

    def test_get_db_path_dry_run(self):
        with patch.object(trade_watcher, "FT_HOME", Path("/opt/freqtrade")):
            db = trade_watcher.get_db_path({"dry_run": True})
        assert db == Path("/opt/freqtrade/tradesv3.dryrun.sqlite")

    def test_get_db_path_live(self):
        with patch.object(trade_watcher, "FT_HOME", Path("/opt/freqtrade")):
            db = trade_watcher.get_db_path({"dry_run": False})
        assert db == Path("/opt/freqtrade/tradesv3.sqlite")

    def test_get_db_path_from_db_url(self):
        with patch.object(trade_watcher, "FT_HOME", Path("/opt/freqtrade")):
            db = trade_watcher.get_db_path({"db_url": "sqlite:///user_data/trades.db"})
        assert db == Path("/opt/freqtrade/user_data/trades.db")

    def test_get_telegram_credentials_from_env(self):
        env = {"TG_TOKEN": "tok123", "ADMIN_CHAT_ID": "999"}
        with patch.dict("os.environ", env, clear=False):
            token, chat_id = trade_watcher.get_telegram_credentials({})
        assert token == "tok123"
        assert chat_id == "999"

    def test_get_telegram_credentials_from_config(self):
        config = {"telegram": {"token": "cfg-tok", "chat_id": 555}}
        with patch.dict("os.environ", {}, clear=True):
            token, chat_id = trade_watcher.get_telegram_credentials(config)
        assert token == "cfg-tok"
        assert chat_id == "555"


# ─────────────────────────────────────────────────────────────────────────
# 6. Integration: main flow
# ─────────────────────────────────────────────────────────────────────────

class TestMainFlow:
    """Test the main() function end-to-end with mocks."""

    @patch("trade_watcher.send_telegram", return_value=True)
    @patch("trade_watcher.save_state")
    @patch("trade_watcher.load_state", return_value={"last_notified_trade_id": 0})
    @patch("trade_watcher.load_config", return_value={"dry_run": True, "telegram": {"token": "t", "chat_id": "1"}})
    def test_main_sends_for_new_trades(self, _cfg, _state, mock_save, mock_send, tmp_path):
        db = tmp_path / "tradesv3.dryrun.sqlite"
        _create_test_db(db, [
            {"id": 1, "pair": "BTC/USDT"},
            {"id": 2, "pair": "ETH/USDT"},
        ])
        with patch("trade_watcher.get_db_path", return_value=db):
            trade_watcher.main()
        assert mock_send.call_count == 2
        mock_save.assert_called_once()
        saved = mock_save.call_args[0][0]
        assert saved["last_notified_trade_id"] == 2

    @patch("trade_watcher.send_telegram")
    @patch("trade_watcher.save_state")
    @patch("trade_watcher.load_state", return_value={"last_notified_trade_id": 5})
    @patch("trade_watcher.load_config", return_value={"dry_run": True})
    def test_main_no_new_trades(self, _cfg, _state, mock_save, mock_send, tmp_path):
        db = tmp_path / "tradesv3.dryrun.sqlite"
        _create_test_db(db, [{"id": 1, "pair": "BTC/USDT"}])
        with patch("trade_watcher.get_db_path", return_value=db):
            trade_watcher.main()
        mock_send.assert_not_called()
        mock_save.assert_not_called()
