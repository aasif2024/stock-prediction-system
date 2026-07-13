"""
utils/ml_utils.py
---------------------------------
Loads the trained model/scaler/company-encoder produced by
machine_learning/train_model.py and exposes a single predict_price()
function used by the /api/predict route.

Because a live prediction request only gives us a single day's
OHLCV values (not history), the rolling/lag indicators used at
training time are approximated from that single day (a common,
documented simplification for a "quick predict" form). For
production-grade accuracy, feed in the last 20-50 days of history
instead — the function signature already accepts optional history.
"""

import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

from config import Config

_model = None
_scaler = None
_company_encoder = None
_metadata = None


def _load_artifacts():
    global _model, _scaler, _company_encoder, _metadata
    if _model is not None:
        return

    if not Config.MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model not found at {Config.MODEL_PATH}. "
            f"Run machine_learning/train_model.py first."
        )

    with open(Config.MODEL_PATH, "rb") as f:
        _model = pickle.load(f)
    with open(Config.SCALER_PATH, "rb") as f:
        _scaler = pickle.load(f)
    with open(Config.ENCODER_PATH, "rb") as f:
        _company_encoder = pickle.load(f)
    with open(Config.METADATA_PATH) as f:
        _metadata = json.load(f)


def get_known_companies():
    _load_artifacts()
    return _metadata["companies"]


def _build_feature_row(equity_name: str, open_, high, low, close, traded_qty, history: list | None):
    """
    Builds a single feature row matching FEATURE_COLS from train_model.py.
    If `history` (a list of past close/volume dicts, oldest first) is
    supplied, real rolling/lag indicators are computed. Otherwise the
    current day's close is used to approximate them.
    """
    if history:
        closes = [h["close"] for h in history] + [close]
        vols = [h["tradedQty"] for h in history] + [traded_qty]
    else:
        closes = [close] * 21
        vols = [traded_qty] * 11

    closes = pd.Series(closes)
    vols = pd.Series(vols)

    ma_5 = closes.tail(5).mean()
    ma_10 = closes.tail(10).mean()
    ma_20 = closes.tail(20).mean()
    vol_5 = vols.tail(5).mean()
    vol_10 = vols.tail(10).mean()

    ema_12 = closes.ewm(span=12, adjust=False).mean().iloc[-1]
    ema_26 = closes.ewm(span=26, adjust=False).mean().iloc[-1]
    macd = ema_12 - ema_26

    bb_mid = closes.tail(20).mean()
    bb_std = closes.tail(20).std() or 0.0
    bb_width = ((bb_mid + 2 * bb_std) - (bb_mid - 2 * bb_std)) / bb_mid if bb_mid else 0.0

    delta = closes.diff()
    gain = delta.clip(lower=0).tail(14).mean()
    loss = (-delta.clip(upper=0)).tail(14).mean()
    rs = gain / (loss + 1e-9) if pd.notna(gain) and pd.notna(loss) else 1.0
    rsi = 100 - 100 / (1 + rs)

    def lag(series, n):
        return series.iloc[-1 - n] if len(series) > n else series.iloc[0]

    company_code = _company_encoder.transform([equity_name])[0]

    row = {
        "open": open_, "high": high, "low": low, "tradedQty": traded_qty,
        "range": high - low,
        "gap": open_ - lag(closes, 1),
        "pct_change": (close - lag(closes, 1)) / (lag(closes, 1) + 1e-9),
        "ma_5": ma_5, "ma_10": ma_10, "ma_20": ma_20,
        "vol_5": vol_5, "vol_10": vol_10,
        "ema_12": ema_12, "ema_26": ema_26, "macd": macd,
        "bb_width": bb_width, "rsi": rsi,
        "close_lag_1": lag(closes, 1), "close_lag_2": lag(closes, 2),
        "close_lag_3": lag(closes, 3), "close_lag_5": lag(closes, 5),
        "vol_lag_1": lag(vols, 1), "vol_lag_2": lag(vols, 2),
        "company_code": company_code,
    }
    return row


def _compute_probability(row: dict, direction: str, close: float) -> float:
    """
    Derives a 0-100 confidence score for the prediction direction by blending
    three market-signal indicators:
      1. RSI alignment  – RSI > 55 favours UP; RSI < 45 favours DOWN.
      2. Price vs MA-20 – price above MA-20 favours UP and vice-versa.
      3. Model R²       – the best model's own R² acts as a base confidence floor.
    The three normalised signals are averaged, then rescaled to [50, 97] to
    reflect realistic prediction uncertainty.
    """
    best_model_name = _metadata.get("best_model", "")
    r2 = _metadata.get("metrics", {}).get(best_model_name, {}).get("R2", 0.8)
    # Clamp R2 to [0, 1]
    r2 = max(0.0, min(1.0, r2))

    rsi = row.get("rsi", 50.0)
    ma_20 = row.get("ma_20", close)

    # ── RSI signal ──────────────────────────────────────────────────────────
    # Map RSI to a 0-1 score aligned with direction.
    # UP: high RSI (55-80) is bullish. DOWN: low RSI (20-45) is bearish.
    if direction == "UP":
        rsi_score = max(0.0, min(1.0, (rsi - 45) / 35))  # 0 at RSI=45, 1 at RSI=80
    else:
        rsi_score = max(0.0, min(1.0, (55 - rsi) / 35))  # 0 at RSI=55, 1 at RSI=20

    # ── MA-20 signal ─────────────────────────────────────────────────────────
    # How far price is above/below 20-day MA, normalised by MA value.
    if ma_20 and ma_20 > 0:
        pct_vs_ma = (close - ma_20) / ma_20  # positive = above MA
    else:
        pct_vs_ma = 0.0
    # Clamp to ±5 % and scale to [0, 1]
    pct_vs_ma = max(-0.05, min(0.05, pct_vs_ma))
    if direction == "UP":
        ma_score = (pct_vs_ma + 0.05) / 0.10  # 0 at -5 %, 1 at +5 %
    else:
        ma_score = (-pct_vs_ma + 0.05) / 0.10

    # ── Blend ─────────────────────────────────────────────────────────────
    # Weight: R² contributes 50 %, market signals 25 % each.
    raw = 0.50 * r2 + 0.25 * rsi_score + 0.25 * ma_score  # in [0, 1]

    # Rescale raw [0,1] → probability [50, 97] % so we never claim certainty.
    probability = 50.0 + raw * 47.0
    return round(max(50.0, min(97.0, probability)), 1)


