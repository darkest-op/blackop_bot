"""
Renders a candlestick chart with the signal's entry, stop-loss, and take-
profit drawn as horizontal lines, so you can see exactly what the setup
looks like before trading it.
"""

import matplotlib
matplotlib.use("Agg")  # headless backend -- no display needed (works in GitHub Actions)

import mplfinance as mpf
import pandas as pd


def render_setup_chart(df: pd.DataFrame, pair: str, timeframe_label: str, sig, out_path: str, lookback: int = 60):
    """
    df: OHLC DataFrame (same one passed to generate_signal), index = datetime
    sig: a Signal object from strategy.py
    out_path: where to save the PNG
    """
    plot_df = df.tail(lookback)[["open", "high", "low", "close"]]

    dp = 2 if "XAU" in pair.upper() else 5

    hlines = []
    colors = []
    labels = []

    if sig.action in ("BUY", "SELL"):
        hlines = [sig.price, sig.stop_loss, sig.take_profit]
        colors = ["#2962ff", "#f23645", "#089981"]  # entry=blue, SL=red, TP=green
        labels = [f"Entry {sig.price:.{dp}f}", f"SL {sig.stop_loss:.{dp}f}", f"TP {sig.take_profit:.{dp}f}"]

    title = f"{pair} -- {timeframe_label} -- {sig.action}"

    mc = mpf.make_marketcolors(up="#089981", down="#f23645", inherit=True)
    style = mpf.make_mpf_style(marketcolors=mc, gridstyle=":", gridcolor="#333333",
                                facecolor="#131722", edgecolor="#131722",
                                figcolor="#131722", rc={"font.size": 9})

    kwargs = dict(
        type="candle",
        style=style,
        title=title,
        ylabel="Price",
        figsize=(9, 5.5),
        tight_layout=True,
        savefig=dict(fname=out_path, dpi=150, bbox_inches="tight"),
    )
    if hlines:
        kwargs["hlines"] = dict(hlines=hlines, colors=colors, linestyle="--", linewidths=1.2)

    mpf.plot(plot_df, **kwargs)
    return out_path
