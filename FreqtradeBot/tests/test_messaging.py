"""Tests for trendrider_messaging — formatting of entry signals, exit reports, alerts."""

from datetime import datetime, timezone
from types import SimpleNamespace

from trendrider_messaging import (
    format_entry_signal,
    format_cornix_signal,
    format_exit_report,
    format_price_alert,
    format_exit_footer,
    build_detailed_reason,
)


class TestFormatEntrySignal:
    def _make_signal(self, **overrides):
        defaults = dict(
            signal_num=1, pair="ETH/USDT:USDT", side_str="LONG", leverage=5,
            setup_name="Trend Pullback", rate=2000.0, sl_price=1880.0,
            stoploss_pct=-0.06,
            rr_ratio=1.7, conf_level="STRONG", conf_numeric=8,
            conf_bar="||||||||-- 8/10", conf_details=["RSI healthy", "Strong trend"],
            regime="Trending Bull", heat_str="1/3 slots", est_hold="2-6h",
            invalidation=1850.0, inv_label="below EMA200",
            rsi_val=45.0, adx_val=35.0, vol_ratio=1.8, macd_hist=0.005,
            market_ctx="BTC: Bullish (RSI 55) | 4H: Uptrend",
            reason="Price pulled back to EMA20 in an uptrend.",
        )
        defaults.update(overrides)
        return defaults

    def test_contains_pair(self):
        msg = format_entry_signal(**self._make_signal())
        assert "ETH/USDT:USDT" in msg

    def test_contains_sl(self):
        msg = format_entry_signal(**self._make_signal())
        assert "1880.00" in msg  # SL

    def test_contains_signal_number(self):
        msg = format_entry_signal(**self._make_signal(signal_num=42))
        assert "#042" in msg

    def test_contains_confidence(self):
        msg = format_entry_signal(**self._make_signal())
        assert "STRONG" in msg
        assert "8/10" in msg

    def test_contains_entry_zone(self):
        msg = format_entry_signal(**self._make_signal(rate=2000.0))
        assert "1994.00" in msg  # 2000 * (1 - 0.003)
        assert "2006.00" in msg  # 2000 * (1 + 0.003)

    def test_contains_regime_and_hold(self):
        msg = format_entry_signal(**self._make_signal())
        assert "Trending Bull" in msg
        assert "2-6h" in msg

    def test_contains_indicator_values(self):
        msg = format_entry_signal(**self._make_signal())
        assert "45.0" in msg  # RSI
        assert "35.0" in msg  # ADX

    def test_returns_string(self):
        assert isinstance(format_entry_signal(**self._make_signal()), str)


