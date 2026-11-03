# Forex Signal Bot

Telegram bot that scans forex pairs, generates BUY/SELL signals with
stop-loss/take-profit, and backtests the strategy -- using real market data
from Alpha Vantage.

## Setup

1. **Get a Telegram bot token**: message @BotFather on Telegram, `/newbot`.
2. **Get a free Alpha Vantage API key**: https://www.alphavantage.co/support/#api-key
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
   (On iSH / mobile, you likely want this running on a VPS or always-on
   machine instead, since iSH suspends in the background.)
4. Set your keys as environment variables:
   ```
   export TELEGRAM_BOT_TOKEN="123456:your-token"
   export ALPHA_VANTAGE_API_KEY="your-key"
   ```
5. Run it:
   ```
   python3 bot.py
   ```

## Commands

- `/signal EURUSD` — current signal on daily candles
- `/signal EURUSD 15min` — current signal on 15-minute candles
- `/scan` — scans the WATCHLIST in `config.py` for fresh signals
- `/backtest EURUSD` — backtests the last ~100 daily candles
- `/backtest EURUSD full` — backtests full available history (slower)

## How the strategy works

- **Signal**: EMA(12) crosses EMA(26) = trend shift. RSI filters out
  signals when the market's already overbought/oversold in that direction.
- **Stop loss / take profit**: sized off ATR (volatility), not a fixed pip
  count, so they scale per-pair automatically. Default is a 2:1 reward-to-risk
  ratio (tune `ATR_SL_MULTIPLIER` / `ATR_TP_MULTIPLIER` in `config.py`).
- **Backtest**: walks forward candle by candle, opens one position at a
  time, closes on SL or TP, reports win rate and net pips.

## Known limitations / next steps

- Alpha Vantage free tier: 25 requests/day, 5/minute — `/scan` pauses
  between pairs to respect this. Upgrade to a paid key or switch to
  Twelve Data / OANDA's v20 API if you outgrow it.
- This is signal-only — it does not place trades. Hooking it up to a
  broker's API (e.g. OANDA v20, MetaTrader via MT bridge) for live
  execution is a natural next step once you've paper-traded it.
- The strategy here (EMA crossover + RSI) is intentionally simple and
  auditable. You'll likely want to backtest alternative strategies
  (e.g. adding a trend filter, multi-timeframe confirmation) before
  trusting it with real capital.
- **Not financial advice** — this is a decision-support tool. Backtest
  results don't guarantee future performance, and forex trading carries
  real risk of loss.
