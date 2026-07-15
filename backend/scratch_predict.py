import sys
import json
sys.path.insert(0, '.')
from utils.ml_utils import get_latest_live_data, predict_price, get_historical_data

equity = 'TATAMOTORS'
print("Fetching live data for", equity, "...")
live = get_latest_live_data(equity)

if not live:
    print("Could not fetch live data.")
    sys.exit(1)

print("Fetching historical data (50 days)...")
history = get_historical_data(equity, days=50)

print("\n--- Live Data ---")
print(json.dumps(live, indent=2))

print("\n--- Running Prediction ---")
try:
    pred = predict_price(
        equity_name=equity,
        open_=live['open'],
        high=live['high'],
        low=live['low'],
        close=live['close'],
        traded_qty=live['traded_qty'],
        history=history
    )
    print(json.dumps(pred, indent=2))
except Exception as e:
    print("Prediction error:", e)
