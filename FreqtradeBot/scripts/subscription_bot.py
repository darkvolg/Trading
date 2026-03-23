#!/usr/bin/env python3
"""
TrendRider Signals — Subscription Management Bot.
Standalone bot running alongside Freqtrade for managing user subscriptions,
referrals, and tier-based access to trading signals.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone

import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

FT_HOME = os.environ.get(
    "FT_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

SUB_DB_PATH = os.path.join(FT_HOME, "subscriptions.db")
TRADE_DB_PATH = os.getenv(
    "FT_DB_PATH", os.path.join(FT_HOME, "tradesv3.dryrun.sqlite")
)
CONFIG_PATH = os.getenv("FT_CONFIG_PATH", os.path.join(FT_HOME, "config.json"))

ADMIN_IDS: list[int] = [
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()
]
FREE_CHANNEL_ID = os.getenv("FREE_CHANNEL_ID", "")
VIP_CHANNEL_ID = os.getenv("VIP_CHANNEL_ID", "")

BOT_USERNAME = "dtrade_signals_bot"
REFERRAL_BONUS_DAYS = 7

# ── CryptoBot (Crypto Pay) ──────────────────────────────────────────────
CRYPTOBOT_API_TOKEN = os.getenv(
    "CRYPTOBOT_API_TOKEN", "REDACTED"
)
CRYPTOBOT_API_URL = "https://pay.crypt.bot/api/"

PAYMENT_PLANS: dict[str, dict] = {
    "basic": {
        "amount": "39.00",
        "description": "TrendRider Basic - 1 Month",
        "tier": "basic",
        "days": 30,
        "label": "Basic ($39/mo)",
    },
    "vip": {
        "amount": "99.00",
        "description": "TrendRider VIP - 1 Month",
        "tier": "vip",
        "days": 30,
        "label": "VIP ($99/mo)",
    },
}


# ── Credentials ──────────────────────────────────────────────────────────


def get_token() -> str:
    """Return Telegram bot token for subscription bot (TrendRider Hub)."""
    token = os.getenv("SUB_BOT_TOKEN")
    if token:
        return token

    # Fallback: TG_TOKEN env or config.json
    token = os.getenv("TG_TOKEN")
    if token:
        return token

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        token = cfg.get("telegram", {}).get("token", "")
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        logger.warning("Cannot read config: %s", exc)

    if not token:
        raise RuntimeError("SUB_BOT_TOKEN is not set and not found in config.json")
    return token


# ── Database ─────────────────────────────────────────────────────────────


def _get_db() -> sqlite3.Connection:
    """Open (and initialize if needed) the subscriptions database."""
    conn = sqlite3.connect(SUB_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            first_name  TEXT,
            tier        TEXT    DEFAULT 'free',
            expires_at  TEXT,
            created_at  TEXT,
            is_active   INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS referrals (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL,
            created_at  TEXT,
            reward_applied INTEGER DEFAULT 0,
            UNIQUE(referrer_id, referred_id)
        );
        """
    )
    conn.commit()
    return conn


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure_subscriber(
    conn: sqlite3.Connection,
    user_id: int,
    username: str | None,
    first_name: str | None,
) -> None:
    """Insert subscriber if not exists, update name fields if they changed."""
    conn.execute(
        """
        INSERT INTO subscribers (user_id, username, first_name, tier, created_at, is_active)
        VALUES (?, ?, ?, 'free', ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET
            username   = excluded.username,
            first_name = excluded.first_name
        """,
        (user_id, username, first_name, _now_iso()),
    )
    conn.commit()


def _get_subscriber(conn: sqlite3.Connection, user_id: int) -> sqlite3.Row | None:
    cur = conn.execute("SELECT * FROM subscribers WHERE user_id = ?", (user_id,))
    return cur.fetchone()


def _set_tier(
    conn: sqlite3.Connection, user_id: int, tier: str, expires_at: str | None
) -> None:
    conn.execute(
        "UPDATE subscribers SET tier = ?, expires_at = ? WHERE user_id = ?",
        (tier, expires_at, user_id),
    )
    conn.commit()