class TestFormatCornixSignal:
    def test_contains_exchange(self):
        msg = format_cornix_signal("ETH/USDT:USDT", "long", 5, 2000.0, 1880.0,
                                   2060.0, 2100.0, 2200.0)
        assert "Exchange: Bybit" in msg

    def test_contains_bybit(self):
        msg = format_cornix_signal("ETH/USDT:USDT", "long", 5, 2000.0, 1880.0,
                                   2060.0, 2100.0, 2200.0)
        assert "Bybit" in msg

    def test_pair_cleaned_to_full_ticker(self):
        msg = format_cornix_signal("ETH/USDT:USDT", "long", 5, 2000.0, 1880.0,
                                   2060.0, 2100.0, 2200.0)
        # pair_clean: "ETH/USDT:USDT" -> "ETHUSDT"
        assert "ETHUSDT" in msg
        assert "/USDT:USDT" not in msg
        assert ":USDT" not in msg

    def test_pair_cleaned_simple(self):
        msg = format_cornix_signal("BTC/USDT", "long", 3, 68000.0, 66500.0,
                                   70040.0, 71400.0, 74800.0)
        assert "BTCUSDT" in msg
        assert "/" not in msg

    def test_single_symbol_only(self):
        """Cornix requires exactly one symbol — no extra tickers in the message."""
        msg = format_cornix_signal("ETH/USDT:USDT", "long", 5, 2000.0, 1880.0,
                                   2060.0, 2100.0, 2200.0)
        # The word USDT should only appear as part of ETHUSDT, not standalone
        assert msg.count("USDT") == 1  # only in "ETHUSDT"

    def test_contains_sl(self):
        msg = format_cornix_signal("ETH/USDT:USDT", "long", 5, 2000.0, 1880.0,
                                   2060.0, 2100.0, 2200.0)
        assert "1880.00" in msg  # SL

    def test_contains_leverage(self):
        msg = format_cornix_signal("ETH/USDT:USDT", "long", 5, 2000.0, 1880.0,
                                   2060.0, 2100.0, 2200.0)
        assert "5x" in msg

    def test_contains_side(self):
        msg = format_cornix_signal("ETH/USDT:USDT", "long", 5, 2000.0, 1880.0,
                                   2060.0, 2100.0, 2200.0)
        assert "LONG" in msg

    def test_no_trailing_section(self):
        """New Cornix format has no Trailing Configuration section."""
        msg = format_cornix_signal("ETH/USDT:USDT", "long", 5, 2000.0, 1880.0,
                                   2060.0, 2100.0, 2200.0)
        assert "Trailing" not in msg

    def test_contains_tp_levels(self):
        """Cornix needs TP lines for take-profit orders."""
        msg = format_cornix_signal("ETH/USDT:USDT", "long", 5, 2000.0, 1880.0,
                                   2060.0, 2100.0, 2200.0)
        assert "TP1: 2060.00" in msg
        assert "TP2: 2100.00" in msg
        assert "TP3: 2200.00" in msg


class TestFormatExitReport:
    def _make_trade(self, **overrides):
        defaults = dict(
            open_rate=2000.0,
            leverage=5,
            open_date_utc=datetime(2026, 3, 23, 10, 0, 0, tzinfo=timezone.utc),
            min_rate=1950.0,
            max_rate=2100.0,
            enter_tag="trend_pullback",
        )
        defaults.update(overrides)
        return SimpleNamespace(**defaults)

    def test_contains_trade_closed(self):
        trade = self._make_trade()
        now = datetime(2026, 3, 23, 14, 0, 0, tzinfo=timezone.utc)
        msg = format_exit_report("ETH/USDT:USDT", trade, 2060.0, "roi", now)
        assert "TRADE CLOSED" in msg

    def test_winning_trade_shows_win(self):
        trade = self._make_trade()
        now = datetime(2026, 3, 23, 14, 0, 0, tzinfo=timezone.utc)
        msg = format_exit_report("ETH/USDT:USDT", trade, 2060.0, "roi", now)
        assert "WIN" in msg

    def test_losing_trade_shows_loss(self):
        trade = self._make_trade()
        now = datetime(2026, 3, 23, 14, 0, 0, tzinfo=timezone.utc)
        msg = format_exit_report("ETH/USDT:USDT", trade, 1900.0, "stop_loss", now)
        assert "LOSS" in msg

    def test_contains_profit_info(self):
        trade = self._make_trade()
        now = datetime(2026, 3, 23, 14, 0, 0, tzinfo=timezone.utc)
        msg = format_exit_report("ETH/USDT:USDT", trade, 2060.0, "roi", now)
        # Profit = ((2060-2000)/2000) * 100 * 5 = 15%
        assert "15.00%" in msg

    def test_contains_pair(self):
        trade = self._make_trade()
        now = datetime(2026, 3, 23, 14, 0, 0, tzinfo=timezone.utc)
        msg = format_exit_report("ETH/USDT:USDT", trade, 2060.0, "roi", now)
        assert "ETH/USDT:USDT" in msg

    def test_contains_entry_exit_prices(self):
        trade = self._make_trade()
        now = datetime(2026, 3, 23, 14, 0, 0, tzinfo=timezone.utc)
        msg = format_exit_report("ETH/USDT:USDT", trade, 2060.0, "roi", now)
        assert "2000.00" in msg  # entry
        assert "2060.00" in msg  # exit

    def test_contains_duration(self):
        trade = self._make_trade()
        now = datetime(2026, 3, 23, 14, 0, 0, tzinfo=timezone.utc)
        msg = format_exit_report("ETH/USDT:USDT", trade, 2060.0, "roi", now)
        assert "4.0h" in msg  # 4 hours

    def test_contains_setup_name(self):
        trade = self._make_trade(enter_tag="trend_pullback")
        now = datetime(2026, 3, 23, 14, 0, 0, tzinfo=timezone.utc)
        msg = format_exit_report("ETH/USDT:USDT", trade, 2060.0, "roi", now)
        assert "Trend Pullback" in msg

    def test_exit_reason_mapped(self):
        trade = self._make_trade()
        now = datetime(2026, 3, 23, 14, 0, 0, tzinfo=timezone.utc)
        msg = format_exit_report("ETH/USDT:USDT", trade, 1900.0, "stop_loss", now)
        assert "Stop Loss hit" in msg


