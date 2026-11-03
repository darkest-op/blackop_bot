"""
Pulls real forex candle data from Alpha Vantage's FX endpoints.

Alpha Vantage free tier limits: 25 requests/day, 5/minute as of writing --
check https://www.alphavantage.co/premium/ if you outgrow it. For heavier
use later, Twelve Data or OANDA's v20 API are good paid/free-tier upgrades.
"""

import requests
import pandas as pd
import time
from config import ALPHA_VANTAGE_API_KEY

BASE_URL = "https://www.alphavantage.co/query"


def _split_pair(pair: str):
    """ 'EURUSD' -> ('EUR', 'USD') """
    pair = pair.upper().replace("/", "")
    if len(pair) != 6:
        raise ValueError(f"Expected a 6-letter pair like EURUSD, got: {pair}")
    return pair[:3], pair[3:]


def get_daily_candles(pair: str, outputsize: str = "compact") -> pd.DataFrame:
    """
    Daily OHLC candles. outputsize='compact' = last 100 days,
    'full' = full history (~20 years).
    Returns a DataFrame indexed by date, oldest first, columns: open high low close
    """
    from_sym, to_sym = _split_pair(pair)
    params = {
        "function": "FX_DAILY",
        "from_symbol": from_sym,
        "to_symbol": to_sym,
        "outputsize": outputsize,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    key = "Time Series FX (Daily)"
    if key not in data:
        raise RuntimeError(f"Alpha Vantage error for {pair}: {data}")

    df = pd.DataFrame.from_dict(data[key], orient="index")
    df = df.rename(columns={
        "1. open": "open", "2. high": "high",
        "3. low": "low", "4. close": "close",
    })
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


def get_intraday_candles(pair: str, interval: str = "15min", outputsize: str = "compact") -> pd.DataFrame:
    """
    Intraday candles. interval: '1min','5min','15min','30min','60min'
    """
    from_sym, to_sym = _split_pair(pair)
    params = {
        "function": "FX_INTRADAY",
        "from_symbol": from_sym,
        "to_symbol": to_sym,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    key = f"Time Series FX ({interval})"
    if key not in data:
        raise RuntimeError(f"Alpha Vantage error for {pair}: {data}")

    df = pd.DataFrame.from_dict(data[key], orient="index")
    df = df.rename(columns={
        "1. open": "open", "2. high": "high",
        "3. low": "low", "4. close": "close",
    })
    df = df.astype(float)
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    return df


def get_latest_price(pair: str) -> float:
    """Real-time-ish exchange rate (CURRENCY_EXCHANGE_RATE endpoint)."""
    from_sym, to_sym = _split_pair(pair)
    params = {
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": from_sym,
        "to_currency": to_sym,
        "apikey": ALPHA_VANTAGE_API_KEY,
    }
    resp = requests.get(BASE_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    try:
        return float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
    except KeyError:
        raise RuntimeError(f"Alpha Vantage error for {pair}: {data}")


def rate_limit_pause(seconds: float = 13.0):
    """Free tier = 5 req/min, so pause ~13s between calls when scanning a list."""
    time.sleep(seconds)
