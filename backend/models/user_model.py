"""
models/user_model.py
---------------------------------
Data-access functions for the `users` table.
Uses RETURNING id for INSERT to support PostgreSQL, MySQL, and SQLite.
"""

from database.db import db_cursor, get_db_type


def _insert_returning_id(cur, sql: str, params: tuple) -> int:
    """
    Executes an INSERT and returns the new row id.
    For PostgreSQL: uses RETURNING id clause.
    For MySQL/SQLite: uses cur.lastrowid.
    """
    if get_db_type() == "postgres":
        cur.execute(sql + " RETURNING id", params)
        row = cur.fetchone()
        return row["id"]
    else:
        cur.execute(sql, params)
        return cur.lastrowid


def create_user(full_name: str, email: str, password_hash: str) -> int:
    with db_cursor(commit=True) as cur:
        return _insert_returning_id(
            cur,
            "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
            (full_name, email, password_hash),
        )


def get_user_by_email(email: str):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cur.fetchone()


def get_user_by_id(user_id: int):
    with db_cursor() as cur:
        cur.execute("SELECT id, full_name, email, created_at FROM users WHERE id = %s", (user_id,))
        return cur.fetchone()


def save_password_reset_otp(email: str, otp: str, expires_at):
    with db_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE users SET reset_otp = %s, reset_otp_exp = %s WHERE email = %s",
            (otp, expires_at, email),
        )


def get_user_by_email_with_otp(email: str):
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        return cur.fetchone()


def update_user_password(email: str, password_hash: str):
    with db_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE users SET password_hash = %s, reset_otp = NULL, reset_otp_exp = NULL WHERE email = %s",
            (password_hash, email),
        )
