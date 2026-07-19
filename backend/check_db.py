"""
check_db.py - Verify and initialize the SQLite database
Run with: python check_db.py
"""
import sqlite3
from config import Config
from database.db import init_sqlite_db

db_path = Config.SQLITE_PATH
print(f"[INFO] SQLite DB path: {db_path}")
print(f"[INFO] DB exists: {db_path.exists()}")

# Ensure parent directory exists
db_path.parent.mkdir(parents=True, exist_ok=True)

# Initialize tables if needed
init_sqlite_db(db_path)
print("[INFO] DB initialized/verified.")

# Check tables and users
conn = sqlite3.connect(str(db_path))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]
print(f"[INFO] Tables: {tables}")

cur.execute("SELECT COUNT(*) as count FROM users")
count = cur.fetchone()["count"]
print(f"[INFO] Total users in DB: {count}")

if count > 0:
    cur.execute("SELECT id, full_name, email, created_at FROM users")
    users = cur.fetchall()
    print("\n[INFO] Registered users:")
    for u in users:
        print(f"  - ID:{u['id']} | {u['full_name']} | {u['email']} | {u['created_at']}")

conn.close()
print("\n[SUCCESS] Database is working correctly!")
