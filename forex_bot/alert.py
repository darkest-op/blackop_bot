"""
Push-only alert script: scans the WATCHLIST, generates signals, and sends
them to your Telegram chat via a single HTTP request. No server, no
polling, no 24/7 process needed -- this is meant to be run on a timer
(see .github/workflows/signals.yml) instead of as a long-running bot.
"""
import os
import requests
import config
from data_fetcher import get_daily_candles, rate_limit_pause
from indicators import add_all_indicators
from strategy import generate_signal

TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def format_signal(pair: str, sig) -> str:
    if sig.action == "HOLD":
        return f"📊 {pair}: HOLD (price {sig.price:.5f}, RSI {sig.rsi:.1f})"
    emoji = "🟢" if sig.action == "BUY" else "🔴"
    return (
        f"{emoji} {pair}: {sig.action}\n"
        f"Entry: {sig.price:.5f} | SL: {sig.stop_loss:.5f} | TP: {sig.take_profit:.5f}\n"
        f"RSI: {sig.rsi:.1f} -- {sig.reason}"
    )

def send_telegram_message(text: str):
    if not config.TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must both be set")
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text}, timeout=15)
    resp.raise_for_status()

def main():
    lines = ["📈 Forex signal check"]
    for i, pair in enumerate(config.WATCHLIST):
        try:
            df = get_daily_candles(pair)
            df = add_all_indicators(df, config.EMA_FAST, config.EMA_SLOW, config.RSI_PERIOD, config.ATR_PERIOD).dropna()
            sig = generate_signal(df)
            lines.append(format_signal(pair, sig))
        except Exception as e:
            lines.append(f"{pair}: error ({e})")
        if i < len(config.WATCHLIST) - 1:
            rate_limit_pause()
    message = "\n\n".join(lines)
    send_telegram_message(message)
    print("Sent:\n", message)

if __name__ == "__main__":
    main()
