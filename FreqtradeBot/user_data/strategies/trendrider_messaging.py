"""
TrendRider Messaging — Telegram message formatting for entry signals and trade reports.
"""

import logging
from datetime import datetime, timedelta, timezone

from trendrider_config import (
    SETUP_NAMES, EXIT_REASONS, ENTRY_ZONE_PCT,
    BYBIT_REFERRAL_LINK,
)

logger = logging.getLogger(__name__)


def build_detailed_reason(entry_tag: str, last: dict, rate: float,
                          ema_fast_period: int, ema_slow_period: int,
                          rsi_period: int = 14) -> str:
    """Build a 2-3 sentence entry reason with concrete indicator levels."""
    rsi_val = last.get(f"rsi_{rsi_period}", 50)
    adx_val = last.get('adx', 0)
    ema_fast = last.get(f'ema_{ema_fast_period}', 0)
    ema_slow = last.get(f'ema_{ema_slow_period}', 0)
    ema_50 = last.get('ema_50', 0)
    ema_200 = last.get('ema_200', 0)
    macd_hist = last.get('macdhist', 0)
    bb_lower = last.get('bb_lower', 0)
    vol_ratio = last.get('volume_ratio', 0)

    parts = []

    if entry_tag == "trend_pullback":
        parts.append(
            f"Price pulled back to EMA{ema_fast_period} ({ema_fast:.1f}) "
            f"in an uptrend — EMA{ema_fast_period} > EMA{ema_slow_period} ({ema_slow:.1f})."
        )
        parts.append(
            f"RSI at {rsi_val:.0f} (healthy zone), ADX {adx_val:.0f} confirms trend strength."
        )
        if vol_ratio > 1.0:
            parts.append(f"Volume {vol_ratio:.1f}x average supports the bounce.")

    elif entry_tag == "ema50_bounce":
        parts.append(
            f"Deep pullback to EMA50 ({ema_50:.1f}), price holding above key support."
        )
        parts.append(
            f"MACD histogram {'positive' if macd_hist > 0 else 'recovering'} "
            f"({macd_hist:.4f}), RSI {rsi_val:.0f} — room to run."
        )
        if adx_val > 20:
            parts.append(f"ADX {adx_val:.0f} — trend intact despite the pullback.")

    elif entry_tag == "rsi_bounce":
        parts.append(
            f"RSI oversold at {rsi_val:.0f}, bouncing off BB lower ({bb_lower:.1f})."
        )
        parts.append(
            f"Price above EMA200 ({ema_200:.1f}) — bullish structure intact."
        )
        if vol_ratio > 1.0:
            parts.append(f"Volume spike {vol_ratio:.1f}x signals buyer interest.")

    else:
        return entry_tag or "Signal"

    return " ".join(parts)


