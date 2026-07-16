# Changelog

All notable changes to the TrendRider trading strategy.

This project follows [Semantic Versioning](https://semver.org/) — strategy version is also embedded in the docstring of `FreqtradeBot/user_data/strategies/TrendRiderStrategy_public.py`.

Format: `Added` / `Changed` / `Fixed` / `Deprecated` / `Removed` / `Backtest` / `Deploy` / `Reverted`.

---

## [v2.16.0] — 2026-07-16

### Changed
- **Bear-gate ADX threshold 25 → 18.** The gate blocks long entries when BTC daily
  `close < SMA200 AND ADX > threshold`. At 25 it only caught *strong* bear trends and
  let the bot trade weak-trend chop below SMA200 — exactly where live lost money after
  the gate reopened on Jul 13 (9 trades, 11% WR, −$2.44). Lowering to 18 keeps the bot
  out of that chop.

### Backtest (2026-01-01 → 2026-07-16, fresh data)
| Gate | Trades | Profit | PF | MaxDD |
|---|---|---|---|---|
| ADX>25 (old) | 143 | +$24.49 (4.90%) | 1.67 | 1.53% |
| **ADX>18 (new)** | **56** | **+$24.12 (4.82%)** | **4.11** | **0.32%** |
| ADX>20 | 74 | +$19.91 | 2.35 | 1.18% |
| ADX>15 | 29 | +$19.11 | 10.71 | 0.22% |

ADX>18 keeps 98% of the profit while cutting trade count in half, lifting profit factor
1.67→4.11 and dropping max drawdown 1.53%→0.32%. July-chop sub-test: old gate −$0.85
(PF 0.54), ADX>18 makes **0 trades** (sits out). This is a risk-gate widening, not
entry-parameter tuning — profit is flat, quality/drawdown improve.

### Deploy
- Senko, restart verified: resolver loads `TrendRiderStrategy_exitfix.py`, new PID clean,
  gate now logs `BTC<SMA200 & ADX>18`. Backup: `.bak_adx18_*`.
- Mode: dry-run, 1h timeframe, 13 USDT-perp pairs.

---

## [v2.15.0] — 2026-07-06

### Fixed
- **CRITICAL: bear-avoidance gate never loaded in live.** `TrendRiderStrategy_public.py`
  defined the same class name `TrendRiderStrategy` as the gated strategy file, and
  freqtrade's resolver loaded the ungated copy. The gate (deployed 2026-05-08) never
  ran: 64 long entries opened during confirmed BTC bear regime (Jun 3 – Jul 6),
  −$10.40 avoidable loss. Public copy's class renamed to `TrendRiderStrategyPublic`.
- Gate is no longer silent: logs `Bear gate VETO {pair}` on every blocked entry and
  warns when BTC 1d data is missing (previously a silent no-op — root cause of the
  bug going unnoticed for 2 months).
- `export_live_stats.py` now reads the strategy version from the running strategy file.

### Why
Live WR collapsed 50% → 17% (Apr → Jul) while BTC fell −25% from the May top.
Diagnosis showed the long-only bot was entering bull traps through the entire bear
leg with the regime gate inactive.

### Backtest
- 2026-01-01 → 2026-07-07 (through the bear market), AND-gate (close<SMA200 & ADX>25):
  139 trades, +$25.34 (+5.07%), PF 1.73, Sortino 5.98, max underwater 1.53%.
- SMA200-only gate variant rejected: 0 trades in 6 months (BTC below SMA200 all year —
  blocks the profitable April window too).

### Deploy
- Senko, restart verified: `Using resolved strategy TrendRiderStrategy from
  '.../TrendRiderStrategy_exitfix.py'`; gate vetoed BTC/ETH/DOGE longs on first tick.
- Mode: dry-run, 1h timeframe, 13 USDT-perp pairs.

### Lesson
Freqtrade resolves strategies by **class name** scanning every `.py` in `strategies/` —
two files with the same class = roulette. After every deploy, verify:
`journalctl -u freqtrade | grep "Using resolved strategy"`. Risk features must log
their own activation.

---

## [v2.14.0] — 2026-05-20

### Added
- **carry_bot** (funding-carry, delta-neutral): P0 safety gates before any live capital —
  capital-aware position sizing (was hardcoded $100), idempotent open, explicit
  `--confirm-mainnet` gate, log dedup. 42/42 tests pass.

### Deploy
- Senko, Bybit testnet. Verified clean tick; mainnet gates refusing without the flag.

---

## [v2.12.1] — 2026-04-27

### Fixed
- **ExitFix**: closed 16h-24h cascade gap in `custom_exit()`. Added two new cuts:
  - `early_loss_cut_19h`: cut if `current_profit < 0` after 19h
  - `early_loss_cut_22h`: cut if `current_profit < -0.01` after 22h

### Why
Live data (25d, 101 trades) showed 9 trades hit `time_exit_24h` at avg -2.92%, total -$13.01 — equal to total bot profit ($11.86) over same period. The existing 16h check at "profit < +1%" let through trades that were profitable at 16h then drifted negative before 24h hard timeout.

### Backtest
- 480d (2024-01-09 → 2026-04-25): identical to V6A baseline
  - Profit: +$24.93 (+4.99%)
  - Sharpe 0.69, Sortino 1.24, MaxDD 4.78%, 737 trades
- No trades reached 16h+ in historical data (all caught by earlier 2h/4h/8h cuts) — fix is **neutral on history, addresses live-only pattern**.

### Deploy
- Senko (`/opt/freqtrade/user_data/strategies/TrendRiderStrategy_public.py`)
- Backup: `.bak_v2120_pre_exitfix_1777278459`
- Mode: dry-run (paper trading), 1h timeframe, 13 USDT-perp pairs
- Bot state at deploy: $511.86 (+$11.86 / +2.37% over 27d), 52.48% WR, PF 1.38

### Monitoring window
30 days, decision date **2026-05-27**.

| Success | Failure |
|---|---|
| `time_exit_24h` hits ≤ 2 (was 9) | `time_exit_24h` hits ≥ 8 |
| Total profit > $25 | Total profit < $11.86 |
| MaxDD < 5% | New 19h/22h cuts kill winners |

### Revert
```bash
ssh senko "cp /opt/freqtrade/user_data/strategies/TrendRiderStrategy_public.py.bak_v2120_pre_exitfix_1777278459 /opt/freqtrade/user_data/strategies/TrendRiderStrategy_public.py && systemctl restart freqtrade"
```

---

## [v2.13.0] — 2026-04-24 → reverted 2026-04-25

### Changed
- Hyperopt-tuned (500 epochs, Sharpe loss, 5 spaces) on 110d data
- ROI thresholds effectively disabled (`{0: 0.34, ...}`), exits via custom_exit + tight stoploss `-0.038`
- Trailing tight (`positive 0.299, offset 0.324`)

### Backtest
- 110d in-sample: +$15.95 vs v2.12.0, validated on both halves of split
- **OOS test (11d hold-out)**: -0.54% / 23.8% WR — failed validation gates

### Reverted
2026-04-25 evening: rolled back to v2.12.0 V6A. Classic overfit signature confirmed: positive in-sample → negative OOS. This kicked off the overnight verification of 4 more hyperopt configs (A/B.1/B.2/B.3/C) — all also failed OOS, leading to the verdict that **hyperopt-parameterization is structurally broken for this strategy**. See `memory/project_session_2026_04_25_evening_v3.md`.

---

## [v2.12.0] — 2026-04-24 (V6A — current production baseline)

### Added
- ROI ladder tuned for 1h crypto realities: `{0: 6%, 60: 3.5%, 240: 2%, 480: 1%, 720: 0}`
  - V4-era ROI (22.9% immediate) was practically unreachable on 1h timeframe — trades peaked below ROI then drifted into loss
- Wide stoploss `-0.06` (6%) — crypto swings 2-4%/hour, tight stops bleed
- Trailing wide: 3% trail activated after +5%
- Cascading early-exit `custom_exit()`:
  - 2h: cut if -1.5%
  - 4h: cut if `< 0`
  - 8h: cut if `< +0.5%`
  - 16h: cut if `< +1%`
  - 24h: hard timeout

### Backtest
- 110d: +55% PnL vs v2.11.0
- 480d (D test, 2024-01-09 → 2026-04-25): +$24.93 (+4.99%), Sharpe 0.69, Sortino 1.24, MaxDD 4.78%, 737 trades, CAGR 2.15% — **stable baseline**

### Deploy
- 2026-04-24, replaces V6
- Production paper-trading, dry-run mode
- Active until v2.12.1 deployed 2026-04-27

---

## Versioning policy

- **Major** (`v3.0.0`): breaking architecture change (e.g., 1h → 4h timeframe, single → multi-strategy ensemble, long-only → long+short)
- **Minor** (`v2.13.0`): new feature, parameter set, or hyperopt result deployed to live
- **Patch** (`v2.12.1`): structural fix, bug fix, or guard-rail addition with neutral backtest

## Discipline gates (all changes)

1. Implement in copy file, not in active strategy
2. Backtest on 480d full history — must not degrade PnL or DD by > 1pp
3. Walk-forward on 2 OOS windows (when applicable)
4. Deploy → tag → release
5. Minimum 30-day live monitoring before next iteration
6. Backup created before deploy, single-command revert documented

**Cannot do:** deploy without backtest; deploy if DD worsens by > 1pp; react to <30d live data.
