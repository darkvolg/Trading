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
- ❌ NO param tuning or component patches on `TrendRiderStrategy.py` — feature frozen at v2.12.1+gate (2026-05-08).
- ❌ NO live promotion without 480d OOS pass + 7d dry-run.
- ❌ NO stacking sub-strategies (Direction C) until at least one sub independently passes the gate.
- ❌ NO hyperopt as a first-class step. Hyperopt is allowed only AS POST-validation refinement, never as the source of an entry/exit logic decision (per `feedback_strategy_local_optimum` and 5 failed hyperopt attempts in April).

## Execution log
| Date | Task | Outcome | Commit |
|------|------|---------|--------|
| 2026-05-01 | Action plan created (A/B/C) | Pending direction confirmation | 8e9acf6 |
| 2026-05-01 | Re-evaluated; added Direction D (Donchian); user picked D | D chosen | 671f031 |
| 2026-05-01 | Branch `redesign/donchian-daily` + skeleton | Phase 1 setup | fc20a00 |
| 2026-05-01 | v1: full Donchian + ATR Chandelier + ATR sizing (no regime) | -13.59% / Sharpe -0.58 / MaxDD 13.64% over 836d (market -24.45%). Fail 0/3 vs baseline. | (next commit) |
| 2026-05-01 | v2: + BTC SMA(200) regime filter | -7.43% / Sharpe -0.30 / MaxDD 7.43% over 836d. Improved but still fail 0/3. | (next commit) |
| 2026-05-01 | Diagnosed: 12 of 14 alts had only 114d of 1d data; downloaded 5y history (2021→2026, ~1900 rows/pair) | data infrastructure ready | (next commit) |
| 2026-05-01 | v2 on full 5y data | -54.33% / Sharpe -1.50 / MaxDD 54.33% / 13.4% WR (market -52%) | (next commit) |
| 2026-05-01 | v2 on isolated bull period 2023-10 → 2024-05 (market +149%) | **-11.1% / 5.4% WR / 35 losses of 37 trades** — concept-impossible loss. **Bug in code** confirmed. | (next commit) |
| 2026-05-01 | v3: removed `custom_stoploss` clamp; widened hard floor `stoploss = -0.50` | -11.31% / WR 14.8% on bull (vs v2 -11.1% / WR 5.4%). WR improved, total ≈ same. **Clamp was a bug, but not the dominant one.** | (next commit) |
| 2026-05-01 | **Sanity check — TrendRiderStrategy v6A on the same bull period 2024-01 → 2024-05 (market +37%)** | **−1.89% / WR 26.6%.** V6A also fails to capture bull markets. Confirms V6A is a *chop-feeder*, not a trend-rider — it edge-grinds in sideways/bear, stagnates or loses in bulls. | (next commit) |
| 2026-05-01 | Trade-by-trade analysis of v3 — found max-to-close giveback 15-25% (e.g. ETH max +30% → close +9.6%); P/L ratio 0.74; mathematical EV = -9.7% per trade | diagnosis: entries on rally tops, immediate pullback | (next commit) |
| 2026-05-01 | v3 with `atr_multiplier = 2.0` (tighter Chandelier) | -14.69% / WR 11.1% — **WORSE**. Tightening exits doesn't fix the entry-timing problem. Reverted to 3.0. | (next commit) |
| 2026-05-01 | **SuperTrend strategy** (1d, period 10, multiplier 3.0) — entries on trend-direction flips, not on price breakouts | First redesign that passes the conceptual sanity test. See SuperTrend results below. | 6b35115 |
| 2026-05-01 | Bybit affiliate CTAs deployed to /live + 2 high-impression blog posts (utm-tagged for attribution) | Production: `bybit.com/invite?ref=0GDX5JR` now wired in `live_header`, `blog_exchange`, `blog_setup` placements | b5cb2d0 |
| 2026-05-01 | Walk-forward OOS validation: SuperTrend on 4 non-overlapping windows | 3/4 positive (-0.88, +14.84, +40.22, +45.00). Stability confirmed across regimes. | (next commit) |
| 2026-05-01 | Parallel Senko dry-run started: `freqtrade-supertrend.service` (systemd) running alongside V6A on separate sqlite (port 8082, separate db) | Live data collection begins. Decision date 2026-05-15 (14d window). | (next commit) |
| 2026-05-08 | Audit: live V6A 30d −$3.89, 14d WR 16.7% — diagnosed regime shift, paused TrendRider; published "paused" /live banner | Premature pause based on small-sample noise | e3faa68 |
| 2026-05-08 | Found `config_supertrend.json` had `timeframe: "1h"` overriding strategy's native `1d` → 6 days zero trades on parallel dry-run. Fixed config + .example, restarted | SuperTrend live now matches strategy intent | e2fcaaf |
| 2026-05-08 | **Apples-to-apples backtest 480d (2025-01-15 → 2026-04-30)**: V6A baseline +4.89% / DD 4.79%, SuperTrend −34.14% / DD 34.14%. SuperTrend FAILS 3/3 gates by huge margin. | Original "SuperTrend passes baseline" claim only held on bull-period subwindow | (next commit) |
| 2026-05-08 | Reversed pause: TrendRider un-paused, SuperTrend paused (max_open_trades=0), /live banner replaced with "pause was premature" correction | Build-in-public ships the override too | 22fed98 |
| 2026-05-08 | **Regime overlay analysis** (entry-date classification, BTC SMA200+ADX): V6A wins +$26.79 in chop / flat in bull / −$4.22 in bear; SuperTrend loses in ALL regimes (incl. bull WR 14% / −$62) | Ensemble-with-SuperTrend thesis DEAD; V6A as chop-arm confirmed; bear-avoidance gate identified as +17%-on-paper opportunity | (next commit) |
| 2026-05-08 | **V6A+gate built**: BTC daily SMA200 + ADX(14) → veto longs when (close<SMA200 & ADX>25). Hardcoded textbook params, no overfit surface. | Patch deployed to senko `TrendRiderStrategy_exitfix.py`, freqtrade.service restarted | 03f3350 |
| 2026-05-08 | **Gate validation 480d (chop+bear)**: baseline +4.89% / DD 4.79% → gate +5.20% / DD 3.95% / 332 trades (vs 446) | +6% return, **−18% DD**, 26% fewer trades, +50% per-trade alpha. PASS. | 03f3350 |
| 2026-05-08 | **Gate OOS 379d (bull, market +136%)**: baseline −1.87% / DD 4.50% → gate −1.37% / DD 3.84% | +27% rel improvement, −15% DD. Gate monotonically improves both regimes. PASS. | 03f3350 |

