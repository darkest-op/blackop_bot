# BLACKOP Telegram webhook (Cloudflare Workers)

This is a lightweight webhook receiver for interactive Telegram commands. It is separate from the Python signal scheduler in GitHub Actions.

## What it currently does

- Responds to /start with a personalized welcome and ANTICOP attribution.
- Responds to /help, /gold, /signals, /status, /performance, and /risk.
- Explicitly reports that XAUUSD data is unavailable until a valid feed is integrated.
- Does not claim to execute trades or fabricate performance.
- Validates Telegram's webhook secret header.

## Free deployment

Cloudflare Workers currently has a Free plan. Check current limits before deployment:
https://developers.cloudflare.com/workers/platform/limits/

1. Sign in to Cloudflare and open Workers & Pages.
2. Create a Worker and paste the contents of `worker.js`.
3. In Worker Settings → Variables and Secrets, add these as **Secrets**:
   - `TELEGRAM_BOT_TOKEN`: the existing BLACKOP BotFather token.
   - `TELEGRAM_WEBHOOK_SECRET`: a newly generated random string using only letters, digits, underscores or hyphens.
4. Deploy. Copy the HTTPS Worker URL.
5. Set Telegram's webhook using the Bot API `setWebhook` method, with:
   - `url`: the Worker URL
   - `secret_token`: the exact same value as `TELEGRAM_WEBHOOK_SECRET`
   - `allowed_updates`: `["message"]`
6. Check the webhook with Telegram's `getWebhookInfo` method.
7. Send /start to BLACKOP and verify the welcome reply.

**Security:** Never put the bot token or webhook secret in this repository, screenshots, or chat messages. Add them only in Cloudflare's encrypted Secret fields. If the bot token has ever been exposed, revoke it through @BotFather and replace the stored secret.

## Important integration notes

- Telegram webhook delivery and long polling cannot be active simultaneously. This Worker uses webhooks.
- GitHub Actions scheduled alerts can continue sending messages with the same bot token; sending messages does not require polling.
- Do not run another getUpdates polling process for this bot after setting the webhook.
- The Worker is a command receiver, not an MT5 host. It cannot run the MQL5 Expert Advisor or execute broker trades.
- Current command responses are intentionally transparent placeholders for features that are not yet connected to validated data or execution.
- Do not claim that BLACKOP is a "trusted" or certified cybersecurity company unless ANTICOP has substantiation for that claim. The welcome copy describes ANTICOP as a cybersecurity company without claiming external certification.

## Telegram Bot API

https://core.telegram.org/bots/api#setwebhook
