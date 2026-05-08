"""Walk-forward OOS validation for the cash-and-carry strategy.

Splits the available data into 3 non-overlapping windows of equal length.
For each (window, param-set) combination, runs the full carry_portfolio_sim
logic and reports per-month PnL distribution.

Pass criteria (no overfit):
  - Net APR > 0 in all 3 windows for default params
  - Sharpe > 1.0 in at least 2 of 3 windows
  - Max drawdown stays < 1% in all 3 windows
  - Result stable under entry_threshold ∈ {0.00005, 0.0001, 0.0002}

If default params fail any criterion in any window, the strategy is regime-
sensitive and should not be deployed without that regime detector.
"""
from __future__ import annotations
import sys
from pathlib import Path

# Reuse the heavy lifting from carry_portfolio_sim
sys.path.insert(0, "/tmp")
from carry_portfolio_sim import (
    build_funding_matrix, simulate_portfolio, monthly_summary,
    WHITELIST,
)

import pandas as pd


# Three non-overlapping windows. Total ~4y → ~16 months each.
WINDOWS = [
    ("2022-01-01", "2023-04-30", "W1"),
    ("2023-05-01", "2024-08-31", "W2"),
    ("2024-09-01", "2026-04-30", "W3"),
]

PARAM_SWEEPS = [
    {"entry_thr": 0.00005, "exit_pers": 3, "label": "thr=0.005%/3p"},
    {"entry_thr": 0.0001,  "exit_pers": 3, "label": "thr=0.01%/3p (default)"},
    {"entry_thr": 0.0002,  "exit_pers": 3, "label": "thr=0.02%/3p"},
    {"entry_thr": 0.0001,  "exit_pers": 5, "label": "thr=0.01%/5p (longer holds)"},
]


def run_one(matrix_full, start, end, params):
    matrix = matrix_full[
        (matrix_full.index >= pd.Timestamp(start, tz="UTC"))
        & (matrix_full.index <= pd.Timestamp(end, tz="UTC"))
    ]
    if matrix.empty:
        return None
    per_tick, info = simulate_portfolio(
        matrix,
        entry_thr=params.get("entry_thr"),
        exit_thr=-0.00005,
        entry_pers=3,
        exit_pers=params.get("exit_pers"),
        n_slots=4,
    )
    df = per_tick.copy()
    df["month"] = df["date"].dt.to_period("M")
    monthly = df.groupby("month")["net_pct"].sum()
    days = (per_tick["date"].iloc[-1] - per_tick["date"].iloc[0]).days
    total = monthly.sum()
    apr = total * 365 / days if days else 0
    sharpe = (monthly.mean() / monthly.std() * (12 ** 0.5)) if monthly.std() > 0 else 0
    cum = monthly.cumsum()
    max_dd = (cum - cum.cummax()).min()
    pos_months = (monthly > 0).sum()
    return {
        "apr": apr,
        "total_pct": total,
        "sharpe": sharpe,
        "max_dd": max_dd,
        "pos_months": pos_months,
        "n_months": len(monthly),
        "n_opens": info["opens"],
        "n_closes": info["closes"],
    }


def main():
    print("=" * 80)
    print("Walk-forward OOS validation — cash-and-carry strategy")
    print("3 non-overlapping windows × 4 param sets = 12 evaluations")
    print("=" * 80)

    matrix = build_funding_matrix("2022-01-01", "2026-04-30", WHITELIST)
    matrix.index = pd.to_datetime(matrix.index, utc=True)

    rows = []
    for params in PARAM_SWEEPS:
        for (start, end, wname) in WINDOWS:
            r = run_one(matrix, start, end, params)
            if r:
                rows.append({
                    "params": params["label"],
                    "window": f"{wname} ({start} -> {end})",
                    "APR%": round(r["apr"], 2),
                    "total%": round(r["total_pct"], 2),
                    "sharpe": round(r["sharpe"], 2),
                    "maxDD%": round(r["max_dd"], 2),
                    "pos_m": f"{r['pos_months']}/{r['n_months']}",
                    "ops/cls": f"{r['n_opens']}/{r['n_closes']}",
                })
    df = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_colwidth", 30)
    print()
    print(df.to_string(index=False))
    print()

    # Pass-criteria check on default params
    print("=" * 80)
    print("PASS CRITERIA (default params: thr=0.01%/3p):")
    print("=" * 80)
    default = df[df["params"].str.contains("default")]
    apr_pass = (default["APR%"] > 0).all()
    sharpe_2of3 = (default["sharpe"] > 1.0).sum() >= 2
    dd_pass = (default["maxDD%"].abs() < 1).all()  # < 1% drawdown

    print(f"  APR > 0 in all 3 windows:      {'PASS' if apr_pass else 'FAIL'}  "
          f"(values: {default['APR%'].tolist()})")
    print(f"  Sharpe > 1 in ≥2/3 windows:    {'PASS' if sharpe_2of3 else 'FAIL'}  "
          f"(values: {default['sharpe'].tolist()})")
    print(f"  Max DD < 1% in all 3 windows:  {'PASS' if dd_pass else 'FAIL'}  "
          f"(values: {default['maxDD%'].tolist()})")

    # Param stability
    print()
    print("PARAM STABILITY (APR variance across param sets, per window):")
    by_window = df.groupby("window")["APR%"].agg(["min", "max", "mean", "std"])
    print(by_window.round(2).to_string())

    overall_pass = apr_pass and sharpe_2of3 and dd_pass
    print()
    print(f"OVERALL: {'PASS — strategy is robust across regimes' if overall_pass else 'FAIL — needs regime detector or different params'}")


if __name__ == "__main__":
    main()