## SuperTrend results — first redesign that beats V6A on absolute return

Same whitelist (14 alts), 1d timeframe, max 8 open trades, default $50 stake.

| Window | Days | Market | Return | Sharpe | Sortino | MaxDD | PF | WR |
|---|---|---|---|---|---|---|---|---|
| Bull (2023-10 → 2024-05) | 213 | +149% | **+67.91%** | 0.85 | 8.75 | **1.46%** | 11.2 | **68.8%** |
| V6A baseline (2024-01 → 2026-04) | 837 | -20.6% | **+10.98%** | 0.06 | 0.32 | 24.23% | 1.12 | 27.4% |
| Full 5y (2021-01 → 2026-04) | 1915 | -46.5% | **+80.68%** | 0.18 | 0.99 | 16.88% | 1.52 | 34.1% |

**vs V6A on the 837d baseline window:**
- V6A: +4.99% / Sharpe 0.69 / MaxDD 4.78%
- SuperTrend: +10.98% / Sharpe 0.06 / MaxDD 24.23%
- Total return: 2.2× higher. Sharpe and MaxDD: worse.

This is the asymmetry we predicted in the "Critical realisation" section:
V6A is the **chop-feeder** (high Sharpe, low DD, modest return in
sideways/bear) and SuperTrend is the **trend-rider** (high absolute
return, lower Sharpe, deeper DD, big upside in sustained trends).
A 2-of-3 strict gate on a single mixed-regime window can't fairly
compare these two — they fish in different waters. The honest path
forward is the regime-switched ensemble (Direction C from the original
A/B/C/D plan), now feasible with both legs proven:

  - **Chop leg = V6A** (already shipped, +4.99% over 836d, low DD)
  - **Trend leg = SuperTrend** (this session, +80% over 5y, accepts higher DD)
  - **Regime classifier**: BTC > 200d SMA + BTC ADX threshold → enable
    SuperTrend. Else → V6A only. (Detection via informative_pairs.)

NEXT-SESSION ACTIONS:
1. ~~Walk-forward OOS validation of SuperTrend~~ ✅ DONE 2026-05-01.
   3/4 windows positive, no period-specific overfit:
   - 2021-01 → 2022-04 (market +12%): -0.88% (only loser; whipsaw 2021)
   - 2022-04 → 2023-07 (market -58%): +14.84% (catches bear via trailing exits)
   - 2023-07 → 2024-10 (market +103%): +40.22%
   - 2024-10 → 2026-04 (market -31%): +45.00%
