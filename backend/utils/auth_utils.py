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


import random

def generate_otp() -> str:
    return str(random.randint(100000, 999999))


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


def send_reset_email(to_email: str, otp: str):
    """Send OTP via SMTP. Requires SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD in env."""
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background: #0d0d0d; margin: 0; padding: 20px;">
      <div style="max-width: 480px; margin: auto; background: #1a1a2e; border-radius: 16px;
                  padding: 40px; border: 1px solid #2a2a4a; text-align: center;">
        <h2 style="color: #00e676; margin-bottom: 8px;">Password Reset OTP</h2>
        <p style="color: #b3b3b3; font-size: 14px; margin-bottom: 32px;">
          You requested a password reset for your <strong style="color:#fff;">Stock Prediction System</strong> account.
        </p>
        <div style="background: #0d0d0d; border-radius: 12px; padding: 24px; margin-bottom: 24px;">
          <p style="color: #b3b3b3; font-size: 13px; margin: 0 0 8px;">Your One-Time Password is:</p>
          <p style="color: #00e676; font-size: 40px; font-weight: bold; letter-spacing: 12px;
                    margin: 0; font-family: monospace;">{otp}</p>
        </div>
        <p style="color: #ff5252; font-size: 13px; margin-bottom: 24px;">
          ⏱ This OTP expires in <strong>10 minutes</strong>.
        </p>
        <p style="color: #666; font-size: 12px;">
          If you did not request this, you can safely ignore this email. Your password will not change.
        </p>
      </div>
    </body>
    </html>
    """
    plain_body = f"Your password reset OTP is: {otp}\n\nThis code will expire in 10 minutes.\n\nIf you did not request this, ignore this email."

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = Config.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg["Subject"] = f"Your OTP: {otp} — Stock Prediction System"

        msg.attach(MIMEText(plain_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"OTP email sent to {to_email}")
    except Exception as e:
        print(f"ERROR: Failed to send email to {to_email}: {e}")
        raise  # Re-raise so route can return a 500 if needed



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
