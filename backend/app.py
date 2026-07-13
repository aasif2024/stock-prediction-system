"""
app.py
---------------------------------
Flask application factory + entry point for the Stock Market Price
Prediction System backend.

Run:
    python app.py
"""

import decimal
from datetime import date, datetime

from flask import Flask, jsonify
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS

from config import Config
from routes.auth_routes import auth_bp
from routes.company_routes import company_bp
from routes.predict_routes import predict_bp
from routes.history_routes import history_bp
from routes.watchlist_routes import watchlist_bp


class CustomJSONProvider(DefaultJSONProvider):
    """Teaches Flask's JSON encoder how to serialize Decimal/datetime
    values that come back from MySQL rows."""

    @staticmethod
    def default(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return DefaultJSONProvider.default(obj)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    app.json_provider_class = CustomJSONProvider
    app.json = CustomJSONProvider(app)

    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

    app.register_blueprint(auth_bp)
    app.register_blueprint(company_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(watchlist_bp)

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "stock-prediction-backend"}), 200

    @app.errorhandler(404)
    def not_found(_e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def server_error(_e):
        return jsonify({"error": "Internal server error"}), 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
