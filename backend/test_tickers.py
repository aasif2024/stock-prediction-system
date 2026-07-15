import yfinance as yf
import sys

tickers = ["TATAMOTORS.NS", "TATAMOTORS.BO", "TTM"]
for t in tickers:
    print(f"Testing {t}...")
    try:
        df = yf.Ticker(t).history(period="1d")
        if not df.empty:
            print(f"Success with {t}!")
            print(df)
        else:
            print(f"Empty data for {t}")
    except Exception as e:
        print(f"Error with {t}: {e}")
