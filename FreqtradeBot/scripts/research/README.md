# Research scripts

Spike scripts for strategy research. Run on Senko (where data lives):

```bash
ssh senko
source /opt/freqtrade/venv/bin/activate
scp <local>/funding_spike.py senko:/tmp/
python3 /tmp/funding_spike.py
```

## `regime_overlay.py`
Classifies BTC daily candles as bull/chop/bear (SMA200 + ADX(14)) and
overlays trade history (V6A live DB + V6A backtest + SuperTrend backtest)
to compute per-regime PnL. Used 2026-05-08 to validate the bear-avoidance
gate hypothesis and to kill the SuperTrend ensemble thesis.

Key output (480d, entry-date classification):
- V6A: chop +$26.79, bull +$1.87, bear −$4.22 → 100% alpha from chop
- SuperTrend: loses in ALL regimes including bull (WR 14% in bull)

## `carry_backtest.py`
Realistic delta-neutral cash-and-carry backtest with full Bybit fee/slippage
modelling (0.42%/cycle: spot 0.2% + perp 0.12% + slippage 0.10%). Models
entry/exit by funding-rate persistence and reports per-pair + portfolio APR.

Key output (full 4y, default params):
- 15/15 pairs net positive after fees
- Per-pair median net APR: ~3.7%
- Avg hold: ~130 days

NOTE: The "portfolio APR with 8-slot cap = ~7%" figure from this script's
last `print` block uses a sum/N_SLOTS approximation that overstates actual
portfolio return when concurrent positions are sparse. Use `carry_portfolio_sim.py`
for honest portfolio-level numbers.

## `walk_forward_carry.py`
Walk-forward OOS validation. Splits 4y data into 3 non-overlapping windows
(W1 2022-01→2023-04, W2 2023-05→2024-08, W3 2024-09→2026-04) and runs
carry_portfolio_sim on each with 4 param combos. Reports per-window APR,
Sharpe, MaxDD; checks pass criteria.

Verdict 2026-05-08 (default thr=0.01%/3p):
- W1 +2.20% APR / Sharpe 2.39 / DD -0.05%
- W2 +10.32% APR / Sharpe 2.53 / DD -0.07%
- W3 +2.21% APR / Sharpe 1.32 / DD -0.23%
ALL 3 windows: positive APR, Sharpe>1, DD<1%. PASS — strategy regime-robust.

## `flash_crash_stress.py`
Synthetic price-shock test. Verifies delta-neutral PnL holds across 11
stress scenarios incl. 50% crash + forced close at the low + 2x leverage
variants.

Verdict 2026-05-08: 11/11 PASS. Worst case (50% crash, 1x lev, forced
close at low): +$0.37 net (funding accrued covers close fees). Even with
2x leverage on perp leg + 40% crash forced close: +$0.34 net. Math holds.

## `carry_portfolio_sim.py`
Proper portfolio simulator: at every 8h tick picks top-K candidates by
recent funding signal, holds while persistence rules pass, tracks per-month
PnL distribution.

Honest output (full 4y, N_SLOTS=4):
- Total net 21.24% / **APR 4.91%**
- 26/52 positive months (50%)
- Best month +4.14%, **worst month −0.18%** (extraordinary downside protection)
- Sharpe (annualized from monthly returns): **1.81**
- Max drawdown over the 4-year run: −0.23%
- Avg concurrent positions: 1.5/4 — strategy is funding-supply-bound, not capital-bound

APR is roughly invariant to slot count (4.7% at 8 slots, 5.3% at 2 slots) —
the constraint is how many alts pay positive funding simultaneously, not
how much capital we deploy.

Stacking with V6A+gate (deployment math, NOT additive percentages):
- 50/50 same-capital split, no leverage: 5% APR / 2% DD / Sharpe 1.1
- 50/50 with 2x leverage on CnC perp leg: ~10% APR / ~4% DD / Sharpe 1.0+
  → double return at same risk = the actual breakthrough configuration.

## `funding_spike.py`
Bybit perp funding-rate carry analysis across 3 windows (bear 480d, bull
379d, full 4y+). Tests three crude strategies: passive-long, direction-
follow (always on the receiving side, 8h flips), extreme-short
(funding>0.05%/8h). Ran 2026-05-08 to decide whether to invest 4-6 weeks
in a delta-neutral cash-and-carry strategy.

Key finding: funding-only component (the actual carry alpha, not price
PnL) is **+9% to +15% APR robustly across all 3 regime windows**. Real
edge. But realising it requires delta-neutral spot+perp infrastructure,
not perp-only flips (which fee-suicide).
