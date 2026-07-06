#!/usr/bin/env python3
"""Export TrendRider bot live stats from freqtrade sqlite to public JSON.

Read: /opt/freqtrade/tradesv3.dryrun.sqlite
Write: /var/www/trendrider/api/live-stats.json

Run: every 5 min via cron.
"""
import json
import math
import re
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path

DB = "/opt/freqtrade/tradesv3.dryrun.sqlite"
OUT = Path("/var/www/trendrider/api/live-stats.json")
STRATEGY_FILE = Path("/opt/freqtrade/user_data/strategies/TrendRiderStrategy_exitfix.py")
STARTING_BALANCE = 500.0


def detect_strategy_version() -> str:
    """Read first 10 lines of strategy file to find version (e.g. v2.12.0)."""
    try:
        head = STRATEGY_FILE.read_text(errors="ignore").splitlines()[:10]
        for line in head:
            m = re.search(r"v(\d+\.\d+\.\d+)", line)
            if m:
                return m.group(1)
    except Exception:
        pass
    return "unknown"


def compute_drawdown(equity: list[dict]) -> dict:
    """Compute max drawdown from equity curve."""
    if not equity:
        return {"max_drawdown_pct": 0.0, "max_drawdown_abs": 0.0}
    peak = STARTING_BALANCE
    max_dd_abs = 0.0
    max_dd_pct = 0.0
    for e in equity:
        bal = e["balance"]
        if bal > peak:
            peak = bal
        dd_abs = peak - bal
        dd_pct = (dd_abs / peak) * 100 if peak else 0
        if dd_abs > max_dd_abs:
            max_dd_abs = dd_abs
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct
    return {
        "max_drawdown_pct": round(max_dd_pct, 2),
        "max_drawdown_abs": round(max_dd_abs, 2),
    }


def compute_profit_factor(trades: list[float]) -> float:
    """Profit factor = gross_profit / gross_loss."""
    gross_profit = sum(t for t in trades if t > 0)
    gross_loss = abs(sum(t for t in trades if t < 0))
    if gross_loss == 0:
        return round(gross_profit, 2) if gross_profit > 0 else 0.0
    return round(gross_profit / gross_loss, 2)


def compute_sqn(returns_pct: list[float]) -> float:
    """System Quality Number = sqrt(N) * mean / stdev of returns."""
    n = len(returns_pct)
    if n < 2:
        return 0.0
    mean = statistics.mean(returns_pct)
    sd = statistics.stdev(returns_pct)
    if sd == 0:
        return 0.0
    return round(math.sqrt(n) * mean / sd, 2)


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN is_open=0 THEN 1 ELSE 0 END) AS closed,
            SUM(CASE WHEN is_open=1 THEN 1 ELSE 0 END) AS open_count,
            COALESCE(SUM(CASE WHEN is_open=0 THEN close_profit_abs ELSE 0 END), 0) AS pnl_abs,
            COALESCE(SUM(CASE WHEN is_open=0 AND close_profit > 0 THEN 1 ELSE 0 END), 0) AS wins,
            COALESCE(SUM(CASE WHEN is_open=0 AND close_profit <= 0 THEN 1 ELSE 0 END), 0) AS losses,
            MIN(open_date) AS first_trade
        FROM trades
    """)
    totals = dict(cur.fetchone())
    closed = totals["closed"] or 0
    wins = totals["wins"] or 0
    wr = round(100.0 * wins / closed, 2) if closed else 0.0
    pnl_abs = round(totals["pnl_abs"] or 0.0, 2)
    balance = round(STARTING_BALANCE + pnl_abs, 2)
    pnl_pct = round(100.0 * pnl_abs / STARTING_BALANCE, 2)

    cur.execute("""
        SELECT close_profit_abs, close_profit
        FROM trades
        WHERE is_open = 0
    """)
    closed_trades_data = cur.fetchall()
    abs_returns = [(r["close_profit_abs"] or 0.0) for r in closed_trades_data]
    pct_returns = [(r["close_profit"] or 0.0) * 100 for r in closed_trades_data]

    profit_factor = compute_profit_factor(abs_returns)
    sqn = compute_sqn(pct_returns)

    cur.execute("""
        SELECT exit_reason,
               COUNT(*) AS count,
               ROUND(AVG(close_profit) * 100, 2) AS avg_pct,
               ROUND(SUM(close_profit_abs), 2) AS total_abs
        FROM trades
        WHERE is_open = 0
        GROUP BY exit_reason
        ORDER BY count DESC
    """)
    exit_breakdown = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT pair, open_date, close_date, close_profit, close_profit_abs, exit_reason, enter_tag
        FROM trades
        WHERE is_open = 0
        ORDER BY close_date DESC
        LIMIT 20
    """)
    recent = []
    for r in cur.fetchall():
        d = dict(r)
        d["close_profit_pct"] = round((d.pop("close_profit") or 0) * 100, 2)
        d["close_profit_abs"] = round(d["close_profit_abs"] or 0, 2)
        recent.append(d)

    cur.execute("""
        SELECT pair, open_date, stake_amount, open_rate
        FROM trades
        WHERE is_open = 1
        ORDER BY open_date ASC
    """)
    open_trades = [dict(r) for r in cur.fetchall()]

    cur.execute("""
        SELECT DATE(close_date) AS day,
               ROUND(SUM(close_profit_abs), 2) AS pnl,
               COUNT(*) AS trades
        FROM trades
        WHERE is_open = 0 AND close_date IS NOT NULL
        GROUP BY DATE(close_date)
        ORDER BY day ASC
    """)
    daily = [dict(r) for r in cur.fetchall()]

    running = STARTING_BALANCE
    equity = []
    for d in daily:
        running = round(running + (d["pnl"] or 0), 2)
        equity.append({"day": d["day"], "balance": running})

    drawdown = compute_drawdown(equity)
    version = detect_strategy_version()

    conn.close()

    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "strategy_version": version,
        "strategy": f"TrendRider v{version} (hyperopt-tuned, ROI ladder + custom_exit)",
        "mode": "dry-run (paper trading)",
        "starting_balance": STARTING_BALANCE,
        "current_balance": balance,
        "pnl_abs": pnl_abs,
        "pnl_pct": pnl_pct,
        "total_trades": totals["total"] or 0,
        "closed_trades": closed,
        "open_trades_count": totals["open_count"] or 0,
        "wins": wins,
        "losses": totals["losses"] or 0,
        "win_rate_pct": wr,
        "profit_factor": profit_factor,
        "sqn": sqn,
        "max_drawdown_pct": drawdown["max_drawdown_pct"],
        "max_drawdown_abs": drawdown["max_drawdown_abs"],
        "first_trade_date": totals["first_trade"],
        "exit_breakdown": exit_breakdown,
        "recent_trades": recent,
        "open_positions": open_trades,
        "equity_curve": equity,
        "daily_pnl": daily,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(stats, default=str, indent=2))
    tmp.replace(OUT)
    dd_pct = drawdown["max_drawdown_pct"]
    print("OK {}: v{}, {} closed, WR {}%, PF {}, MaxDD {}%, SQN {}, balance {}".format(OUT, version, closed, wr, profit_factor, dd_pct, sqn, balance))


if __name__ == "__main__":
    main()
