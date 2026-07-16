#!/usr/bin/env bash
# startup.sh – runs on Render before gunicorn starts.
# Initialises the SQLite database and seeds the companies table.
set -e

echo "==> [startup] Starting deployment setup..."

# Create database directory inside backend (writable on Render)
mkdir -p database

# Initialise the SQLite DB schema (idempotent — uses CREATE TABLE IF NOT EXISTS)
python - <<'PYEOF'
import sys
sys.path.insert(0, ".")

from config import Config
from database.db import init_sqlite_db

db_path = Config.SQLITE_PATH
db_path.parent.mkdir(parents=True, exist_ok=True)

if not db_path.exists():
    print(f"[startup] Creating new SQLite DB at {db_path}")
    init_sqlite_db(db_path)
else:
    print(f"[startup] SQLite DB already exists at {db_path}")
    # Re-run schema to ensure any new tables are created
    init_sqlite_db(db_path)

print("[startup] Database schema is ready.")
PYEOF

# Seed companies from ml_model/metadata.json (idempotent — uses ON CONFLICT DO NOTHING)
echo "==> [startup] Seeding companies..."
python - <<'PYEOF'
import sys, json
sys.path.insert(0, ".")

from config import Config
from models.company_model import upsert_company

metadata_path = Config.METADATA_PATH
if not metadata_path.exists():
    print(f"[startup] WARNING: metadata.json not found at {metadata_path}. Skipping company seed.")
    sys.exit(0)

with open(metadata_path) as f:
    metadata = json.load(f)

companies = metadata.get("companies", [])
if not companies:
    print("[startup] No companies found in metadata.json. Skipping.")
    sys.exit(0)

sector_mapping = {
    "AMBUJACEM": "cement & materials",
    "BANKINDIA": "banking & finance",
    "DABUR": "consumer goods",
    "EVEREADY": "consumer goods",
    "JSL": "materials",
    "MARICO": "consumer goods",
    "TATAMOTORS": "auto mobiles & auto components"
}

for equity in companies:
    sector = sector_mapping.get(equity.upper(), "other")
    cid = upsert_company(equity, equity, sector)
    print(f"[startup]   seeded: {equity} (id={cid})")

print(f"[startup] Seeded {len(companies)} companies.")
PYEOF

echo "==> [startup] Setup complete! Starting gunicorn..."
exec gunicorn --workers 1 --timeout 120 --bind 0.0.0.0:${PORT:-5000} app:app
