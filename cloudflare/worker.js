/**
 * BLACKOP Telegram webhook — Cloudflare Workers Free
 *
 * Required Worker secrets:
 *   TELEGRAM_BOT_TOKEN
 *   TELEGRAM_WEBHOOK_SECRET
 *
 * Set Telegram's webhook URL to the deployed Worker URL and pass the same
 * TELEGRAM_WEBHOOK_SECRET as setWebhook's secret_token.
 */

const BRAND = "ANTICOP";

function commandOf(text = "") {
  return text.trim().split(/\s+/)[0].split("@")[0].toLowerCase();
}

function welcome(firstName = "") {
  const greeting = firstName ? `Hello, ${firstName}! 👋\n\n` : "Hello! 👋\n\n";
  return greeting + `Welcome to BLACKOP — your Forex market research assistant.

📊 WHAT BLACKOP OFFERS
• Forex market signal research
• BUY / SELL / HOLD analysis when market data is available
• Entry, stop-loss and take-profit estimates
• Technical-indicator commentary
• Scheduled market updates
• Historical strategy research and risk guidance

🤖 COMMANDS
/start — welcome and product overview
/help — command guide
/gold — gold (XAUUSD) data status
/signals — scheduled signal service status
/status — BLACKOP system status
/performance — performance-report status
/risk — risk and safety information

🛡️ A product of ANTICOP
A cybersecurity company focused on practical technology and digital-security solutions.

⚠️ BLACKOP provides informational market research, not financial advice or guaranteed results. It does not currently execute trades in your HFM or Weltrade accounts. Always verify prices, spreads, contract specifications and risk with your broker.

Trade carefully. Protect your capital.`;
}

function replyFor(text, firstName = "") {
  const cmd = commandOf(text);
  if (cmd === "/start") return welcome(firstName);
  if (cmd === "/help") return `🧭 BLACKOP COMMAND GUIDE

/start — product introduction
/help — show this guide
/gold — XAUUSD data-feed status
/signals — scheduled signal service status
/status — bot service status
/performance — performance-report status
/risk — risk and safety information

BLACKOP's scheduled alerts are handled separately by GitHub Actions. Interactive market analysis and broker execution are being developed.`;
  if (cmd === "/gold") return "🥇 GOLD (XAUUSD)\n\nThe current Alpha Vantage FX_DAILY integration does not provide valid XAUUSD candles. Gold analysis is temporarily unavailable while we connect and validate a dedicated gold data source. No guessed prices or signals will be sent.";
  if (cmd === "/signals") return "📡 SIGNAL SERVICE\n\nBLACKOP's scheduled signal workflow runs through GitHub Actions. This Telegram receiver handles interactive commands; it does not generate or execute trades itself.";
  if (cmd === "/status") return "🟢 BLACKOP TELEGRAM RECEIVER: online\n📡 Scheduled alerts: managed by GitHub Actions\n🥇 XAUUSD feed: under repair\n⚙️ Automatic broker execution: not connected";
  if (cmd === "/performance") return "📈 PERFORMANCE\n\nA verified performance report is not available through this command yet. We will not invent win rates or profits. Historical backtests and actual broker results must be reported separately.";
  if (cmd === "/risk") return "🛡️ RISK NOTICE\n\nBLACKOP is a research and signal tool, not a broker or financial adviser. Signals can be wrong. Stop-loss execution can slip, and minimum lot sizes, spread, commissions and leverage affect actual risk. Do not risk money you cannot afford to lose. BLACKOP does not currently place trades.";
  return "I didn't recognise that command. Use /help to see what BLACKOP can do.";
}

async function sendTelegram(token, chatId, text) {
  const response = await fetch(`https://api.telegram.org/bot${token}/sendMessage`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text })
  });
  if (!response.ok) throw new Error(`Telegram sendMessage failed: ${response.status}`);
}

export default {
  async fetch(request, env) {
    if (request.method === "GET") {
      return new Response("BLACKOP webhook is running.", { status: 200 });
    }
    if (request.method !== "POST") {
      return new Response("Method not allowed", { status: 405 });
    }

    const suppliedSecret = request.headers.get("X-Telegram-Bot-Api-Secret-Token");
    if (!env.TELEGRAM_WEBHOOK_SECRET ||
        suppliedSecret !== env.TELEGRAM_WEBHOOK_SECRET) {
      return new Response("Unauthorized", { status: 401 });
    }

    let update;
    try {
      update = await request.json();
    } catch {
      return new Response("Bad request", { status: 400 });
    }

    const message = update.message || update.edited_message;
    const text = message?.text;
    const chatId = message?.chat?.id;
    if (!text || !chatId) return new Response("OK", { status: 200 });

    const firstName = message.from?.first_name || "";
    const answer = replyFor(text, firstName);

    try {
      await sendTelegram(env.TELEGRAM_BOT_TOKEN, chatId, answer);
    } catch (error) {
      // Do not expose credentials or error details in the HTTP response.
      return new Response("Telegram delivery failed", { status: 502 });
    }
    return new Response("OK", { status: 200 });
  }
};
