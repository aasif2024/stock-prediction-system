from database.db import db_cursor

with db_cursor() as cur:
    cur.execute("SELECT * FROM companies")
    for row in cur.fetchall():
        print(row)
