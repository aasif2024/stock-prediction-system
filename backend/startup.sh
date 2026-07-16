#!/usr/bin/env bash
# startup.sh – run once on Render before gunicorn starts.
# This seeds the database so the app works on a fresh deployment.
set -e

echo "==> Running startup.sh ..."

# Initialise database + seed companies
python -c "
from database.db import init_sqlite_db, get_connection
from config import Config

# Ensure DB exists
db_path = Config.SQLITE_PATH
db_path.parent.mkdir(parents=True, exist_ok=True)
if not db_path.exists():
    print(f'Initialising SQLite DB at {db_path}...')
    init_sqlite_db(db_path)
else:
    print(f'SQLite DB already exists at {db_path}')
"

# Seed companies table
python seed_companies.py || echo 'seed_companies failed (non-fatal – companies may already exist)'

echo "==> Startup complete. Starting gunicorn..."
exec gunicorn app:app