def predict_price(equity_name: str, open_: float, high: float, low: float,
                   close: float, traded_qty: float, history: list | None = None) -> dict:
    """
    Returns {"predicted_price": float, "direction": "UP"|"DOWN",
             "change_pct": float, "probability": float}
    """
    _load_artifacts()

    if equity_name not in _company_encoder.classes_:
        raise ValueError(
            f"Unknown company '{equity_name}'. Known companies: {list(_company_encoder.classes_)}"
        )

    row = _build_feature_row(equity_name, open_, high, low, close, traded_qty, history)
    feature_cols = _metadata["feature_columns"]
    X = np.array([[row[c] for c in feature_cols]])
    X_scaled = _scaler.transform(X)

    predicted_price = float(_model.predict(X_scaled)[0])
    direction = "UP" if predicted_price > close else "DOWN"
    change_pct = ((predicted_price - close) / close) * 100 if close else 0.0
    probability = _compute_probability(row, direction, close)

    return {
        "predicted_price": round(predicted_price, 2),
        "direction": direction,
        "change_pct": round(change_pct, 2),
        "probability": probability,
    }


def get_historical_data(equity_name: str, days: int = 30) -> list:
    """
    Fetches real-time historical data from Yahoo Finance for the given NSE equity.
    Returns the last `days` of closing prices formatted for the frontend chart.
    """
    ticker_symbol = f"{equity_name}.NS"
    try:
        # Fetching a bit more data to ensure we get `days` trading days
        period = f"{days + 15}d"
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period=period)
        
        if df.empty:
            return []
            
        df = df.tail(days)
        
        results = []
        for date, row in df.iterrows():
            results.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "tradedQty": float(row["Volume"])
            })
        return results
    except Exception as e:
        print(f"Error reading live historical data for {ticker_symbol}: {e}")
        return []

def get_latest_live_data(equity_name: str) -> dict:
    """
    Fetches the very latest (today's/last trading day) OHLCV data from Yahoo Finance.
    """
    ticker_symbol = f"{equity_name}.NS"
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period="5d") # Fetch last 5 days to guarantee at least 1 valid day
        if df.empty:
            return {}
        
        latest = df.iloc[-1]
        date = df.index[-1]

        # Calculate day over day change
        change_pct = 0.0
        change_val = 0.0
        if len(df) > 1:
            prev = df.iloc[-2]
            change_val = latest["Close"] - prev["Close"]
            change_pct = (change_val / prev["Close"]) * 100
        
        return {
            "equity_name": equity_name,
            "date": date.strftime("%Y-%m-%d"),
            "open": round(float(latest["Open"]), 2),
            "high": round(float(latest["High"]), 2),
            "low": round(float(latest["Low"]), 2),
            "close": round(float(latest["Close"]), 2),
            "traded_qty": int(latest["Volume"]),
            "change_val": round(float(change_val), 2),
            "change_pct": round(float(change_pct), 2)
        }
    except Exception as e:
        print(f"Error reading latest live data for {ticker_symbol}: {e}")
        return {}

def get_all_latest_live_data(equity_names: list) -> list:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_equity = {executor.submit(get_latest_live_data, eq): eq for eq in equity_names}
        for future in as_completed(future_to_equity):
            data = future.result()
            if data:
                results.append(data)
    return results

def get_company_news(equity_name: str) -> list:
    """
    Fetches the latest news articles for a given company using Yahoo Finance.
    """
    ticker_symbol = f"{equity_name}.NS"
    try:
        ticker = yf.Ticker(ticker_symbol)
        # Yahoo finance returns a list of dictionaries for news
        news_data = ticker.news
        if not news_data:
            return []
            
        formatted_news = []
        for article in news_data[:8]: # Limit to latest 8 articles
            content = article.get("content", article) # Handle both new nested format and old format
            
            title = content.get("title") or article.get("title", "")
            
            provider = content.get("provider", {})
            publisher = provider.get("displayName") or article.get("publisher", "")
            
            click_url = content.get("clickThroughUrl", {})
            link = click_url.get("url") or article.get("link", "")
            
            timestamp = article.get("providerPublishTime", 0)
            pub_date_str = content.get("pubDate", "")
            if not timestamp and pub_date_str:
                from datetime import datetime
                try:
                    dt = datetime.strptime(pub_date_str, "%Y-%m-%dT%H:%M:%SZ")
                    timestamp = int(dt.timestamp())
                except:
                    pass
                    
            if title and link:
                formatted_news.append({
                    "title": title,
                    "publisher": publisher,
                    "link": link,
                    "providerPublishTime": timestamp,
                })
        return formatted_news
    except Exception as e:
        print(f"Error reading news for {ticker_symbol}: {e}")
        return []