class TestFormatPriceAlert:
    def test_contains_pair_and_zone(self):
        msg = format_price_alert(
            pair="ETH/USDT:USDT", close=2000.0, zone_name="EMA50",
            zone_price=1980.0, dist=1.0, rsi_val=45.0, adx_val=30.0, vol_ratio=1.5,
        )
        assert "ETH/USDT:USDT" in msg
        assert "EMA50" in msg

    def test_contains_price_alert_header(self):
        msg = format_price_alert(
            pair="ETH/USDT:USDT", close=2000.0, zone_name="EMA50",
            zone_price=1980.0, dist=1.0, rsi_val=45.0, adx_val=30.0, vol_ratio=1.5,
        )
        assert "PRICE ALERT" in msg

    def test_contains_indicator_values(self):
        msg = format_price_alert(
            pair="BTC/USDT:USDT", close=50000.0, zone_name="EMA200",
            zone_price=49500.0, dist=1.0, rsi_val=55.0, adx_val=28.0, vol_ratio=1.2,
        )
        assert "55.0" in msg
        assert "28.0" in msg
        assert "1.20" in msg

    def test_contains_zone_price(self):
        msg = format_price_alert(
            pair="ETH/USDT:USDT", close=2000.0, zone_name="EMA50",
            zone_price=1980.0, dist=1.0, rsi_val=45.0, adx_val=30.0, vol_ratio=1.5,
        )
        assert "1980.00" in msg


class TestFormatExitFooter:
    def test_with_stats(self):
        footer = format_exit_footer("*Last 30 days:* 5W/2L")
        assert "5W/2L" in footer
        assert "TrendRider" in footer

    def test_empty_stats(self):
        footer = format_exit_footer("")
        assert "TrendRider" in footer

    def test_contains_trade_history_link(self):
        footer = format_exit_footer("")
        assert "Trade History" in footer


class TestBuildDetailedReason:
    def test_trend_pullback(self, mock_last_candle_bullish):
        reason = build_detailed_reason(
            "trend_pullback", mock_last_candle_bullish, 100.0,
            ema_fast_period=20, ema_slow_period=50,
        )
        assert "EMA20" in reason
        assert "RSI" in reason

    def test_ema50_bounce(self, mock_last_candle_bullish):
        reason = build_detailed_reason(
            "ema50_bounce", mock_last_candle_bullish, 97.0,
            ema_fast_period=20, ema_slow_period=50,
        )
        assert "EMA50" in reason
        assert "MACD" in reason

    def test_rsi_bounce(self, mock_last_candle_bullish):
        reason = build_detailed_reason(
            "rsi_bounce", mock_last_candle_bullish, 96.0,
            ema_fast_period=20, ema_slow_period=50,
        )
        assert "RSI" in reason
        assert "EMA200" in reason

    def test_unknown_tag_returns_tag(self):
        reason = build_detailed_reason(
            "unknown_setup", {}, 100.0,
            ema_fast_period=20, ema_slow_period=50,
        )
        assert reason == "unknown_setup"