def format_entry_signal(signal_num: int, pair: str, side_str: str, leverage: int,
                        setup_name: str, rate: float, sl_price: float, stoploss_pct: float,
                        rr_ratio: float,
                        conf_level: str, conf_numeric: int, conf_bar: str,
                        conf_details: list, regime: str, heat_str: str,
                        est_hold: str, invalidation: float, inv_label: str,
                        rsi_val: float, adx_val: float, vol_ratio: float,
                        macd_hist: float, market_ctx: str, reason: str) -> str:
    """Format the main Telegram entry signal message."""
    entry_low = rate * (1 - ENTRY_ZONE_PCT)
    entry_high = rate * (1 + ENTRY_ZONE_PCT)

    side_emoji = "\U0001f7e2" if side_str == "LONG" else "\U0001f534"
    macd_indicator = "\u2705 +" if macd_hist > 0 else "\u26a0\ufe0f -"
    rsi_indicator = "\u2705" if 35 < rsi_val < 65 else "\u26a0\ufe0f"
    adx_indicator = "\u2705" if adx_val > 20 else "\u26a0\ufe0f"
    vol_indicator = "\u2705" if vol_ratio > 1.0 else "\u26a0\ufe0f"

    return (
        f"*TRENDRIDER AI SIGNAL #{signal_num:03d}*\n"
        f"{'='*28}\n"
        f"*{pair}* | {side_emoji} *{side_str}* | {leverage}x\n"
        f"*Setup:* {setup_name}\n"
        f"{'='*28}\n\n"
        f"\U0001f3af *Entry Zone:* `{entry_low:.2f}` - `{entry_high:.2f}` USDT\n"
        f"\U0001f6e1 *Stop Loss:* `{sl_price:.2f}` ({stoploss_pct*100:+.1f}%)\n"
        f"  R:R = 1:{rr_ratio:.1f}\n\n"
        f"*AI Confidence:* {conf_level} ({conf_numeric}/10)\n"
        f"  {conf_bar}\n"
        f"  {', '.join(conf_details)}\n\n"
        f"*Regime:* {regime}\n"
        f"*Portfolio:* {heat_str}\n"
        f"*Est. Hold:* {est_hold}\n"
        f"*Invalidation:* `{invalidation:.2f}` ({inv_label})\n\n"
        f"*Indicators:*\n"
        f"  {rsi_indicator} RSI: {rsi_val:.1f} | {adx_indicator} ADX: {adx_val:.1f}\n"
        f"  {vol_indicator} Volume: {vol_ratio:.2f}x | {macd_indicator}\n\n"
        f"*Market:* {market_ctx}\n\n"
        f"*Why:* {reason}\n"
        f"{'='*28}\n"
        f"\U0001f4c8 [Trade on Bybit]({BYBIT_REFERRAL_LINK})\n"
        f"_TrendRider AI | @TrendRiderSignals_"
    )


def format_cornix_signal(pair: str, side: str, leverage: int, rate: float,
                         sl_price: float, tp1: float, tp2: float,
                         tp3: float) -> str:
    """Format Cornix-compatible signal message.

    Cornix requires exactly ONE symbol per message. The symbol must be
    a clean futures ticker like BTCUSDT (no slashes, no :USDT suffix).
    """
    # Clean pair: "BTC/USDT:USDT" -> "BTCUSDT", "ETH/USDT" -> "ETHUSDT"
    pair_clean = pair.split(':')[0].replace('/', '')
    side_upper = side.upper()

    entry_low = rate * (1 - ENTRY_ZONE_PCT)
    entry_high = rate * (1 + ENTRY_ZONE_PCT)

    return (
        f"\U0001f4ca {pair_clean} {side_upper}\n"
        f"Exchange: Bybit\n"
        f"Leverage: {leverage}x\n"
        f"Entry: {entry_low:.2f}-{entry_high:.2f}\n"
        f"TP1: {tp1:.2f}\n"
        f"TP2: {tp2:.2f}\n"
        f"TP3: {tp3:.2f}\n"
        f"SL: {sl_price:.2f}"
    )


