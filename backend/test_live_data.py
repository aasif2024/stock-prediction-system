"""
test_live_data.py - Tests login + live data API end-to-end
"""
import requests
import json
import bcrypt
import sqlite3

# Create a test user with known password
password = "test1234"
pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

conn = sqlite3.connect("../database/stock_prediction.db")
cur = conn.cursor()
cur.execute("DELETE FROM users WHERE email = ?", ("livetest@stocksense.com",))
cur.execute(
    "INSERT INTO users (full_name, email, password_hash) VALUES (?, ?, ?)",
    ("Live Test", "livetest@stocksense.com", pw_hash),
)
conn.commit()
conn.close()
print("Test user created: livetest@stocksense.com / test1234")

# Login
login_res = requests.post(
    "http://localhost:5000/api/auth/login",
    json={"email": "livetest@stocksense.com", "password": "test1234"},
)
print(f"Login status: {login_res.status_code}")

if login_res.status_code == 200:
    token = login_res.json()["token"]
    print("Login SUCCESS!")

    headers = {"Authorization": f"Bearer {token}"}

    # Test live data for RELIANCE
    live_res = requests.get(
        "http://localhost:5000/api/predict/latest/RELIANCE", headers=headers
    )
    print(f"Live data status: {live_res.status_code}")
    if live_res.status_code == 200:
        d = live_res.json()["live_data"]
        print(f"RELIANCE: Date={d['date']} Open={d['open']} High={d['high']} Low={d['low']} Close={d['close']} Vol={d['traded_qty']}")
        print("\n✅ Live data is working! The fields will now auto-fill in the Predict page.")
    else:
        print(f"Live data error: {live_res.text}")
else:
    print(f"Login failed: {login_res.text}")
