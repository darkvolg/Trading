"""Bybit exchange wrapper for cash-and-carry.

Single ccxt client with:
- Sub-account auth (separate from V6A's account)
- Rate-limited (Bybit's enableRateLimit + retry-on-429 logic)
- Atomic spot+perp pair operations (open / close)
- Read-only fallback when keys not set (testing/development)

NOT a generic exchange abstraction — specific to Bybit USDT pairs and
the cash-and-carry use case.
"""
from __future__ import annotations
import functools
import logging
import random
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def _ccxt():
    """Lazy import so dataclass consumers don't need ccxt installed."""
    import ccxt as _c
    return _c


def _is_rate_limit(exc: Exception) -> bool:
    """Heuristic: ccxt RateLimitExceeded or HTTP 429 in message."""
    name = type(exc).__name__
    return "RateLimit" in name or "429" in str(exc)


def _is_network(exc: Exception) -> bool:
    name = type(exc).__name__
    return any(k in name for k in ("NetworkError", "RequestTimeout", "ExchangeNotAvailable"))


def with_retry(retries: int = 3, base_delay: float = 0.5, max_delay: float = 8.0):
    """Decorator: retry on network / rate-limit errors with jittered backoff.

    Does NOT retry on order placement endpoints — caller decides idempotency.
    Used internally for read-only ops (fetch_*).
    """
    def deco(fn):
        @functools.wraps(fn)
        def wrap(*args, **kwargs):
            for attempt in range(retries + 1):
                try:
                    return fn(*args, **kwargs)
                except Exception as e:
                    if attempt == retries:
                        raise
                    if not (_is_rate_limit(e) or _is_network(e)):
                        raise
                    delay = min(max_delay, base_delay * (2 ** attempt))
                    delay += random.uniform(0, delay * 0.25)
                    logger.warning(
                        "%s attempt %d/%d failed (%s: %s); retrying in %.2fs",
                        fn.__name__, attempt + 1, retries + 1,
                        type(e).__name__, e, delay,
                    )
                    time.sleep(delay)
        return wrap
    return deco


def spot_symbol(base: str) -> str:
    return f"{base}/USDT"


def perp_symbol(base: str) -> str:
    return f"{base}/USDT:USDT"


@dataclass
class FillResult:
    """Result of a single market order fill."""
    side: str            # 'buy' / 'sell'
    market: str          # 'spot' / 'perp'
    base: str            # e.g. 'BTC'
    qty: float           # base-asset quantity
    avg_price: float
    fee_quote: float     # fee paid, in quote (USDT)
    order_id: str

    @property
    def notional(self) -> float:
        return self.qty * self.avg_price


