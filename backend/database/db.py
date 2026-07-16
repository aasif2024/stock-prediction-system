"""
database/db.py
---------------------------------
Wrapper around PyMySQL and SQLite to hand out dict-cursor connections
and automatically fall back to SQLite if MySQL is unavailable.
"""

import sqlite3
from contextlib import contextmanager
import pymysql
import pymysql.cursors

from config import Config


class SQLiteCursorWrapper:
    def __init__(self, sqlite_cursor):
        self.cursor = sqlite_cursor

    def execute(self, sql, parameters=None):
        sql = self._convert_sql(sql)
        if parameters is not None:
            # PyMySQL parameters might be list or tuple. Ensure compatibility.
            if not isinstance(parameters, (tuple, list, dict)):
                parameters = (parameters,)
            return self.cursor.execute(sql, parameters)
        else:
            return self.cursor.execute(sql)

    def executemany(self, sql, seq_of_parameters):
        sql = self._convert_sql(sql)
        return self.cursor.executemany(sql, seq_of_parameters)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [dict(r) for r in rows]

    @property
    def lastrowid(self):
        return self.cursor.lastrowid

    @property
    def rowcount(self):
        return self.cursor.rowcount

    def close(self):
        self.cursor.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _convert_sql(self, sql):
        # Convert %s placeholders to SQLite's ?
        sql = sql.replace("%s", "?")
        # Replace MySQL specific ON DUPLICATE KEY UPDATE with SQLite ON CONFLICT
        if "ON DUPLICATE KEY UPDATE" in sql:
            sql = sql.replace(
                "ON DUPLICATE KEY UPDATE company_name = VALUES(company_name), sector = VALUES(sector)",
                "ON CONFLICT(equity_name) DO UPDATE SET company_name = excluded.company_name, sector = excluded.sector"
            )
        return sql


class SQLiteConnectionWrapper:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON;")

    def cursor(self):
        return SQLiteCursorWrapper(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def init_sqlite_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name       TEXT NOT NULL,
        email           TEXT NOT NULL UNIQUE,
        password_hash   TEXT NOT NULL,
        reset_otp       TEXT DEFAULT NULL,
        reset_otp_exp   DATETIME DEFAULT NULL,
        created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS companies (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name    TEXT NOT NULL,
        equity_name     TEXT NOT NULL UNIQUE,
        sector          TEXT DEFAULT NULL,
        created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS prediction_history (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id             INTEGER NOT NULL,
        company_id          INTEGER NOT NULL,
        input_open          REAL NOT NULL,
        input_high          REAL NOT NULL,
        input_low           REAL NOT NULL,
        input_close         REAL NOT NULL,
        input_traded_qty    INTEGER NOT NULL,
        predicted_price     REAL NOT NULL,
        direction           TEXT CHECK(direction IN ('UP', 'DOWN')) NOT NULL,
        predicted_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
    );

    CREATE INDEX IF NOT EXISTS idx_prediction_user ON prediction_history(user_id);
    CREATE INDEX IF NOT EXISTS idx_prediction_company ON prediction_history(company_id);

    CREATE TABLE IF NOT EXISTS watchlist (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL,
        equity_name     TEXT NOT NULL,
        shares          INTEGER DEFAULT 0,
        buy_price       REAL DEFAULT 0.0,
        added_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE(user_id, equity_name)
    );
    CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id);
    """)
    conn.commit()
    conn.close()


def get_db_type():
    """Returns the active database type ('mysql' or 'sqlite')."""
    return Config.DATABASE_TYPE


def get_connection():
    """Opens a connection to the database. Defaults to SQLite or falls back to it if MySQL fails."""
    if Config.DATABASE_TYPE == "mysql":
        try:
            connection_args = {
                "host": Config.MYSQL_HOST,
                "port": Config.MYSQL_PORT,
                "user": Config.MYSQL_USER,
                "password": Config.MYSQL_PASSWORD,
                "database": Config.MYSQL_DB,
                "cursorclass": pymysql.cursors.DictCursor,
                "autocommit": False,
            }
            if Config.MYSQL_SSL:
                connection_args["ssl"] = {"ssl_mode": "REQUIRED"} # required by aiven
            
            return pymysql.connect(**connection_args)
        except Exception as e:
            print(f"Warning: Failed to connect to MySQL database: {e}. Falling back to SQLite...")
            Config.DATABASE_TYPE = "sqlite"

    # SQLite connection
    db_dir = Config.SQLITE_PATH.parent
    db_dir.mkdir(parents=True, exist_ok=True)
    if not Config.SQLITE_PATH.exists():
        print(f"Initializing SQLite database at {Config.SQLITE_PATH}...")
        init_sqlite_db(Config.SQLITE_PATH)

    return SQLiteConnectionWrapper(str(Config.SQLITE_PATH))


@contextmanager
def db_cursor(commit: bool = False):
    """
    Context manager that yields a cursor and guarantees the connection
    is closed. Set commit=True for INSERT/UPDATE/DELETE statements.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        raise
    finally:
        try:
            cur.close()
        except Exception:
            pass
        conn.close()

