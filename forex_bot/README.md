# Forex Signal Bot

Telegram forex signal bot using Alpha Vantage market data. It supports interactive Telegram commands and scheduled push alerts through GitHub Actions.

## Scheduled alerts (free GitHub Actions)

1. Create a Telegram bot with @BotFather and copy its token.
2. Get your Telegram chat ID by messaging your bot, then checking the Telegram Bot API getUpdates endpoint.
3. Get a free Alpha Vantage API key from https://www.alphavantage.co/support/#api-key.
4. In GitHub, open **Settings → Secrets and variables → Actions** and add:
   - TELEGRAM_BOT_TOKEN
   - TELEGRAM_CHAT_ID
   - ALPHA_VANTAGE_API_KEY
5. The workflow runs at 7am, 11am, 4pm and 9pm Rwanda time (UTC+2). You can also run it manually from the Actions tab.

## Interactive Telegram bot

Install dependencies with `pip install -r requirements.txt`, set TELEGRAM_BOT_TOKEN and ALPHA_VANTAGE_API_KEY as environment variables, then run `python3 bot.py`. The interactive bot needs an always-on host.

Commands: `/start`, `/signal EURUSD`, `/signal EURUSD 15min`, `/scan`, `/backtest EURUSD`, `/backtest EURUSD full`.

## Strategy

EMA(12)/EMA(26) crossover with an RSI filter; ATR-based stop loss and take profit. Backtest and paper-trade before risking real money. This is a decision-support tool, not financial advice.
