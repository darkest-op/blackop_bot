"""
Configuration for the forex trading bot.

Set these as environment variables before running (never hardcode real keys
in source files, especially if you ever push this to GitHub):

    export TELEGRAM_BOT_TOKEN="123456:ABC-your-botfather-token"
    export ALPHA_VANTAGE_API_KEY="your-free-key-from-alphavantage.co"

Get a free Alpha Vantage key at: https://www.alphavantage.co/support/#api-key
"""

import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")

# Default pairs you can /scan without typing them out
WATCHLIST = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]

# Strategy parameters (tweak these to tune the system)
EMA_FAST = 12
EMA_SLOW = 26
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
ATR_PERIOD = 14
ATR_SL_MULTIPLIER = 1.5   # stop loss = entry -/+ (ATR * this)
ATR_TP_MULTIPLIER = 3.0   # take profit = entry -/+ (ATR * this) -> 2:1 reward/risk

if not TELEGRAM_BOT_TOKEN:
    print("[WARN] TELEGRAM_BOT_TOKEN not set. Export it before running bot.py.")
if not ALPHA_VANTAGE_API_KEY:
    print("[WARN] ALPHA_VANTAGE_API_KEY not set. Export it before running bot.py.")
