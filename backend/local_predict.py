import sys
import json
import pandas as pd
import numpy as np

sys.path.insert(0, '.')
from utils.ml_utils import predict_price

dataset_path = '../machine_learning/data/sample_dataset.xlsx'
print(f"Reading dataset from {dataset_path}...")

# Load dataset
try:
    sheets = pd.read_excel(dataset_path, sheet_name=None)
    frames = []
    for name, sheet_df in sheets.items():
        frames.append(sheet_df)
    df = pd.concat(frames, ignore_index=True)
except Exception as e:
    print(f"Failed to read dataset: {e}")
    sys.exit(1)

equity = 'TATAMOTORS'
# Filter for TATAMOTORS
tata_df = df[df['equityName'] == equity].copy()

if tata_df.empty:
    print(f"No data found for {equity} in the dataset.")
    sys.exit(1)

# Clean and sort by date
tata_df["date"] = pd.to_datetime(tata_df["date"])
tata_df = tata_df.sort_values("date")

# Get history for the last 50 days (excluding the very last day which we'll use as 'live' for prediction)
history_df = tata_df.iloc[:-1].tail(50)
latest_row = tata_df.iloc[-1]

history = []
for _, row in history_df.iterrows():
    history.append({
        "close": float(row["close"]),
        "tradedQty": float(row["tradedQty"])
    })

print(f"\n--- Latest Data (Date: {latest_row['date']}) ---")
print(f"Open: {latest_row['open']}")
print(f"High: {latest_row['high']}")
print(f"Low: {latest_row['low']}")
print(f"Close: {latest_row['close']}")
print(f"Volume: {latest_row['tradedQty']}")

print("\n--- Running Prediction ---")
try:
    pred = predict_price(
        equity_name=equity,
        open_=float(latest_row['open']),
        high=float(latest_row['high']),
        low=float(latest_row['low']),
        close=float(latest_row['close']),
        traded_qty=float(latest_row['tradedQty']),
        history=history
    )
    print(json.dumps(pred, indent=2))
except Exception as e:
    print("Prediction error:", e)
