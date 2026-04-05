"""
TrendRider AI Confidence — AI-powered signal scoring, market regime detection, market context.
"""

import logging
from trendrider_config import (
    BTC_RSI_HEALTHY_MIN, BTC_RSI_HEALTHY_MAX,
    FNG_NEUTRAL_MIN, FNG_NEUTRAL_MAX,
    FUNDING_HEALTHY_THRESHOLD, CONFIDENCE_MAX_SCORE,
)

logger = logging.getLogger(__name__)


def calc_confidence(last: dict, adx_threshold: int, rsi_period: int = 14) -> tuple:
    """Calculate signal confidence based on weighted indicator alignment.

    Max score ~17.5. Returns (level_str, bar_str, details_list, numeric_level).
    """
    score = 0.0
    details = []
    rsi_val = last.get(f"rsi_{rsi_period}", 50)

    # RSI in healthy zone (not overbought): +1.5
    if 35 < rsi_val < 60:
        score += 1.5
        details.append("RSI healthy")

    # Strong trend (ADX): +2.5 strong, +1.5 moderate
    adx_val = last.get('adx', 0)
    if adx_val > 30:
        score += 2.5
        details.append("Strong trend")
    elif adx_val > adx_threshold:
        score += 1.5
        details.append("Moderate trend")

    # Volume confirmation: +2.5 high, +1.5 normal
    vol_ratio = last.get('volume_ratio', 0)
    if vol_ratio > 1.5:
        score += 2.5
        details.append("High volume")
    elif vol_ratio > 1.0:
        score += 1.5
        details.append("Normal volume")

    # MACD positive histogram: +1.5, bonus +0.5 if rising
    macd_hist = last.get('macdhist', 0)
    macd_hist_prev = last.get('macdhist_prev', 0)
    if macd_hist > 0:
        score += 1.5
        if macd_hist > macd_hist_prev:
            score += 0.5
            details.append("MACD positive+rising")
        else:
            details.append("MACD positive")

    # OBV rising AND above EMA: +1.5
    if last.get('obv', 0) > last.get('obv_ema', 0):
        score += 1.5
        details.append("OBV rising")

    # BTC healthy (RSI 40-70): +1.5
    btc_rsi = last.get('btc_rsi_1h', 50)
    if BTC_RSI_HEALTHY_MIN < btc_rsi < BTC_RSI_HEALTHY_MAX:
        score += 1.5
        details.append("BTC healthy")

    # 4h trend alignment AND ADX_4h > 20: +1.5
    if last.get('is_bull_4h', 0) == 1 and last.get('adx_4h', 0) > 20:
        score += 1.5
        details.append("4H trend aligned")

    # Bollinger Band position (close near lower = good for long): +1
    close = last.get('close', 0)
    bb_lower = last.get('bb_lower', 0)
    bb_upper = last.get('bb_upper', 0)
    bb_range = bb_upper - bb_lower if bb_upper > bb_lower else 1
    if bb_lower > 0 and close > 0:
        bb_position = (close - bb_lower) / bb_range
        if bb_position < 0.35:
            score += 1.0
            details.append("Near BB lower")

    # Plus_DI > Minus_DI spread > 10: +1
    plus_di = last.get('plus_di', 0)
    minus_di = last.get('minus_di', 0)
    if plus_di - minus_di > 10:
        score += 1.0
        details.append("Strong DI spread")

    # FNG bonus: neutral/healthy (40-60): +1
    fng_val = last.get('fng_value', 50)
    if FNG_NEUTRAL_MIN <= fng_val <= FNG_NEUTRAL_MAX:
        score += 1.0
        details.append("FNG neutral")

    # On-chain: healthy funding rate: +1
    funding = last.get('funding_rate', 0)
    if abs(funding) < FUNDING_HEALTHY_THRESHOLD:
        score += 1
        details.append("Healthy funding")

    # Smooth mapping to 1-10
    numeric = max(1, min(10, round(score * 10 / CONFIDENCE_MAX_SCORE)))

    # Level label with emoji
    if numeric >= 8:
        level = "\U0001f680 STRONG"
        fill_char = "\U0001f7e9"
    elif numeric >= 6:
        level = "\u2705 GOOD"
        fill_char = "\U0001f7e8"
    elif numeric >= 4:
        level = "\u26a1 MEDIUM"
        fill_char = "\U0001f7e5"
    else:
        level = "\u26a0\ufe0f WEAK"
        fill_char = "\U0001f7e5"

    # Dynamic bar with colored squares
    empty_char = "\u2b1c"
    bar = fill_char * numeric + empty_char * (10 - numeric) + f" {numeric}/10"

    return level, bar, details, numeric


def market_context(last: dict) -> str:
    """Generate market context string: BTC status, 4H trend, funding."""
    btc_rsi = last.get('btc_rsi_1h', 50)
    btc_bull = last.get('btc_is_bull_1h', 0)
    bull_4h = last.get('is_bull_4h', 0)

    if btc_bull and btc_rsi > 55:
        btc_status = "\U0001f7e2 Bullish"
    elif btc_rsi > 40:
        btc_status = "\U0001f7e1 Neutral"
    else:
        btc_status = "\U0001f534 Bearish"

    tf_4h = "\U0001f7e2 Uptrend" if bull_4h else "\U0001f534 Downtrend"

    parts = [f"BTC: {btc_status} (RSI {btc_rsi:.0f})", f"4H: {tf_4h}"]

    funding = last.get('funding_rate', 0)
    if funding != 0:
        funding_pct = funding * 100
        parts.append(f"Fund: {funding_pct:+.3f}%")

    return " | ".join(parts)


def get_market_regime(last: dict) -> str:
    """Detect market regime from ADX + EMA200 + BB width."""
    adx_val = last.get('adx', 0)
    ema_200 = last.get('ema_200', 0)
    close = last.get('close', 0)
    is_bull = last.get('is_bull', 0)
    bb_width = last.get('bb_width', 0)
    bb_width_sma = last.get('bb_width_sma', 0)

    high_vol = bb_width > bb_width_sma * 1.5 if bb_width_sma > 0 else False

    if adx_val < 20:
        return "Ranging (High Vol)" if high_vol else "Ranging"
    elif is_bull and close > ema_200:
        return "Trending Bull"
    else:
        return "Trending Bear (High Vol)" if high_vol else "Trending Bear"


def get_estimated_hold(conf_numeric: int) -> str:
    """Get estimated hold time based on confidence level."""
    if conf_numeric >= 8:
        return "2-6h"
    elif conf_numeric >= 6:
        return "6-24h"
    return "24-48h"


