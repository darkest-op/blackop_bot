"""
Risk-based position sizing: given your account capital and a fixed risk
percentage, works out how big a position to take so a stop-loss hit only
costs a small, controlled slice of your account -- never a guess, never
"however much feels right in the moment".

IMPORTANT ASSUMPTIONS (verify against your actual broker before trading):
- Standard lot = 100,000 units. Pip value per standard lot is assumed
  ~$10/pip for USD-quoted forex pairs (e.g. EURUSD) -- this is the common
  case but varies by pair and account currency.
- Gold (XAU/USD): assumed 1 standard lot = 100 oz, so each $0.01 (1 "pip"
  in this bot's convention) move = ~$1/lot.
- These are industry-standard approximations, not your specific broker's
  contract specs. Brokers differ (mini/micro/cent accounts, different
  contract sizes) -- always confirm the pip value your broker actually
  quotes before sizing a real position.
"""

from dataclasses import dataclass


@dataclass
class PositionSize:
    risk_amount: float      # dollars risked on this trade
    lots: float              # suggested position size in standard lots
    units: int                # suggested position size in raw units
    pip_value_per_lot: float  # assumption used


def pip_value_per_standard_lot(pair: str) -> float:
    if "XAU" in pair.upper():
        return 1.0  # ~$1 per "point" (0.01 move) per standard lot (100oz) -- verify with broker
    return 10.0  # ~$10/pip per standard lot for USD-quoted forex pairs -- verify with broker


def calculate_position_size(capital: float, risk_percent: float, risk_pips: float, pair: str) -> PositionSize:
    """
    capital: total account capital (your currency, e.g. USD)
    risk_percent: how much of capital to risk on this one trade, e.g. 1.0 for 1%
    risk_pips: distance from entry to stop-loss, in pips (or gold "points")
    """
    risk_amount = capital * (risk_percent / 100)
    pip_value = pip_value_per_standard_lot(pair)

    if risk_pips <= 0:
        return PositionSize(risk_amount=risk_amount, lots=0.0, units=0, pip_value_per_lot=pip_value)

    lots = risk_amount / (risk_pips * pip_value)
    units = round(lots * 100_000)
    return PositionSize(risk_amount=risk_amount, lots=round(lots, 3), units=units, pip_value_per_lot=pip_value)


def format_position_line(capital: float, risk_percent: float, risk_pips: float, pair: str) -> str:
    pos = calculate_position_size(capital, risk_percent, risk_pips, pair)
    if pos.lots <= 0:
        return "💰 Position size: unavailable (invalid stop distance)."

    # Flag unrealistically small position sizes -- common with very small accounts
    size_note = ""
    if pos.units < 1000:
        size_note = " (smaller than most brokers' minimum trade size -- consider a cent/micro account, or risking a bit more than usual on this trade)"

    return (
        f"💰 Position size (risking {risk_percent:.1f}% of ${capital:.2f} = ${pos.risk_amount:.2f}): "
        f"~{pos.lots:.3f} lots (~{pos.units:,} units){size_note}\n"
        f"Assumes ~${pos.pip_value_per_lot:.0f}/pip per standard lot -- verify against your broker's actual contract specs."
    )
