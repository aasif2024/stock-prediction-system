"""
config.py
---------------------------------
Centralized configuration for the Flask backend. All values can be
overridden with environment variables so real credentials never need
to be hard-coded or committed to source control.

Database priority:
  1. If DATABASE_URL is set  → uses PostgreSQL (Supabase)
  2. If DATABASE_TYPE=mysql  → uses MySQL
  3. Otherwise               → uses SQLite (local dev)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-in-production")
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"

    # JWT
    JWT_SECRET = os.environ.get("JWT_SECRET", "change-this-jwt-secret-in-production")
    JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))

    # ── Database ──────────────────────────────────────────────────────────────
    # If DATABASE_URL is provided (Supabase/PostgreSQL), use postgres.
    DATABASE_URL = os.environ.get("DATABASE_URL", "")

    # Auto-detect: if DATABASE_URL is set, override DATABASE_TYPE to postgres
    _default_db_type = "postgres" if os.environ.get("DATABASE_URL") else "sqlite"
    DATABASE_TYPE = os.environ.get("DATABASE_TYPE", _default_db_type)

    # MySQL (legacy / fallback)
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQL_DB", "stock_prediction_db")
    MYSQL_SSL = os.environ.get("MYSQL_SSL", "false").lower() == "true"

    # SQLite (local dev fallback)
    _sqlite_env = os.environ.get("SQLITE_PATH", "")
    SQLITE_PATH = Path(_sqlite_env) if _sqlite_env else BASE_DIR / "database" / "stock_prediction.db"

    # ML artifacts
    ML_MODEL_DIR = BASE_DIR / "ml_model"
    MODEL_PATH = ML_MODEL_DIR / "model.pkl"
    SCALER_PATH = ML_MODEL_DIR / "scaler.pkl"
    ENCODER_PATH = ML_MODEL_DIR / "company_encoder.pkl"
    METADATA_PATH = ML_MODEL_DIR / "metadata.json"

    # CORS
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS",
        "http://localhost:3000,https://stock-prediction-system-seven.vercel.app"
    ).split(",")

    # SMTP Settings
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "noreply@stocksense.com")
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
