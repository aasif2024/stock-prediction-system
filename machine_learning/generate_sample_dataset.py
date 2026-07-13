"""
generate_sample_dataset.py
---------------------------------
Generates a SAMPLE stock dataset that matches the schema described in the
project report (companyName, equityName, date, open, close, high, low,
tradedQty). This is only a placeholder so the ML pipeline and backend can
be trained/tested end-to-end.

>>> REPLACE machine_learning/data/sample_dataset.xlsx WITH YOUR REAL NSE
    DATASET (same column names) BEFORE GOING TO PRODUCTION. <<<

Run:
    python generate_sample_dataset.py
"""

import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

COMPANIES = [
    ("Tata Motors Limited", "TATAMOTORS"),
    ("Marico Limited", "MARICO"),
    ("Dabur India Limited", "DABUR"),
    ("Bank of India", "BANKINDIA"),
    ("Ambuja Cements Limited", "AMBUJACEM"),
    ("Eveready Industries India Limited", "EVEREADY"),
    ("Jindal Stainless Limited", "JSL"),
]

START_DATE = "2018-01-01"
END_DATE = "2024-12-31"


def generate_company_series(name, symbol, dates):
    n = len(dates)
    # random-walk close price
    returns = np.random.normal(loc=0.0004, scale=0.02, size=n)
    close = 100 * np.exp(np.cumsum(returns))
    open_ = close * (1 + np.random.normal(0, 0.005, n))
    high = np.maximum(open_, close) * (1 + np.abs(np.random.normal(0, 0.01, n)))
    low = np.minimum(open_, close) * (1 - np.abs(np.random.normal(0, 0.01, n)))
    qty = np.random.randint(10_000, 5_000_000, n)

    return pd.DataFrame({
        "companyName": name,
        "equityName": symbol,
        "date": dates,
        "open": open_.round(2),
        "high": high.round(2),
        "low": low.round(2),
        "close": close.round(2),
        "tradedQty": qty,
    })


def main():
    dates = pd.bdate_range(START_DATE, END_DATE)  # business days only
    frames = [generate_company_series(name, sym, dates) for name, sym in COMPANIES]
    df = pd.concat(frames, ignore_index=True)

    out_dir = Path(__file__).parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "sample_dataset.xlsx"
    df.to_excel(out_path, index=False)
    print(f"Sample dataset written to {out_path} ({len(df)} rows, {df['equityName'].nunique()} companies)")


if __name__ == "__main__":
    main()
