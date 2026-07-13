"""
routes/predict_routes.py
---------------------------------
POST /api/predict
"""

from flask import Blueprint, request, jsonify, g

from models.company_model import get_company_by_equity
from models.prediction_model import save_prediction
from utils.auth_utils import token_required
from utils.ml_utils import predict_price

predict_bp = Blueprint("predict", __name__, url_prefix="/api/predict")


@predict_bp.route("", methods=["POST"])
@token_required
def predict():
    data = request.get_json(silent=True) or {}

    required = ["equity_name", "open", "high", "low", "close", "traded_qty"]
    missing = [f for f in required if data.get(f) in (None, "")]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    try:
        equity_name = str(data["equity_name"]).strip().upper()
        open_ = float(data["open"])
        high = float(data["high"])
        low = float(data["low"])
        close = float(data["close"])
        traded_qty = float(data["traded_qty"])
    except (TypeError, ValueError):
        return jsonify({"error": "open, high, low, close, traded_qty must be numeric"}), 400

    if high < low:
        return jsonify({"error": "'high' cannot be less than 'low'"}), 400

    from utils.ml_utils import predict_price, get_historical_data
    
    # Fetch real history to ensure production-grade accuracy for rolling indicators (RSI, MA20, etc.)
    real_history = get_historical_data(equity_name, days=50)

    try:
        result = predict_price(equity_name, open_, high, low, close, traded_qty, history=real_history)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 500

    company = get_company_by_equity(equity_name)
    if company:
        save_prediction(
            user_id=g.user_id,
            company_id=company["id"],
            input_open=open_, input_high=high, input_low=low, input_close=close,
            input_traded_qty=traded_qty,
            predicted_price=result["predicted_price"],
            direction=result["direction"],
        )

    return jsonify({
        "equity_name": equity_name,
        "last_close": close,
        **result,
    }), 200

@predict_bp.route("/history/<equity_name>", methods=["GET"])
@token_required
def history(equity_name):
    from utils.ml_utils import get_historical_data
    try:
        data = get_historical_data(equity_name)
        return jsonify({"historical_data": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@predict_bp.route("/latest/<equity_name>", methods=["GET"])
@token_required
def latest_live(equity_name):
    from utils.ml_utils import get_latest_live_data
    try:
        data = get_latest_live_data(equity_name)
        if not data:
            return jsonify({"error": f"Failed to fetch live data for {equity_name}"}), 404
        return jsonify({"live_data": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@predict_bp.route("/latest-all", methods=["GET"])
@token_required
def latest_all():
    from utils.ml_utils import get_all_latest_live_data
    from models.company_model import get_all_companies
    try:
        # Get all supported companies
        companies = get_all_companies()
        equity_names = [c["equity_name"] for c in companies]
        
        # Fetch live data in bulk
        data = get_all_latest_live_data(equity_names)
        return jsonify({"live_data": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@predict_bp.route("/news/<equity_name>", methods=["GET"])
@token_required
def get_news(equity_name):
    from utils.ml_utils import get_company_news
    try:
        news = get_company_news(equity_name)
        return jsonify({"news": news}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
