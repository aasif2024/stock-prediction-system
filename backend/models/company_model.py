"""
models/company_model.py
---------------------------------
Data-access functions for the `companies` table.
"""

from database.db import db_cursor, get_db_type


def get_all_companies():
    with db_cursor() as cur:
        cur.execute("SELECT id, company_name, equity_name, sector FROM companies ORDER BY company_name")
        return cur.fetchall()


def get_company_by_equity(equity_name: str):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM companies WHERE equity_name = %s", (equity_name,))
        return cur.fetchone()


def upsert_company(company_name: str, equity_name: str, sector: str | None = None) -> int:
    with db_cursor(commit=True) as cur:
        if get_db_type() == "sqlite":
            cur.execute(
                """
                INSERT INTO companies (company_name, equity_name, sector)
                VALUES (%s, %s, %s)
                ON CONFLICT(equity_name) DO UPDATE SET company_name = excluded.company_name, sector = excluded.sector
                """,
                (company_name, equity_name, sector),
            )
        else:
            cur.execute(
                """
                INSERT INTO companies (company_name, equity_name, sector)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE company_name = VALUES(company_name), sector = VALUES(sector)
                """,
                (company_name, equity_name, sector),
            )
        cur.execute("SELECT id FROM companies WHERE equity_name = %s", (equity_name,))
        return cur.fetchone()["id"]
