"""
TrendRider Configuration — HyroTrader Evaluation Config — tighter risk parameters.

HyroTrader $50K Evaluation Rules:
- Stoploss on every trade (within 5 min) — stoploss_on_exchange: true in config
- Max 3% risk per trade — STOPLOSS = -0.03
- Max 5% daily loss limit — MAX_DAILY_LOSS = -0.05
- Max 10% total drawdown — MAX_TOTAL_DRAWDOWN = -0.10

All magic numbers from the strategy collected in one place.
"""

# --- Fear & Greed Index ---
FNG_HEALTHY_MIN = 25
FNG_HEALTHY_MAX = 85
FNG_NEUTRAL_MIN = 40
FNG_NEUTRAL_MAX = 60
FNG_CACHE_TTL = 14400  # 4 hours

# --- BTC Context ---
BTC_RSI_HEALTHY_MIN = 40
BTC_RSI_HEALTHY_MAX = 70
BTC_RSI_LONG_MIN = 35

# --- Funding Rate ---
FUNDING_EXTREME_THRESHOLD = 0.0003
FUNDING_HEALTHY_THRESHOLD = 0.0001

# --- Open Interest ---
OI_SPIKE_THRESHOLD = 0.20  # 20% increase

# --- Price Alerts ---
ALERT_COOLDOWN_SECONDS = 14400  # 4 hours
EMA_PROXIMITY_PCT = 1.5  # percent

# --- Entry Zone ---
ENTRY_ZONE_PCT = 0.003  # +-0.3%

# --- Stoploss (HyroTrader: max 3% risk per trade) ---
STOPLOSS = -0.03  # 3% (HyroTrader limit, was -0.06)

# --- Take Profit Levels (tighter for faster evaluation) ---
TP1_PCT = 0.02   # +2% (was +3%)
TP2_PCT = 0.04   # +4% (was +5%)
TP3_PCT = 0.08   # +8% (was +10%)

# --- HyroTrader Risk Limits ---
MAX_DAILY_LOSS = -0.05       # 5% max daily loss
MAX_TOTAL_DRAWDOWN = -0.10   # 10% max total drawdown

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
}

# --- Bybit Affiliate (single source of truth: trendrider_config.py) ---

# --- Exit Reasons ---
EXIT_REASONS = {
    "roi": "ROI target reached",
    "stop_loss": "Stop Loss hit",
    "trailing_stop_loss": "Trailing Stop",
    "exit_signal": "Exit signal",
    "rsi_overbought": "RSI overbought (>81)",
    "ema_bearish_cross": "EMA bearish crossover",
    "trend_broken": "Trend broken (below EMA200)",
    "force_exit": "Force exit",
}
