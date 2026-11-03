"""
EMA-crossover + RSI-filter strategy.

Logic (deliberately simple and auditable rather than a black box):
  BUY  when ema_fast crosses above ema_slow AND rsi is not overbought
  SELL when ema_fast crosses below ema_slow AND rsi is not oversold
  otherwise HOLD

Stop loss / take profit are ATR-based, which scales them to each pair's
actual volatility instead of a fixed pip count:
  BUY:  SL = entry - ATR*mult,  TP = entry + ATR*mult*reward_ratio
  SELL: SL = entry + ATR*mult,  TP = entry - ATR*mult*reward_ratio

This is a starting point, not a guarantee of profitability -- backtest
and paper-trade before risking real money, and treat this as a decision-
support tool rather than financial advice.
"""

from dataclasses import dataclass
import pandas as pd
import config


@dataclass
class Signal:
    action: str          # "BUY", "SELL", "HOLD"
    price: float
    stop_loss: float | None
    take_profit: float | None
    rsi: float
    reason: str


def generate_signal(df: pd.DataFrame) -> Signal:
    """
    df must already have ema_fast, ema_slow, rsi, atr columns (see indicators.py)
    and at least 2 rows so we can detect a crossover on the latest candle.
    """
    if len(df) < 2:
        raise ValueError("Need at least 2 candles to detect a crossover")

    prev, last = df.iloc[-2], df.iloc[-1]
    price = last["close"]
    cur_atr = last["atr"]
    cur_rsi = last["rsi"]

    crossed_up = prev["ema_fast"] <= prev["ema_slow"] and last["ema_fast"] > last["ema_slow"]
    crossed_down = prev["ema_fast"] >= prev["ema_slow"] and last["ema_fast"] < last["ema_slow"]

    if crossed_up and cur_rsi < config.RSI_OVERBOUGHT:
        sl = price - cur_atr * config.ATR_SL_MULTIPLIER
        tp = price + cur_atr * config.ATR_TP_MULTIPLIER
        return Signal("BUY", price, sl, tp, cur_rsi,
                       f"EMA{config.EMA_FAST} crossed above EMA{config.EMA_SLOW}, RSI {cur_rsi:.1f} not overbought")

    if crossed_down and cur_rsi > config.RSI_OVERSOLD:
        sl = price + cur_atr * config.ATR_SL_MULTIPLIER
        tp = price - cur_atr * config.ATR_TP_MULTIPLIER
        return Signal("SELL", price, sl, tp, cur_rsi,
                       f"EMA{config.EMA_FAST} crossed below EMA{config.EMA_SLOW}, RSI {cur_rsi:.1f} not oversold")

    return Signal("HOLD", price, None, None, cur_rsi, "No fresh crossover, or RSI filter blocked it")
