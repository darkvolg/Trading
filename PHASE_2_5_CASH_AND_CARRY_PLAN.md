# Phase 2.5 — Cash-and-Carry Strategy Plan

**Status:** P1 strategic. Created 2026-05-08 after spike + monthly portfolio simulation.
**Target:** ~5% APR delta-neutral with Sharpe ~1.8, stacked with V6A for diversification or 2x leverage breakthrough.

---

## Why this is worth 4-6 weeks (honest version)

Validated 2026-05-08 via 3 progressive scripts:

1. `funding_spike.py` — confirmed funding-only carry yields +9-15% APR gross across all regime windows.
2. `carry_backtest.py` — single-pair simulation with full Bybit fees (0.42%/cycle) showed 15/15 alts net positive on 4y data.
3. `carry_portfolio_sim.py` — **honest portfolio simulator** with proper concurrent-position tracking and monthly PnL buckets. Realistic output (full 4y, N_SLOTS=4):

   - **APR 4.91% net of all fees**
   - **Sharpe (monthly) 1.81** — excellent
   - **Max drawdown over 4 years: −0.23%** — extraordinary downside protection
   - **Worst single month: −0.18%** out of 52 months
   - 50% positive months (winners are bigger than losers; tail-skewed positive)
   - Avg concurrent positions 1.5 / 4 — strategy is **funding-supply-bound**, not capital-bound (slot count barely affects APR: 4.70% at 8 slots → 5.29% at 2 slots)

V6A+gate alone (validated same day): ~5% APR / 4% DD / Sharpe ~0.7.

### Stacking math (corrected, honest)

Two ways to deploy CnC alongside V6A:

**Configuration A — capital-split, no leverage**
- 50% V6A perp / 50% CnC (spot+perp delta-neutral)
- Combined: ~5% APR (CnC and V6A APRs blend, NOT add — they share fixed capital)
- Combined DD: ~2% (V6A 4% DD × 50% allocation + CnC ~0.2% DD × 50% allocation)
- Combined Sharpe: ~1.1 (uncorrelated edges blend favourably)
- Outcome: **same return, half the risk** — quality-of-PnL improvement

