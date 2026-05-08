"""Bybit account capability audit for Phase 2.5.1.

Reads keys from /etc/freqtrade.env via shell-sourced env vars.
Reports account type (unified vs classic), API permissions,
and current balances on spot vs derivatives wallets.

Does NOT print secrets. Read-only operations only.
"""
import os
import sys
import json

import ccxt

API_KEY = os.environ.get("FREQTRADE__EXCHANGE__KEY")
API_SECRET = os.environ.get("FREQTRADE__EXCHANGE__SECRET")

if not API_KEY or not API_SECRET:
    print("ERROR: keys not in env. Source /etc/freqtrade.env first.")
    sys.exit(1)


def header(s):
    print(f"\n=== {s} ===")


def main():
    # Public-only client to dodge IP whitelist on private endpoints
    bybit_pub = ccxt.bybit({"enableRateLimit": True})
    header("PUBLIC market capabilities (no auth needed)")
    try:
        bybit_pub.load_markets()
        whitelist = ["BTC", "ETH", "SOL", "DOGE", "XRP", "ADA", "AVAX", "DOT",
                     "POL", "NEAR", "ATOM", "SUI", "LINK", "OP", "BNB"]
        missing_spot, missing_perp = [], []
        for sym in whitelist:
            spot_sym = f"{sym}/USDT"
            perp_sym = f"{sym}/USDT:USDT"
            if spot_sym not in bybit_pub.markets:
                missing_spot.append(sym)
            if perp_sym not in bybit_pub.markets:
                missing_perp.append(sym)
        print(f"  Whitelist alts missing from SPOT: {missing_spot or 'none'}")
        print(f"  Whitelist alts missing from PERP: {missing_perp or 'none'}")
        # Sample basis check: spot vs perp price for top 3 pairs
        print()
        print("  Spot vs Perp basis (current quote):")
        for sym in whitelist[:8]:
            try:
                spot_t = bybit_pub.fetch_ticker(f"{sym}/USDT")
                perp_t = bybit_pub.fetch_ticker(f"{sym}/USDT:USDT")
                spot_px = spot_t.get("last") or spot_t.get("close") or 0
                perp_px = perp_t.get("last") or perp_t.get("close") or 0
                if spot_px and perp_px:
                    basis_bp = (perp_px - spot_px) / spot_px * 10000
                    print(f"    {sym}: spot={spot_px}  perp={perp_px}  basis={basis_bp:+.1f} bp")
            except Exception as e:
                print(f"    {sym}: err {e}")
    except Exception as e:
        print(f"  ERROR loading markets: {e}")
        return

    header("Private API check (will FAIL if IP not whitelisted)")
    bybit = ccxt.bybit({
        "apiKey": API_KEY,
        "secret": API_SECRET,
        "enableRateLimit": True,
        "options": {"defaultType": "swap"},
    })

    header("API key info")
    try:
        info = bybit.privateGetV5UserQueryApi()
        result = info.get("result", {})
        # Don't print id/secretKey; print only useful metadata
        safe = {
            "permissions": result.get("permissions", {}),
            "readOnly": result.get("readOnly"),
            "expiredAt": result.get("expiredAt"),
            "createdAt": result.get("createdAt"),
            "isMaster": result.get("isMaster"),
            "uta": result.get("uta"),  # 1 = unified trading account
            "vipLevel": result.get("vipLevel"),
        }
        print(json.dumps(safe, indent=2))
    except Exception as e:
        print(f"  ERROR querying API info: {e}")

    header("Account info (unified margin status)")
    try:
        acc = bybit.privateGetV5AccountInfo()
        print(json.dumps(acc.get("result", {}), indent=2))
    except Exception as e:
        print(f"  ERROR: {e}")

    header("Wallet balance — UNIFIED account")
    try:
        bal = bybit.privateGetV5AccountWalletBalance({"accountType": "UNIFIED"})
        result = bal.get("result", {}).get("list", [])
        if result:
            for acct in result:
                print(f"accountType={acct.get('accountType')}  "
                      f"totalEquity={acct.get('totalEquity')}  "
                      f"totalWalletBalance={acct.get('totalWalletBalance')}  "
                      f"totalAvailableBalance={acct.get('totalAvailableBalance')}")
                for coin in acct.get("coin", []):
                    eq = float(coin.get("equity", 0) or 0)
                    if eq > 0:
                        print(f"  {coin['coin']}: equity={eq}  walletBalance={coin.get('walletBalance')}  free={coin.get('availableToWithdraw')}")
        else:
            print("  empty result")
    except Exception as e:
        print(f"  ERROR: {e}")

    header("Wallet balance — CONTRACT account (legacy futures)")
    try:
        bal = bybit.privateGetV5AccountWalletBalance({"accountType": "CONTRACT"})
        result = bal.get("result", {}).get("list", [])
        for acct in result:
            for coin in acct.get("coin", []):
                eq = float(coin.get("equity", 0) or 0)
                if eq > 0:
                    print(f"  {coin['coin']}: equity={eq}")
    except Exception as e:
        print(f"  (CONTRACT account not present or err: {e})")

    header("Wallet balance — SPOT account (legacy spot)")
    try:
        bal = bybit.privateGetV5AccountWalletBalance({"accountType": "SPOT"})
        result = bal.get("result", {}).get("list", [])
        for acct in result:
            for coin in acct.get("coin", []):
                eq = float(coin.get("equity", 0) or 0)
                if eq > 0:
                    print(f"  {coin['coin']}: equity={eq}")
    except Exception as e:
        print(f"  (SPOT account not present or err: {e})")

    header("Markets capabilities")
    try:
        bybit.load_markets()
        spot = [s for s in bybit.markets if bybit.markets[s].get("type") == "spot" and bybit.markets[s].get("active")]
        swap = [s for s in bybit.markets if bybit.markets[s].get("type") == "swap" and bybit.markets[s].get("active")]
        print(f"  Active spot markets: {len(spot)}")
        print(f"  Active swap (perp) markets: {len(swap)}")
        # Check that whitelist alts exist on BOTH markets
        whitelist = ["BTC", "ETH", "SOL", "DOGE", "XRP", "ADA", "AVAX", "DOT",
                     "POL", "NEAR", "ATOM", "SUI", "LINK", "OP", "BNB"]
        missing_spot = []
        missing_perp = []
        for sym in whitelist:
            spot_sym = f"{sym}/USDT"
            perp_sym = f"{sym}/USDT:USDT"
            if spot_sym not in bybit.markets:
                missing_spot.append(sym)
            if perp_sym not in bybit.markets:
                missing_perp.append(sym)
        print(f"  Whitelist alts missing from SPOT: {missing_spot or 'none'}")
        print(f"  Whitelist alts missing from PERP: {missing_perp or 'none'}")
    except Exception as e:
        print(f"  ERROR loading markets: {e}")


if __name__ == "__main__":
    main()
