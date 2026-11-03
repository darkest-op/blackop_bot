"""
Persistent trade tracking: every BUY/SELL signal alert.py sends gets logged
as "open" here. On each run, before generating new signals, this checks
whether any open trade has since hit its stop-loss or take-profit (using
real candle data since the entry time) and reports the result.

Storage: a JSON file (trades.json) living next to this script. GitHub
Actions runners are thrown away after each run, so the workflow must
commit this file back to the repo for the next run to see it -- see the
"Commit updated trade log" step in .github/workflows/signals.yml.
"""

import json
import os
from datetime import datetime, timezone

LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trades.json")


def load_trades() -> dict:
    if not os.path.exists(LOG_PATH):
        return {"open": [], "closed": []}
    with open(LOG_PATH) as f:
        return json.load(f)


def save_trades(data: dict):
    with open(LOG_PATH, "w") as f:
        json.dump(data, f, indent=2, default=str)


def log_new_trade(data: dict, pair: str, timeframe: str, direction: str,
                   entry: float, stop_loss: float, take_profit: float):
    data["open"].append({
        "pair": pair,
        "timeframe": timeframe,
        "direction": direction,
        "entry": entry,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "opened_at": datetime.now(timezone.utc).isoformat(),
    })


def check_trade_outcome(trade: dict, candles_since_entry) -> str | None:
    """
    candles_since_entry: a DataFrame (high, low columns) of candles that
    happened at or after the trade was opened. Returns 'WIN', 'LOSS', or
    None if still open. If both SL and TP were touched within the same
    unresolved window, this conservatively assumes LOSS first (we can't
    know which happened first from daily/hourly candle data alone).
    """
    if candles_since_entry.empty:
        return None

    direction = trade["direction"]
    sl = trade["stop_loss"]
    tp = trade["take_profit"]

    for _, candle in candles_since_entry.iterrows():
        if direction == "BUY":
            hit_sl = candle["low"] <= sl
            hit_tp = candle["high"] >= tp
        else:  # SELL
            hit_sl = candle["high"] >= sl
            hit_tp = candle["low"] <= tp

        if hit_sl:
            return "LOSS"
        if hit_tp:
            return "WIN"
    return None


def close_trade(data: dict, trade: dict, result: str):
    trade["result"] = result
    trade["closed_at"] = datetime.now(timezone.utc).isoformat()
    data["open"].remove(trade)
    data["closed"].append(trade)


def tracked_win_rate(data: dict) -> tuple[int, int, float]:
    """Real tracked performance from actual signals this bot has sent (not a backtest)."""
    closed = data["closed"]
    wins = sum(1 for t in closed if t.get("result") == "WIN")
    losses = sum(1 for t in closed if t.get("result") == "LOSS")
    total = wins + losses
    rate = (wins / total * 100) if total else 0.0
    return wins, losses, rate
