"""carry_bot — delta-neutral cash-and-carry strategy on Bybit.

Long spot + short perp same notional → delta-neutral. Collect funding
from short perp leg when funding rate is positive.

Validated by FreqtradeBot/scripts/research/carry_portfolio_sim.py:
~5% APR / Sharpe 1.81 / max-DD −0.23% over 4 years.

Components:
    config.py          — params, env vars, defaults
    exchange.py        — ccxt wrapper (Bybit sub-account)
    funding_signal.py  — funding fetch + persistence rules
    positions.py       — delta-neutral pair manager (next session)
    risk.py            — liquidation watch + kill switch (next session)
    scheduler.py       — 8h tick driver + slot rotation (next session)
    main.py            — entrypoint
"""

__version__ = "0.1.0"
