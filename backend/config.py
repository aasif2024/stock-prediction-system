"""
config.py
---------------------------------
Centralized configuration for the Flask backend. All values can be
overridden with environment variables so real credentials never need
to be hard-coded or committed to source control.
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

    # MySQL
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQL_DB", "stock_prediction_db")

    # Database selection ('mysql' or 'sqlite')
    DATABASE_TYPE = os.environ.get("DATABASE_TYPE", "sqlite")
    SQLITE_PATH = BASE_DIR.parent / "database" / "stock_prediction.db"

    # ML artifacts
    ML_MODEL_DIR = BASE_DIR / "ml_model"
    MODEL_PATH = ML_MODEL_DIR / "model.pkl"
    SCALER_PATH = ML_MODEL_DIR / "scaler.pkl"
    ENCODER_PATH = ML_MODEL_DIR / "company_encoder.pkl"
    METADATA_PATH = ML_MODEL_DIR / "metadata.json"

    # CORS
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000,https://stock-prediction-system-seven.vercel.app").split(",")

    # SMTP Settings
    SMTP_SERVER = os.environ.get("SMTP_SERVER", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL", "noreply@stocksense.com")
    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
