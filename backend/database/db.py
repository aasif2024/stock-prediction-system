"""
database/db.py
---------------------------------
Unified database layer supporting:
  - PostgreSQL (Supabase) via psycopg2  →  DATABASE_TYPE=postgres
  - SQLite (local dev / fallback)       →  DATABASE_TYPE=sqlite
  - MySQL                               →  DATABASE_TYPE=mysql

Priority order when DATABASE_URL is set: postgres > mysql > sqlite
"""

import sqlite3
from contextlib import contextmanager

from config import Config


# ─────────────────────────────────────────────────────────────────────────────
# PostgreSQL helpers (psycopg2)
# ─────────────────────────────────────────────────────────────────────────────

class PostgresCursorWrapper:
    """Wraps a psycopg2 cursor to return dict rows (like PyMySQL DictCursor)."""

    def __init__(self, cursor):
        self._cur = cursor

    def execute(self, sql, parameters=None):
        # Convert ON CONFLICT syntax for PostgreSQL (same as SQLite, already compatible)
        sql = self._convert_sql(sql)
        if parameters is not None:
            if not isinstance(parameters, (tuple, list, dict)):
                parameters = (parameters,)
            self._cur.execute(sql, parameters)
        else:
            self._cur.execute(sql)

    def executemany(self, sql, seq):
        sql = self._convert_sql(sql)
        self._cur.executemany(sql, seq)

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        cols = [desc[0] for desc in self._cur.description]
        return dict(zip(cols, row))

    def fetchall(self):
        rows = self._cur.fetchall()
        if not rows:
            return []
        cols = [desc[0] for desc in self._cur.description]
        return [dict(zip(cols, r)) for r in rows]

    @property
    def lastrowid(self):
        return self._cur.fetchone()[0] if self._cur.rowcount > 0 else None

    @property
    def rowcount(self):
        return self._cur.rowcount

    def close(self):
        self._cur.close()

    def _convert_sql(self, sql: str) -> str:
        # MySQL ON DUPLICATE KEY → PostgreSQL ON CONFLICT
        if "ON DUPLICATE KEY UPDATE" in sql:
            sql = sql.replace(
                "ON DUPLICATE KEY UPDATE company_name = VALUES(company_name), sector = VALUES(sector)",
                "ON CONFLICT(equity_name) DO UPDATE SET company_name = EXCLUDED.company_name, sector = EXCLUDED.sector"
            )
        # Replace AUTOINCREMENT (MySQL/SQLite) with SERIAL for Postgres schema init
        sql = sql.replace("AUTOINCREMENT", "")
        return sql


class PostgresConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return PostgresCursorWrapper(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def init_postgres_db(conn):
    """Creates all tables in Supabase/PostgreSQL if they don't exist."""
    cur = conn.cursor()
    cur._cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              SERIAL PRIMARY KEY,
            full_name       VARCHAR(120)  NOT NULL,
            email           VARCHAR(150)  NOT NULL UNIQUE,
            password_hash   VARCHAR(255)  NOT NULL,
            reset_otp       VARCHAR(6)    DEFAULT NULL,
            reset_otp_exp   TIMESTAMP     DEFAULT NULL,
            created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS companies (
            id              SERIAL PRIMARY KEY,
            company_name    VARCHAR(200)  NOT NULL,
            equity_name     VARCHAR(50)   NOT NULL UNIQUE,
            sector          VARCHAR(120)  DEFAULT NULL,
            created_at      TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS prediction_history (
            id                  SERIAL PRIMARY KEY,
            user_id             INTEGER NOT NULL,
            company_id          INTEGER NOT NULL,
            input_open          NUMERIC(12,2) NOT NULL,
            input_high          NUMERIC(12,2) NOT NULL,
            input_low           NUMERIC(12,2) NOT NULL,
            input_close         NUMERIC(12,2) NOT NULL,
            input_traded_qty    BIGINT        NOT NULL,
            predicted_price     NUMERIC(12,2) NOT NULL,
            direction           VARCHAR(4)    NOT NULL CHECK(direction IN ('UP', 'DOWN')),
            predicted_at        TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_pred_user    FOREIGN KEY (user_id)    REFERENCES users(id)     ON DELETE CASCADE,
            CONSTRAINT fk_pred_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_prediction_user    ON prediction_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_prediction_company ON prediction_history(company_id);

        CREATE TABLE IF NOT EXISTS watchlist (
            id              SERIAL PRIMARY KEY,
            user_id         INTEGER NOT NULL,
            equity_name     VARCHAR(50) NOT NULL,
            shares          INTEGER DEFAULT 0,
            buy_price       NUMERIC(12,2) DEFAULT 0.0,
            added_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_watch_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, equity_name)
        );

        CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist(user_id);
    """)
    conn.commit()
    print("[db] PostgreSQL schema initialised.")


# ─────────────────────────────────────────────────────────────────────────────
# SQLite helpers
# ─────────────────────────────────────────────────────────────────────────────

class SQLiteCursorWrapper:
    def __init__(self, sqlite_cursor):
        self.cursor = sqlite_cursor

    def execute(self, sql, parameters=None):
        sql = self._convert_sql(sql)
        if parameters is not None:
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

    def _convert_sql(self, sql):
        sql = sql.replace("%s", "?")
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


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_db_type():
    """Returns the active database type ('postgres', 'mysql', or 'sqlite')."""
    return Config.DATABASE_TYPE


def get_connection():
    """Opens and returns a database connection based on DATABASE_TYPE config."""

    # ── PostgreSQL / Supabase ─────────────────────────────────────────────
    if Config.DATABASE_TYPE == "postgres":
        try:
            import psycopg2
            conn = psycopg2.connect(Config.DATABASE_URL, sslmode="require")
            conn.autocommit = False
            wrapper = PostgresConnectionWrapper(conn)
            # Ensure schema exists on every fresh connection attempt
            init_postgres_db(wrapper)
            return wrapper
        except Exception as e:
            print(f"[db] ERROR: Cannot connect to PostgreSQL: {e}")
            raise

    # ── MySQL ─────────────────────────────────────────────────────────────
    if Config.DATABASE_TYPE == "mysql":
        try:
            import pymysql
            import pymysql.cursors
            args = {
                "host": Config.MYSQL_HOST,
                "port": Config.MYSQL_PORT,
                "user": Config.MYSQL_USER,
                "password": Config.MYSQL_PASSWORD,
                "database": Config.MYSQL_DB,
                "cursorclass": pymysql.cursors.DictCursor,
                "autocommit": False,
            }
            if Config.MYSQL_SSL:
                args["ssl"] = {"ssl_mode": "REQUIRED"}
            return pymysql.connect(**args)
        except Exception as e:
            print(f"[db] Warning: MySQL failed: {e}. Falling back to SQLite...")
            Config.DATABASE_TYPE = "sqlite"

    # ── SQLite (default / fallback) ───────────────────────────────────────
    db_dir = Config.SQLITE_PATH.parent
    db_dir.mkdir(parents=True, exist_ok=True)
    if not Config.SQLITE_PATH.exists():
        print(f"[db] Initialising SQLite DB at {Config.SQLITE_PATH}")
        init_sqlite_db(Config.SQLITE_PATH)
    return SQLiteConnectionWrapper(str(Config.SQLITE_PATH))


@contextmanager
def db_cursor(commit: bool = False):
    """
    Context manager that yields a cursor.
    Set commit=True for INSERT / UPDATE / DELETE.
    Works with PostgreSQL, MySQL, and SQLite.
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
