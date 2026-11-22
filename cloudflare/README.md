# BLACKOP Telegram webhook — deployed on Cloudflare Workers

Worker name: `blackop-telegram`

Live endpoint:
`https://blackop-telegram.anticop-blackop.workers.dev`

This Worker is deployed to the account's `workers.dev` subdomain. It is a Telegram webhook receiver, separate from the Python signal scheduler in GitHub Actions.

## Commands implemented

- `/start` — personalized welcome and ANTICOP attribution
- `/help` — command guide
- `/gold` — honest XAUUSD feed status (the current Alpha Vantage FX_DAILY integration is not valid for gold)
- `/signals` — scheduled signal service status
- `/status` — service status
- `/performance` — does not invent performance metrics
- `/risk` — risk disclaimer

The Worker is deployed, but Telegram commands are **not active until secrets are configured and the webhook is registered**.

## Required secrets

In Cloudflare Dashboard → Workers & Pages → `blackop-telegram` → Settings → Variables and Secrets, add these as encrypted **Secrets**:

1. `TELEGRAM_BOT_TOKEN` — the existing token from @BotFather.
2. `TELEGRAM_WEBHOOK_SECRET` — a strong random value containing 1–256 characters from Telegram's allowed set (A-Z, a-z, 0-9, underscore, hyphen). Use the exact same value as the GitHub Actions repository secret below.

Do not paste either secret into GitHub source files, commits, chat, or screenshots.

## Register the Telegram webhook safely

The repository includes a manual GitHub Actions workflow at `.github/workflows/set-telegram-webhook.yml`.

In GitHub → Settings → Secrets and variables → Actions, add:

- `TELEGRAM_WEBHOOK_SECRET` — the same value configured in Cloudflare.

The existing scheduled workflow already references `TELEGRAM_BOT_TOKEN`. Then open Actions → **Register BLACKOP Telegram webhook** → Run workflow.

The workflow calls Telegram's `setWebhook` endpoint using the Worker URL and secret. Check the action log for Telegram's `ok: true` response. Then send `/start` to BLACKOP.

## Important

- Telegram webhooks and long polling (`getUpdates`) cannot run simultaneously. Do not start a second polling process.
- Existing GitHub Actions scheduled alerts can continue sending messages using the bot token; sending messages is separate from receiving updates.
- This Worker does not host MT5 or execute trades.
- The Worker does not yet have a validated XAUUSD price feed or verified performance reporting.
- Never claim trading profitability or certification without evidence.
