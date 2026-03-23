"""
TrendRider Configuration — centralized constants and thresholds.

All magic numbers from the strategy collected in one place.
"""

# --- Fear & Greed Index ---
FNG_HEALTHY_MIN = 25
FNG_HEALTHY_MAX = 85
FNG_NEUTRAL_MIN = 40
FNG_NEUTRAL_MAX = 60
FNG_SHORT_MIN = 15
FNG_SHORT_MAX = 75
FNG_CACHE_TTL = 14400  # 4 hours

# --- BTC Context ---
BTC_RSI_HEALTHY_MIN = 40
BTC_RSI_HEALTHY_MAX = 70
BTC_RSI_LONG_MIN = 35
BTC_RSI_SHORT_MAX = 65

# --- Funding Rate ---
FUNDING_EXTREME_THRESHOLD = 0.0003
FUNDING_HEALTHY_THRESHOLD = 0.0001
FUNDING_SHORT_BLOCK = -0.0003

# --- Open Interest ---
OI_SPIKE_THRESHOLD = 0.20  # 20% increase

# --- Price Alerts ---
ALERT_COOLDOWN_SECONDS = 14400  # 4 hours
EMA_PROXIMITY_PCT = 1.5  # percent

# --- Entry Zone ---
ENTRY_ZONE_PCT = 0.003  # +-0.3%

# --- Take Profit Levels ---
TP1_PCT = 0.03   # +3%
TP2_PCT = 0.05   # +5%
TP3_PCT = 0.10   # +10%

# --- DCA ---
DCA_MAX_ENTRIES = 3  # 1 initial + 2 DCA
DCA_TRIGGER_1 = -0.03
DCA_TRIGGER_2 = -0.05
DCA_SIZE_RATIO = 0.5

# --- Partial TP ---
TP1_CLOSE_RATIO = 0.3  # close 30%
TP2_CLOSE_RATIO = 0.3  # close 30%

# --- Confidence ---
CONFIDENCE_MAX_SCORE = 17.5
CONFIDENCE_MIN_DEFAULT = 5
CONFIDENCE_MIN_BEAR = 6

# --- Estimated Hold Time ---
EST_HOLD_MAP = {
    8: "2-6h",     # conf >= 8
    6: "6-24h",    # conf >= 6
    0: "24-48h",   # conf < 6
}

# --- Setup Names ---
SETUP_NAMES = {
    "trend_pullback": "Trend Pullback",
    "ema50_bounce": "EMA50 Bounce",
    "rsi_bounce": "RSI Oversold Bounce",
    "short_pullback": "Short Pullback",
    "short_ema50_rejection": "EMA50 Rejection",
    "short_rsi_overbought": "RSI Overbought",
}

# --- Exit Reasons ---
EXIT_REASONS = {
    "roi": "ROI target reached",
    "stop_loss": "Stop Loss hit",
    "trailing_stop_loss": "Trailing Stop",
    "exit_signal": "Exit signal",
    "rsi_overbought": "RSI overbought (>81)",
    "ema_bearish_cross": "EMA bearish crossover",
    "trend_broken": "Trend broken (below EMA200)",
    "rsi_oversold_short": "RSI oversold (<19)",
    "ema_bullish_cross_short": "EMA bullish crossover (short exit)",
    "trend_broken_short": "Trend broken (above EMA200)",
    "partial_tp1": "Partial TP1 (+3%)",
    "partial_tp2": "Partial TP2 (+5%)",
    "force_exit": "Force exit",
}
