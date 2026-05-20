"""Cash-and-carry configuration: pairs, thresholds, env-driven secrets.

Hardcoded defaults match the validated `carry_portfolio_sim.py` parameters.
Override at runtime via env vars to retune without redeploy.
"""
from dataclasses import dataclass, field
import os


# Same alts as V6A — all confirmed on both spot AND perp on Bybit MAINNET
# (2026-05-08 audit). Bybit TESTNET supports only a subset; missing pairs are
# silently skipped at fetch time — see `TESTNET_WHITELIST` below for the lean
# set used during testnet shake-down.
DEFAULT_WHITELIST = (
    "BTC", "ETH", "SOL", "DOGE", "XRP", "ADA", "AVAX", "DOT",
    "POL", "NEAR", "ATOM", "SUI", "LINK", "OP", "BNB",
)

# Bybit testnet has a reduced perp listing — confirmed missing 2026-05-08:
# AVAX/USDT:USDT, ATOM/USDT:USDT. Use this list when CARRY_TESTNET=true
# unless the user overrides via env. Keeps logs clean.
TESTNET_WHITELIST = tuple(s for s in DEFAULT_WHITELIST if s not in {"AVAX", "ATOM"})


@dataclass(frozen=True)
class CarryConfig:
    # --- Strategy params (validated 2026-05-08, see PHASE_2_5_CASH_AND_CARRY_PLAN.md) ---
    whitelist: tuple = DEFAULT_WHITELIST

    # 0.01% per 8h ≈ 11% APR — minimum funding rate to bother entering.
    # Sweep on full 4y showed 0.01-0.02% is sweet spot; lower = over-trades + fees.
    entry_threshold: float = 0.0001

    # Exit when funding crosses near-zero or negative.
    exit_threshold: float = -0.00005

    # Need N consecutive 8h periods passing the threshold before action.
    # 3 periods (24h) filters intraday noise without missing real regime shifts.
    entry_persistence: int = 3
    exit_persistence: int = 3

    # Capital allocation: max concurrent positions. Slot count barely affects
    # APR (4.7% @ 8 vs 5.3% @ 2 per portfolio sim) — pick based on capital
    # diversification preference, not return optimisation.
    n_slots: int = 4

    # Delta-rebalance threshold: if |spot_qty - perp_qty| / position_qty > X,
    # rebalance. Start conservative; tune from testnet observation.
    delta_drift_pct: float = 0.005  # 0.5%

    # Perp leg leverage. Start at 1x for safety. Config B (10% APR target)
    # uses 2x once empirics validate.
    perp_leverage: int = 1

    # Position size as fraction of total capital per slot. With 4 slots,
    # each position uses 25% of capital (split between spot and perp margin).
    position_size_pct: float = 0.25

    # Used when exchange balance fetch fails OR has_credentials=False
    # (testnet shake-down without keys). Bot will NOT open below this notional
    # in live mode — small_capital_floor acts as hard min order size guard.
    fallback_notional_usdt: float = 100.0
    small_capital_floor_usdt: float = 25.0

    # --- Operational ---
    # Loop cadence. Funding ticks 3x/day on Bybit (00:00, 08:00, 16:00 UTC).
    # Wake just after each tick to make decisions.
    tick_offset_minutes: int = 5

    # If funding stays negative >24h while in position, force-close even if
    # exit_persistence not yet hit. Catches sudden regime flips.
    stale_force_close_hours: int = 24

    # --- Bybit account ---
    api_key: str = ""
    api_secret: str = ""
    sub_account_uid: str = ""  # for logging/identification
    testnet: bool = True       # default safe; flip via env in production

    # --- Risk ---
    # Kill-switch file path; if exists, scheduler refuses new entries.
    kill_switch_path: str = "/tmp/carry_bot_kill"

    # Daily PnL alarm: notify if loss > X% of capital in 24h
    daily_loss_alarm_pct: float = 0.01  # 1%

    # --- Logging ---
    db_path: str = "/opt/freqtrade/carry_bot.sqlite"
    log_path: str = "/var/log/carry_bot.log"


def from_env() -> CarryConfig:
    """Build config from environment, with defaults for everything not set.

    Env vars (all optional):
        CARRY_API_KEY, CARRY_API_SECRET     — required for live trading
        CARRY_TESTNET                       — "true"/"false", default "true"
        CARRY_N_SLOTS                       — int, default 4
        CARRY_ENTRY_THRESHOLD               — float, default 0.0001
        CARRY_EXIT_THRESHOLD                — float, default -0.00005
        CARRY_PERP_LEVERAGE                 — int, default 1
        CARRY_KILL_SWITCH_PATH              — path, default /tmp/carry_bot_kill
    """
    def _get_float(name: str, default: float) -> float:
        v = os.environ.get(name)
        return float(v) if v else default

    def _get_int(name: str, default: int) -> int:
        v = os.environ.get(name)
        return int(v) if v else default

    def _get_bool(name: str, default: bool) -> bool:
        v = os.environ.get(name, "").lower()
        if not v:
            return default
        return v in ("1", "true", "yes", "y")

    testnet = _get_bool("CARRY_TESTNET", True)
    # Default whitelist depends on env: testnet has a reduced perp listing.
    whitelist = TESTNET_WHITELIST if testnet else DEFAULT_WHITELIST
    return CarryConfig(
        whitelist=whitelist,
        api_key=os.environ.get("CARRY_API_KEY", ""),
        api_secret=os.environ.get("CARRY_API_SECRET", ""),
        sub_account_uid=os.environ.get("CARRY_SUB_UID", ""),
        testnet=testnet,
        n_slots=_get_int("CARRY_N_SLOTS", 4),
        entry_threshold=_get_float("CARRY_ENTRY_THRESHOLD", 0.0001),
        exit_threshold=_get_float("CARRY_EXIT_THRESHOLD", -0.00005),
        perp_leverage=_get_int("CARRY_PERP_LEVERAGE", 1),
        kill_switch_path=os.environ.get("CARRY_KILL_SWITCH_PATH", "/tmp/carry_bot_kill"),
    )
