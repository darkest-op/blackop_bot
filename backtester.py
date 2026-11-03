"""
Simple single-position backtester: walks forward candle by candle, opens a
trade on a BUY/SELL signal, and closes it when price hits the stop loss or
take profit (whichever comes first within the available data). No pyramiding,
no overlapping trades -- one open position at a time, which keeps the stats
easy to reason about.
"""

from dataclasses import dataclass, field
import pandas as pd
from indicators import add_all_indicators
from strategy import generate_signal
import config


@dataclass
class Trade:
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    entry_time: pd.Timestamp
    exit_price: float = None
    exit_time: pd.Timestamp = None
    result: str = None       # "WIN" / "LOSS"
    pips: float = None


@dataclass
class BacktestResult:
    trades: list = field(default_factory=list)

    @property
    def total_trades(self):
        return len(self.trades)

    @property
    def wins(self):
        return sum(1 for t in self.trades if t.result == "WIN")

    @property
    def losses(self):
        return sum(1 for t in self.trades if t.result == "LOSS")

    @property
    def win_rate(self):
        return (self.wins / self.total_trades * 100) if self.total_trades else 0.0

    @property
    def total_pips(self):
        return sum(t.pips for t in self.trades if t.pips is not None)

    def summary(self) -> str:
        if self.total_trades == 0:
            return "No trades were triggered in this period."
        return (
            f"Trades: {self.total_trades} | Wins: {self.wins} | Losses: {self.losses}\n"
            f"Win rate: {self.win_rate:.1f}%\n"
            f"Net pips: {self.total_pips:+.1f}"
        )


def _is_jpy_pair(pair: str) -> bool:
    return "JPY" in pair.upper()


def _pip_size(pair: str) -> float:
    pair = pair.upper()
    if "XAU" in pair:
        return 0.01  # gold: conventionally 1 pip = $0.01/oz (some brokers use 0.1 -- check yours)
    if "JPY" in pair:
        return 0.01
    return 0.0001


def run_backtest(raw_df: pd.DataFrame, pair: str = "EURUSD") -> BacktestResult:
    df = add_all_indicators(
        raw_df,
        ema_fast=config.EMA_FAST,
        ema_slow=config.EMA_SLOW,
        rsi_period=config.RSI_PERIOD,
        atr_period=config.ATR_PERIOD,
    ).dropna().reset_index()
    date_col = df.columns[0]

    pip_size = _pip_size(pair)

    result = BacktestResult()
    open_trade: Trade | None = None

    for i in range(2, len(df)):
        window = df.iloc[:i + 1]
        row = df.iloc[i]

        if open_trade is None:
            sig = generate_signal(window.set_index(date_col))
            if sig.action in ("BUY", "SELL"):
                open_trade = Trade(
                    direction=sig.action,
                    entry_price=sig.price,
                    stop_loss=sig.stop_loss,
                    take_profit=sig.take_profit,
                    entry_time=row[date_col],
                )
        else:
            # Check if this candle's high/low hit SL or TP
            if open_trade.direction == "BUY":
                hit_tp = row["high"] >= open_trade.take_profit
                hit_sl = row["low"] <= open_trade.stop_loss
            else:  # SELL
                hit_tp = row["low"] <= open_trade.take_profit
                hit_sl = row["high"] >= open_trade.stop_loss

            if hit_tp or hit_sl:
                # Conservative assumption: if both hit same candle, count as loss
                if hit_sl and hit_tp:
                    exit_price, outcome = open_trade.stop_loss, "LOSS"
                elif hit_tp:
                    exit_price, outcome = open_trade.take_profit, "WIN"
                else:
                    exit_price, outcome = open_trade.stop_loss, "LOSS"

                pips = (exit_price - open_trade.entry_price) / pip_size
                if open_trade.direction == "SELL":
                    pips = -pips

                open_trade.exit_price = exit_price
                open_trade.exit_time = row[date_col]
                open_trade.result = outcome
                open_trade.pips = pips
                result.trades.append(open_trade)
                open_trade = None

    return result
