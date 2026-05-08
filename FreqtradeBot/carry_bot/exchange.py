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
import logging
import time
from dataclasses import dataclass

import ccxt

logger = logging.getLogger(__name__)


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

    def _build_client(self, key: str, sec: str) -> ccxt.bybit:
        c = ccxt.bybit({
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

    def fetch_funding_rate(self, base: str) -> float:
        """Latest funding rate for the perp."""
        sym = perp_symbol(base)
        info = self._client.fetch_funding_rate(sym)
        rate = info.get("fundingRate")
        if rate is None:
            raise RuntimeError(f"no fundingRate in response for {sym}: {info}")
        return float(rate)

    def fetch_funding_history(self, base: str, since_ms: int | None = None,
                              limit: int = 200) -> list[dict]:
        """Recent funding history. Returns list of {timestamp, rate}."""
        sym = perp_symbol(base)
        rows = self._client.fetch_funding_rate_history(sym, since_ms, limit)
        return [
            {"timestamp": r["timestamp"], "rate": float(r["fundingRate"])}
            for r in rows
        ]

    def fetch_basis_bp(self, base: str) -> float:
        """(perp - spot) / spot in basis points. Negative = perp discount."""
        spot = self._client.fetch_ticker(spot_symbol(base))
        perp = self._client.fetch_ticker(perp_symbol(base))
        spot_px = spot.get("last") or spot.get("close")
        perp_px = perp.get("last") or perp.get("close")
        if not spot_px or not perp_px:
            raise RuntimeError(f"missing price: spot={spot_px} perp={perp_px}")
        return (perp_px - spot_px) / spot_px * 10000

    # ---------- Private (require keys + IP whitelist) ----------

    def fetch_spot_balance(self, asset: str) -> float:
        bal = self._client.fetch_balance({"type": "spot"})
        return float(bal.get(asset, {}).get("free", 0) or 0)

    def fetch_perp_position(self, base: str) -> dict | None:
        """Current open perp position, or None."""
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
                }
        return None

    def set_leverage(self, base: str, leverage: int) -> None:
        sym = perp_symbol(base)
        try:
            self._client.set_leverage(leverage, sym)
        except ccxt.ExchangeError as e:
            # Bybit raises if leverage is already set to the requested value;
            # treat as success.
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