def _add_days(conn: sqlite3.Connection, user_id: int, days: int) -> None:
    """Add days to a user's subscription. Upgrade free users to VIP."""
    sub = _get_subscriber(conn, user_id)
    if not sub:
        return

    now = datetime.now(timezone.utc)

    if sub["tier"] == "free" or not sub["expires_at"]:
        # Free user or no expiry: start from now
        new_expiry = now + timedelta(days=days)
        _set_tier(conn, user_id, "vip", new_expiry.strftime("%Y-%m-%dT%H:%M:%SZ"))
    else:
        # Existing subscription: extend from current expiry or now, whichever is later
        try:
            current_expiry = datetime.fromisoformat(
                sub["expires_at"].replace("Z", "+00:00")
            )
        except (ValueError, TypeError):
            current_expiry = now

        base = max(current_expiry, now)
        new_expiry = base + timedelta(days=days)
        _set_tier(conn, user_id, sub["tier"], new_expiry.strftime("%Y-%m-%dT%H:%M:%SZ"))


def _referral_count(conn: sqlite3.Connection, user_id: int) -> int:
    cur = conn.execute(
        "SELECT COUNT(*) FROM referrals WHERE referrer_id = ?", (user_id,)
    )
    return cur.fetchone()[0]


def _resolve_user(conn: sqlite3.Connection, identifier: str) -> int | None:
    """Resolve a user_id from a numeric ID or @username string."""
    identifier = identifier.lstrip("@")
    if identifier.isdigit():
        return int(identifier)
    cur = conn.execute(
        "SELECT user_id FROM subscribers WHERE username = ?", (identifier,)
    )
    row = cur.fetchone()
    return row["user_id"] if row else None


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ── CryptoBot helpers ────────────────────────────────────────────────────


async def _create_cryptobot_invoice(plan_key: str, user_id: int) -> dict | None:
    """Call CryptoBot API to create a payment invoice.

    Returns the API response dict on success, or None on failure.
    """
    plan = PAYMENT_PLANS.get(plan_key)
    if not plan:
        return None

    payload = {
        "currency_type": "fiat",
        "fiat": "USD",
        "amount": plan["amount"],
        "description": plan["description"],
        "payload": f"{plan_key}_{user_id}",
        "paid_btn_name": "openBot",
        "paid_btn_url": f"https://t.me/{BOT_USERNAME}",
    }

    headers = {
        "Crypto-Pay-API-Token": CRYPTOBOT_API_TOKEN,
        "Content-Type": "application/json",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{CRYPTOBOT_API_URL}createInvoice",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15),
            ) as resp:
                data = await resp.json()
                if resp.status == 200 and data.get("ok"):
                    return data.get("result", {})
                logger.error(
                    "CryptoBot API error: status=%d, body=%s", resp.status, data
                )
                return None
    except Exception:
        logger.exception("CryptoBot API request failed")
        return None


