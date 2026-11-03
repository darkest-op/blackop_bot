"""
Push-only alert script: for each pair in WATCHLIST and each timeframe in
config.AUTO_TIMEFRAMES, fetches real candles, generates a signal, renders
a chart of the setup, and sends it to Telegram as a photo with a caption.

No server, no polling -- meant to run on a timer (see
.github/workflows/signals.yml) or be triggered manually.
"""

import os
import tempfile
import requests
import config
from data_fetcher import get_candles, rate_limit_pause
from indicators import add_all_indicators
from strategy import generate_signal
from backtester import run_backtest
from risk import format_position_line
import trade_log

TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def _decimals_for(pair: str) -> int:
    return 2 if "XAU" in pair.upper() else 5


def format_caption(pair: str, timeframe_label: str, sig, backtest_note: str, position_line: str = "", tracked_note: str = "") -> str:
    dp = _decimals_for(pair)

    if sig.action == "HOLD":
        return (
            f"📊 {pair} ({timeframe_label}): HOLD\n"
            f"Price: {sig.price:.{dp}f} | RSI: {sig.rsi:.1f}\n"
            f"{sig.reason}"
        )

    emoji = "🟢" if sig.action == "BUY" else "🔴"
    pip_size = 0.01 if "XAU" in pair.upper() or "JPY" in pair.upper() else 0.0001
    target_pips = abs(sig.take_profit - sig.price) / pip_size
    risk_pips = abs(sig.price - sig.stop_loss) / pip_size
    pip_label = "points" if "XAU" in pair.upper() else "pips"  # gold moves are usually quoted as $ or "points", not classic pips

    header = (
        f"{emoji} {pair} ({timeframe_label}): {sig.action}\n"
        f"Entry: {sig.price:.{dp}f}\n"
        f"Stop loss: {sig.stop_loss:.{dp}f} (risking ~{risk_pips:.0f} {pip_label})\n"
        f"Take profit: {sig.take_profit:.{dp}f} (targeting ~{target_pips:.0f} {pip_label})\n"
        f"RSI: {sig.rsi:.1f}\n"
        f"Reason: {sig.reason}"
    )
    blocks = [header]
    if position_line:
        blocks.append(position_line)
    blocks.append(backtest_note)
    if tracked_note:
        blocks.append(tracked_note)
    blocks.append("⚠️ Not financial advice -- backtested stats are historical, not a guarantee.")
    return "\n\n".join(blocks)


def format_outcome_message(trade: dict, pip_result: float) -> str:
    dp = _decimals_for(trade["pair"])
    pip_label = "points" if "XAU" in trade["pair"].upper() else "pips"

    if trade["result"] == "WIN":
        return (
            f"🎉👏 Trade closed: {trade['pair']} ({trade['timeframe']}) {trade['direction']}\n"
            f"Today's trade was successful — we hit the target!\n"
            f"Entry {trade['entry']:.{dp}f} → Take profit {trade['take_profit']:.{dp}f} "
            f"(+{abs(pip_result):.0f} {pip_label})"
        )
    else:
        return (
            f"😞 Trade closed: {trade['pair']} ({trade['timeframe']}) {trade['direction']}\n"
            f"Sorry for the loss — the stop loss was hit this time.\n"
            f"Entry {trade['entry']:.{dp}f} → Stop loss {trade['stop_loss']:.{dp}f} "
            f"(-{abs(pip_result):.0f} {pip_label})\n\n"
            f"The stop loss did its job and kept the loss small and controlled — that's what "
            f"it's there for. No strategy wins every trade; what matters is the track record "
            f"over many trades, not any single one."
        )


def get_tracked_note(trades_data: dict) -> str:
    """Real performance from this bot's actual signal history (not a backtest)."""
    wins, losses, rate = trade_log.tracked_win_rate(trades_data)
    total = wins + losses
    if total == 0:
        return "📒 Live tracked record: no closed trades yet -- this bot logs and follows up on every signal it sends."
    return f"📒 Live tracked record (actual signals sent so far): {wins}W/{losses}L ({rate:.0f}%)."


def get_backtest_note(df, pair: str) -> str:
    """Honest historical context -- NOT a per-trade probability claim."""
    try:
        result = run_backtest(df, pair=pair)
        if result.total_trades == 0:
            return "📈 Track record: not enough recent signals in this window to measure reliably."
        return (
            f"📈 Track record on this pair/timeframe (last {result.total_trades} signals): "
            f"{result.wins}W/{result.losses}L ({result.win_rate:.0f}% win rate), "
            f"net {result.total_pips:+.0f} pips."
        )
    except Exception:
        return "📈 Track record: unavailable this run."


