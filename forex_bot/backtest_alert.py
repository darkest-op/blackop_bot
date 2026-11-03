"""
Push-only backtest script: runs the strategy's backtest on every pair in
WATCHLIST and sends a results summary to Telegram. Same no-server pattern
as alert.py -- trigger it manually from the GitHub Actions tab whenever
you want a fresh read on how the strategy's been performing.
"""

import config
from data_fetcher import get_daily_candles, rate_limit_pause
from backtester import run_backtest
from alert import send_telegram_message  # reuse the same Telegram sender


def main():
    lines = ["📊 Strategy backtest (last ~100 daily candles per pair)"]
    for i, pair in enumerate(config.WATCHLIST):
        try:
            df = get_daily_candles(pair)
            result = run_backtest(df, pair=pair)
            lines.append(f"— {pair} —\n{result.summary()}")
        except Exception as e:
            lines.append(f"{pair}: error ({e})")
        if i < len(config.WATCHLIST) - 1:
            rate_limit_pause()  # stay under Alpha Vantage's free-tier rate limit

    lines.append("\n⚠️ Backtest results don't guarantee future performance.")
    message = "\n\n".join(lines)
    send_telegram_message(message)
    print("Sent:\n", message)


if __name__ == "__main__":
    main()
