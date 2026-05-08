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