def send_telegram_message(text: str):
    if not config.TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must both be set")
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=15)
    resp.raise_for_status()


def send_telegram_photo(photo_path: str, caption: str):
    if not config.TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must both be set")
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as f:
        resp = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024]},  # Telegram caption limit
            files={"photo": f},
            timeout=30,
        )
    resp.raise_for_status()


def _pip_size(pair: str) -> float:
    return 0.01 if "XAU" in pair.upper() or "JPY" in pair.upper() else 0.0001


def check_open_trades(trades_data: dict, interval_map: dict):
    """Checks every open logged trade against real candles since it was opened,
    and sends a result message (win/loss) the moment one resolves."""
    import pandas as pd

    df_cache = {}
    for trade in list(trades_data["open"]):
        key = (trade["pair"], trade["timeframe"])
        if key not in df_cache:
            try:
                df_cache[key] = get_candles(trade["pair"], interval_map.get(trade["timeframe"]))
            except Exception as e:
                print(f"Could not fetch candles to check {key}: {e}")
                continue
        df = df_cache[key]

        # Timestamps from different sources aren't perfectly timezone-aligned --
        # this comparison is approximate, good enough for daily/hourly checks.
        entry_time = pd.to_datetime(trade["opened_at"]).tz_localize(None)
        candles_since = df[df.index >= entry_time]

        result = trade_log.check_trade_outcome(trade, candles_since)
        if result:
            pip_size = _pip_size(trade["pair"])
            if result == "WIN":
                pip_result = abs(trade["take_profit"] - trade["entry"]) / pip_size
            else:
                pip_result = abs(trade["entry"] - trade["stop_loss"]) / pip_size

            trade_log.close_trade(trades_data, trade, result)
            msg = format_outcome_message(trade, pip_result)
            try:
                send_telegram_message(msg)
            except Exception as e:
                print(f"Failed to send outcome message: {e}")
            print(f"Closed trade: {trade}\n{msg}\n")


def process_one(pair: str, timeframe_label: str, interval, tmpdir: str, trades_data: dict):
    from chart import render_setup_chart  # imported here so this file still works without matplotlib for quick tests

    df = get_candles(pair, interval)
    ind_df = add_all_indicators(
        df, config.EMA_FAST, config.EMA_SLOW, config.RSI_PERIOD, config.ATR_PERIOD
    ).dropna()
    sig = generate_signal(ind_df)
    backtest_note = get_backtest_note(df, pair)
    tracked_note = get_tracked_note(trades_data)

    position_line = ""
    if sig.action in ("BUY", "SELL"):
        risk_pips = abs(sig.price - sig.stop_loss) / _pip_size(pair)
        if config.ACCOUNT_CAPITAL > 0:
            position_line = format_position_line(config.ACCOUNT_CAPITAL, config.RISK_PERCENT, risk_pips, pair)
        else:
            position_line = (
                "💰 Position size: set the ACCOUNT_CAPITAL secret (your account balance) "
                "to get a suggested position size for this trade."
            )
        trade_log.log_new_trade(trades_data, pair, timeframe_label, sig.action, sig.price, sig.stop_loss, sig.take_profit)

    caption = format_caption(pair, timeframe_label, sig, backtest_note, position_line, tracked_note)

    chart_path = os.path.join(tmpdir, f"{pair}_{timeframe_label}.png")
    render_setup_chart(ind_df, pair, timeframe_label, sig, chart_path)
    send_telegram_photo(chart_path, caption)
    print(f"Sent {pair} {timeframe_label}:\n{caption}\n")


def main():
    trades_data = trade_log.load_trades()
    interval_map = dict(config.AUTO_TIMEFRAMES)
    interval_map.update(dict(config.MANUAL_TIMEFRAMES))

    check_open_trades(trades_data, interval_map)

    combos = [(pair, label, interval) for pair in config.WATCHLIST for label, interval in config.AUTO_TIMEFRAMES]
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, (pair, timeframe_label, interval) in enumerate(combos):
            try:
                process_one(pair, timeframe_label, interval, tmpdir, trades_data)
            except Exception as e:
                try:
                    send_telegram_message(f"{pair} ({timeframe_label}): error ({e})")
                except Exception:
                    print(f"Error on {pair} {timeframe_label}: {e} (and failed to notify Telegram)")
            if i < len(combos) - 1:
                rate_limit_pause()  # stay under Alpha Vantage's 5-requests/minute free-tier limit

    trade_log.save_trades(trades_data)


if __name__ == "__main__":
    main()