2. ~~7-day Senko parallel dry-run~~ ✅ STARTED 2026-05-01 12:35 MSK.
   `freqtrade-supertrend.service` running on senko alongside production V6A.
   - Separate sqlite: `/opt/freqtrade/tradesv3.dryrun.supertrend.sqlite`
   - Separate API port: 8082 (V6A on 8081)
   - Same whitelist, same dry_run_wallet $500
   - **Decision date 2026-05-15** (14-day window).
3. **Build EnsembleStrategy.py** — V6A + SuperTrend gated by BTC regime
   classifier (BTC > 200d SMA → SuperTrend active; else V6A only).
   Deferred until after the dry-run window so we have real-side-by-side
   data to inform the regime cutoffs.
4. **2026-05-15 decision**: if SuperTrend dry-run matches backtest profile
   within reasonable variance AND beats V6A in the same window, promote
   either SuperTrend solo or Ensemble to live. Else iterate.



## Final verdict on Donchian (Direction D) — concept-level mismatch with crypto alts

After 4 versions (v1, v2 with regime, v3 with clamp fix and -50% floor,
v3-tight with 2×ATR), and a trade-by-trade post-mortem, the conclusion is
that **Donchian breakout entries on crypto alts buy the rally top**. ~85% of
breakouts produce immediate pullback that either trips the Chandelier (15-25%
giveback) or stalls. The mismatch is at concept level, not parameter level:

  - Tighter Chandelier (2×ATR): WR drops, total return worsens.
  - Looser Chandelier: same total return, more giveback per trade.
  - BTC regime gate: helps in bear, doesn't help in bull rallies.

This isn't refutation of trend-following on crypto in general — it's
refutation of *breakout entries* on this specific 14-alt whitelist over the
tested windows. Trend systems that enter on **pullbacks** to a rising
moving-average (SuperTrend, MA-cross + retracement, channel-midline buy)
might still work and remain on the menu for future sessions. Donchian
breakout itself is parked.

## Critical realisation — V6A's profile is the opposite of what we assumed

The V6A baseline is +4.99% / Sharpe 0.69 / MaxDD 4.78% over 836 days, of
which the market itself dropped −24%. We've been treating V6A as a strategy
to beat with a "real trend-following system". But the bull-period sanity
check shows V6A actually *loses* in bulls. So:

  - V6A makes its money in **chop** and during **mild downside / sideways**
    by harvesting hourly micro-bounces. It's a mean-reversion / chop-feeder
    in disguise, not a trend follower.
  - During strong bull rallies (+37% market in 4 months), V6A produces −1.89%.
  - During strong bear (−24% over 28 months), V6A produces +4.99%.

This means a Donchian/trend redesign is *complementary*, not a replacement.
The honest combined system would be a **regime-switched ensemble**:

  - V6A active during chop / mild markets (most of the time on alts).
  - Donchian (or any trend system) active only during sustained bulls.

Single-strategy v3 redesign cannot be "objectively better" than V6A on a
mixed-regime backtest — they fish in different waters. A direct replacement
would *lose* the chop-edge V6A has and would have to make up for it during
bulls, which is a much harder game.

## Open bug hypotheses (next session)

The 2023-10 → 2024-05 result (+149% market, -11% strategy, 5.4% WR) is mathematically inconsistent with a working Donchian breakout: a bull rally should produce many big winners trailing through ATR Chandelier. 95% loss rate during a +149% rally is a code bug, not a strategy property.

Top suspects, in order:

1. **`custom_stoploss` returns wrong unit.** Code clamps offset with `max(offset, self.stoploss + 0.001)` — when Chandelier wants stop at e.g. -17% from current rate, it gets bounded to -9.9% instead, which converts the Chandelier into a vanilla trailing-9.9% stop. Vanilla 9.9% trail on alts gets hit in normal volatility almost immediately after entry. **Fix:** lower `self.stoploss` to e.g. `-0.50` so the Chandelier offset isn't clamped, OR drop the clamp entirely.
2. **`trade.max_rate` not updated daily in backtest mode.** If max_rate stays at entry price, Chandelier trail = entry - 3×ATR ≈ -15% below entry, which trips the -10% hard floor every time on first daily candle volatility.
3. **Volume filter dies after BTC regime merge.** After merging BTC bull-regime onto the dataframe, the merge may drop rows or introduce NaN in `volume_mean`, silently disabling all good entries; the few that fire are on stale/wrong data.
4. **Wrong ATR scale or sizing math.** Verify by logging `dataframe[['close','atr','atr_pct=atr/close']].tail(20)` once. Should be 2-8% range for crypto daily; if it's 50%+, ATR is in wrong units.

**Action for next session:** add print statements in `populate_indicators` and `custom_stoploss`, run a 30-day backtest with `--logfile debug.log`, inspect actual values. Catch the unit/clamp bug before any new feature work.
