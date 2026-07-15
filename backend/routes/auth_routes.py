"""
routes/auth_routes.py
---------------------------------
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
"""

import re

from flask import Blueprint, request, jsonify

from models.user_model import create_user, get_user_by_email, update_user_password
from utils.auth_utils import hash_password, verify_password, generate_token, token_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    full_name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not full_name or not email or not password:
        return jsonify({"error": "full_name, email and password are required"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "Invalid email format"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    if get_user_by_email(email):
        return jsonify({"error": "An account with this email already exists"}), 409

    user_id = create_user(full_name, email, hash_password(password))
    token = generate_token(user_id, email)

    return jsonify({
        "message": "Registration successful",
        "token": token,
        "user": {"id": user_id, "full_name": full_name, "email": email},
    }), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid email or password"}), 401

    token = generate_token(user["id"], user["email"])
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {"id": user["id"], "full_name": user["full_name"], "email": user["email"]},
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@token_required
def logout():
    # JWTs are stateless: "logging out" just means the client discards the
    # token. This endpoint exists for API completeness / future blocklisting.
    return jsonify({"message": "Logged out successfully"}), 200


@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = get_user_by_email(email)
    if user:
        from utils.auth_utils import generate_reset_token, send_reset_email
        from config import Config
        token = generate_reset_token(email)
        reset_url = f"{Config.FRONTEND_URL}/reset-password?token={token}"
        send_reset_email(email, reset_url)

    # Always return success to prevent email enumeration
    return jsonify({"message": "If an account exists, a reset email has been sent."}), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    token = data.get("token")
    new_password = data.get("new_password") or ""

    if not token or not new_password:
        return jsonify({"error": "Token and new password are required"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    from utils.auth_utils import verify_reset_token
    email = verify_reset_token(token)
    if not email:
        return jsonify({"error": "Invalid or expired reset token"}), 400

    user = get_user_by_email(email)
    if not user:
        return jsonify({"error": "User no longer exists"}), 404

    update_user_password(email, hash_password(new_password))

    return jsonify({"message": "Password reset successfully"}), 200

