"""
routes/company_routes.py
---------------------------------
GET /api/companies
"""

from flask import Blueprint, jsonify

from models.company_model import get_all_companies
from utils.auth_utils import token_required

company_bp = Blueprint("companies", __name__, url_prefix="/api/companies")


@company_bp.route("", methods=["GET"])
@token_required
def list_companies():
    companies = get_all_companies()
    return jsonify({"companies": companies}), 200
