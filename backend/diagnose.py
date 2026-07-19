"""
diagnose.py - Full diagnostic for watchlist + time + live data issues
"""
import requests
import sqlite3

BASE = "http://localhost:5000"

# ─── Check DB watchlist directly ────────────────────────────────────────────
print("=" * 60)
print("1. DATABASE WATCHLIST CHECK")
conn = sqlite3.connect("../database/stock_prediction.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT user_id, equity_name, shares, buy_price FROM watchlist ORDER BY user_id")
rows = cur.fetchall()
print(f"   Total watchlist rows: {len(rows)}")
for r in rows:
    print(f"   user_id={r['user_id']} | {r['equity_name']} | shares={r['shares']} | buy_price={r['buy_price']}")

cur.execute("SELECT id, email FROM users")
users = cur.fetchall()
print("\n2. REGISTERED USERS")
for u in users:
    print(f"   ID={u['id']} | {u['email']}")
conn.close()

# ─── Test login with known user ──────────────────────────────────────────────
print("\n3. API LOGIN TEST (user ID=1 = Aasif)")
login = requests.post(f"{BASE}/api/auth/login", 
    json={"email": "mohammedaasif1435@gmail.com", "password": "aasif1435"})
print(f"   Login attempt: {login.status_code} -> {login.json()}")

# Try test user
print("\n4. API LOGIN TEST (livetest user)")
login2 = requests.post(f"{BASE}/api/auth/login",
    json={"email": "livetest@stocksense.com", "password": "test1234"})
print(f"   Login attempt: {login2.status_code}")
if login2.status_code == 200:
    token = login2.json()["token"]
    uid = login2.json()["user"]["id"]
    print(f"   Logged in as user_id={uid}")

    headers = {"Authorization": f"Bearer {token}"}
    wl = requests.get(f"{BASE}/api/watchlist/", headers=headers)
    print(f"\n5. WATCHLIST API for user_id={uid}: status={wl.status_code}")
    print(f"   Response: {wl.json()}")

print("\nDONE")
