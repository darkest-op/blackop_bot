"""Pull real forex candle data from Alpha Vantage FX endpoints."""
import requests
import pandas as pd
import time
from config import ALPHA_VANTAGE_API_KEY
BASE_URL = "https://www.alphavantage.co/query"

def _split_pair(pair: str):
    pair = pair.upper().replace("/", "")
    if len(pair) != 6: raise ValueError(f"Expected a 6-letter pair like EURUSD, got: {pair}")
    return pair[:3], pair[3:]

def _to_frame(data, key, pair):
    if key not in data: raise RuntimeError(f"Alpha Vantage error for {pair}: {data}")
    df = pd.DataFrame.from_dict(data[key], orient="index")
    df = df.rename(columns={"1. open":"open","2. high":"high","3. low":"low","4. close":"close"}).astype(float)
    df.index = pd.to_datetime(df.index)
    return df.sort_index()

def get_daily_candles(pair: str, outputsize: str = "compact") -> pd.DataFrame:
    a, b = _split_pair(pair)
    params = {"function":"FX_DAILY","from_symbol":a,"to_symbol":b,"outputsize":outputsize,"apikey":ALPHA_VANTAGE_API_KEY}
    resp = requests.get(BASE_URL, params=params, timeout=15); resp.raise_for_status()
    return _to_frame(resp.json(), "Time Series FX (Daily)", pair)

def get_intraday_candles(pair: str, interval: str = "15min", outputsize: str = "compact") -> pd.DataFrame:
    a, b = _split_pair(pair)
    params = {"function":"FX_INTRADAY","from_symbol":a,"to_symbol":b,"interval":interval,"outputsize":outputsize,"apikey":ALPHA_VANTAGE_API_KEY}
    resp = requests.get(BASE_URL, params=params, timeout=15); resp.raise_for_status()
    return _to_frame(resp.json(), f"Time Series FX ({interval})", pair)

def get_latest_price(pair: str) -> float:
    a, b = _split_pair(pair)
    params = {"function":"CURRENCY_EXCHANGE_RATE","from_currency":a,"to_currency":b,"apikey":ALPHA_VANTAGE_API_KEY}
    resp = requests.get(BASE_URL, params=params, timeout=15); resp.raise_for_status()
    data = resp.json()
    try: return float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
    except KeyError: raise RuntimeError(f"Alpha Vantage error for {pair}: {data}")

def rate_limit_pause(seconds: float = 13.0):
    time.sleep(seconds)