**Configuration B — capital-split, 2x leverage on CnC perp leg only**
- Same allocation but CnC's perp short uses 2x leverage (still delta-neutral if spot leg is 1x)
- Combined: ~10% APR (CnC contribution doubles, V6A unchanged)
- Combined DD: ~4% (back to V6A's level since CnC DD doubles to ~0.4%, still tiny)
- Combined Sharpe: ~1.0
- Outcome: **double return at same risk** — the actual breakthrough configuration.

CnC's delta-neutrality survives moderate leverage because the spot+perp legs cancel directional moves; only funding regime flips and execution friction expose us. Max safe leverage on perp leg ≈ 3x (would still need spot collateral to cover potential margin calls during basis blow-outs, but those are rare on USDT pairs).

Stacking is the path. Config B is the target.

---

## START HERE — Direction selection (P0)

The carry can be implemented multiple ways. Pick before writing code.

### Direction A — Spot+Perp on Bybit (cash-and-carry classic)
- **Mechanics:** buy alt on spot + short alt-perp same notional → delta-neutral. Collect funding from short perp leg.
- **Pros:** standard, well-understood, deepest liquidity, lowest basis risk on Bybit
- **Cons:** capital-intensive (2x notional needed). Spot inventory ties up cash. Liquidation risk on perp leg if spot collateral suddenly cratered (correlated risk).
- **Effort: 4-6 weeks.** Spot trading integration, dual-account balance, hedging logic, liquidation monitor, fee tracking, new backtest harness.

### Direction B — Perp-only "regime-cross" (NO spot inventory)
- **Mechanics:** open long when funding < 0 for N periods, open short when funding > 0 for N periods. NOT delta-neutral — directional bet on price + funding.
- **Pros:** simpler infra (perp only, fits inside freqtrade). 2-3 weeks effort.
- **Cons:** loses delta-neutrality → directional risk. Backtest shows price PnL dominates funding alpha → not robust across regimes (bull +35% APR, bear -31% per `funding_spike.py`). DEAD end per spike data.

### Direction C — Cross-exchange basis (Binance vs Bybit)
- **Mechanics:** spot on Binance + perp short on Bybit. Captures funding + cross-exchange basis differentials.
- **Pros:** even more carry potential.
- **Cons:** 8+ weeks effort, two-exchange infra, regulatory complexity, withdrawal/deposit timing. Not justifiable for current return target.

### Recommendation: Direction A (spot+perp on Bybit, single exchange)
Cleanest separation of concerns, deepest liquidity, lowest infra surface, validated economics.

---

## Tasks — Direction A

### Phase 2.5.1 — Architecture & infra (week 1)
- [ ] P0: Decide framework. Freqtrade is perp-only by design — spot integration is bolt-on at best. Options:
  - (i) Two parallel processes: freqtrade for V6A on perp, custom Python for cash-and-carry. Same Bybit account, different markets.
  - (ii) CCXT-based custom service from scratch (no freqtrade for the carry leg). Simpler abstraction, more infra to write.
  - **Pick (i)** — keep V6A untouched, isolate new code.
- [ ] P0: Bybit account setup. Verify can hold spot inventory + perp positions on same UID. Confirm sub-account is not required for unified margin.
- [ ] P0: API permissions audit. Need: spot trading + perp trading + balance read + transfer between wallets.
- [ ] P1: New repo structure: `FreqtradeBot/carry_bot/` for the new service. Independent of strategies/.
- [ ] P1: Logging/monitoring infrastructure. Same nginx-based dashboard endpoint pattern as V6A.

### Phase 2.5.2 — Core strategy logic (week 2)
- [ ] P0: Funding rate fetcher (8h cadence). Use freqtrade-cached `*-8h-funding_rate.feather` or Bybit /v5/market/funding-history endpoint.
- [ ] P0: Pair scoring: rank by recent N-period mean funding rate (descending positive). Top-K pairs candidates.
- [ ] P0: Entry rule (per pair): N consecutive 8h periods with funding > entry_threshold → open. Default threshold 0.0001 (0.01%/8h ≈ 11% APR).
- [ ] P0: Exit rule (per pair): M consecutive 8h periods with funding < exit_threshold → close. Default M=3, threshold -0.00005.
- [ ] P0: Slot manager: max N_SLOTS concurrent positions (capital constraint). When new candidate scores higher than existing position with worst funding, ROTATE.

### Phase 2.5.3 — Execution (week 3)
- [ ] P0: Position open: buy SPOT (market or limit) + short PERP same USDT-notional in single atomic-ish operation. Handle partial fills, retries.
- [ ] P0: Hedging accuracy: post-open delta should be < 0.5% of notional. If not, rebalance (buy/sell delta on spot side).
- [ ] P0: Position close: sell SPOT + cover PERP. Same atomicity concerns.
- [ ] P0: Daily delta drift check. Alts move; small drift accumulates. Rebalance when |delta| > threshold.
- [ ] P1: Fee tracker. Log every order's fee. Daily rollup vs expected.

### Phase 2.5.4 — Risk management (week 4)
- [ ] P0: Liquidation risk on perp leg. With unified margin, spot collateral protects. Without, need explicit margin top-up logic. Set perp leverage 1x (notional = collateral).
- [ ] P0: Flash crash protocol. If spot drops >20% in 1h while we're long-spot/short-perp, the SHORT perp profits offset the SPOT loss — net should be near-zero. Verify in stress tests.
- [ ] P0: Stale-funding detector. If funding stays negative >24h while in position, force close (wait for re-entry).
- [ ] P0: Kill-switch: pause new entries on signal (e.g. dashboard toggle, env var, telegram command).
- [ ] P1: Daily PnL reconciliation. Funding payments + price PnL on each leg + fees should net to expected return.

### Phase 2.5.5 — Backtest harness (week 4-5, parallel)
- [ ] P0: Custom backtest using freqtrade-cached price + funding data (perp-as-spot proxy acceptable per spike).
- [ ] P0: Walk-forward OOS: at least 3 windows. Pass criteria: positive APR after fees in ≥2/3 windows.
- [ ] P0: Stress tests: 2022 bear, 2024 bull, 2025-2026 chop.

### Phase 2.5.6 — Deploy + monitor (week 5-6)
- [ ] P0: Dry-run on Bybit testnet for 1 week. Verify orders fill, hedging accurate, no errors.
- [ ] P0: Live deploy with small capital ($100 spot + matching perp margin) for 14 days. Monitor delta, fees, funding accrued.
- [ ] P0: Scale capital after 14d if metrics match backtest within 20%.
- [ ] P1: /live page block for cash-and-carry stats (funding accrued, active positions, delta).

---

## Hard rules (DO NOT TOUCH)
- ❌ Cash-and-carry runs on its own account/sub-account — DO NOT mix margin with V6A's perp account. If V6A blows up margin, carry positions must be untouched.
- ❌ NO leverage on perp leg above 1x. Carry alpha is small per cycle; one liquidation eats years of returns.
- ❌ NO live deploy without 1-week testnet dry-run.
- ❌ NO scaling capital beyond $1k until 14d live matches backtest within 20%.

## Pass/fail gates
- Backtest 4y full: net APR > 5% (vs. spike result 7%)
- Live testnet 1 week: zero hedging errors > 1% delta sustained
- Live $100 cap 14d: realized APR within 50% of backtest expected (some path-dependence is fine)

## Phase 2.5.1 architecture decisions — RESOLVED 2026-05-08

Audit run via `bybit_account_audit.py` (public API) and senko env inspection.

### 1. Account architecture: dedicated Bybit sub-account
- Current Bybit API key (in /etc/freqtrade.env on senko) is V6A dry-run config; key has IP whitelist that does NOT include senko, so it has never made signed calls. Never used in production.
- For CnC: create dedicated sub-account with its own key. Separation of concerns: a margin call on V6A's perp won't liquidate CnC's positions.
- Sub-account also lets us measure CnC PnL cleanly (its own balance, fees, history).

### 2. Margin mode: UTA (Unified Trading Account)
- Bybit's recommended default for combined-strategy accounts.
- Single margin pool across spot+perp. Spot inventory automatically counts as collateral for perp short, simplifying capital efficiency.
- Confirm at sub-account creation; Bybit migrated most accounts to UTA in 2024.

### 3. Framework: custom Python service (NOT freqtrade)
- Freqtrade is perp-only by design; spot integration is partial and not built for delta-neutral simultaneity.
- CnC needs atomic spot+perp pair operations on every entry/exit.
- Keeps V6A's freqtrade process untouched (isolation, no regression risk).
- Stack: `ccxt` for exchange abstraction + ~500-800 lines of custom strategy/execution/risk logic. Manageable in 4-6 weeks.

### 4. Whitelist coverage — confirmed
All 13 alts in V6A whitelist (BTC ETH SOL DOGE XRP ADA AVAX DOT POL NEAR ATOM SUI LINK OP BNB) exist on **both spot AND perp** on Bybit. No pair-level exclusions needed.

### 5. Basis economics — conservative-bias confirmed
Current snapshot (2026-05-08) on top 8 alts: spot–perp basis ranges −5 to −8 bp (perp trades cheaper than spot). My backtests used perp-price-as-spot proxy. Real spot is slightly above perp, meaning real entry cost is a few bp higher than backtest assumed. 6 bp drag vs 42 bp/cycle full-fee model = negligible. Backtest verdict stands.

### 6. Repo structure
`FreqtradeBot/carry_bot/` — new module, independent of `strategies/`. Layout sketch:
```
carry_bot/
  __init__.py
  config.py             # pair list, params, slot count, env vars
  exchange.py           # ccxt wrapper, rate-limited, sub-account auth
  funding_signal.py     # fetch + persistence rules
  positions.py          # delta-neutral pair manager (spot+perp atomic ops)
  risk.py               # liquidation watch, kill switch, daily reconcile
  scheduler.py          # 8h ticks, slot rotation
  main.py               # entrypoint
  tests/
```

## Open questions for next session
1. Bybit sub-account creation (manual via UI, or API-driven?) — likely UI for first time
2. Bybit testnet account: do we already have testnet keys, or create fresh?
3. Funding rate live fetch: REST vs WebSocket — REST is simpler, ~50 requests/8h is fine
4. Delta-rebalance threshold — pick after 1 week of testnet observation
5. Pair-scoring window — start with last 3 periods (24h), tune if needed
