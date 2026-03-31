"""Tests for the TrendRider Health Monitor."""

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests

# Ensure scripts/ is importable
SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import health_monitor  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────
# 1. Alert sending
# ─────────────────────────────────────────────────────────────────────────

class TestSendTelegramAlert:
    """Verify Telegram alerts are sent correctly."""

    @patch("health_monitor.requests.post")
    def test_send_alert_success(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)
        result = health_monitor.send_telegram_alert(
            "fake-token", "12345", "Test alert"
        )
        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["chat_id"] == "12345"
        assert payload["text"] == "Test alert"

    @patch("health_monitor.requests.post")
    def test_send_alert_failure_status(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=403, text="Forbidden"
        )
        result = health_monitor.send_telegram_alert(
            "bad-token", "12345", "Test"
        )
        assert result is False

    def test_send_alert_missing_credentials(self):
        result = health_monitor.send_telegram_alert("", "", "Test")
        assert result is False

    @patch("health_monitor.requests.post", side_effect=requests.RequestException("network"))
    def test_send_alert_network_error(self, _mock):
        result = health_monitor.send_telegram_alert(
            "tok", "123", "Test"
        )
        assert result is False


# ─────────────────────────────────────────────────────────────────────────
# 2. Deduplication / no-spam
# ─────────────────────────────────────────────────────────────────────────

class TestDeduplication:
    """Ensure the same alert is not repeated within the cooldown window."""

    def test_first_alert_fires(self):
        state: dict = {}
        assert health_monitor._should_alert(state, "api_down") is True

    def test_recent_alert_suppressed(self):
        state = {"api_down": time.time() - 60}  # 60 sec ago
        assert health_monitor._should_alert(state, "api_down") is False

    def test_old_alert_fires_again(self):
        state = {"api_down": time.time() - 7200}  # 2 hours ago
        assert health_monitor._should_alert(state, "api_down") is True

    def test_mark_alerted_updates_state(self):
        state: dict = {}
        health_monitor._mark_alerted(state, "api_down")
        assert "api_down" in state
        assert time.time() - state["api_down"] < 2

    def test_different_keys_independent(self):
        state = {"api_down": time.time()}  # just fired
        assert health_monitor._should_alert(state, "api_down") is False
        assert health_monitor._should_alert(state, "drawdown") is True


# ─────────────────────────────────────────────────────────────────────────
# 3. Health check — API ping parsing
# ─────────────────────────────────────────────────────────────────────────

class TestCheckApiPing:
    """Verify API ping interprets responses correctly."""

    @patch("health_monitor.requests.get")
    def test_ping_ok(self, mock_get):
        mock_get.return_value = MagicMock(status_code=200)
        ok, detail = health_monitor.check_api_ping(
            "http://localhost:8081", None
        )
        assert ok is True
        assert "OK" in detail

    @patch("health_monitor.requests.get", side_effect=requests.RequestException("refused"))
    def test_ping_unreachable(self, _mock):
        ok, detail = health_monitor.check_api_ping(
            "http://localhost:8081", None
        )
        assert ok is False
        assert "unreachable" in detail.lower()


# ─────────────────────────────────────────────────────────────────────────
# 4. Log error detection
# ─────────────────────────────────────────────────────────────────────────

class TestCheckLogErrors:
    """Test error scanning in log files."""

    def test_no_log_dir(self, tmp_path):
        """If log directory doesn't exist, check should pass gracefully."""
        with patch.object(health_monitor, "LOG_DIR", tmp_path / "nonexistent"):
            ok, detail = health_monitor.check_log_errors()
        assert ok is True

    def test_detects_recent_errors(self, tmp_path):
        """ERROR lines without parseable timestamps are included."""
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_file = log_dir / "freqtrade.log"
        log_file.write_text(
            "INFO all good\nERROR something broke\nERROR another failure\n"
        )
        with patch.object(health_monitor, "LOG_DIR", log_dir):
            ok, detail = health_monitor.check_log_errors()
        assert ok is False
        assert "2 recent errors" in detail

    def test_no_errors_in_log(self, tmp_path):
        log_dir = tmp_path / "logs"
        log_dir.mkdir()
        log_file = log_dir / "freqtrade.log"
        log_file.write_text("INFO all good\nINFO another line\n")
        with patch.object(health_monitor, "LOG_DIR", log_dir):
            ok, detail = health_monitor.check_log_errors()
        assert ok is True


# ─────────────────────────────────────────────────────────────────────────
# 5. Drawdown detection
# ─────────────────────────────────────────────────────────────────────────

class TestCheckDrawdown:
    @patch("health_monitor.requests.get")
    def test_normal_drawdown(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"profit_all_percent": -5.0}),
        )
        ok, detail = health_monitor.check_drawdown(
            "http://localhost:8081", None
        )
        assert ok is True

    @patch("health_monitor.requests.get")
    def test_excessive_drawdown(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"profit_all_percent": -25.0}),
        )
        ok, detail = health_monitor.check_drawdown(
            "http://localhost:8081", None
        )
        assert ok is False
        assert "Drawdown alert" in detail


# ─────────────────────────────────────────────────────────────────────────
# 6. State persistence
# ─────────────────────────────────────────────────────────────────────────

class TestStatePersistence:
    def test_save_and_load(self, tmp_path):
        state_file = tmp_path / ".health_state.json"
        with patch.object(health_monitor, "STATE_FILE", state_file):
            health_monitor._save_state({"api_down": 12345.0})
            loaded = health_monitor._load_state()
        assert loaded["api_down"] == 12345.0

    def test_load_missing_file(self, tmp_path):
        with patch.object(
            health_monitor, "STATE_FILE", tmp_path / "nope.json"
        ):
            loaded = health_monitor._load_state()
        assert loaded == {}


# ─────────────────────────────────────────────────────────────────────────
# 7. Credentials loading
# ─────────────────────────────────────────────────────────────────────────

class TestCredentials:
    def test_env_vars_take_priority(self, monkeypatch):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "env-token")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "env-chat")
        token, chat_id = health_monitor.get_telegram_credentials()
        assert token == "env-token"
        assert chat_id == "env-chat"

    def test_fallback_to_config(self, tmp_path, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
        monkeypatch.delenv("TG_TOKEN", raising=False)
        monkeypatch.delenv("TG_CHAT_ID", raising=False)
        cfg = tmp_path / "config.json"
        cfg.write_text(
            json.dumps({"telegram": {"token": "cfg-tok", "chat_id": "999"}})
        )
        with patch.object(health_monitor, "CONFIG_PATH", cfg):
            token, chat_id = health_monitor.get_telegram_credentials()
        assert token == "cfg-tok"
        assert chat_id == "999"
