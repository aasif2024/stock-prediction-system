"""
reset_aasif_password.py - Reset Aasif's password to a known value
"""
import bcrypt
import sqlite3

new_password = "Aasif@1435"
pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

conn = sqlite3.connect("../database/stock_prediction.db")
cur = conn.cursor()
cur.execute(
    "UPDATE users SET password_hash = ? WHERE email = ?",
    (pw_hash, "mohammedaasif1435@gmail.com"),
)
conn.commit()
affected = cur.rowcount
conn.close()

if affected:
    print("Password reset successfully!")
    print("Email   : mohammedaasif1435@gmail.com")
    print("Password: Aasif@1435")
else:
    print("ERROR: User not found!")