class BybitClient:
    """Thin Bybit wrapper. Configurable for testnet vs mainnet."""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.testnet = testnet
        # Don't store the secret as an instance attribute — hand it off to
        # ccxt directly. self._client retains the credentials internally.
        self._client = self._build_client(api_key, api_secret)

    def _build_client(self, key: str, sec: str):
        ccxt_mod = _ccxt()
        c = ccxt_mod.bybit({
            "apiKey": key,
            "secret": sec,
            "enableRateLimit": True,
            # Default to swap; explicit per-call type override for spot.
            "options": {"defaultType": "swap"},
        })
        if self.testnet:
            c.set_sandbox_mode(True)
        return c

    @property
    def has_credentials(self) -> bool:
        return bool(self._client.apiKey)

    # ---------- Public ----------

    @with_retry()
    def fetch_funding_rate(self, base: str) -> float:
        """Latest funding rate for the perp."""
        sym = perp_symbol(base)
        info = self._client.fetch_funding_rate(sym)
        rate = info.get("fundingRate")
        if rate is None:
            raise RuntimeError(f"no fundingRate in response for {sym}: {info}")
        return float(rate)

    @with_retry()
    def fetch_funding_history(self, base: str, since_ms: int | None = None,
                              limit: int = 200) -> list[dict]:
        """Recent funding history. Returns list of {timestamp, rate}."""
        sym = perp_symbol(base)
        rows = self._client.fetch_funding_rate_history(sym, since_ms, limit)
        return [
            {"timestamp": r["timestamp"], "rate": float(r["fundingRate"])}
            for r in rows
        ]

    @with_retry()
    def fetch_basis_bp(self, base: str) -> float:
        """(perp - spot) / spot in basis points. Negative = perp discount."""
        spot = self._client.fetch_ticker(spot_symbol(base))
        perp = self._client.fetch_ticker(perp_symbol(base))
        spot_px = spot.get("last") or spot.get("close")
        perp_px = perp.get("last") or perp.get("close")
        if not spot_px or not perp_px:
            raise RuntimeError(f"missing price: spot={spot_px} perp={perp_px}")
        return (perp_px - spot_px) / spot_px * 10000

    @with_retry()
    def fetch_perp_price(self, base: str) -> float:
        t = self._client.fetch_ticker(perp_symbol(base))
        px = t.get("last") or t.get("close")
        if not px:
            raise RuntimeError(f"missing perp price for {base}")
        return float(px)

    # ---------- Private (require keys + IP whitelist) ----------

    def fetch_spot_balance(self, asset: str) -> float:
        bal = self._client.fetch_balance({"type": "spot"})
        return float(bal.get(asset, {}).get("free", 0) or 0)

    @with_retry()
    def fetch_unified_usdt(self) -> float:
        """Free USDT available in unified margin (UTA) account.

        Used by scheduler to size new positions as a fraction of capital.
        On non-UTA fallback to spot wallet free USDT.
        """
        try:
            bal = self._client.fetch_balance()
            usdt = bal.get("USDT") or {}
            free = usdt.get("free")
            if free is not None:
                return float(free)
        except Exception as e:
            logger.warning("fetch_unified_usdt unified failed (%s); trying spot", e)
        return self.fetch_spot_balance("USDT")

    @with_retry()
    def fetch_perp_position(self, base: str) -> dict | None:
        """Current open perp position, or None.

        Includes liquidation_price for risk monitor — it's the level where
        the perp leg would be force-closed by Bybit. Distance to it must
        stay large; with 1x leverage and spot collateral via UTA it's
        normally far below entry, but we monitor regardless.
        """
        sym = perp_symbol(base)
        positions = self._client.fetch_positions([sym])
        for p in positions:
            qty = float(p.get("contracts", 0) or 0)
            if qty != 0:
                return {
                    "side": p.get("side"),
                    "qty": qty,
                    "entry": float(p.get("entryPrice", 0) or 0),
                    "leverage": float(p.get("leverage", 1) or 1),
                    "unrealized_pnl": float(p.get("unrealizedPnl", 0) or 0),
                    "liquidation_price": float(p.get("liquidationPrice", 0) or 0),
                    "mark_price": float(p.get("markPrice", 0) or 0),
                }
        return None

    @with_retry()
    def fetch_open_positions(self) -> dict[str, dict]:
        """All open perp positions keyed by base symbol. Used by reconcile."""
        positions = self._client.fetch_positions()
        out = {}
        for p in positions:
            sym = p.get("symbol", "")
            qty = float(p.get("contracts", 0) or 0)
            if qty == 0:
                continue
            base = sym.split("/")[0]
            out[base] = {
                "side": p.get("side"),
                "qty": qty,
                "entry": float(p.get("entryPrice", 0) or 0),
                "liquidation_price": float(p.get("liquidationPrice", 0) or 0),
                "mark_price": float(p.get("markPrice", 0) or 0),
            }
        return out

    def set_leverage(self, base: str, leverage: int) -> None:
        sym = perp_symbol(base)
        try:
            self._client.set_leverage(leverage, sym)
        except Exception as e:
            # Bybit raises if leverage is already set to the requested value;
            # treat as success. Generic catch since ccxt.ExchangeError isn't
            # imported at module level (lazy ccxt).
            if "leverage not modified" in str(e).lower():
                return
            raise

    def open_carry_pair(self, base: str, notional_usdt: float,
                        leverage: int = 1) -> tuple[FillResult, FillResult]:
        """Open delta-neutral position: buy spot + sell perp same notional.

        Atomic-ish: if perp open fails, immediately sell spot to revert.
        """
        if not self.has_credentials:
            raise RuntimeError("open_carry_pair needs credentials")

        # Set leverage first (cheap, idempotent)
        self.set_leverage(base, leverage)

        # 1) Buy spot (full notional in USDT)
        spot_fill = self._market_order(
            symbol=spot_symbol(base), side="buy",
            quote_amount=notional_usdt, market="spot",
        )

        try:
            # 2) Sell same base qty on perp
            perp_fill = self._market_order(
                symbol=perp_symbol(base), side="sell",
                base_amount=spot_fill.qty, market="perp",
            )
        except Exception as e:
            logger.error(f"perp open failed for {base}: {e}; reverting spot")
            self._market_order(
                symbol=spot_symbol(base), side="sell",
                base_amount=spot_fill.qty, market="spot",
            )
            raise

        return spot_fill, perp_fill

    def close_carry_pair(self, base: str, qty: float) -> tuple[FillResult, FillResult]:
        """Close delta-neutral position: sell spot + buy back perp."""
        if not self.has_credentials:
            raise RuntimeError("close_carry_pair needs credentials")

        spot_fill = self._market_order(
            symbol=spot_symbol(base), side="sell",
            base_amount=qty, market="spot",
        )
        perp_fill = self._market_order(
            symbol=perp_symbol(base), side="buy",
            base_amount=qty, market="perp",
        )
        return spot_fill, perp_fill

    def rebalance_pair(self, base: str, spot_qty: float,
                       perp_qty: float) -> FillResult | None:
        """Re-equalise spot and perp legs after delta drift.

        If spot_qty > perp_qty: increase perp short (sell more perp).
        If perp_qty > spot_qty: increase spot long (buy more spot).
        Returns the FillResult of the corrective trade, or None if drift
        below precision.
        """
        if not self.has_credentials:
            raise RuntimeError("rebalance_pair needs credentials")

        delta = spot_qty - perp_qty
        if abs(delta) < 1e-9:
            return None

        if delta > 0:
            # Spot heavier than perp → grow short perp
            return self._market_order(
                symbol=perp_symbol(base), side="sell",
                base_amount=delta, market="perp",
            )
        # Perp heavier than spot → buy more spot
        return self._market_order(
            symbol=spot_symbol(base), side="buy",
            base_amount=abs(delta), market="spot",
        )

    # ---------- Internals ----------

    def _market_order(self, symbol: str, side: str, market: str,
                      quote_amount: float | None = None,
                      base_amount: float | None = None) -> FillResult:
        """Place a market order, return normalised FillResult.

        For spot buys we typically size in USDT (quote_amount); for sells we
        size in base. Bybit `createOrder` with `cost` arg handles quote-side.
        """
        params = {"type": market}
        if quote_amount is not None:
            # Bybit spot buy: market order with quoteOrderQty
            order = self._client.create_order(
                symbol=symbol, type="market", side=side,
                amount=None, price=None,
                params={**params, "cost": quote_amount},
            )
        else:
            order = self._client.create_order(
                symbol=symbol, type="market", side=side,
                amount=base_amount, price=None,
                params=params,
            )

        return self._normalise_fill(order, market)

    def _normalise_fill(self, order: dict, market: str) -> FillResult:
        base = order.get("symbol", "/").split("/")[0]
        return FillResult(
            side=order.get("side", ""),
            market=market,
            base=base,
            qty=float(order.get("filled", 0) or 0),
            avg_price=float(order.get("average", 0) or 0),
            fee_quote=float((order.get("fee") or {}).get("cost", 0) or 0),
            order_id=str(order.get("id", "")),
        )

    # ---------- Health / heartbeat ----------

    def ping(self) -> bool:
        """Public-API liveness check. Doesn't require keys."""
        try:
            self._client.fetch_time()
            return True
        except Exception as e:
            logger.warning(f"ping failed: {e}")
            return False
