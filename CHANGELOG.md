# Changelog

All notable changes to the TrendRider trading strategy.

This project follows [Semantic Versioning](https://semver.org/) — strategy version is also embedded in the docstring of `FreqtradeBot/user_data/strategies/TrendRiderStrategy_public.py`.

Format: `Added` / `Changed` / `Fixed` / `Deprecated` / `Removed` / `Backtest` / `Deploy` / `Reverted`.

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
