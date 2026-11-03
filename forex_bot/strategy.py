"""EMA crossover + RSI filter with ATR-based stop loss and take profit."""
from dataclasses import dataclass
import pandas as pd
import config
@dataclass
class Signal:
    action: str
    price: float
    stop_loss: float | None
    take_profit: float | None
    rsi: float
    reason: str
def generate_signal(df: pd.DataFrame) -> Signal:
    if len(df) < 2: raise ValueError("Need at least 2 candles to detect a crossover")
    prev, last = df.iloc[-2], df.iloc[-1]
    price, cur_atr, cur_rsi = last["close"], last["atr"], last["rsi"]
    crossed_up = prev["ema_fast"] <= prev["ema_slow"] and last["ema_fast"] > last["ema_slow"]
    crossed_down = prev["ema_fast"] >= prev["ema_slow"] and last["ema_fast"] < last["ema_slow"]
    if crossed_up and cur_rsi < config.RSI_OVERBOUGHT:
        sl, tp = price - cur_atr * config.ATR_SL_MULTIPLIER, price + cur_atr * config.ATR_TP_MULTIPLIER
        return Signal("BUY", price, sl, tp, cur_rsi, f"EMA{config.EMA_FAST} crossed above EMA{config.EMA_SLOW}, RSI {cur_rsi:.1f} not overbought")
    if crossed_down and cur_rsi > config.RSI_OVERSOLD:
        sl, tp = price + cur_atr * config.ATR_SL_MULTIPLIER, price - cur_atr * config.ATR_TP_MULTIPLIER
        return Signal("SELL", price, sl, tp, cur_rsi, f"EMA{config.EMA_FAST} crossed below EMA{config.EMA_SLOW}, RSI {cur_rsi:.1f} not oversold")
    return Signal("HOLD", price, None, None, cur_rsi, "No fresh crossover, or RSI filter blocked it")
