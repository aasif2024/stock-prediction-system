from database.db import db_cursor

with db_cursor() as cur:
    cur.execute("SELECT * FROM companies WHERE equity_name='TATAMOTORS'")
    print(cur.fetchall())
