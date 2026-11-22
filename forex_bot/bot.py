"""
BLACKOP Telegram bot entry point.

Interactive commands:
  /start                 - branded welcome and feature overview
  /help                  - command guide
  /signal EURUSD         - current daily signal
  /signal EURUSD 15min   - current intraday signal
  /scan                  - scan configured watchlist
  /backtest EURUSD       - backtest recent daily history
  /risk                  - explain current risk settings

Run with TELEGRAM_BOT_TOKEN and ALPHA_VANTAGE_API_KEY set.
This polling process must remain running to receive commands.
"""

from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import config
from data_fetcher import get_daily_candles, get_intraday_candles, rate_limit_pause
from indicators import add_all_indicators
from strategy import generate_signal
from backtester import run_backtest


WELCOME_TEXT = """👋 Welcome to BLACKOP!

Your market research and trading-support assistant.

📊 WHAT BLACKOP OFFERS
• Forex market signal analysis
• BUY / SELL / HOLD research signals
• Entry, stop-loss and take-profit levels
• Technical indicators and market commentary
• Watchlist scanning
• Historical strategy backtesting
• Risk-management guidance
• Scheduled market updates

🤖 AVAILABLE COMMANDS
/signal EURUSD — get a daily signal
/signal EURUSD 15min — get an intraday signal
/scan — scan the configured watchlist
/backtest EURUSD — review historical strategy results
/risk — view risk-management settings
/help — see the command guide

🥇 GOLD (XAUUSD)
Gold data support is being upgraded. Some gold requests may be unavailable until the dedicated data feed is connected.

🛡️ A PRODUCT OF ANTICOP
A trusted cybersecurity company focused on building practical technology and digital-security solutions.

⚠️ IMPORTANT
BLACKOP provides informational research, not guaranteed trading outcomes or financial advice. Signals can be wrong. Always verify prices, spreads, contract sizes and risk with your broker before placing a trade.

Let's analyse the markets responsibly. 🚀
"""


def format_signal(pair: str, sig) -> str:
    dp = 2 if "XAU" in pair.upper() else 5
    if sig.action == "HOLD":
        return f"📊 {pair}: HOLD\nPrice: {sig.price:.{dp}f} | RSI: {sig.rsi:.1f}\n{sig.reason}"

    emoji = "🟢" if sig.action == "BUY" else "🔴"
    return (
        f"{emoji} {pair}: {sig.action}\n"
        f"Entry: {sig.price:.{dp}f}\n"
        f"Stop loss: {sig.stop_loss:.{dp}f}\n"
        f"Take profit: {sig.take_profit:.{dp}f}\n"
        f"RSI: {sig.rsi:.1f}\n"
        f"Reason: {sig.reason}\n\n"
        f"⚠️ Informational research only. Verify before trading."
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    first_name = update.effective_user.first_name if update.effective_user else None
    greeting = f"Hello, {first_name}! 👋\n\n" if first_name else ""
    await update.effective_message.reply_text(greeting + WELCOME_TEXT)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🧭 BLACKOP COMMAND GUIDE\n\n"
        "/start — welcome and feature overview\n"
        "/help — this guide\n"
        "/signal EURUSD — daily signal\n"
        "/signal EURUSD 15min — 15-minute signal\n"
        "/scan — scan the configured watchlist\n"
        "/backtest EURUSD — backtest recent history\n"
        "/risk — risk settings and safety notes\n\n"
        "Use /start at any time to see what BLACKOP offers."
    )


async def risk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    capital_status = (
        f"Configured reference capital: {config.ACCOUNT_CAPITAL:.2f}"
        if config.ACCOUNT_CAPITAL > 0
        else "Reference capital: not configured"
    )
    await update.effective_message.reply_text(
        "🛡️ BLACKOP RISK SETTINGS\n\n"
        f"Configured risk per signal: {config.RISK_PERCENT:.2f}%\n"
        f"{capital_status}\n\n"
        "Position-size estimates are approximate and must be checked against "
        "your broker's contract specifications, minimum volume, spread and fees. "
        "BLACKOP does not place trades or guarantee that a suggested size limits "
        "actual loss to the stated percentage."
    )


async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage: /signal EURUSD [15min|30min|60min]")
        return

    pair = context.args[0].upper()
    interval = context.args[1] if len(context.args) > 1 else None

    await update.effective_message.reply_text(f"Fetching {pair}...")
    try:
        df = get_intraday_candles(pair, interval) if interval else get_daily_candles(pair)
        df = add_all_indicators(
            df, config.EMA_FAST, config.EMA_SLOW, config.RSI_PERIOD, config.ATR_PERIOD
        ).dropna()
        sig = generate_signal(df)
        await update.effective_message.reply_text(format_signal(pair, sig))
    except Exception as e:
        await update.effective_message.reply_text(
            f"Unable to analyse {pair}: {e}\nPlease try again later."
        )


async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        f"Scanning watchlist: {', '.join(config.WATCHLIST)}..."
    )
    results = []
    for i, pair in enumerate(config.WATCHLIST):
        try:
            df = get_daily_candles(pair)
            df = add_all_indicators(
                df, config.EMA_FAST, config.EMA_SLOW, config.RSI_PERIOD, config.ATR_PERIOD
            ).dropna()
            sig = generate_signal(df)
            results.append(format_signal(pair, sig))
        except Exception as e:
            results.append(f"{pair}: data unavailable ({e})")
        if i < len(config.WATCHLIST) - 1:
            rate_limit_pause()

    await update.effective_message.reply_text("\n\n".join(results))


async def backtest_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage: /backtest EURUSD [full]")
        return

    pair = context.args[0].upper()
    outputsize = (
        "full" if len(context.args) > 1 and context.args[1].lower() == "full"
        else "compact"
    )

    await update.effective_message.reply_text(
        f"Backtesting {pair} ({outputsize} history)... this may take a moment."
    )
    try:
        df = get_daily_candles(pair, outputsize=outputsize)
        result = run_backtest(df, pair=pair)
        await update.effective_message.reply_text(
            f"📈 Backtest results for {pair}\n\n{result.summary()}\n\n"
            "Historical results do not predict future performance."
        )
    except Exception as e:
        await update.effective_message.reply_text(f"Unable to backtest {pair}: {e}")


async def post_init(app):
    # Keep Telegram's command menu aligned with commands implemented here.
    await app.bot.set_my_commands([
        BotCommand("start", "Welcome and BLACKOP overview"),
        BotCommand("help", "Show available commands"),
        BotCommand("signal", "Get a market signal"),
        BotCommand("scan", "Scan the configured watchlist"),
        BotCommand("backtest", "Backtest a trading strategy"),
        BotCommand("risk", "View risk settings"),
    ])


def main():
    if not config.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("Set TELEGRAM_BOT_TOKEN before starting BLACKOP.")

    app = (
        ApplicationBuilder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("risk", risk_cmd))
    app.add_handler(CommandHandler("signal", signal_cmd))
    app.add_handler(CommandHandler("scan", scan_cmd))
    app.add_handler(CommandHandler("backtest", backtest_cmd))

    print("BLACKOP interactive bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
