"""Tests for subscription_bot persistent keyboard menu."""

import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add scripts directory to sys.path
SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

# Mock aiohttp before importing subscription_bot
if "aiohttp" not in sys.modules:
    _aiohttp = types.ModuleType("aiohttp")
    _aiohttp.ClientSession = MagicMock
    _aiohttp.ClientTimeout = MagicMock
    sys.modules["aiohttp"] = _aiohttp

# Mock shared_utils
if "shared_utils" not in sys.modules:
    _shared_utils = types.ModuleType("shared_utils")
    _shared_utils.calc_command = AsyncMock()
    _shared_utils.query_stats = MagicMock(return_value="*Stats*\nNo trades.")
    sys.modules["shared_utils"] = _shared_utils

from subscription_bot import (  # noqa: E402
    MENU_BTN_CALC,
    MENU_BTN_HELP,
    MENU_BTN_PLANS,
    MENU_BTN_REFER,
    MENU_BTN_STATS,
    MENU_BTN_STATUS,
    get_main_menu,
    menu_button_handler,
)


class TestGetMainMenu:
    """Tests for get_main_menu helper."""

    def test_returns_reply_keyboard_markup(self):
        from telegram import ReplyKeyboardMarkup

        menu = get_main_menu()
        assert isinstance(menu, ReplyKeyboardMarkup)

    def test_resize_keyboard_enabled(self):
        menu = get_main_menu()
        assert menu.resize_keyboard is True

    def test_has_three_rows(self):
        menu = get_main_menu()
        assert len(menu.keyboard) == 3

    def test_buttons_text(self):
        menu = get_main_menu()
        texts = [[btn.text for btn in row] for row in menu.keyboard]
        assert texts == [
            [MENU_BTN_STATS, MENU_BTN_PLANS],
            [MENU_BTN_STATUS, MENU_BTN_REFER],
            [MENU_BTN_CALC, MENU_BTN_HELP],
        ]


def _make_update(text: str) -> MagicMock:
    """Create a mock Update with given message text."""
    update = MagicMock()
    update.message.text = text
    update.message.reply_text = AsyncMock()
    update.effective_user = MagicMock()
    update.effective_user.id = 12345
    update.effective_user.username = "testuser"
    update.effective_user.first_name = "Test"
    return update


@pytest.mark.asyncio
class TestMenuButtonHandler:
    """Tests for menu_button_handler routing."""

    @patch("subscription_bot.stats_command", new_callable=AsyncMock)
    async def test_stats_button(self, mock_stats):
        update = _make_update(MENU_BTN_STATS)
        ctx = MagicMock()
        await menu_button_handler(update, ctx)
        mock_stats.assert_awaited_once_with(update, ctx)

    @patch("subscription_bot.plans_command", new_callable=AsyncMock)
    async def test_plans_button(self, mock_plans):
        update = _make_update(MENU_BTN_PLANS)
        ctx = MagicMock()
        await menu_button_handler(update, ctx)
        mock_plans.assert_awaited_once_with(update, ctx)

    @patch("subscription_bot.status_command", new_callable=AsyncMock)
    async def test_status_button(self, mock_status):
        update = _make_update(MENU_BTN_STATUS)
        ctx = MagicMock()
        await menu_button_handler(update, ctx)
        mock_status.assert_awaited_once_with(update, ctx)

    @patch("subscription_bot.refer_command", new_callable=AsyncMock)
    async def test_refer_button(self, mock_refer):
        update = _make_update(MENU_BTN_REFER)
        ctx = MagicMock()
        await menu_button_handler(update, ctx)
        mock_refer.assert_awaited_once_with(update, ctx)

    async def test_calc_button_sends_usage_hint(self):
        update = _make_update(MENU_BTN_CALC)
        ctx = MagicMock()
        await menu_button_handler(update, ctx)
        update.message.reply_text.assert_awaited_once()
        call_text = update.message.reply_text.call_args[0][0]
        assert "/calc" in call_text
        assert "1000" in call_text

    @patch("subscription_bot.help_command", new_callable=AsyncMock)
    async def test_help_button(self, mock_help):
        update = _make_update(MENU_BTN_HELP)
        ctx = MagicMock()
        await menu_button_handler(update, ctx)
        mock_help.assert_awaited_once_with(update, ctx)

    async def test_unknown_text_does_nothing(self):
        """Unknown text should not trigger any handler or raise."""
        update = _make_update("random text")
        ctx = MagicMock()
        await menu_button_handler(update, ctx)
        update.message.reply_text.assert_not_awaited()
