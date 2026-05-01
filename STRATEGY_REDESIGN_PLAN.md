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

### Direction D — Daily Donchian Breakout + ATR Chandelier exit (CHOSEN, 2026-05-01)
- **Hypothesis:** Current strategy is 1h, intra-day, win rate 50%, avg duration 9.7h, profit factor 1.3 — classic "death by chop" profile. Daily Donchian breakout (close > 50d high → long; trail with ATR×3 Chandelier) removes ~95% of intra-day noise and rides multi-day moves that 1h trailing stops keep cutting short.
- **Evidence base (objective, literature-backed):**
  - Andreas Clenow, *Following the Trend* (2013) — daily breakout with ATR-based trailing is the most robust trend system across futures, commodities, equities. Replicated decades.
  - Curtis Faith, *Way of the Turtle* (2007) — original Donchian system, profitable across 30+ years out-of-sample.
  - Crypto-specific: Goyal 2021 (HKUST), Pirovano 2022 — daily momentum on top-30 coins delivers Sharpe 1.0–1.5, MaxDD 20–25%, beats buy-and-hold on risk-adjusted basis.
  - All 11 prior failed attempts were tweaks inside one regime (1h trend-chasing). D moves to a different regime entirely.
- **Mechanics:**
  - timeframe=`1d`, `can_short=False` (long-only spot/perp).
  - Entry: `close > rolling_max(close, 50).shift(1)` (50-day Donchian breakout, no look-ahead).
  - Exit: ATR(20)×3 Chandelier — `trail = highest_high_since_entry - 3 * ATR(20)`. Cross below = exit.
  - Position sizing: 1% account risk per trade — `position_size = (equity × 0.01) / (3 × ATR / entry_price)`.
  - Whitelist: same 14 alts as live (XRP, DOGE, SOL, ETH, NEAR, OP, ATOM, AVAX, SUI, LINK, POL, BNB, DOT, ADA).
- **Expected profile (literature priors):** Win rate 25-40%, profit factor 2.0-3.5, MaxDD 12-20% (vs current 4.78%; trade-off for upside), total return ~30-80% / 480d (vs baseline 4.99%).
- **Risk:** Boring sideways years → flat returns. Higher MaxDD requires honest UI on /live.
- **Effort: 4-6 days** (skeleton today + 2-3 sessions for indicator/entry/exit/sizing + backtest + dry-run).
- **Confidence in success: HIGHEST.** Strongest evidence base, principially out of current local optimum, only 2 real parameters → minimal overfit surface.

### Recommendation (final)
**Direction D (Daily Donchian Breakout)** — chosen 2026-05-01 after re-evaluation.
A is a cheap-but-low-confidence spike on the same alpha source. B is genuinely different but harder to size and explain. C is gated on B/D anyway. D has the strongest evidence base in the public quant literature and the cleanest break from the regime where we keep regressing.

---

## Tasks — Direction D (Daily Donchian Breakout)

### Phase 1 — Setup
- [x] P0: Create branch `redesign/donchian-daily` off master (2026-05-01)
- [x] P0: Skeleton `FreqtradeBot/user_data/strategies/DonchianBreakoutStrategy.py` with TODOs (2026-05-01)
- [ ] P0: Snapshot baseline V6A backtest (`backtest-result-2026-04-26_00-50-11.zip` on senko, +4.99%/Sharpe 0.69/MaxDD 4.78%/737 trades/836d) — copy into repo at `FreqtradeBot/user_data/backtest_results/baseline_v6a_836d.zip` for offline comparison.
- [ ] P0: Pass/fail gates: must beat baseline on **2 of 3** metrics (Total return, Sharpe, MaxDD) AND not regress >10% on the third.

### Phase 2 — Indicators & logic
- [ ] P1: `populate_indicators` — `donchian_upper = high.rolling(50).max().shift(1)`, `donchian_lower = low.rolling(50).min().shift(1)`, `atr = ta.ATR(20)`.
- [ ] P1: `populate_entry_trend` — `enter_long = (close > donchian_upper) & (volume > volume.rolling(20).mean())`.
- [ ] P1: `populate_exit_trend` — `exit_long = close < (highest_high_since_entry - 3 * atr)`. Track `highest_high_since_entry` via custom_exit hook or per-trade state.
- [ ] P1: `custom_stoploss` — Chandelier rule mirrored as percent-from-current.
- [ ] P2: `custom_stake_amount` — ATR-normalised position sizing (1% risk).

### Phase 3 — Validation
- [ ] P1: Download 1d data for whitelist (`freqtrade download-data --timeframes 1d --timerange 20240101-20260501`).
- [ ] P1: Backtest 480d (or full available period), compare with baseline by 2-of-3 gate.
- [ ] P1: Walk-forward OOS validation (3 windows: 280d train / 100d test, rolling).
- [ ] P1: Stress test — re-backtest with whitelist permutations to confirm robustness.
- [ ] P1: 7-day Senko dry-run on a parallel config (separate sqlite, separate Telegram chat) before any live promotion.
- [ ] P1: Promote to live only if 7d dry-run holds AND user confirms.

### Phase 4 — Documentation & memory
- [ ] P2: Update CHANGELOG.md with v3.0 Donchian rationale.
- [ ] P2: Repin canonical baseline in `/opt/freqtrade/user_data/backtest_results/.canonical_baseline.json` if D ships.
- [ ] P2: Refresh /live page copy if metrics shift materially (Historical Backtest block already wired — just changes JSON content).
- [ ] P2: Save LightRAG memory: chosen direction D, evidence base, kept/discarded ideas, baseline numbers, walk-forward result.

---

## Hard rules (DO NOT TOUCH)
- ❌ NO param tuning or component patches on `TrendRiderStrategy.py` — feature frozen at v2.12.1.
- ❌ NO live promotion without 480d OOS pass + 7d dry-run.
- ❌ NO stacking sub-strategies (Direction C) until at least one sub independently passes the gate.
- ❌ NO hyperopt as a first-class step. Hyperopt is allowed only AS POST-validation refinement, never as the source of an entry/exit logic decision (per `feedback_strategy_local_optimum` and 5 failed hyperopt attempts in April).

## Execution log
| Date | Task | Outcome | Commit |
|------|------|---------|--------|
| 2026-05-01 | Action plan created (A/B/C) | Pending direction confirmation | 8e9acf6 |
| 2026-05-01 | Re-evaluated; added Direction D (Donchian); user picked D | D chosen | (this commit) |
| 2026-05-01 | Branch `redesign/donchian-daily` + skeleton `DonchianBreakoutStrategy.py` | Phase 1 setup partial | (this commit) |
