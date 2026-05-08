# Phase 2.5 — Cash-and-Carry Strategy Plan

**Status:** P1 strategic. Created 2026-05-08 after spike validation.
**Target:** ~7-9% APR (full cycle) / ~18% APR (bulls), delta-neutral, stacked on top of V6A+gate.

---

## Why this is worth 4-6 weeks

Validated 2026-05-08 via `FreqtradeBot/scripts/research/carry_backtest.py`:

- Funding-only carry yields **+9 to +15% APR** robustly across all 3 regime windows (bear 480d, bull 379d, full 4y+) per `funding_spike.py`
- Realistic cash-and-carry backtest with full Bybit fees (0.42%/cycle round-trip + slippage) shows **15/15 pairs net positive on 4y data**, portfolio ~7% APR with 8-slot cap, ~18% in bull periods specifically
- V6A+gate alone tops out around 5% APR / 4% DD (validated 2026-05-08)
- Stack: V6A directional + cash-and-carry delta-neutral on same capital → uncorrelated edges → **~12-14% APR @ same ~4% DD = 2.5x baseline return at same risk**

This is the breakthrough configuration the project was looking for.

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

## Open questions for next session
1. Bybit unified margin vs cross margin vs isolated — which gives best capital efficiency for spot+perp combo?
2. Funding history fetch: freqtrade cache (already have 4y) vs Bybit API direct (needed for live)
3. Delta-rebalance threshold — empirically, how much drift accumulates per day on liquid alts?
4. Pair-scoring window — last 3 periods (24h) vs last 9 periods (3 days)?
