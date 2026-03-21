#!/usr/bin/env python3
"""Export Freqtrade trades from SQLite to CSV + summary JSON.

Usage:
    python export_trades.py              # export only
    python export_trades.py --notify     # export + send Telegram summary
"""

import argparse
import csv
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

FT_HOME = os.environ.get("FT_HOME", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.getenv("FT_DB_PATH", os.path.join(FT_HOME, "tradesv3.dryrun.sqlite"))
CSV_PATH = os.getenv("FT_CSV_PATH", os.path.join(FT_HOME, "trades_history.csv"))
JSON_PATH = os.getenv("FT_JSON_PATH", os.path.join(FT_HOME, "trades_summary.json"))
CONFIG_PATH = os.getenv("FT_CONFIG_PATH", os.path.join(FT_HOME, "config.json"))

CSV_COLUMNS = [
    "Date (open)", "Date (close)", "Pair", "Side", "Entry Price",
    "Exit Price", "Profit %", "Profit $", "Duration", "Exit Reason", "Leverage",
]

QUERY = """
SELECT pair, open_date, close_date, open_rate, close_rate,
       close_profit AS profit_ratio, close_profit_abs AS profit_abs,
       exit_reason, leverage, stake_amount
FROM trades
WHERE is_open = 0
ORDER BY close_date ASC
"""


def load_trades(db_path: str) -> list[dict]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(QUERY).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def fmt_dt(val: str | None) -> str:
    if not val:
        return ""
    return val.replace(" ", "T")[:19]


def calc_duration(open_date: str, close_date: str) -> str:
    """Calculate trade duration from open/close dates."""
    if not open_date or not close_date:
        return "0h"
    try:
        fmt = "%Y-%m-%d %H:%M:%S"
        od = datetime.strptime(open_date[:19], fmt)
        cd = datetime.strptime(close_date[:19], fmt)
        hours = (cd - od).total_seconds() / 3600
        if hours < 1:
            return f"{int(hours * 60)}m"
        return f"{hours:.1f}h"
    except (ValueError, TypeError):
        return "N/A"


def write_csv(trades: list[dict], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_COLUMNS)
        for t in trades:
            side = "short" if (t.get("leverage") or 1) < 0 else "long"
            leverage = abs(t.get("leverage") or 1)
            w.writerow([
                fmt_dt(t["open_date"]),
                fmt_dt(t["close_date"]),
                t["pair"],
                side,
                f'{t["open_rate"]:.6f}',
                f'{t["close_rate"]:.6f}',
                f'{(t["profit_ratio"] or 0) * 100:.2f}',
                f'{t["profit_abs"] or 0:.2f}',
                calc_duration(t["open_date"], t["close_date"]),
                t["exit_reason"] or "",
                f'{leverage:.0f}x',
            ])


def build_summary(trades: list[dict]) -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not trades:
        return {"updated": now, "total_trades": 0, "win_rate": 0,
                "total_profit_pct": 0, "total_profit_usd": 0,
                "avg_duration_hours": 0, "best_trade": None,
                "worst_trade": None, "by_pair": {}}

    profits = [(t["profit_ratio"] or 0) * 100 for t in trades]
    profits_abs = [t["profit_abs"] or 0 for t in trades]
    durations = []
    for t in trades:
        try:
            fmt = "%Y-%m-%d %H:%M:%S"
            od = datetime.strptime(str(t["open_date"])[:19], fmt)
            cd = datetime.strptime(str(t["close_date"])[:19], fmt)
            durations.append((cd - od).total_seconds() / 3600)
        except (ValueError, TypeError):
            durations.append(0)
    wins = sum(1 for p in profits if p > 0)

    best = max(trades, key=lambda t: t["profit_ratio"] or 0)
    worst = min(trades, key=lambda t: t["profit_ratio"] or 0)

    by_pair: dict[str, dict] = {}
    for t in trades:
        pair = t["pair"]
        entry = by_pair.setdefault(pair, {"trades": 0, "profit_pct": 0.0, "wins": 0})
        entry["trades"] += 1
        entry["profit_pct"] += (t["profit_ratio"] or 0) * 100
        if (t["profit_ratio"] or 0) > 0:
            entry["wins"] += 1

    by_pair_clean = {}
    for pair, v in sorted(by_pair.items(), key=lambda x: -x[1]["profit_pct"]):
        by_pair_clean[pair] = {
            "trades": v["trades"],
            "profit_pct": round(v["profit_pct"], 2),
            "win_rate": round(v["wins"] / v["trades"] * 100, 1),
        }

    return {
        "updated": now,
        "total_trades": len(trades),
        "win_rate": round(wins / len(trades) * 100, 1),
        "total_profit_pct": round(sum(profits), 2),
        "total_profit_usd": round(sum(profits_abs), 2),
        "avg_duration_hours": round(sum(durations) / len(durations), 1),
        "best_trade": {"pair": best["pair"], "profit_pct": round((best["profit_ratio"] or 0) * 100, 2)},
        "worst_trade": {"pair": worst["pair"], "profit_pct": round((worst["profit_ratio"] or 0) * 100, 2)},
        "by_pair": by_pair_clean,
    }


def send_telegram(summary: dict) -> None:
    import requests

    token = os.environ.get("TG_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")

    if not token or not chat_id:
        try:
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
            tg = cfg.get("telegram", {})
            token = token or tg.get("token", "")
            chat_id = chat_id or str(tg.get("chat_id", ""))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    if not token or not chat_id:
        print("Telegram credentials not found, skipping notification.")
        return

    s = summary
    text = (
        f"📊 *Trade Export Summary*\n"
        f"Trades: {s['total_trades']} | Win rate: {s['win_rate']}%\n"
        f"Profit: {s['total_profit_pct']}% (${s['total_profit_usd']})\n"
        f"Avg duration: {s['avg_duration_hours']}h\n"
    )
    if s.get("best_trade"):
        text += f"Best: {s['best_trade']['pair']} +{s['best_trade']['profit_pct']}%\n"
    if s.get("worst_trade"):
        text += f"Worst: {s['worst_trade']['pair']} {s['worst_trade']['profit_pct']}%\n"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
    print("Telegram notification sent.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Export Freqtrade trades to CSV")
    parser.add_argument("--notify", action="store_true", help="Send summary to Telegram")
    args = parser.parse_args()

    if not Path(DB_PATH).exists():
        print(f"Database not found: {DB_PATH}")
        return

    trades = load_trades(DB_PATH)
    print(f"Found {len(trades)} closed trades.")

    write_csv(trades, CSV_PATH)
    print(f"CSV saved: {CSV_PATH}")

    summary = build_summary(trades)
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Summary saved: {JSON_PATH}")

    if args.notify:
        send_telegram(summary)


if __name__ == "__main__":
    main()
