import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'stock_prediction.db')

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE users ADD COLUMN reset_otp VARCHAR(6)")
        cur.execute("ALTER TABLE users ADD COLUMN reset_otp_exp DATETIME")
        conn.commit()
        print("Successfully added OTP columns to local SQLite database.")
    except sqlite3.OperationalError as e:
        print(f"OperationalError (columns might already exist): {e}")
    finally:
        conn.close()
else:
    print(f"Database not found at {db_path}")
