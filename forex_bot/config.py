"""Configuration for the forex trading bot. Keep API keys in environment variables."""
import os
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
WATCHLIST = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
EMA_FAST = 12
EMA_SLOW = 26
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
ATR_PERIOD = 14
ATR_SL_MULTIPLIER = 1.5
ATR_TP_MULTIPLIER = 3.0
if not TELEGRAM_BOT_TOKEN:
    print("[WARN] TELEGRAM_BOT_TOKEN not set. Export it before running bot.py.")
if not ALPHA_VANTAGE_API_KEY:
    print("[WARN] ALPHA_VANTAGE_API_KEY not set. Export it before running bot.py.")