def format_exit_report(pair: str, trade, rate: float, exit_reason: str,
                       current_time: datetime) -> str:
    """Format the trade exit report message."""
    # Calculate results (LONG only)
    profit_pct = ((rate - trade.open_rate) / trade.open_rate) * 100 * trade.leverage
    duration_hours = (current_time - trade.open_date_utc).total_seconds() / 3600

    side_str = "LONG"
    reason_text = EXIT_REASONS.get(exit_reason, exit_reason)

    # Result
    result_line = f"+{profit_pct:.2f}%" if profit_pct > 0 else f"{profit_pct:.2f}%"

    # Duration formatting
    if duration_hours < 1:
        dur_str = f"{int(duration_hours * 60)}m"
    elif duration_hours < 24:
        dur_str = f"{duration_hours:.1f}h"
    else:
        dur_str = f"{duration_hours/24:.1f}d"

    # R:R achieved
    risk_pct = 6.0  # abs(stoploss * 100)
    reward_pct = abs(profit_pct / trade.leverage) if trade.leverage else abs(profit_pct)
    rr_achieved = reward_pct / risk_pct if risk_pct > 0 else 0

    # Max drawdown
    max_dd = ((trade.open_rate - trade.min_rate) / trade.open_rate) * 100 if trade.min_rate else 0

    # Review with profit tier emoji
    if profit_pct > 5:
        review = "Strong momentum, excellent trade"
        result_emoji = "\U0001f7e2 STRONG WIN"
    elif profit_pct > 3:
        review = "Clean setup, solid gain"
        result_emoji = "\U0001f7e2 WIN"
    elif profit_pct > 0:
        review = "Modest gain, trailing stop secured profit"
        result_emoji = "\U0001f7e1 MODEST"
    elif exit_reason == "stop_loss":
        review = "Setup invalidated, SL protected capital"
        result_emoji = "\U0001f534 LOSS"
    elif exit_reason == "trailing_stop_loss":
        review = "Gave back gains after reversal"
        result_emoji = "\U0001f534 LOSS"
    else:
        review = "Market conditions changed"
        result_emoji = "\U0001f534 LOSS"

    # Setup name from enter_tag
    enter_tag = getattr(trade, 'enter_tag', '') or ''
    setup_name = SETUP_NAMES.get(enter_tag, enter_tag or "—")

    msg = (
        f"*TRADE CLOSED* {result_emoji}\n"
        f"{'='*28}\n"
        f"*{pair}* | {side_str} | {trade.leverage}x\n"
        f"*Setup:* {setup_name}\n"
        f"{'='*28}\n\n"
        f"*Entry:* `{trade.open_rate:.2f}`\n"
        f"*Exit:* `{rate:.2f}`\n"
        f"*Result:* *{result_line}*\n"
        f"*R:R:* 1:{rr_achieved:.1f} achieved\n"
        f"*Duration:* {dur_str}\n"
        f"*Reason:* {reason_text}\n\n"
        f"*Max price:* `{trade.max_rate:.2f}`\n"
        f"*Max DD:* {max_dd:.1f}%\n\n"
        f"*Review:* {review}\n\n"
    )

    return msg


def format_exit_footer(stats_line: str) -> str:
    """Format the footer of exit report with stats and links."""
    footer = ""
    if stats_line:
        footer += f"{stats_line}\n\n"
    footer += (
        f"{'='*28}\n"
        f"[Full Trade History](https://docs.google.com/spreadsheets/d/1ZWRJ0PcBSk910MZv426PrleriBnInykr3OebWXJPm-g)\n"
        f"_TrendRider AI | @TrendRiderSignals_"
    )
    return footer


def format_price_alert(pair: str, close: float, zone_name: str,
                       zone_price: float, dist: float,
                       rsi_val: float, adx_val: float, vol_ratio: float) -> str:
    """Format price alert message."""
    return (
        f"*PRICE ALERT*\n"
        f"{'='*28}\n"
        f"*{pair}* approaching entry zone\n\n"
        f"*Price:* `{close:.2f}` USDT\n"
        f"*{zone_name}:* `{zone_price:.2f}` ({dist:.1f}% above)\n\n"
        f"*RSI:* {rsi_val:.1f} | *ADX:* {adx_val:.1f} | *Vol:* {vol_ratio:.2f}x\n"
        f"{'='*28}\n"
        f"_Watch for entry signal_"
    )


def get_running_stats() -> str:
    """Get running stats for last 30 days from trade history."""
    try:
        from freqtrade.persistence import Trade
        trades = Trade.get_trades_proxy(is_open=False)

        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        recent = [t for t in trades if t.close_date and t.close_date >= cutoff]

        if not recent:
            return "No trades in last 30 days"

        wins = sum(1 for t in recent if t.profit_ratio and t.profit_ratio > 0)
        losses = len(recent) - wins
        win_rate = (wins / len(recent)) * 100 if recent else 0
        avg_profit = sum(t.profit_ratio * 100 for t in recent if t.profit_ratio) / len(recent)
        total_profit = sum(t.profit_ratio * 100 for t in recent if t.profit_ratio)

        return (
            f"*Last 30 days:* {wins}W/{losses}L "
            f"({win_rate:.0f}% WR) | "
            f"Avg {avg_profit:+.2f}% | "
            f"Total {total_profit:+.1f}%"
        )
    except Exception as e:
        logger.warning(f"Failed to get running stats: {e}")
        return ""


