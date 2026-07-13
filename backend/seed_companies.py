"""
seed_companies.py
---------------------------------
Populates the `companies` table from the dataset used to train the
model (machine_learning/saved_model/metadata.json), so the frontend's
company dropdown and the predict/history APIs have matching rows.

Run (after schema.sql has been applied and train_model.py has run):
    python seed_companies.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd

from config import Config
from models.company_model import upsert_company


def main():
    if not Config.METADATA_PATH.exists():
        raise FileNotFoundError(
            f"{Config.METADATA_PATH} not found. Run machine_learning/train_model.py first."
        )
    with open(Config.METADATA_PATH) as f:
        metadata = json.load(f)

    equity_names = metadata["companies"]

    # Try to pull the full company name from the original dataset if present
    dataset_path = Path(__file__).parent.parent / "machine_learning" / "data" / "sample_dataset.xlsx"
    name_lookup = {}
    if dataset_path.exists():
        df = pd.read_excel(dataset_path)
        name_lookup = dict(zip(df["equityName"], df["companyName"]))

    sector_mapping = {
        "AMBUJACEM": "cement & materials",
        "BANKINDIA": "banking & finance",
        "DABUR": "consumer goods",
        "EVEREADY": "consumer goods",
        "JSL": "materials",
        "MARICO": "consumer goods",
        "TATAMOTORS": "auto mobiles & auto components"
    }

    for equity in equity_names:
        company_name = name_lookup.get(equity, equity)
        sector = sector_mapping.get(equity.upper(), "other")
        cid = upsert_company(company_name, equity, sector)
        print(f"  upserted company_id={cid}: {company_name} ({equity}) - Sector: {sector}")

    print(f"\nSeeded {len(equity_names)} companies.")


if __name__ == "__main__":
    main()
