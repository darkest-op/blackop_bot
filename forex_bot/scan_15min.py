"""
Manual-only 15-minute quick scan. Same output as alert.py (chart + caption
per pair) but on the 15-min timeframe, kept as its own script so it's never
run automatically -- trigger it from the Actions tab when you want a closer,
faster-moving look. Costs 1 Alpha Vantage call per pair (2 total).

Note: unlike the scheduled alert.py signals, quick-scan signals are NOT
saved to trades.json (no persistent tracking, no win/loss follow-up) --
this keeps the workflow simple (no git write-back needed) for what's meant
to be an occasional quick look, not a tracked trade source.
"""

import tempfile
import config
from alert import process_one, send_telegram_message


def main():
    # Ephemeral, not loaded from or saved to disk -- see note above.
    scratch_trades_data = {"open": [], "closed": []}

    with tempfile.TemporaryDirectory() as tmpdir:
        for i, pair in enumerate(config.WATCHLIST):
            for label, interval in config.MANUAL_TIMEFRAMES:
                try:
                    process_one(pair, label, interval, tmpdir, scratch_trades_data)
                except Exception as e:
                    try:
                        send_telegram_message(f"{pair} ({label}): error ({e})")
                    except Exception:
                        print(f"Error on {pair} {label}: {e}")


if __name__ == "__main__":
    main()
