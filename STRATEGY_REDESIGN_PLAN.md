# Strategy Redesign — Action Plan
**Status:** P1 strategic. Started 2026-05-01. Live bot stays on v2.12.1 ExitFix until redesign passes 480d OOS backtest.

> **Why this exists:** TrendRiderStrategy (1h, trend-following, EMA + RSI + volume) is at a local optimum.
> 11 attempts (5 hyperopt configs + 6 structural mods: LooseCut / ConfSize / MTFGate / ChaseGuard / SHORT / SHORT-Bear) all regressed on the 480d OOS backtest. Live performance ≈ historical (~$10/30d on $1k, +1% monthly).
> No more param tuning or component-level patches — only fundamental redesign.

---

## START HERE — Direction selection (P0, blocks everything else)

We need to pick ONE direction before writing code. Each candidate has a different worldview about where alpha lives. Pick based on which mismatch with the current strategy best explains the regression pattern we keep hitting.

### Direction A — Timeframe shift (15m or 4h)
- **Hypothesis:** 1h is the most-traded timeframe → most efficient → least edge. 15m has more noise but more setups; 4h has less noise and survives longer-duration moves that 1h trailing stops chop out.
- **Evidence for:** April live data shows avg trade duration 9h 42m — already longer than the 1h candle, suggesting we're under-resolving the holding period. Many trades exit early on 1h trailing then move further.
- **Risk:** 15m needs lower stake (more trades, more fees → fee drag dominates on small account). 4h means ~6x fewer signals per pair, so portfolio whitelist must grow to keep trade count reasonable.
- **Effort:** Lowest (1-2 days). Same strategy file, change `timeframe = "4h"` and re-tune ROI/stop/trail to match candle duration.
- **Confidence in success:** Medium-low. Same alpha source, different speed.

### Direction B — Non-trend (mean-reversion)
- **Hypothesis:** Trend-following on the same alts (XRP, DOGE, SOL, NEAR, OP, ETH, ATOM, AVAX, SUI, LINK, POL, BNB, DOT, ADA) is a crowded trade. Mean-reversion (oversold bounce + range-bound bands) trades the same coins with opposite logic, and may catch the $0 PnL months when trend regime is dead.
- **Evidence for:** April win rate 50% with avg duration 9.7h is the signature of a chop-fighting trend strategy. Mean-reversion explicitly profits from chop.
- **Risk:** Mean-reversion has tail-risk asymmetry — wins are small, losses can be catastrophic in trends. Strict max-loss-per-trade is mandatory. Will look bad in obvious bull/bear regimes.
- **Effort:** High (4-7 days). New entry logic (Bollinger + RSI extremes + ATR sizing), new exit logic (target = midline, hard stop on band breach), new whitelist filter (prefer range-bound pairs by ADX < 20).
- **Confidence in success:** Medium. Genuinely different alpha, but harder to size positions and explain to users.

### Direction C — Regime-switched ensemble (current strategy + mean-reversion, gated)
- **Hypothesis:** The two prior approaches are complementary. A regime classifier (e.g., BTC ADX or VIX-equivalent) picks which sub-strategy is active per pair per day.
- **Evidence for:** Live bot's losing months historically cluster in chop weeks (per memory `project_strategy_pivot_2026_03`). A switch could unlock those months without breaking the bull-trend months.
- **Risk:** Two strategies = two surfaces to break. Regime detector itself can mis-classify and pour money into the wrong sub. Backtest validation requires both sub-strategies to pass independently first — meaning C *requires* finishing B first.
- **Effort:** Highest (1.5-2 weeks). Build B → validate B → build regime classifier → integrate ensemble → re-validate full system.
- **Confidence in success:** Medium-high IF B works standalone. Otherwise it just stacks failure modes.

### Recommendation
**Start with A (timeframe shift to 4h)** as a 1-2 day spike. Cheap to test, validates whether the alpha source is even still alive at a different speed. If A passes the 480d OOS gate, ship it. If A fails, B becomes mandatory (2 weeks). C is only worth it if B succeeds — don't plan for C yet.

> **DECISION REQUIRED:** confirm direction (A / B / C / something else) before tasks below activate.

---

## Tasks (activated after direction is picked)

### Phase 1 — Setup (any direction)
- [ ] P0: Create branch `redesign/<direction>` off master
- [ ] P0: Snapshot current 480d backtest as baseline-control (saved JSON in `FreqtradeBot/user_data/backtest_results/baseline_v2.13.0_480d.json`)
- [ ] P0: Define pass/fail gates: must beat baseline on **2 of 3** metrics (Total return, Sharpe, MaxDD) AND not regress >10% on the third.

### Phase 2A — Timeframe shift (if Direction A)
- [ ] P1: Duplicate `TrendRiderStrategy.py` → `TrendRiderStrategy4h.py`
- [ ] P1: Change `timeframe = "4h"`, re-scale ROI table (×4 durations), trailing offset, stoploss
- [ ] P1: Re-download 4h data for whitelist (`freqtrade download-data --timeframes 4h`)
- [ ] P1: Backtest 480d, compare vs baseline, log result
- [ ] P1: If pass — dry-run 7d on Senko (parallel to live v2.12.1, separate config)
- [ ] P1: If 7d dry-run holds — promote to live, archive v2.12.1 as backup

### Phase 2B — Mean-reversion (if Direction B)
- [ ] P1: Create `MeanReversionStrategy.py` skeleton
- [ ] P1: Indicators: Bollinger(20, 2), RSI(14), ATR(14), ADX(14)
- [ ] P1: Entry long: close < BB lower AND RSI < 25 AND ADX < 20
- [ ] P1: Exit: target = BB middle (50% TP), full exit at BB middle OR stop = -1.5×ATR from entry
- [ ] P1: Whitelist filter: only pairs with ADX < 25 in last 7 days
- [ ] P2: Position sizing by ATR (constant USD risk per trade, not constant stake)
- [ ] P1: Backtest 480d, then compare against baseline
- [ ] P1: Walk-forward OOS validation (3 windows of 160d, train→test)
- [ ] P1: 7d Senko dry-run if backtest passes
- [ ] P1: Promote to live if dry-run holds

### Phase 2C — Ensemble (only after B passes)
- [ ] P2: Build regime classifier (BTC 1d ADX > 25 = trend, < 20 = range, between = mixed)
- [ ] P2: Wrap strategies in `EnsembleStrategy.py` with regime gate
- [ ] P2: Backtest 480d ensemble, must beat both subs individually
- [ ] P2: Live promotion path same as A/B

### Phase 3 — Documentation & memory (all directions)
- [ ] P2: Update CHANGELOG.md with v3.0 redesign rationale
- [ ] P2: Refresh /live page copy if metrics shift materially
- [ ] P2: Save LightRAG memory: redesign verdict, kept/discarded ideas, baseline numbers

---

## Hard rules (DO NOT TOUCH)
- ❌ NO param tuning or component patches on `TrendRiderStrategy.py` — feature frozen at v2.12.1.
- ❌ NO live promotion without 480d OOS pass + 7d dry-run.
- ❌ NO stacking sub-strategies (Direction C) until at least one sub independently passes the gate.
- ❌ NO hyperopt as a first-class step. Hyperopt is allowed only AS POST-validation refinement, never as the source of an entry/exit logic decision (per `feedback_strategy_local_optimum` and 5 failed hyperopt attempts in April).

## Execution log
| Date | Task | Outcome | Commit |
|------|------|---------|--------|
| 2026-05-01 | Action plan created | Pending direction confirmation | — |
