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
        from utils.auth_utils import generate_otp, send_reset_email
        from models.user_model import save_password_reset_otp
        from datetime import datetime, timedelta
        
        otp = generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        save_password_reset_otp(email, otp, expires_at)
        send_reset_email(email, otp)

    # Always return success to prevent email enumeration
    return jsonify({"message": "If an account exists, a reset OTP has been sent."}), 200


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    otp = data.get("otp") or ""
    new_password = data.get("new_password") or ""

    if not email or not otp or not new_password:
        return jsonify({"error": "Email, OTP and new password are required"}), 400

    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    from models.user_model import get_user_by_email_with_otp, update_user_password
    user = get_user_by_email_with_otp(email)
    if not user:
        return jsonify({"error": "No account found with this email"}), 404
        
    db_otp = user.get("reset_otp")
    db_exp_str = user.get("reset_otp_exp")
    
    if not db_otp or db_otp != otp:
        return jsonify({"error": "Invalid OTP"}), 400
        
    if not db_exp_str:
        return jsonify({"error": "OTP expired"}), 400
        
    from datetime import datetime
    try:
        if isinstance(db_exp_str, str):
            db_exp = datetime.strptime(db_exp_str, "%Y-%m-%d %H:%M:%S.%f")
        else:
            db_exp = db_exp_str
            
        if datetime.utcnow() > db_exp:
            return jsonify({"error": "OTP has expired"}), 400
    except ValueError:
        try:
            db_exp = datetime.strptime(db_exp_str, "%Y-%m-%d %H:%M:%S")
            if datetime.utcnow() > db_exp:
                return jsonify({"error": "OTP has expired"}), 400
        except Exception:
            pass

    update_user_password(email, hash_password(new_password))

    return jsonify({"message": "Password reset successfully"}), 200

