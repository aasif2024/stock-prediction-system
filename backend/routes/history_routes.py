"""
routes/history_routes.py
---------------------------------
GET /api/history
"""

from flask import Blueprint, jsonify, g

from models.prediction_model import get_predictions_for_user, delete_prediction
from utils.auth_utils import token_required

history_bp = Blueprint("history", __name__, url_prefix="/api/history")


@history_bp.route("", methods=["GET"])
@token_required
def history():
    predictions = get_predictions_for_user(g.user_id)
    return jsonify({"history": predictions}), 200


@history_bp.route("/<int:prediction_id>", methods=["DELETE"])
@token_required
def delete_history_item(prediction_id):
    success = delete_prediction(g.user_id, prediction_id)
    if success:
        return jsonify({"message": "Prediction deleted successfully"}), 200
    else:
        return jsonify({"error": "Prediction not found or unauthorized"}), 404
