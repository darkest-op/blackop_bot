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

# Your account capital, for risk-based position sizing (risk.py).
# Set as a GitHub secret named ACCOUNT_CAPITAL. Defaults to 0 (sizing
# disabled / shows a reminder to set it) if not provided.
ACCOUNT_CAPITAL = float(os.environ.get("ACCOUNT_CAPITAL", "0") or 0)

# How much of your capital to risk on any single trade. Kept conservative
# by default -- raise this only if you understand the tradeoff (bigger
# positions = bigger swings in both directions).
RISK_PERCENT = float(os.environ.get("RISK_PERCENT", "1.0") or 1.0)

# Focused watchlist: EUR/USD and Gold (XAU/USD). Alpha Vantage treats XAU
# as a physical currency code, so it works through the same FX endpoints.
WATCHLIST = ["EURUSD", "XAUUSD"]

# Timeframes checked automatically by the scheduled alert (alert.py).
# Kept to 2 to stay well under Alpha Vantage's 25-calls/day free limit:
# 2 pairs x 2 timeframes x 4 runs/day = 16 calls/day.
AUTO_TIMEFRAMES = [
    ("1h", "60min"),
    ("1day", None),  # None = use the daily endpoint, not intraday
]

# 15-min is available too, but only via the separate manual-trigger
# "15-min quick scan" workflow, to avoid blowing the daily call budget.
MANUAL_TIMEFRAMES = [("15min", "15min")]

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