async def _handle_payment_deeplink(
    update: Update, plan_key: str, user_id: int
) -> None:
    """Create a CryptoBot invoice and send the payment link to the user."""
    plan = PAYMENT_PLANS.get(plan_key)
    if not plan:
        await update.message.reply_text("Unknown plan. Use /plans to see options.")
        return

    await update.message.reply_text(
        f"Creating payment link for *{plan['label']}*...\nPlease wait.",
        parse_mode="Markdown",
    )

    invoice = await _create_cryptobot_invoice(plan_key, user_id)
    if not invoice:
        await update.message.reply_text(
            "Sorry, failed to create payment link. Please try again later "
            "or contact support."
        )
        return

    pay_url = invoice.get("pay_url") or invoice.get("bot_invoice_url", "")
    if not pay_url:
        await update.message.reply_text(
            "Payment service returned an unexpected response. Please contact support."
        )
        return

    keyboard = [
        [InlineKeyboardButton(f"Pay {plan['label']}", url=pay_url)],
        [InlineKeyboardButton("View All Plans", callback_data="plans")],
    ]

    await update.message.reply_text(
        f"*Payment for {plan['label']}*\n"
        f"============================\n\n"
        f"Amount: *${plan['amount']}*\n"
        f"Duration: {plan['days']} days\n\n"
        f"Click the button below to pay via CryptoBot.\n"
        f"After payment, your subscription will be activated automatically.\n\n"
        f"============================\n"
        f"_Powered by @CryptoBot_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ── /start ───────────────────────────────────────────────────────────────


async def start_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message, register user, handle referral deep links."""
    user = update.effective_user
    if not user:
        return

    conn = _get_db()
    try:
        _ensure_subscriber(conn, user.id, user.username, user.first_name)

        # Handle deep links: /start ref_*, pay_basic, pay_vip
        args = ctx.args or []
        if args and args[0].startswith("ref_"):
            try:
                referrer_id = int(args[0][4:])
            except ValueError:
                referrer_id = None

            if referrer_id and referrer_id != user.id:
                referrer = _get_subscriber(conn, referrer_id)
                if referrer:
                    # Check if this referral already exists
                    existing = conn.execute(
                        "SELECT id FROM referrals WHERE referrer_id = ? AND referred_id = ?",
                        (referrer_id, user.id),
                    ).fetchone()

                    if not existing:
                        conn.execute(
                            """
                            INSERT INTO referrals (referrer_id, referred_id, created_at, reward_applied)
                            VALUES (?, ?, ?, 1)
                            """,
                            (referrer_id, user.id, _now_iso()),
                        )
                        conn.commit()

                        # Grant referrer +7 days
                        _add_days(conn, referrer_id, REFERRAL_BONUS_DAYS)

                        # Notify referrer
                        display = f"@{user.username}" if user.username else user.first_name
                        try:
                            await ctx.bot.send_message(
                                chat_id=referrer_id,
                                text=(
                                    f"\U0001f389 {display} joined via your link! "
                                    f"+{REFERRAL_BONUS_DAYS} days VIP added to your account."
                                ),
                                parse_mode="Markdown",
                            )
                        except Exception:
                            logger.warning("Could not notify referrer %d", referrer_id)

        # Handle payment deep links: ?start=pay_basic or ?start=pay_vip
        if args and args[0].startswith("pay_"):
            plan_key = args[0][4:]  # "basic" or "vip"
            if plan_key in PAYMENT_PLANS:
                conn.close()
                await _handle_payment_deeplink(update, plan_key, user.id)
                return

        keyboard = [
            [InlineKeyboardButton("View Plans", callback_data="plans")],
            [InlineKeyboardButton("My Status", callback_data="status")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "*Welcome to TrendRider Signals!*\n"
            "============================\n\n"
            "Algorithmic crypto signals powered by TrendRider strategy.\n\n"
            "*Subscription tiers:*\n"
            "  Free  — Delayed signals (3h), monthly report\n"
            "  Basic ($39/mo) — Real-time signals, Cornix format, weekly recap\n"
            "  VIP ($99/mo) — Everything + post-trade analysis, daily briefings, priority support\n\n"
            "Use /plans for details or /help for all commands.\n"
            "============================\n"
            "_@TrendRiderSignals_",
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
    finally:
        conn.close()


# ── /plans ───────────────────────────────────────────────────────────────


PLANS_TEXT = (
    "*TrendRider Signal Plans*\n"
    "============================\n\n"
    "\U0001f539 *Free* — $0/mo\n"
    "  \u2022 Delayed signals (3h after real-time)\n"
    "  \u2022 Monthly performance report\n\n"
    "\U0001f538 *Basic* — $39/mo\n"
    "  \u2022 Real-time signals as they fire\n"
    "  \u2022 Cornix-ready format (copy-paste)\n"
    "  \u2022 Weekly performance recap\n\n"
    "\U0001f4ce *VIP* — $99/mo\n"
    "  \u2022 Everything in Basic\n"
    "  \u2022 Post-trade analysis & lessons\n"
    "  \u2022 Daily market briefings\n"
    "  \u2022 Priority support\n\n"
    "Invite friends with /refer to earn free VIP days!\n"
    "============================\n"
    "_Use /pay to subscribe via crypto._"
)


async def plans_command(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show available subscription tiers."""
    await update.message.reply_text(PLANS_TEXT, parse_mode="Markdown")


# ── /pay ─────────────────────────────────────────────────────────────────


async def pay_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a CryptoBot payment link: /pay basic or /pay vip."""
    user = update.effective_user
    if not user:
        return

    conn = _get_db()
    try:
        _ensure_subscriber(conn, user.id, user.username, user.first_name)
    finally:
        conn.close()

    args = ctx.args or []
    if not args or args[0].lower() not in PAYMENT_PLANS:
        keyboard = [
            [
                InlineKeyboardButton(
                    "Basic — $39/mo",
                    url=f"https://t.me/{BOT_USERNAME}?start=pay_basic",
                ),
            ],
            [
                InlineKeyboardButton(
                    "VIP — $99/mo",
                    url=f"https://t.me/{BOT_USERNAME}?start=pay_vip",
                ),
            ],
        ]
        await update.message.reply_text(
            "*Choose a plan to subscribe:*\n\n"
            "\U0001f538 *Basic* — $39/mo — Real-time signals, Cornix format\n"
            "\U0001f4ce *VIP* — $99/mo — Everything + analysis & briefings\n",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        return

    plan_key = args[0].lower()
    await _handle_payment_deeplink(update, plan_key, user.id)


# ── /status ──────────────────────────────────────────────────────────────


async def status_command(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user's current subscription status."""
    user = update.effective_user
    if not user:
        return

    conn = _get_db()
    try:
        sub = _get_subscriber(conn, user.id)
        if not sub:
            await update.message.reply_text(
                "You are not registered yet. Use /start to begin."
            )
            return

        tier = sub["tier"].upper()
        refs = _referral_count(conn, user.id)
        ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user.id}"

        if sub["tier"] == "free" or not sub["expires_at"]:
            expiry_line = "Expires: N/A (free tier)"
        else:
            try:
                exp_dt = datetime.fromisoformat(
                    sub["expires_at"].replace("Z", "+00:00")
                )
                remaining = exp_dt - datetime.now(timezone.utc)
                days_left = max(0, remaining.days)
                expiry_line = (
                    f"Expires: {exp_dt.strftime('%Y-%m-%d')} ({days_left} days left)"
                )
            except (ValueError, TypeError):
                expiry_line = "Expires: unknown"

        await update.message.reply_text(
            f"*Your Subscription*\n"
            f"============================\n"
            f"Tier: *{tier}*\n"
            f"{expiry_line}\n"
            f"Referrals: {refs}\n\n"
            f"Your referral link:\n`{ref_link}`\n"
            f"============================\n"
            f"_Share your link to earn +{REFERRAL_BONUS_DAYS} days VIP per referral!_",
            parse_mode="Markdown",
        )
    finally:
        conn.close()


