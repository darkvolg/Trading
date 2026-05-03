#!/usr/bin/env python3
"""Export TrendRider canonical backtest stats to public JSON.

Reads:
  - Pointer file: /opt/freqtrade/user_data/backtest_results/.canonical_baseline.json
    Format: {"baseline_zip": "backtest-result-2026-04-26_00-50-11.zip"}
  - Backtest zip: /opt/freqtrade/user_data/backtest_results/<baseline_zip>

Writes:
  - /var/www/trendrider/api/backtest-stats.json

Run: 1x/day via cron (changes only when a new canonical baseline is pinned).

Falls back to .last_result.json when the canonical pointer is missing — useful
for local dry-runs but unsafe for the public-facing /live page (latest run may
be an experiment, not the baseline). Use --dry-run to print without writing.
"""
import argparse
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

BACKTEST_DIR = Path("/opt/freqtrade/user_data/backtest_results")
POINTER = BACKTEST_DIR / ".canonical_baseline.json"
LAST_RESULT = BACKTEST_DIR / ".last_result.json"
OUT = Path("/var/www/trendrider/api/backtest-stats.json")
STARTING_BALANCE = 500.0


def resolve_baseline_zip() -> Path:
    """Return path to canonical baseline zip; fallback to last_result."""
    if POINTER.exists():
        try:
            data = json.loads(POINTER.read_text())
            zip_name = data.get("baseline_zip")
            if zip_name:
                return BACKTEST_DIR / zip_name
        except Exception as e:
            print(f"[WARN] Cannot parse {POINTER}: {e}", file=sys.stderr)
    if LAST_RESULT.exists():
        try:
            data = json.loads(LAST_RESULT.read_text())
            zip_name = data.get("latest_backtest")
            if zip_name:
                print(f"[WARN] No canonical pointer; falling back to latest: {zip_name}",
                      file=sys.stderr)
                return BACKTEST_DIR / zip_name
        except Exception as e:
            print(f"[ERROR] Cannot parse {LAST_RESULT}: {e}", file=sys.stderr)
    print("[ERROR] No baseline pointer and no last_result. Aborting.", file=sys.stderr)
    sys.exit(1)


def load_strategy_block(zip_path: Path) -> tuple[str, dict]:
    """Open zip, return (strategy_name, strategy_metrics_dict)."""
    if not zip_path.exists():
        print(f"[ERROR] Backtest zip missing: {zip_path}", file=sys.stderr)
        sys.exit(1)
    inner_name = zip_path.stem + ".json"
    with zipfile.ZipFile(zip_path) as zf:
        try:
            raw = zf.read(inner_name)
        except KeyError:
            inner = next((n for n in zf.namelist() if n.endswith(".json")), None)
            if inner is None:
                print(f"[ERROR] No JSON inside {zip_path}", file=sys.stderr)
                sys.exit(1)
            raw = zf.read(inner)
    payload = json.loads(raw)
    strategies = payload.get("strategy") or {}
    if not strategies:
        print(f"[ERROR] No 'strategy' block in {zip_path}", file=sys.stderr)
        sys.exit(1)
    name = next(iter(strategies))
    return name, strategies[name]


def build_equity_curve(daily_profit: list, starting_balance: float) -> list[dict]:
    """Convert daily_profit (list of [date_str, profit_abs]) to equity points.

    Freqtrade emits daily_profit as a list of [iso_date, abs_profit] pairs.
    Each entry already covers a calendar day; cumulative sum gives equity.
    """
    if not daily_profit:
        return []
    running = float(starting_balance)
    out = []
    for entry in daily_profit:
        if isinstance(entry, (list, tuple)) and len(entry) >= 2:
            day, profit = entry[0], entry[1]
        elif isinstance(entry, dict):
            day = entry.get("date") or entry.get("day")
            profit = entry.get("profit_abs") or entry.get("pnl") or 0
        else:
            continue
        try:
            running += float(profit or 0)
        except (TypeError, ValueError):
            pass
        out.append({"day": str(day)[:10], "balance": round(running, 2)})
    return out


