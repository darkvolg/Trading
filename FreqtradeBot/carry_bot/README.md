# carry_bot — operations guide

Delta-neutral cash-and-carry on Bybit USDT perp+spot. Long spot + short
perp same notional → directional risk cancels, position earns funding from
short perp leg whenever funding rate is positive.

Validated economics: ~5% APR / Sharpe 1.81 / max-DD −0.23% across 4y of
historical data (see `FreqtradeBot/scripts/research/carry_portfolio_sim.py`).
With 2x leverage on the perp leg the same edge yields ~10% APR at ~4% DD —
the breakthrough configuration when stacked alongside V6A.

## Layout

```
carry_bot/
├── config.py          CarryConfig + from_env() loader
├── exchange.py        BybitClient: ccxt wrapper, atomic spot+perp ops
├── funding_signal.py  PairSignal + SignalBook (persistence rules)
├── positions.py       SQLite-backed PositionStore
├── risk.py            RiskGate: kill switch, stale close, liq monitor
├── scheduler.py       8h tick driver + rebalance + reconcile
├── main.py            CLI entrypoint
└── tests/             36 unit tests (no network deps)
```

## Run modes

```bash
# Single-tick run (cron-driven)
python -m carry_bot.main --once

# Long-running loop (sleeps to next funding tick)
python -m carry_bot.main --loop

# Decision-only — observe signals, never place orders (testnet shake-down)
python -m carry_bot.main --once --signals-only

# Force testnet (overrides CARRY_TESTNET env)
python -m carry_bot.main --once --testnet

# Verbose: print HTTP-level ccxt traces
python -m carry_bot.main --once -v
```

## Environment

All env vars optional; from_env() falls back to safe defaults.

| Variable | Default | Notes |
|---|---|---|
| `CARRY_API_KEY` | `""` | Bybit sub-account key |
| `CARRY_API_SECRET` | `""` | Bybit sub-account secret |
| `CARRY_TESTNET` | `true` | flip to `false` only after live-deploy decision |
| `CARRY_N_SLOTS` | `4` | concurrent position cap |
| `CARRY_ENTRY_THRESHOLD` | `0.0001` | 0.01%/8h ≈ 11% APR equivalent |
| `CARRY_EXIT_THRESHOLD` | `-0.00005` | exit when funding ≤ this |
| `CARRY_PERP_LEVERAGE` | `1` | start at 1x; 2x is the post-validation target |
| `CARRY_KILL_SWITCH_PATH` | `/tmp/carry_bot_kill` | touch the file to halt new entries |

Add to `/etc/freqtrade.env` (mode 600):
```bash
export CARRY_API_KEY=...
export CARRY_API_SECRET=...
export CARRY_TESTNET=true
```

## Production cron (after testnet validation)

Bybit funding is paid every 8h at 00:00 / 08:00 / 16:00 UTC. Wake bot
5 min after each tick:

```cron
5 0,8,16 * * *  /opt/freqtrade/venv/bin/python -m carry_bot.main --once >> /var/log/carry_bot.log 2>&1
```

## Risk safeguards

Three gates run every tick before any new entry, plus reconciliation
of local book against exchange-reported positions.

### Kill switch

```bash
touch /tmp/carry_bot_kill
```

Next tick will:
1. Refuse all new entries
2. Force-close every open position
3. Log a `kill-switch active` alarm message

To resume:
```bash
rm /tmp/carry_bot_kill
```

### Stale-funding force close

If a position has been held > 24h **and** the latest funding rate < 0,
the bot will exit even if `exit_persistence` is not yet hit. Catches
fast regime flips that the persistence rule lags.

Configurable via `CarryConfig.stale_force_close_hours`.

### Liquidation distance monitor

For each open perp position, on every tick the bot computes
`distance = |mark - liq| / mark`. With 1x leverage and UTA spot
collateral the distance should be > 50%. If it drops below 10%, an
alarm fires (logs warning; doesn't auto-pause — humans investigate).

Common causes when this fires:
- UTA migration was reverted (spot no longer collateralises perp)
- Manual collateral movement out of the sub-account
- Leverage was raised manually mid-position

### Reconciliation

Every tick compares the local SQLite position book to the perp positions
the exchange reports. Three classes of mismatch trigger alarms:

- In local book but not on exchange → exchange closed it (liquidation? manual?)
- On exchange but not in local book → manual position bypassing the bot
- Qty mismatch > 5% → drift since last rebalance

Reconciliation alarms are warnings only; humans decide. The bot does
NOT auto-correct exchange-reported state — diverging silently is
strictly worse than alarming and parking.

### Daily PnL alarm

If realised + unrealised 24h PnL drops below
`-daily_loss_alarm_pct × capital` (default 1%), an alarm logs.
Doesn't auto-pause — delta-neutral PnL drift is usually fee/basis
noise, not a real loss; a human should look first.

## Delta rebalance

Spot and perp legs drift apart over time (slightly different fill
prices, slow fills, stoploss triggers). When `|spot_qty - perp_qty| /
spot_qty > 0.5%`, the bot places a corrective trade on the smaller
leg before the next entry cycle.

The rebalance fee accumulates into `position.rebalance_fees_quote` for
PnL accounting.

## Testnet shake-down protocol (Phase 2.5.3 → 2.5.6)

1. **Sub-account on Bybit testnet** — register at testnet.bybit.com,
   generate API key with Spot + Derivatives Trading + Read.
2. **Set env, run signals-only for one tick**:
   ```bash
   export CARRY_API_KEY=...
   export CARRY_API_SECRET=...
   export CARRY_TESTNET=true
   python -m carry_bot.main --once --signals-only -v
   ```
   Verify: connects to api-testnet.bybit.com, fetches funding rates
   for all 15 alts, no errors.
3. **Run actual order placement on testnet for 7 days**:
   ```bash
   # cron entry as above, but ensure CARRY_TESTNET=true
   ```
   Verify: opens/closes happen at funding-tick boundaries, delta drift
   stays small, no liquidation alarms, fees accumulate as expected.
4. **Mainnet sub-account + $100 capital for 14 days** — only after
   testnet validates.
5. **Scale capital** if 14d realized matches backtest expected within 20%.

## Pass/fail gates

- **Testnet 7d**: zero hedging errors > 1% delta sustained, no missed exits
- **Mainnet $100 14d**: realized APR within 50% of backtest expected
- **Stacking deploy**: only after solo CnC validates on $100 14d

## Files & state

- `/opt/freqtrade/carry_bot.sqlite` — open positions, closed audit, signal state, funding history
- `/var/log/carry_bot.log` — operational log
- `/tmp/carry_bot_kill` — kill-switch sentinel (touch to halt)
- Backup `carry_bot.sqlite` daily — rotation runbook in `OPERATIONS.md` (TBD).

## Tests

```bash
cd FreqtradeBot
for t in carry_bot/tests/test_*.py; do python "$t"; done
```

36 tests across 5 files. No external dependencies.
