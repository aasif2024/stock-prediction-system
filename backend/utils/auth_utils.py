"""
utils/auth_utils.py
---------------------------------
Password hashing (bcrypt) and JWT issuing/validation, plus a
@token_required decorator to protect routes.
"""

from functools import wraps
from datetime import datetime, timedelta, timezone

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import bcrypt
import jwt
from flask import request, jsonify, g

from config import Config


def hash_password(plain_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def generate_token(user_id: int, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=Config.JWT_EXPIRY_HOURS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])


def generate_reset_token(email: str) -> str:
    payload = {
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "iat": datetime.now(timezone.utc),
        "purpose": "password_reset"
    }
    return jwt.encode(payload, Config.JWT_SECRET, algorithm="HS256")


def verify_reset_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, Config.JWT_SECRET, algorithms=["HS256"])
        if payload.get("purpose") != "password_reset":
            return None
        return payload.get("email")
    except:
        return None


def send_reset_email(to_email: str, reset_url: str):
    if not Config.SMTP_SERVER or not Config.SMTP_USERNAME or not Config.SMTP_PASSWORD:
        print(f"\n--- MOCK EMAIL ---")
        print(f"To: {to_email}")
        print(f"Subject: Password Reset Request")
        print(f"Reset Link: {reset_url}")
        print(f"------------------\n")
        return
        
    try:
        msg = MIMEMultipart()
        msg["From"] = Config.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = "Password Reset Request"
        
        body = f"Click the following link to reset your password:\n\n{reset_url}\n\nThis link will expire in 15 minutes."
        msg.attach(MIMEText(body, "plain"))
        
        server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
        server.starttls()
        server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")


def token_required(f):
    """Decorator that requires a valid 'Authorization: Bearer <token>' header."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired, please log in again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        g.user_id = payload["user_id"]
        g.email = payload["email"]
        return f(*args, **kwargs)

    return decorated
