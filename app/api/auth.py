"""Auth API — POST /api/auth/login"""
import bcrypt
from flask import Blueprint, request, jsonify
from ..utils.auth import create_token

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Simple email/password login.
    Returns a JWT token for subsequent requests.
    """
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    # For demo: accept demo@voiceinvoice.in / demo1234
    # In production: query users table and check bcrypt hash
    DEMO_EMAIL = "demo@voiceinvoice.in"
    DEMO_PASS  = "demo1234"

    if email == DEMO_EMAIL and password == DEMO_PASS:
        token = create_token(user_id="demo-user-001", role="admin")
        return jsonify({
            "token": token,
            "user": {"email": email, "name": "Demo Admin", "role": "admin"},
        }), 200

    return jsonify({"error": "Invalid credentials"}), 401
