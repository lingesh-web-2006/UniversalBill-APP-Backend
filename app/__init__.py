"""
VoiceInvoice Backend
Flask application factory with FastAPI integration.
"""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from flask import Flask, json
from flask_cors import CORS
from .config import Config
from .db import close_db_connection
from .api.voice import voice_bp
from .api.invoice import invoice_bp
from .api.company import company_bp
from .api.product import product_bp
from .api.auth import auth_bp

class CustomJSONProvider(json.provider.DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


def create_app(config: Config = None) -> Flask:
    """Application factory — creates and configures the Flask app."""
    app = Flask(__name__)
    app.config.from_object(config or Config())
    app.json_provider_class = CustomJSONProvider
    app.json = CustomJSONProvider(app)

    # Initialize database teardown
    app.teardown_appcontext(close_db_connection)

    CORS(app, origins=app.config["CORS_ORIGINS"].split(","))

    # Register blueprints (all under /api prefix)
    app.register_blueprint(auth_bp,    url_prefix="/api/auth")
    app.register_blueprint(voice_bp,   url_prefix="/api/voice")
    app.register_blueprint(invoice_bp, url_prefix="/api/invoice")
    app.register_blueprint(company_bp, url_prefix="/api/companies")
    app.register_blueprint(product_bp, url_prefix="/api/products")

    # Global error handlers
    register_error_handlers(app)

    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        tb = traceback.format_exc()
        # Save to file to ensure we can read it
        with open("crash_debug.txt", "w") as f:
            f.write(tb)
        print(f"GLOBAL ERROR CAUGHT: {e}")
        print(tb)
        return {"error": "Internal Server Error", "message": str(e), "traceback_saved": True}, 500

    return app


import traceback

def register_error_handlers(app: Flask):
    """Register global error handlers for consistent API responses."""
    
    @app.errorhandler(400)
    def bad_request(e):
        return {"error": "Bad request", "message": str(e)}, 400

    @app.errorhandler(401)
    def unauthorized(e):
        return {"error": "Unauthorized", "message": "Invalid or missing token"}, 401

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not found", "message": str(e)}, 404

    @app.errorhandler(429)
    def rate_limited(e):
        return {"error": "Rate limited", "message": "Too many requests"}, 429

    @app.errorhandler(500)
    def server_error(e):
        tb = traceback.format_exc()
        try:
            with open("debug_error.log", "a") as f:
                f.write(f"\n--- {datetime.now()} ---\n{tb}\n")
        except:
            pass
        return {"error": "Internal server error", "message": str(e), "traceback": tb}, 500
