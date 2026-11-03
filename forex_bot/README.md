# Forex Signal Bot

Telegram bot that watches EUR/USD and Gold (XAU/USD), generates BUY/SELL
signals with stop-loss/take-profit, sends a chart screenshot of each setup,
and backtests the strategy -- using real market data from Alpha Vantage.

## Two ways to run this

**Option A: Free automatic alerts (recommended, zero cost, no card, no server)**
Uses GitHub Actions to run `alert.py` on a timer, 4x/day, and push signals
straight to your Telegram chat. No bot commands, no always-on process needed.
See "Free setup: GitHub Actions alerts" below.

**Option B: Interactive bot** (`/signal`, `/scan`, `/backtest` on demand)
Needs a server that stays on 24/7 (a paid VPS, or your own always-on
computer) because it listens for your messages in real time. See
"Interactive setup" below.

---

## Free setup: GitHub Actions alerts (Option A)

1. **Get a Telegram bot token**: message @BotFather on Telegram, `/newbot`.
2. **Get your chat ID** (so the bot knows where to send messages):
   - Send any message to your new bot first (e.g. "hi")
   - Then open this in a browser, with your real token pasted in:
     `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
   - Look for `"chat":{"id":123456789` — that number is your chat ID
3. **Get a free Alpha Vantage API key**: https://www.alphavantage.co/support/#api-key
4. **Push this whole folder to a GitHub repo** (see the step-by-step below
   if you haven't done this before).
5. In your GitHub repo: **Settings → Secrets and variables → Actions →
   New repository secret**, and add each one:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - `ALPHA_VANTAGE_API_KEY`
   - `ACCOUNT_CAPITAL` — your trading account balance as a plain number
     (e.g. `80`). Used for position-size suggestions. Optional — if you
     skip it, alerts still work, just without a sizing suggestion.
   - `RISK_PERCENT` — how much of your capital to risk per trade, as a
     number (e.g. `1` for 1%). Optional, defaults to 1% if you skip it.
6. That's it. The workflow in `.github/workflows/signals.yml` runs
   automatically at 7am, 11am, 4pm, and 9pm Rwanda time (edit the `cron`
   lines in that file to change the schedule — they're written in UTC,
   and Rwanda is UTC+2).
7. To test it immediately instead of waiting: go to the **Actions** tab
   in your repo → "Forex Signal Alerts" → **Run workflow**.

### What each alert looks like

Each pair/timeframe combo arrives as a **chart screenshot** (candles with
entry, stop-loss, and take-profit drawn as dashed lines) with a caption:
```
🟢 EURUSD (1h): BUY
Entry: 1.10500
Stop loss: 1.10300 (risking ~20 pips)
Take profit: 1.10900 (targeting ~40 pips)
RSI: 55.0
Reason: EMA12 crossed above EMA26, RSI 55.0 not overbought

💰 Position size (risking 1.0% of $80.00 = $0.80): ~0.004 lots (~400
units) (smaller than most brokers' minimum trade size -- consider a
cent/micro account, or risking a bit more than usual on this trade)
Assumes ~$10/pip per standard lot -- verify against your broker's actual
contract specs.

📈 Track record on this pair/timeframe (last 6 signals): 4W/2L (67% win
rate), net +120 pips.

📒 Live tracked record (actual signals sent so far): 3W/1L (75%).

⚠️ Not financial advice -- backtested stats are historical, not a guarantee.
```
Two different "track record" lines appear on purpose:
- **📈 Backtested** — recalculated fresh each time from ~100 days of
  historical candles for that pair/timeframe.
- **📒 Live tracked** — this bot's actual real-world signal history,
  pulled from `trades.json` (more below). Starts empty and builds up
  the longer you run it.

Neither is a prediction or a per-trade confidence score — both are
honest historical stats, and small sample sizes aren't statistically
reliable. Treat them as context, not a guarantee.

### Position sizing

If you've set `ACCOUNT_CAPITAL`, every BUY/SELL signal includes a
suggested position size so a stop-loss hit only costs a small, fixed
slice of your account (1% by default via `RISK_PERCENT`) — this matters
more for protecting your money than any signal logic does. **With a
small account (under ~$500), the suggested size will often come out
below most brokers' minimum trade size** — that's not a bug, it's an
honest reflection of the math, and it's worth paying attention to:
either use a cent/micro account that supports tiny sizes, or accept
you'll need to risk a bit more than 1% per trade, deliberately and
knowingly, not by accident.

### Win/loss result messages

Every BUY/SELL signal gets logged to `trades.json` in the repo. On each
future run, before sending new signals, the bot checks whether any open
trade has since hit its take-profit or stop-loss (using real candle data)
and sends a result message:
- 🎉👏 on a win — target hit
- 😞 on a loss — stop hit, with a short reminder that the stop did its
  job by keeping the loss small, and that one trade doesn't define the
  strategy's track record

**Honesty note on "learning from mistakes":** this bot logs every
outcome and shows you the real win rate it's built up (the "📒 Live
tracked record" line) — that's genuinely useful feedback. It does
*not* automatically retrain itself or rewrite its own strategy after a
loss — that's a much bigger project than what's built here, and I'd
rather tell you plainly than have the bot seem smarter than it is. If
the live tracked win rate drifts low over time, that's your signal to
come back and manually tighten `RSI_OVERBOUGHT`/`RSI_OVERSOLD` or the
ATR multipliers in `config.py`.

**Why `trades.json` needs to be committed back to the repo:** GitHub
Actions runners are thrown away after each run, so without saving this
file back to your repo, the bot would "forget" every open trade the
moment the run ends and could never check whether it won or lost. The
`signals.yml` workflow has a step that commits this file automatically
— you'll see small automatic commits appear in your repo's history
labeled "Update trade log [skip ci]". That's normal and expected.

### Timeframes

The scheduled alert checks **1h and 1day** automatically (2 pairs × 2
timeframes × 4 runs/day = 16 Alpha Vantage calls/day, safely under the
free tier's 25/day limit). **15-min** is available as a separate
manual-only workflow — **"15-Min Quick Scan"** in the Actions tab — so
checking it doesn't eat into your daily quota. 1-minute isn't included:
the free tier can't sustain checking it regularly without blowing through
the daily limit.

### Checking the strategy's track record

A second workflow, **"Forex Strategy Backtest"**, is manual-only (no
schedule) — trigger it from the Actions tab the same way, and it'll send
you a win-rate/net-pips summary for every pair in your watchlist, based
on the last ~100 days of real price data. Run it whenever you want a
fresh read before trusting the live signals with real trades.

## Interactive setup (Option B)

1. Same bot token + Alpha Vantage key as above.
2. Install dependencies: `pip install -r requirements.txt`
3. Set your keys as environment variables:
   ```
   export TELEGRAM_BOT_TOKEN="123456:your-token"
   export ALPHA_VANTAGE_API_KEY="your-key"
   ```
4. Run it: `python3 bot.py`
5. This process needs to stay running 24/7, so it needs a VPS or
   always-on machine — not iSH, not Netlify (see the project notes).

### Commands (Option B only)

- `/signal EURUSD` — current signal on daily candles
- `/signal EURUSD 15min` — current signal on 15-minute candles
- `/scan` — scans the WATCHLIST in `config.py`
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
- **Position sizing assumptions** (`risk.py`) use standard industry
  approximations for pip value ($10/pip per standard lot for forex,
  ~$1/point per standard lot for gold) — these vary by broker and
  account type. Always confirm your actual broker's contract specs
  before sizing a real position.
- **Trade outcome detection is approximate**: it checks candle highs/lows
  against SL/TP using the closest available timeframe data, and if a
  candle's range touches both levels, it conservatively assumes the loss
  happened first (daily/hourly candles can't show the exact order within
  that candle). Minor timestamp misalignment between data sources is
  possible too — treat the win/loss log as a close approximation, not a
  tick-perfect broker statement.
