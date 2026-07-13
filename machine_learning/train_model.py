"""
train_model.py
---------------------------------
End-to-end training pipeline for the Stock Price Prediction system.

Steps:
 1. Load the Excel dataset (all sheets)
 2. Clean data (duplicates, missing values, dtypes)
 3. Feature engineering (moving averages, RSI, MACD, Bollinger Bands, lags)
 4. Train/test split (chronological, per company)
 5. Train Linear Regression, Random Forest, Gradient Boosting
 6. Evaluate with MAE, MSE, RMSE, R2
 7. Save the best model + scaler + feature list + company encoder to
    machine_learning/saved_model/ (and copy into backend/ml_model/)

Run:
    python train_model.py --data data/sample_dataset.xlsx
"""

import argparse
import json
import pickle
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler, LabelEncoder

REQUIRED_COLUMNS = [
    "companyName", "equityName", "date", "open", "high", "low", "close", "tradedQty",
]

FEATURE_COLS = [
    "open", "high", "low", "tradedQty",
    "range", "gap", "pct_change",
    "ma_5", "ma_10", "ma_20",
    "vol_5", "vol_10",
    "ema_12", "ema_26", "macd",
    "bb_width", "rsi",
    "close_lag_1", "close_lag_2", "close_lag_3", "close_lag_5",
    "vol_lag_1", "vol_lag_2",
    "company_code",
]


def load_dataset(path: Path) -> pd.DataFrame:
    """Reads every sheet in the Excel workbook and concatenates them."""
    sheets = pd.read_excel(path, sheet_name=None)
    frames = []
    for name, sheet_df in sheets.items():
        print(f"  sheet '{name}': {sheet_df.shape[0]} rows, columns={list(sheet_df.columns)}")
        frames.append(sheet_df)
    df = pd.concat(frames, ignore_index=True)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Dataset is missing required columns: {missing}. "
            f"Found columns: {list(df.columns)}"
        )
    return df


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    df = df.dropna(subset=REQUIRED_COLUMNS)

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    for col in ["open", "high", "low", "close", "tradedQty"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close", "tradedQty"])

    df = df.sort_values(["equityName", "date"]).reset_index(drop=True)
    print(f"  cleaned: {before} -> {len(df)} rows")
    return df


def add_features(group: pd.DataFrame) -> pd.DataFrame:
    d = group.copy()
    d["range"] = d["high"] - d["low"]
    d["gap"] = d["open"] - d["close"].shift(1)
    d["pct_change"] = d["close"].pct_change()

    for w in [5, 10, 20]:
        d[f"ma_{w}"] = d["close"].rolling(w).mean()
        d[f"vol_{w}"] = d["tradedQty"].rolling(w).mean()

    d["ema_12"] = d["close"].ewm(span=12, adjust=False).mean()
    d["ema_26"] = d["close"].ewm(span=26, adjust=False).mean()
    d["macd"] = d["ema_12"] - d["ema_26"]

    bb_mid = d["close"].rolling(20).mean()
    bb_std = d["close"].rolling(20).std()
    d["bb_width"] = ((bb_mid + 2 * bb_std) - (bb_mid - 2 * bb_std)) / bb_mid

    delta = d["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    d["rsi"] = 100 - 100 / (1 + rs)

    for lag in [1, 2, 3, 5]:
        d[f"close_lag_{lag}"] = d["close"].shift(lag)
    for lag in [1, 2]:
        d[f"vol_lag_{lag}"] = d["tradedQty"].shift(lag)

    d["target"] = d["close"].shift(-1)  # next-day close
    return d


def build_features(df: pd.DataFrame, company_encoder: LabelEncoder) -> pd.DataFrame:
    df["company_code"] = company_encoder.transform(df["equityName"])
    df = df.groupby("equityName", group_keys=False).apply(add_features)
    # pandas drops the groupby key column from the result in newer versions;
    # reconstruct it from company_code so downstream code can rely on it.
    if "equityName" not in df.columns:
        df["equityName"] = company_encoder.inverse_transform(df["company_code"])
    df = df.dropna().reset_index(drop=True)
    return df


def train_and_evaluate(X_train, X_test, y_train, y_test):
    models = {
        "Linear Regression": LinearRegression(),
        "Random Forest": RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42),
    }

    results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        mae = mean_absolute_error(y_test, preds)
        mse = mean_squared_error(y_test, preds)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, preds)
        results[name] = {"model": model, "MAE": mae, "MSE": mse, "RMSE": rmse, "R2": r2}
        print(f"  {name:<20} MAE={mae:8.3f}  MSE={mse:10.3f}  RMSE={rmse:8.3f}  R2={r2:.4f}")

    best_name = max(results, key=lambda n: results[n]["R2"])
    return best_name, results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default="data/sample_dataset.xlsx",
                         help="Path to the Excel dataset")
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    data_path = (base_dir / args.data) if not Path(args.data).is_absolute() else Path(args.data)

    print(f"\n1. Loading dataset from {data_path}")
    df = load_dataset(data_path)

    print("\n2. Cleaning dataset")
    df = clean_dataset(df)

    print(f"\n   Columns: {list(df.columns)}")
    print(f"   Companies: {df['equityName'].nunique()}")

    print("\n3. Encoding companies + feature engineering")
    company_encoder = LabelEncoder()
    company_encoder.fit(df["equityName"])
    df = build_features(df, company_encoder)
    print(f"   Usable rows after feature engineering: {len(df)}")

    print("\n4. Train/test split (chronological, 80/20)")
    df = df.sort_values("date")
    split_idx = int(len(df) * 0.8)
    train_df, test_df = df.iloc[:split_idx], df.iloc[split_idx:]

    X_train, y_train = train_df[FEATURE_COLS].values, train_df["target"].values
    X_test, y_test = test_df[FEATURE_COLS].values, test_df["target"].values
    print(f"   Train: {len(X_train)} rows | Test: {len(X_test)} rows")

    scaler = MinMaxScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    print("\n5. Training models")
    best_name, results = train_and_evaluate(X_train_s, X_test_s, y_train, y_test)
    best_model = results[best_name]["model"]
    print(f"\n6. Best model: {best_name} (R2={results[best_name]['R2']:.4f})")

    save_dir = base_dir / "saved_model"
    save_dir.mkdir(exist_ok=True)

    with open(save_dir / "model.pkl", "wb") as f:
        pickle.dump(best_model, f)
    with open(save_dir / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open(save_dir / "company_encoder.pkl", "wb") as f:
        pickle.dump(company_encoder, f)

    metadata = {
        "best_model": best_name,
        "feature_columns": FEATURE_COLS,
        "companies": sorted(df["equityName"].unique().tolist()),
        "metrics": {
            name: {k: v for k, v in r.items() if k != "model"}
            for name, r in results.items()
        },
    }
    with open(save_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n7. Saved model, scaler, encoder, metadata -> {save_dir}")

    # Copy into backend so the Flask API can load it directly
    backend_ml_dir = base_dir.parent / "backend" / "ml_model"
    backend_ml_dir.mkdir(exist_ok=True)
    for fname in ["model.pkl", "scaler.pkl", "company_encoder.pkl", "metadata.json"]:
        shutil.copy(save_dir / fname, backend_ml_dir / fname)
    print(f"   Copied artifacts to {backend_ml_dir}")


if __name__ == "__main__":
    main()
