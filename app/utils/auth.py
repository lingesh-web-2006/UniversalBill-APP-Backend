"""JWT auth utilities."""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app


def create_token(user_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "role": role,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=current_app.config["JWT_EXPIRY_HOURS"]),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])


def require_auth(f):
    """Decorator — validates Bearer JWT on protected routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing token"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
            request.user_id = payload["sub"]
            request.user_role = payload["role"]
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated
