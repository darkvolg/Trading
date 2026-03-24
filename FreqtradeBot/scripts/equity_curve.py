#!/usr/bin/env python3
"""
Equity Curve Generator — builds equity curve PNG from SQLite trades
and sends it to Telegram.

Run via cron (Sunday 12:00 UTC):
    0 12 * * 0 /usr/bin/python3 /path/to/scripts/equity_curve.py

Flags:
    --dry-run       Save PNG locally, don't send to Telegram
    --save PATH     Save PNG to specified path
    --balance N     Starting balance in USDT (default: 1000)
"""

import argparse
import io
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import matplotlib.ticker as mticker
except ImportError as e:
    def _notify_error(msg):
        try:
            token = os.getenv("TG_TOKEN", "")
            chat_id = os.getenv("TG_CHAT_ID", "")
            if token and chat_id:
                body = json.dumps({"chat_id": chat_id, "text": msg}).encode()
                req = Request(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    data=body,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                urlopen(req, timeout=10)
        except Exception:
            pass
    _notify_error(f"equity_curve.py: Import error: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
FT_HOME = os.environ.get(
    "FT_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
DB_PATH = os.getenv("FT_DB_PATH", os.path.join(FT_HOME, "tradesv3.dryrun.sqlite"))
CONFIG_PATH = os.getenv("FT_CONFIG_PATH", os.path.join(FT_HOME, "config.json"))

# Visual style
BG_COLOR = "#1a1a2e"
GRID_COLOR = "#16213e"
EQUITY_COLOR = "#00d4aa"
EQUITY_FILL_ALPHA = 0.15
DD_COLOR = "#ff6b6b"
DD_FILL_ALPHA = 0.35
TEXT_COLOR = "#e0e0e0"
ACCENT_COLOR = "#00d4aa"
WATERMARK = "@TrendRiderSignals"


# ---------------------------------------------------------------------------
# Telegram helpers
# ---------------------------------------------------------------------------
def get_telegram_config() -> tuple[str, str]:
    """Return (token, chat_id) from env vars or config.json."""
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")
    if token and chat_id:
        return token, chat_id
    with open(CONFIG_PATH, "r") as f:
        cfg = json.load(f)
    tg = cfg.get("telegram", {})
    return tg["token"], str(tg["chat_id"])


def send_photo(token: str, chat_id: str, photo_bytes: bytes, caption: str) -> dict:
    """Send a photo to Telegram via multipart/form-data using stdlib only."""
    boundary = "----FormBoundary" + os.urandom(8).hex()
    body = bytearray()
    # chat_id field
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode()
    )
    # caption field
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode()
    )
    # parse_mode
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        'Content-Disposition: form-data; name="parse_mode"\r\n\r\nMarkdown\r\n'.encode()
    )
    # photo file
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        'Content-Disposition: form-data; name="photo"; filename="equity_curve.png"\r\n'.encode()
    )
    body.extend(b"Content-Type: image/png\r\n\r\n")
    body.extend(photo_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    req = Request(
        f"https://api.telegram.org/bot{token}/sendPhoto",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def send_text(token: str, chat_id: str, text: str) -> dict:
    """Send a plain text message to Telegram."""
    payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
    req = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def fetch_trades(db_path: str) -> list[dict]:
    """Fetch all closed trades from the SQLite database."""
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT close_date, close_profit_abs, profit_ratio, pair
            FROM trades
            WHERE is_open = 0
            ORDER BY close_date
            """
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Chart
# ---------------------------------------------------------------------------
def build_chart(trades: list[dict], starting_balance: float) -> bytes:
    """Generate equity curve PNG and return as bytes."""
    # Parse dates and compute cumulative equity
    dates = []
    equity = []
    cum_profit = 0.0
    wins = 0

    for t in trades:
        dt_str = t["close_date"]
        # Handle both "YYYY-MM-DD HH:MM:SS" and ISO formats
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(dt_str.split("+")[0].strip(), fmt)
                break
            except ValueError:
                continue
        else:
            dt = datetime.strptime(dt_str[:19], "%Y-%m-%d %H:%M:%S")

        cum_profit += t["close_profit_abs"]
        dates.append(dt)
        equity.append(starting_balance + cum_profit)
        if t["profit_ratio"] > 0:
            wins += 1

    total_trades = len(trades)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
    final_equity = equity[-1]
    total_profit = final_equity - starting_balance
    profit_pct = (total_profit / starting_balance) * 100

    # Drawdown calculation
    peak = []
    drawdown_pct = []
    running_peak = equity[0]
    for eq in equity:
        running_peak = max(running_peak, eq)
        peak.append(running_peak)
        dd = (eq - running_peak) / running_peak * 100 if running_peak > 0 else 0.0
        drawdown_pct.append(dd)

    max_dd = min(drawdown_pct)

    # --- Plot ---
    fig, (ax_eq, ax_dd) = plt.subplots(
        2, 1,
        figsize=(12, 8),
        dpi=150,
        gridspec_kw={"height_ratios": [7, 3], "hspace": 0.12},
    )
    fig.patch.set_facecolor(BG_COLOR)

    for ax in (ax_eq, ax_dd):
        ax.set_facecolor(BG_COLOR)
        ax.tick_params(colors=TEXT_COLOR, labelsize=9)
        ax.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.6)
        for spine in ax.spines.values():
            spine.set_color(GRID_COLOR)

    # --- Equity subplot ---
    ax_eq.plot(dates, equity, color=EQUITY_COLOR, linewidth=1.8, label="Equity")
    ax_eq.fill_between(
        dates, starting_balance, equity,
        alpha=EQUITY_FILL_ALPHA, color=EQUITY_COLOR,
    )

    ax_eq.set_title(
        "TrendRider Equity Curve",
        fontsize=16, fontweight="bold", color=TEXT_COLOR, pad=15,
    )
    ax_eq.set_ylabel("Equity (USDT)", fontsize=11, color=TEXT_COLOR)
    ax_eq.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))

    # Stats legend box
    stats_text = (
        f"Final Equity: ${final_equity:,.2f}\n"
        f"Total Profit: ${total_profit:+,.2f} ({profit_pct:+.1f}%)\n"
        f"Trades: {total_trades}  |  Win Rate: {win_rate:.1f}%\n"
        f"Max Drawdown: {max_dd:.2f}%"
    )
    props = dict(boxstyle="round,pad=0.6", facecolor="#0f3460", alpha=0.85, edgecolor=ACCENT_COLOR)
    ax_eq.text(
        0.02, 0.97, stats_text,
        transform=ax_eq.transAxes, fontsize=9, verticalalignment="top",
        color=TEXT_COLOR, bbox=props, family="monospace",
    )

    # Annotate final value
    ax_eq.annotate(
        f"${final_equity:,.2f}",
        xy=(dates[-1], equity[-1]),
        xytext=(15, 10), textcoords="offset points",
        fontsize=10, fontweight="bold", color=EQUITY_COLOR,
        arrowprops=dict(arrowstyle="->", color=EQUITY_COLOR, lw=1.2),
    )

    ax_eq.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax_eq.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax_eq.get_xticklabels(), visible=False)

    # --- Drawdown subplot ---
    ax_dd.fill_between(dates, 0, drawdown_pct, alpha=DD_FILL_ALPHA, color=DD_COLOR)
    ax_dd.plot(dates, drawdown_pct, color=DD_COLOR, linewidth=1.0)
    ax_dd.set_ylabel("Drawdown (%)", fontsize=11, color=TEXT_COLOR)
    ax_dd.set_xlabel("Date", fontsize=11, color=TEXT_COLOR)
    ax_dd.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.1f%%"))
    ax_dd.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax_dd.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax_dd.get_xticklabels(), rotation=30, ha="right", fontsize=8)

    # Annotate max drawdown
    if max_dd < 0:
        max_dd_idx = drawdown_pct.index(max_dd)
        ax_dd.annotate(
            f"{max_dd:.2f}%",
            xy=(dates[max_dd_idx], max_dd),
            xytext=(10, -15), textcoords="offset points",
            fontsize=9, fontweight="bold", color=DD_COLOR,
            arrowprops=dict(arrowstyle="->", color=DD_COLOR, lw=1.0),
        )

    # Watermark
    fig.text(
        0.95, 0.02, WATERMARK,
        fontsize=8, color=TEXT_COLOR, alpha=0.3,
        ha="right", va="bottom", style="italic",
    )

    # Render to bytes
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="TrendRider Equity Curve Generator")
    parser.add_argument("--dry-run", action="store_true", help="Save PNG locally, don't send to Telegram")
    parser.add_argument("--save", type=str, default=None, help="Save PNG to specified path")
    parser.add_argument("--balance", type=float, default=1000, help="Starting balance in USDT (default: 1000)")
    args = parser.parse_args()

    trades = fetch_trades(DB_PATH)

    token, chat_id = get_telegram_config()

    # Not enough trades
    if len(trades) < 2:
        msg = "Not enough trades for equity curve yet"
        print(msg)
        if not args.dry_run:
            send_text(token, chat_id, msg)
        return

    print(f"Found {len(trades)} closed trades, building equity curve...")

    png_bytes = build_chart(trades, args.balance)

    # Save if requested
    if args.save:
        with open(args.save, "wb") as f:
            f.write(png_bytes)
        print(f"Saved to {args.save}")

    if args.dry_run:
        if not args.save:
            out_path = os.path.join(os.getcwd(), "equity_curve.png")
            with open(out_path, "wb") as f:
                f.write(png_bytes)
            print(f"Dry run — saved to {out_path}")
        return

    # Compute stats for caption
    cum_profit = 0.0
    wins = 0
    for t in trades:
        cum_profit += t["close_profit_abs"]
        if t["profit_ratio"] > 0:
            wins += 1

    final_equity = args.balance + cum_profit
    total_trades = len(trades)
    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0

    # Max drawdown
    running_peak = args.balance
    max_dd = 0.0
    eq = args.balance
    for t in trades:
        eq += t["close_profit_abs"]
        running_peak = max(running_peak, eq)
        dd = (eq - running_peak) / running_peak * 100 if running_peak > 0 else 0.0
        max_dd = min(max_dd, dd)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    caption = (
        "\U0001f4c8 TrendRider Equity Curve\n\n"
        f"Equity: {final_equity:,.2f} USDT\n"
        f"Trades: {total_trades}\n"
        f"Win Rate: {win_rate:.1f}%\n"
        f"Max DD: {max_dd:.2f}%\n\n"
        f"Updated: {today}"
    )

    print("Sending to Telegram...")
    send_photo(token, chat_id, png_bytes, caption)
    print("Done.")


if __name__ == "__main__":
    main()
