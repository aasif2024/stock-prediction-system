#!/usr/bin/env bash
# startup.sh – runs on Render before gunicorn starts.
# Handles both PostgreSQL (Supabase) and SQLite setups.
set -e

echo "==> [startup] Starting deployment setup..."

python - <<'PYEOF'
import sys
sys.path.insert(0, ".")

from config import Config

print(f"[startup] DATABASE_TYPE = {Config.DATABASE_TYPE}")

if Config.DATABASE_TYPE == "postgres":
    print("[startup] Using PostgreSQL (Supabase). Initialising schema...")
    import psycopg2
    from database.db import PostgresConnectionWrapper, init_postgres_db

    conn_raw = psycopg2.connect(Config.DATABASE_URL, sslmode="require")
    conn_raw.autocommit = False
    conn = PostgresConnectionWrapper(conn_raw)
    init_postgres_db(conn)
    conn.close()
    print("[startup] PostgreSQL schema ready.")

else:
    print(f"[startup] Using SQLite at {Config.SQLITE_PATH}")
    from pathlib import Path
    from database.db import init_sqlite_db
    db_path = Config.SQLITE_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    init_sqlite_db(db_path)
    print("[startup] SQLite schema ready.")

PYEOF

# Seed companies table (idempotent - uses ON CONFLICT DO NOTHING)
echo "==> [startup] Seeding companies..."
python - <<'PYEOF'
import sys, json
sys.path.insert(0, ".")

from config import Config
from models.company_model import upsert_company

metadata_path = Config.METADATA_PATH
if not metadata_path.exists():
    print(f"[startup] WARNING: metadata.json not found at {metadata_path}. Skipping.")
    sys.exit(0)

with open(metadata_path) as f:
    metadata = json.load(f)

companies = metadata.get("companies", [])

name_mapping = {
    "AMBUJACEM": "Ambuja Cements Limited",
    "BANKINDIA": "Bank of India",
    "DABUR": "Dabur India Limited",
    "EVEREADY": "Eveready Industries India Limited",
    "JSL": "Jindal Stainless Limited",
    "MARICO": "Marico Limited",
    "TATAMOTORS": "Tata Motors Limited"
}

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
    company_name = name_mapping.get(equity.upper(), equity)
    cid = upsert_company(company_name, equity, sector)
    print(f"[startup]   seeded: {company_name} (id={cid})")

print(f"[startup] Done. {len(companies)} companies seeded.")
PYEOF

echo "==> [startup] All setup complete. Starting gunicorn..."
exec gunicorn --workers 1 --timeout 120 --bind 0.0.0.0:${PORT:-5000} app:app