def build_pair_breakdown(per_pair: list) -> list[dict]:
    """Slim down results_per_pair to the fields the UI cares about."""
    if not per_pair:
        return []
    out = []
    for p in per_pair:
        if not isinstance(p, dict):
            continue
        if (p.get("key") or "").upper() == "TOTAL":
            continue
        out.append({
            "pair": p.get("key"),
            "trades": p.get("trades", 0),
            "wins": p.get("wins", 0),
            "losses": p.get("losses", 0),
            "winrate_pct": round(100 * (p.get("winrate") or 0), 2),
            "profit_total_pct": round(p.get("profit_total_pct") or 0, 2),
            "profit_total_abs": round(p.get("profit_total_abs") or 0, 2),
            "duration_avg": p.get("duration_avg"),
            "sharpe": round(p.get("sharpe") or 0, 2),
            "profit_factor": round(p.get("profit_factor") or 0, 2),
            "max_drawdown_pct": round(100 * (p.get("max_drawdown_account") or 0), 2),
        })
    out.sort(key=lambda x: x["profit_total_abs"], reverse=True)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Export canonical backtest stats")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print JSON to stdout without writing the file")
    parser.add_argument("--zip", type=str, default=None,
                        help="Override canonical pointer (path to specific zip)")
    args = parser.parse_args()

    zip_path = Path(args.zip) if args.zip else resolve_baseline_zip()
    name, s = load_strategy_block(zip_path)

    total_trades = int(s.get("total_trades") or 0)
    wins = int(s.get("wins") or 0)
    losses = int(s.get("losses") or 0)
    win_rate = round(100 * wins / total_trades, 2) if total_trades else 0.0
    profit_pct = round(100 * (s.get("profit_total") or 0), 2)
    profit_abs = round(s.get("profit_total_abs") or 0, 2)
    final_balance = round(s.get("final_balance") or 0, 2)
    starting_balance = float(s.get("dry_run_wallet") or STARTING_BALANCE)
    max_dd_pct = round(100 * (s.get("max_drawdown_account") or 0), 2)
    max_dd_abs = round(s.get("max_drawdown_abs") or 0, 2)

    equity_curve = build_equity_curve(s.get("daily_profit") or [], starting_balance)
    pair_breakdown = build_pair_breakdown(s.get("results_per_pair") or [])

    stats = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "baseline_file": zip_path.name,
        "strategy_name": name,
        "backtest_start": s.get("backtest_start"),
        "backtest_end": s.get("backtest_end"),
        "backtest_days": int(s.get("backtest_days") or 0),
        "starting_balance": starting_balance,
        "final_balance": final_balance,
        "total_return_pct": profit_pct,
        "total_return_abs": profit_abs,
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,
        "win_rate_pct": win_rate,
        "profit_factor": round(s.get("profit_factor") or 0, 2),
        "expectancy": round(s.get("expectancy") or 0, 4),
        "expectancy_ratio": round(s.get("expectancy_ratio") or 0, 4),
        "sharpe": round(s.get("sharpe") or 0, 2),
        "sortino": round(s.get("sortino") or 0, 2),
        "calmar": round(s.get("calmar") or 0, 2),
        "cagr_pct": round(100 * (s.get("cagr") or 0), 2),
        "max_drawdown_pct": max_dd_pct,
        "max_drawdown_abs": max_dd_abs,
        "max_consecutive_wins": int(s.get("max_consecutive_wins") or 0),
        "max_consecutive_losses": int(s.get("max_consecutive_losses") or 0),
        "best_pair": s.get("best_pair"),
        "worst_pair": s.get("worst_pair"),
        "market_change_pct": round(100 * (s.get("market_change") or 0), 2),
        "equity_curve": equity_curve,
        "pair_breakdown": pair_breakdown,
        "exit_reason_summary": s.get("exit_reason_summary") or [],
    }

    if args.dry_run:
        print(json.dumps(stats, default=str, indent=2)[:2000])
        print(f"... ({len(stats['equity_curve'])} equity points, "
              f"{len(stats['pair_breakdown'])} pairs)")
        return

    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(stats, default=str, indent=2))
    tmp.replace(OUT)
    print(f"OK {OUT}: {name} {profit_pct}% / Sharpe {stats['sharpe']} / "
          f"MaxDD {max_dd_pct}% / {total_trades} trades / "
          f"{stats['backtest_days']}d / equity points {len(equity_curve)}")


if __name__ == "__main__":
    main()
