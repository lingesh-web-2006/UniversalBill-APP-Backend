"""Company API — GET /api/companies, GET /api/companies/<id>"""
from flask import Blueprint, jsonify, request
from ..models import Company
from ..db import query_db, execute_db

company_bp = Blueprint("company", __name__)


@company_bp.route("/", methods=["GET"])
def list_companies():
    rows = query_db("SELECT * FROM companies WHERE is_active = True ORDER BY name")
    companies = [Company(**r) for r in rows]
    return jsonify({"companies": [c.to_dict() for c in companies]}), 200


@company_bp.route("/<company_id>", methods=["GET"])
def get_company(company_id):
    row = query_db("SELECT * FROM companies WHERE id = %s", [company_id], one=True)
    if not row:
        return jsonify({"error": "Company not found"}), 404
    return jsonify(Company(**row).to_dict()), 200


@company_bp.route("/", methods=["POST"])
def create_company():
    data = request.get_json(force=True)
    required = ["name", "gst_number", "address", "city", "state", "pincode"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400

    keys = required + ["phone", "email", "template", "brand_color", "logo_url"]
    cols = ", ".join(keys)
    placeholders = ", ".join(["%s"] * len(keys))
    vals = [data.get(k) for k in keys]

    sql = f"INSERT INTO companies ({cols}) VALUES ({placeholders}) RETURNING id"
    row = query_db(sql, vals, one=True)
    
    # Fetch full object for return
    new_row = query_db("SELECT * FROM companies WHERE id = %s", [row['id']], one=True)
    return jsonify(Company(**new_row).to_dict()), 201


@company_bp.route("/<company_id>", methods=["DELETE"])
def delete_company(company_id):
    """
    Soft delete a company by deactivating it.
    """
    execute_db("UPDATE companies SET is_active = False WHERE id = %s", [company_id])
    return jsonify({"success": True, "message": "Company deactivated"}), 200
