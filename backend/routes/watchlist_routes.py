from flask import Blueprint, request, jsonify, g
from utils.auth_utils import token_required
from models.watchlist_model import add_to_watchlist, remove_from_watchlist, get_watchlist
from utils.ml_utils import get_latest_live_data

watchlist_bp = Blueprint("watchlist", __name__, url_prefix="/api/watchlist")

@watchlist_bp.route("/", methods=["GET"])
@token_required
def get_user_watchlist():
    try:
        user_id = g.user_id
        watchlist = get_watchlist(user_id)
        
        # Enrich the watchlist with live data
        enriched_watchlist = []
        for item in watchlist:
            equity_name = item["equity_name"]
            live_data = get_latest_live_data(equity_name)
            
            # Merge dictionary
            enriched_item = dict(item)
            if live_data:
                enriched_item.update(live_data)
            
            enriched_watchlist.append(enriched_item)
            
        return jsonify({"watchlist": enriched_watchlist}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@watchlist_bp.route("/", methods=["POST"])
@token_required
def add_item():
    try:
        user_id = g.user_id
        data = request.json
        equity_name = data.get("equity_name")
        shares = int(data.get("shares", 0))
        buy_price = float(data.get("buy_price", 0.0))
        
        if not equity_name:
            return jsonify({"error": "equity_name is required"}), 400
            
        result = add_to_watchlist(user_id, equity_name, shares, buy_price)
        if result["status"] == "error":
            return jsonify({"error": result["message"]}), 400
            
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@watchlist_bp.route("/<equity_name>", methods=["DELETE"])
@token_required
def remove_item(equity_name):
    try:
        user_id = g.user_id
        result = remove_from_watchlist(user_id, equity_name)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
