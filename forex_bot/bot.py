"""
Telegram bot entry point.
Commands: /start, /signal EURUSD [15min|30min|60min], /scan, /backtest EURUSD [full]
"""
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import config
from data_fetcher import get_daily_candles, get_intraday_candles, rate_limit_pause
from indicators import add_all_indicators
from strategy import generate_signal
from backtester import run_backtest

def format_signal(pair: str, sig) -> str:
    if sig.action == "HOLD":
        return f"📊 {pair}: HOLD\nPrice: {sig.price:.5f} | RSI: {sig.rsi:.1f}\n{sig.reason}"
    emoji = "🟢" if sig.action == "BUY" else "🔴"
    return (f"{emoji} {pair}: {sig.action}\nEntry: {sig.price:.5f}\n"
            f"Stop loss: {sig.stop_loss:.5f}\nTake profit: {sig.take_profit:.5f}\n"
            f"RSI: {sig.rsi:.1f}\nReason: {sig.reason}\n\n"
            "⚠️ Not financial advice -- verify before trading real funds.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Forex signal bot online.\n\n/signal EURUSD - current signal\n"
        "/signal EURUSD 15min - intraday signal\n/scan - scan your watchlist\n"
        "/backtest EURUSD - backtest recent history\n")

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /signal EURUSD [15min|30min|60min]")
        return
    pair = context.args[0].upper()
    interval = context.args[1] if len(context.args) > 1 else None
    await update.message.reply_text(f"Fetching {pair}...")
    try:
        df = get_intraday_candles(pair, interval) if interval else get_daily_candles(pair)
        df = add_all_indicators(df, config.EMA_FAST, config.EMA_SLOW, config.RSI_PERIOD, config.ATR_PERIOD).dropna()
        await update.message.reply_text(format_signal(pair, generate_signal(df)))
    except Exception as e:
        await update.message.reply_text(f"Error fetching {pair}: {e}")

async def scan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Scanning watchlist: {', '.join(config.WATCHLIST)}...")
    results = []
    for i, pair in enumerate(config.WATCHLIST):
        try:
            df = get_daily_candles(pair)
            df = add_all_indicators(df, config.EMA_FAST, config.EMA_SLOW, config.RSI_PERIOD, config.ATR_PERIOD).dropna()
            results.append(format_signal(pair, generate_signal(df)))
        except Exception as e:
            results.append(f"{pair}: error ({e})")
        if i < len(config.WATCHLIST) - 1: rate_limit_pause()
    await update.message.reply_text("\n\n".join(results))

async def backtest_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /backtest EURUSD [full]")
        return
    pair = context.args[0].upper()
    outputsize = "full" if len(context.args) > 1 and context.args[1].lower() == "full" else "compact"
    await update.message.reply_text(f"Backtesting {pair} ({outputsize} history)... this may take a moment.")
    try:
        result = run_backtest(get_daily_candles(pair, outputsize=outputsize), pair=pair)
        await update.message.reply_text(f"📈 Backtest results for {pair}\n\n{result.summary()}")
    except Exception as e:
        await update.message.reply_text(f"Error backtesting {pair}: {e}")

def main():
    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal_cmd))
    app.add_handler(CommandHandler("scan", scan_cmd))
    app.add_handler(CommandHandler("backtest", backtest_cmd))
    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
