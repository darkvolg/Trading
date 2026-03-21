"""
TrendRiderStrategy — "Trend Rider"

Philosophy: Ride established uptrends with WIDE stoploss.
Key insight: crypto swings 2-4% per hour. Stoploss must be >= 5-6%.

Lessons from v1-v5:
- v4 bull backtest: -9.74% (28 trades, 6 min avg, trailing too tight)
- v6.0 bull backtest: -72.76% (369 trades, 2 min avg, stoploss too tight)
- Problem: 1.5x ATR ~ 1.5% stoploss, but BTC swings 2-3%/hour
- Solution: 3x ATR stoploss (~4-6%), NO custom stoploss, let ROI+trailing work

Rules:
- LONG only (shorts failed in v5)
- Bear market = no trading
- WIDE stoploss (6%) to survive normal volatility
- WIDE trailing (2% trail after 2.5% profit)
- FEW high-quality entries (quality > quantity)
"""

import talib.abstract as ta
from datetime import datetime
from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter, merge_informative_pair
from pandas import DataFrame
from functools import reduce


class TrendRiderStrategy(IStrategy):
    INTERFACE_VERSION = 3

    # --- ROI: Wide, let winners run ---
    minimal_roi = {
        "0": 0.10,      # 10% immediate
        "120": 0.06,    # 6% after 2h
        "360": 0.04,    # 4% after 6h
        "720": 0.025,   # 2.5% after 12h
        "1440": 0.015,  # 1.5% after 24h
        "2880": 0.01,   # 1% after 48h
    }

    # --- Stoploss: WIDE for crypto volatility ---
    stoploss = -0.06           # 6% (was 4% in v4 — too tight!)
    use_custom_stoploss = False # DISABLED — custom stoploss was the killer

    # --- Trailing Stop: WIDE ---
    trailing_stop = True
    trailing_stop_positive = 0.03        # 3% trail
    trailing_stop_positive_offset = 0.05 # Activate after +5%
    trailing_only_offset_is_reached = True

    # --- General ---
    timeframe = "1h"
    startup_candle_count = 210
    process_only_new_candles = True
    can_short = False

    # --- Protections (moved from config.json for Freqtrade 2026.2+) ---
    protections = [
        {
            "method": "CooldownPeriod",
            "stop_duration": 20
        },
        {
            "method": "StoplossGuard",
            "lookback_period": 720,
            "trade_limit": 3,
            "stop_duration": 60,
            "only_per_pair": False
        },
        {
            "method": "MaxDrawdown",
            "lookback_period": 1440,
            "max_allowed_drawdown": 0.10,
            "stop_duration": 300,
            "trade_limit": 5
        }
    ]

    # --- HyperOpt Results (applied from optimization session 2026-03-21) ---
    buy_params = {
        "ema_fast": 9,
        "ema_slow": 16,
        "rsi_period": 16,
        "rsi_pullback_low": 40,
        "rsi_pullback_high": 58,
        "rsi_bounce": 30,
        "adx_threshold": 27,
        "volume_factor": 1.014,
    }

    sell_params = {
        "rsi_exit": 81,
    }

    # --- HyperOpt Parameters ---
    ema_fast = IntParameter(5, 15, default=9, space="buy")
    ema_slow = IntParameter(15, 30, default=21, space="buy")
    rsi_period = IntParameter(10, 20, default=14, space="buy")
    rsi_pullback_low = IntParameter(30, 48, default=40, space="buy")
    rsi_pullback_high = IntParameter(52, 65, default=58, space="buy")
    rsi_bounce = IntParameter(25, 35, default=30, space="buy")
    rsi_exit = IntParameter(72, 85, default=78, space="sell")
    adx_threshold = IntParameter(20, 35, default=25, space="buy")
    volume_factor = DecimalParameter(1.0, 2.5, default=1.3, space="buy")

    # --- Leverage: fixed, not optimized (fix #9) ---
    leverage_value = 3

    def leverage(self, pair: str, current_time, current_rate: float,
                 proposed_leverage: float, max_leverage: float, entry_tag: str,
                 side: str, **kwargs) -> float:
        return min(float(self.leverage_value), max_leverage)

    def informative_pairs(self):
        pairs = self.dp.current_whitelist() if self.dp else []
        informative = []
        for pair in pairs:
            informative.append((pair, "4h"))
        # BTC as market sentiment
        informative.append(("BTC/USDT:USDT", "1h"))
        informative.append(("BTC/USDT:USDT", "4h"))
        return informative

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # EMAs (all periods for hyperopt ranges)
        for period in range(5, 31):
            dataframe[f"ema_{period}"] = ta.EMA(dataframe, timeperiod=period)
        dataframe["ema_50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema_200"] = ta.EMA(dataframe, timeperiod=200)

        # RSI (all periods for hyperopt range 10-20)
        for period in range(10, 21):
            dataframe[f"rsi_{period}"] = ta.RSI(dataframe, timeperiod=period)

        # ADX
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["plus_di"] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe["minus_di"] = ta.MINUS_DI(dataframe, timeperiod=14)

        # MACD
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe["macd"] = macd["macd"]
        dataframe["macdsignal"] = macd["macdsignal"]
        dataframe["macdhist"] = macd["macdhist"]

        # Bollinger Bands
        bb = ta.BBANDS(dataframe, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
        dataframe["bb_upper"] = bb["upperband"]
        dataframe["bb_middle"] = bb["middleband"]
        dataframe["bb_lower"] = bb["lowerband"]

        # Volume (fix #4: epsilon guard against division by zero)
        dataframe["volume_ema"] = ta.EMA(dataframe["volume"], timeperiod=20)
        dataframe["volume_ratio"] = dataframe["volume"] / (dataframe["volume_ema"] + 1e-10)

        # OBV
        dataframe["obv"] = ta.OBV(dataframe)
        dataframe["obv_ema"] = ta.EMA(dataframe["obv"], timeperiod=20)

        # Regime
        dataframe["is_bull"] = (
            (dataframe["close"] > dataframe["ema_200"]) &
            (dataframe["ema_50"] > dataframe["ema_200"])
        ).astype(int)

        dataframe["is_bear"] = (
            (dataframe["close"] < dataframe["ema_200"]) &
            (dataframe["ema_50"] < dataframe["ema_200"])
        ).astype(int)

        # Pullback detection: price dipped to EMA support and bouncing
        ema_slow_key = f"ema_{self.ema_slow.value}"
        if ema_slow_key in dataframe.columns:
            dataframe["pullback_to_ema"] = (
                (dataframe["low"] <= dataframe[ema_slow_key] * 1.01) &
                (dataframe["close"] > dataframe[ema_slow_key]) &
                (dataframe["close"] > dataframe["open"])  # Bullish candle
            ).astype(int)
        else:
            dataframe["pullback_to_ema"] = 0

        # EMA50 support bounce
        dataframe["ema50_bounce"] = (
            (dataframe["low"] <= dataframe["ema_50"] * 1.01) &
            (dataframe["close"] > dataframe["ema_50"]) &
            (dataframe["close"] > dataframe["open"])
        ).astype(int)

        # --- 4h Multi-Timeframe confirmation ---
        if self.dp:
            # 4h data for current pair
            df_4h = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe='4h')
            if len(df_4h) > 0:
                df_4h['ema_50_4h'] = ta.EMA(df_4h, timeperiod=50)
                df_4h['ema_200_4h'] = ta.EMA(df_4h, timeperiod=200)
                df_4h['rsi_14_4h'] = ta.RSI(df_4h, timeperiod=14)
                df_4h['adx_4h'] = ta.ADX(df_4h, timeperiod=14)
                df_4h['is_bull_4h'] = (
                    (df_4h['close'] > df_4h['ema_200_4h']) &
                    (df_4h['ema_50_4h'] > df_4h['ema_200_4h'])
                ).astype(int)
                # Merge 4h data into 1h using merge_informative_pair
                dataframe = merge_informative_pair(
                    dataframe,
                    df_4h[['date', 'ema_50_4h', 'ema_200_4h', 'rsi_14_4h', 'adx_4h', 'is_bull_4h']],
                    self.timeframe, '4h', ffill=True
                )
            else:
                dataframe['ema_50_4h_4h'] = 0
                dataframe['ema_200_4h_4h'] = 0
                dataframe['rsi_14_4h_4h'] = 50
                dataframe['adx_4h_4h'] = 0
                dataframe['is_bull_4h_4h'] = 0

            # BTC market sentiment
            df_btc = self.dp.get_pair_dataframe(pair='BTC/USDT:USDT', timeframe='1h')
            if len(df_btc) > 0:
                df_btc['btc_ema_200'] = ta.EMA(df_btc, timeperiod=200)
                df_btc['btc_ema_50'] = ta.EMA(df_btc, timeperiod=50)
                df_btc['btc_rsi'] = ta.RSI(df_btc, timeperiod=14)
                df_btc['btc_is_bull'] = (
                    (df_btc['close'] > df_btc['btc_ema_200']) &
                    (df_btc['btc_ema_50'] > df_btc['btc_ema_200'])
                ).astype(int)
                dataframe = merge_informative_pair(
                    dataframe,
                    df_btc[['date', 'btc_ema_200', 'btc_ema_50', 'btc_rsi', 'btc_is_bull']],
                    self.timeframe, '1h', ffill=True
                )
            else:
                dataframe['btc_is_bull_1h'] = 1
                dataframe['btc_rsi_1h'] = 50
        else:
            # Safety fallback when dp is not available
            dataframe['is_bull_4h_4h'] = dataframe['is_bull']
            dataframe['rsi_14_4h_4h'] = dataframe['rsi_14'] if 'rsi_14' in dataframe.columns else 50
            dataframe['adx_4h_4h'] = dataframe['adx']
            dataframe['btc_is_bull_1h'] = 1
            dataframe['btc_rsi_1h'] = 50

        # Ensure columns exist (safety for backtesting edge cases)
        for col, default in [('is_bull_4h_4h', 1), ('rsi_14_4h_4h', 50), ('adx_4h_4h', 20), ('btc_is_bull_1h', 1), ('btc_rsi_1h', 50)]:
            if col not in dataframe.columns:
                dataframe[col] = default

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        rsi = f"rsi_{self.rsi_period.value}"
        ema_fast = f"ema_{self.ema_fast.value}"
        ema_slow = f"ema_{self.ema_slow.value}"

        # === LONG 1: Trend Pullback to EMA ===
        # Price pulls back to EMA21 support in strong uptrend, then bounces
        conditions_pullback = [
            dataframe["is_bull"] == 1,
            dataframe["pullback_to_ema"] == 1,
            dataframe[rsi] > self.rsi_pullback_low.value,
            dataframe[rsi] < self.rsi_pullback_high.value,
            dataframe["adx"] > self.adx_threshold.value,
            dataframe["volume_ratio"] > self.volume_factor.value,
            dataframe["plus_di"] > dataframe["minus_di"],         # Bullish DI
            dataframe["obv"] > dataframe["obv_ema"],
            dataframe["volume"] > 0,
            dataframe["btc_is_bull_1h"] == 1,   # BTC must be bullish
            dataframe["is_bull_4h_4h"] == 1,    # 4h trend must confirm
        ]
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_pullback),
            ["enter_long", "enter_tag"]
        ] = (1, "trend_pullback")

        # === LONG 2: EMA50 Support Bounce ===
        # Deeper pullback to EMA50 in uptrend — stronger support
        conditions_ema50 = [
            dataframe["is_bull"] == 1,
            dataframe["ema50_bounce"] == 1,
            dataframe[rsi] > 30,
            dataframe[rsi] < 50,
            dataframe["adx"] > 20,
            dataframe["volume_ratio"] > 1.0,
            dataframe["macdhist"] > dataframe["macdhist"].shift(1),
            dataframe["volume"] > 0,
            dataframe["btc_is_bull_1h"] == 1,   # BTC must be bullish
            dataframe["is_bull_4h_4h"] == 1,    # 4h trend must confirm
        ]
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_ema50),
            ["enter_long", "enter_tag"]
        ] = (1, "ema50_bounce")

        # === LONG 3: RSI Oversold Bounce ===
        # RSI crosses 30 from below in bull/neutral market
        conditions_rsi = [
            dataframe["close"] > dataframe["ema_200"],
            dataframe[rsi].shift(1) < self.rsi_bounce.value,
            dataframe[rsi] > self.rsi_bounce.value,
            dataframe["close"] > dataframe["bb_lower"],
            dataframe["close"] > dataframe["open"],                # Bullish candle
            dataframe["volume_ratio"] > 0.8,
            dataframe["obv"] > dataframe["obv_ema"],
            dataframe["volume"] > 0,
            dataframe["btc_is_bull_1h"] == 1,   # BTC must be bullish
        ]
        dataframe.loc[
            reduce(lambda x, y: x & y, conditions_rsi),
            ["enter_long", "enter_tag"]
        ] = (1, "rsi_bounce")

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        rsi = f"rsi_{self.rsi_period.value}"
        ema_fast = f"ema_{self.ema_fast.value}"
        ema_slow = f"ema_{self.ema_slow.value}"

        # EXIT 1: RSI very overbought
        dataframe.loc[
            (dataframe[rsi] > self.rsi_exit.value) &
            (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"]
        ] = (1, "rsi_overbought")

        # EXIT 2: Bearish EMA cross with MACD confirmation
        dataframe.loc[
            (dataframe[ema_fast] < dataframe[ema_slow]) &
            (dataframe[ema_fast].shift(1) >= dataframe[ema_slow].shift(1)) &
            (dataframe["macdhist"] < 0) &
            (dataframe[rsi] > 50) &
            (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"]
        ] = (1, "ema_bearish_cross")

        # EXIT 3: Price drops below EMA200 (trend broken)
        dataframe.loc[
            (dataframe["close"] < dataframe["ema_200"]) &
            (dataframe["close"].shift(1) >= dataframe["ema_200"].shift(1)) &
            (dataframe["volume"] > 0),
            ["exit_long", "exit_tag"]
        ] = (1, "trend_broken")

        return dataframe

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float,
                           time_in_force: str, current_time: datetime, entry_tag: str | None,
                           side: str, **kwargs) -> bool:
        # Calculate levels
        sl_price = rate * (1 + self.stoploss)  # stoploss is negative
        tp1_price = rate * 1.03   # +3%
        tp2_price = rate * 1.05   # +5% (trailing activates)
        tp3_price = rate * 1.10   # +10% (ROI target)
        leverage = self.leverage_value
        stake = self.stake_amount if hasattr(self, 'stake_amount') else 50

        # Entry reason mapping
        reasons = {
            "trend_pullback": "Откат к EMA16 в сильном тренде, отскок с подтверждением объёма",
            "ema50_bounce": "Глубокий откат к EMA50, отскок с растущим MACD",
            "rsi_bounce": "RSI перепродан, отскок от нижней Боллинджера в бычьем рынке",
        }
        reason = reasons.get(entry_tag, entry_tag or "Signal")

        # Get current indicators for context
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if len(dataframe) > 0:
            last = dataframe.iloc[-1]
            rsi_key = f"rsi_{self.rsi_period.value}"
            rsi_val = last.get(rsi_key, 0)
            adx_val = last.get("adx", 0)
            vol_ratio = last.get("volume_ratio", 0)
        else:
            rsi_val = adx_val = vol_ratio = 0

        msg = (
            f"*TRENDRIDER SIGNAL*\n"
            f"{'='*25}\n"
            f"*{pair}* | *LONG* | {leverage}x\n"
            f"{'='*25}\n\n"
            f"*Entry:* `{rate:.2f}` USDT\n"
            f"*Stop Loss:* `{sl_price:.2f}` ({self.stoploss*100:+.1f}%)\n\n"
            f"*Targets:*\n"
            f"  TP1: `{tp1_price:.2f}` (+3%) — 40%\n"
            f"  TP2: `{tp2_price:.2f}` (+5%) — 35%\n"
            f"  TP3: `{tp3_price:.2f}` (+10%) — 25%\n\n"
            f"*Индикаторы:*\n"
            f"  RSI: {rsi_val:.1f} | ADX: {adx_val:.1f} | Vol: {vol_ratio:.2f}x\n\n"
            f"*Причина:* {reason}\n"
            f"{'='*25}\n"
            f"_TrendRider Algo | Bybit Futures_"
        )

        self.dp.send_msg(msg, always_send=True)
        return True

    def confirm_trade_exit(self, pair: str, trade, order_type: str, amount: float,
                          rate: float, time_in_force: str, exit_reason: str,
                          current_time: datetime, **kwargs) -> bool:
        # Calculate results
        profit_pct = ((rate - trade.open_rate) / trade.open_rate) * 100 * trade.leverage
        duration_hours = (current_time - trade.open_date_utc).total_seconds() / 3600

        # Exit reason mapping
        exit_reasons = {
            "roi": "ROI target reached",
            "stop_loss": "Stop Loss hit",
            "trailing_stop_loss": "Trailing Stop",
            "exit_signal": "Exit signal",
            "rsi_overbought": "RSI overbought (>81)",
            "ema_bearish_cross": "EMA bearish crossover",
            "trend_broken": "Trend broken (below EMA200)",
            "force_exit": "Force exit",
        }
        reason_text = exit_reasons.get(exit_reason, exit_reason)

        # Result emoji
        if profit_pct > 0:
            emoji = "+" if profit_pct < 3 else "++"
            result_line = f"+{profit_pct:.2f}%"
        else:
            emoji = "-"
            result_line = f"{profit_pct:.2f}%"

        # Duration formatting
        if duration_hours < 1:
            dur_str = f"{int(duration_hours * 60)}m"
        elif duration_hours < 24:
            dur_str = f"{duration_hours:.1f}h"
        else:
            dur_str = f"{duration_hours/24:.1f}d"

        msg = (
            f"*TRADE CLOSED* {'✅' if profit_pct > 0 else '❌'}\n"
            f"{'='*25}\n"
            f"*{pair}* | LONG | {trade.leverage}x\n"
            f"{'='*25}\n\n"
            f"*Entry:* `{trade.open_rate:.2f}`\n"
            f"*Exit:* `{rate:.2f}`\n"
            f"*Result:* *{result_line}*\n"
            f"*Duration:* {dur_str}\n"
            f"*Reason:* {reason_text}\n"
            f"*Max price:* `{trade.max_rate:.2f}`\n"
            f"{'='*25}\n"
            f"_TrendRider Algo | Bybit Futures_"
        )

        self.dp.send_msg(msg, always_send=True)
        return True