# ── /refer ───────────────────────────────────────────────────────────────


async def refer_command(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user's unique referral link."""
    user = update.effective_user
    if not user:
        return

    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{user.id}"

    conn = _get_db()
    try:
        refs = _referral_count(conn, user.id)
    finally:
        conn.close()

    await update.message.reply_text(
        f"*Referral Program*\n"
        f"============================\n\n"
        f"Your link:\n`{ref_link}`\n\n"
        f"Each person who joins via your link = "
        f"+{REFERRAL_BONUS_DAYS} days VIP for you.\n\n"
        f"Total referrals: {refs}\n"
        f"============================\n"
        f"_Share and earn!_",
        parse_mode="Markdown",
    )


# ── /calc ────────────────────────────────────────────────────────────────


async def calc_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Risk calculator: /calc <deposit> <risk_percent>"""
    args = ctx.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/calc <deposit> <risk_percent>`\nExample: `/calc 1000 2`",
            parse_mode="Markdown",
        )
        return

    try:
        deposit = float(args[0])
        risk_pct = float(args[1])
    except ValueError:
        await update.message.reply_text("Please provide valid numbers.")
        return

    risk_amount = deposit * risk_pct / 100

    lines = [
        "*RISK CALCULATOR*",
        "============================",
        f"Deposit: ${deposit:,.0f}",
        f"Risk per trade: {risk_pct}% (${risk_amount:,.2f})",
        "",
    ]

    for sl_pct in (6, 3):
        pos_size = risk_amount / (sl_pct / 100)
        margin = pos_size / 3
        lines += [
            f"With SL at -{sl_pct}% {'(TrendRider default)' if sl_pct == 6 else ''}:",
            f"  Position size: ${pos_size:,.2f}",
            f"  With 3x leverage: margin ${margin:,.2f}",
            f"  Max loss: ${risk_amount:,.2f}",
            "",
        ]

    lines += [
        "============================",
        "_Adjust risk to your comfort level_",
    ]

    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


# ── /stats ───────────────────────────────────────────────────────────────


def _query_stats() -> str:
    """Read Freqtrade SQLite and build stats message."""
    if not os.path.exists(TRADE_DB_PATH):
        return "*TRENDRIDER STATS*\n\nNo database found. Bot may not have started yet."

    conn = sqlite3.connect(TRADE_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    since = (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    cur.execute(
        """
        SELECT id, pair, open_date, close_date, open_rate, close_rate,
               close_profit_abs AS profit_abs, close_profit AS profit_ratio,
               stake_amount, is_open
        FROM trades
        WHERE open_date >= ?
        ORDER BY open_date DESC
        """,
        (since,),
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return (
            "*TRENDRIDER STATS*\n============================\n"
            "No trades yet. Bot is monitoring markets.\n"
            "============================\n_TrendRider Algo | @TrendRiderSignals_"
        )

    total = len(rows)
    open_trades = sum(1 for r in rows if r["is_open"])
    closed = [r for r in rows if not r["is_open"]]
    wins = [r for r in closed if (r["profit_abs"] or 0) > 0]
    losses = [r for r in closed if (r["profit_abs"] or 0) <= 0]
    win_rate = len(wins) / len(closed) * 100 if closed else 0

    total_profit = sum(r["profit_abs"] or 0 for r in closed)
    avg_profit = total_profit / len(closed) if closed else 0

    total_stake = sum(r["stake_amount"] or 0 for r in closed) or 1
    total_profit_pct = total_profit / total_stake * 100
    avg_profit_pct = avg_profit / (total_stake / len(closed)) * 100 if closed else 0

    best = max(closed, key=lambda r: r["profit_abs"] or 0) if closed else None
    worst = min(closed, key=lambda r: r["profit_abs"] or 0) if closed else None

    # By pair
    pair_map: dict[str, dict] = {}
    for r in closed:
        pair = r["pair"]
        entry = pair_map.setdefault(pair, {"count": 0, "profit": 0.0})
        entry["count"] += 1
        entry["profit"] += r["profit_abs"] or 0

    lines = [
        "*TRENDRIDER STATS*",
        "============================",
        "Period: last 30 days",
        "",
        f"Trades: {total} | Open: {open_trades}",
        f"Win: {len(wins)} | Loss: {len(losses)}",
        f"Win Rate: {win_rate:.1f}%",
        "",
        f"Total Profit: {'+' if total_profit >= 0 else ''}${total_profit:.2f}"
        f" ({'+' if total_profit_pct >= 0 else ''}{total_profit_pct:.2f}%)",
        f"Avg Profit: {'+' if avg_profit >= 0 else ''}${avg_profit:.2f}"
        f" ({'+' if avg_profit_pct >= 0 else ''}{avg_profit_pct:.2f}%)",
    ]

    if best:
        bp = (best["profit_ratio"] or 0) * 100
        lines.append(
            f"Best: {best['pair']} {'+' if best['profit_abs'] >= 0 else ''}"
            f"${best['profit_abs']:.2f} ({'+' if bp >= 0 else ''}{bp:.1f}%)"
        )
    if worst:
        wp = (worst["profit_ratio"] or 0) * 100
        lines.append(
            f"Worst: {worst['pair']} {'+' if worst['profit_abs'] >= 0 else ''}"
            f"${worst['profit_abs']:.2f} ({'+' if wp >= 0 else ''}{wp:.1f}%)"
        )

    lines.append("")
    lines.append("By Pair:")
    for pair, data in sorted(pair_map.items(), key=lambda x: -x[1]["profit"]):
        short = pair.replace("/USDT", "").replace("/USDT:USDT", "")
        sign = "+" if data["profit"] >= 0 else ""
        lines.append(f"  {short}: {data['count']} trades, {sign}${data['profit']:.2f}")

    lines += [
        "",
        "============================",
        "_TrendRider Algo | @TrendRiderSignals_",
    ]
    return "\n".join(lines)


async def stats_command(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show trading statistics for the last 30 days."""
    try:
        text = _query_stats()
    except Exception as exc:
        logger.exception("Stats query failed")
        text = f"Error reading stats: {exc}"
    await update.message.reply_text(text, parse_mode="Markdown")


# ── /help ────────────────────────────────────────────────────────────────


HELP_TEXT = (
    "*TrendRider Signals Bot*\n"
    "============================\n"
    "Available commands:\n\n"
    "`/start` \u2014 Welcome & registration\n"
    "`/plans` \u2014 Subscription tiers & pricing\n"
    "`/pay` \u2014 Subscribe (pay via crypto)\n"
    "`/status` \u2014 Your subscription info\n"
    "`/refer` \u2014 Your referral link\n"
    "`/calc <deposit> <risk%>` \u2014 Risk calculator\n"
    "`/stats` \u2014 Trading stats (last 30 days)\n"
    "`/help` \u2014 This message\n"
    "============================\n"
    "_@TrendRiderSignals_"
)


async def help_command(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help message."""
    await update.message.reply_text(HELP_TEXT, parse_mode="Markdown")


# ── Admin commands ───────────────────────────────────────────────────────


async def grant_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin: /grant <user_id_or_@username> <tier> <days>"""
    user = update.effective_user
    if not user or not _is_admin(user.id):
        await update.message.reply_text("Access denied.")
        return

    args = ctx.args or []
    if len(args) < 3:
        await update.message.reply_text(
            "Usage: `/grant <user_id_or_@username> <tier> <days>`\n"
            "Example: `/grant 12345 vip 30`",
            parse_mode="Markdown",
        )
        return

    identifier = args[0]
    tier = args[1].lower()
    if tier not in ("free", "basic", "vip"):
        await update.message.reply_text("Tier must be one of: free, basic, vip")
        return

    try:
        days = int(args[2])
    except ValueError:
        await update.message.reply_text("Days must be an integer.")
        return

    conn = _get_db()
    try:
        resolved_id = _resolve_user(conn, identifier)
        if resolved_id is None:
            await update.message.reply_text(f"User `{identifier}` not found.")
            return

        if tier == "free":
            _set_tier(conn, resolved_id, "free", None)
        else:
            expires = (
                datetime.now(timezone.utc) + timedelta(days=days)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")
            _set_tier(conn, resolved_id, tier, expires)

        await update.message.reply_text(
            f"Granted *{tier.upper()}* for {days} days to user `{resolved_id}`.",
            parse_mode="Markdown",
        )
    finally:
        conn.close()


async def revoke_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin: /revoke <user_id_or_@username> — reset to free tier."""
    user = update.effective_user
    if not user or not _is_admin(user.id):
        await update.message.reply_text("Access denied.")
        return

    args = ctx.args or []
    if len(args) < 1:
        await update.message.reply_text(
            "Usage: `/revoke <user_id_or_@username>`", parse_mode="Markdown"
        )
        return

    conn = _get_db()
    try:
        resolved_id = _resolve_user(conn, args[0])
        if resolved_id is None:
            await update.message.reply_text(f"User `{args[0]}` not found.")
            return

        _set_tier(conn, resolved_id, "free", None)
        await update.message.reply_text(
            f"User `{resolved_id}` revoked to *FREE* tier.", parse_mode="Markdown"
        )
    finally:
        conn.close()


async def users_command(update: Update, _ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin: list all subscribers."""
    user = update.effective_user
    if not user or not _is_admin(user.id):
        await update.message.reply_text("Access denied.")
        return

    conn = _get_db()
    try:
        cur = conn.execute(
            "SELECT user_id, username, first_name, tier, expires_at, is_active "
            "FROM subscribers ORDER BY created_at DESC"
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    if not rows:
        await update.message.reply_text("No subscribers yet.")
        return

    lines = [f"*Subscribers ({len(rows)})*", "============================"]
    for r in rows:
        name = f"@{r['username']}" if r["username"] else r["first_name"] or "N/A"
        tier = r["tier"].upper()
        exp = r["expires_at"][:10] if r["expires_at"] else "N/A"
        active = "active" if r["is_active"] else "inactive"
        lines.append(f"`{r['user_id']}` {name} | {tier} | exp: {exp} | {active}")

    # Telegram message limit is 4096 chars; split if needed
    text = "\n".join(lines)
    if len(text) > 4000:
        # Send in chunks
        chunk_lines: list[str] = []
        chunk_len = 0
        for line in lines:
            if chunk_len + len(line) + 1 > 3900 and chunk_lines:
                await update.message.reply_text(
                    "\n".join(chunk_lines), parse_mode="Markdown"
                )
                chunk_lines = []
                chunk_len = 0
            chunk_lines.append(line)
            chunk_len += len(line) + 1
        if chunk_lines:
            await update.message.reply_text(
                "\n".join(chunk_lines), parse_mode="Markdown"
            )
    else:
        await update.message.reply_text(text, parse_mode="Markdown")


async def broadcast_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin: /broadcast <message> — send message to all active subscribers."""
    user = update.effective_user
    if not user or not _is_admin(user.id):
        await update.message.reply_text("Access denied.")
        return

    if not ctx.args:
        await update.message.reply_text(
            "Usage: `/broadcast <message>`", parse_mode="Markdown"
        )
        return

    # Everything after /broadcast is the message
    message_text = update.message.text
    if not message_text:
        return
    # Strip the /broadcast command itself
    broadcast_body = message_text.split(None, 1)
    if len(broadcast_body) < 2:
        await update.message.reply_text(
            "Usage: `/broadcast <message>`", parse_mode="Markdown"
        )
        return
    broadcast_body = broadcast_body[1]

    conn = _get_db()
    try:
        cur = conn.execute(
            "SELECT user_id FROM subscribers WHERE is_active = 1"
        )
        recipients = [r["user_id"] for r in cur.fetchall()]
    finally:
        conn.close()

    sent = 0
    failed = 0
    for uid in recipients:
        try:
            await ctx.bot.send_message(
                chat_id=uid, text=broadcast_body, parse_mode="Markdown"
            )
            sent += 1
        except Exception:
            logger.warning("Failed to send broadcast to %d", uid)
            failed += 1

    await update.message.reply_text(
        f"Broadcast complete: {sent} sent, {failed} failed."
    )


# ── main ─────────────────────────────────────────────────────────────────


def main() -> None:
    token = get_token()
    app = Application.builder().token(token).build()

    # User commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("plans", plans_command))
    app.add_handler(CommandHandler("pay", pay_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("refer", refer_command))
    app.add_handler(CommandHandler("calc", calc_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("help", help_command))

    # Admin commands
    app.add_handler(CommandHandler("grant", grant_command))
    app.add_handler(CommandHandler("revoke", revoke_command))
    app.add_handler(CommandHandler("users", users_command))
    app.add_handler(CommandHandler("broadcast", broadcast_command))

    logger.info("TrendRider subscription bot started (polling)")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
