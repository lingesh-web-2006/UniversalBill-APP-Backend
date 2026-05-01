"""Product API — search, list, AI-estimate"""
from flask import Blueprint, jsonify, request
from ..models import Product
from ..services.ai_service import ai_service
from ..db import query_db, execute_db

product_bp = Blueprint("product", __name__)


@product_bp.route("/", methods=["GET"])
def list_products():
    company_id = request.args.get("company_id")
    search = request.args.get("q", "")

    sql = "SELECT * FROM products WHERE is_active = True"
    params = []
    
    if company_id:
        sql += " AND company_id = %s"
        params.append(company_id)
    if search:
        sql += " AND name ILIKE %s"
        params.append(f"%{search}%")
    
    sql += " ORDER BY name"
    rows = query_db(sql, params)
    products = [Product(**r) for r in rows]
    return jsonify({"products": [p.to_dict() for p in products]}), 200


@product_bp.route("/estimate", methods=["POST"])
def estimate_product():
    """Use AI to estimate price for an unknown product."""
    data = request.get_json(force=True)
    product_name = data.get("product_name")
    if not product_name:
        return jsonify({"error": "product_name is required"}), 400

    result = ai_service.estimate_product_price(
        product_name=product_name,
        company_context=data.get("company_context", "general retail"),
        quantity=data.get("quantity", 1),
        unit=data.get("unit", "piece"),
    )
    if not result["success"]:
        return jsonify({"error": result["error"]}), 422

    return jsonify({"estimate": result["data"]}), 200


@product_bp.route("/", methods=["POST"])
def create_product():
    data = request.get_json(force=True)
    required = ["company_id", "name", "unit_price"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing: {', '.join(missing)}"}), 400

    import json
    keys = ["company_id", "name", "unit_price", "unit", "gst_rate", "hsn_code", "aliases"]
    cols = ", ".join(keys)
    placeholders = ", ".join(["%s"] * len(keys))
    
    # Handle aliases as JSON string for psycopg2
    vals = [
        data["company_id"], 
        data["name"], 
        data["unit_price"], 
        data.get("unit", "piece"),
        data.get("gst_rate", 18.0),
        data.get("hsn_code"),
        json.dumps(data.get("aliases", []))
    ]

    sql = f"INSERT INTO products ({cols}) VALUES ({placeholders}) RETURNING id"
    row = query_db(sql, vals, one=True)
    
    new_row = query_db("SELECT * FROM products WHERE id = %s", [row['id']], one=True)
    return jsonify(Product(**new_row).to_dict()), 201

@product_bp.route("/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json(force=True)
    
    # Check if exists
    exists = query_db("SELECT id FROM products WHERE id = %s", [product_id], one=True)
    if not exists:
        return jsonify({"error": "Product not found"}), 404

    keys = ["name", "unit_price", "unit", "gst_rate", "hsn_code", "aliases"]
    updates = []
    vals = []
    
    import json
    for k in keys:
        if k in data:
            updates.append(f"{k} = %s")
            val = data[k]
            if k == "aliases":
                val = json.dumps(val)
            vals.append(val)
    
    if not updates:
        return jsonify({"error": "No fields to update"}), 400
        
    vals.append(product_id)
    sql = f"UPDATE products SET {', '.join(updates)} WHERE id = %s"
    execute_db(sql, vals)
    
    updated = query_db("SELECT * FROM products WHERE id = %s", [product_id], one=True)
    return jsonify(Product(**updated).to_dict()), 200

@product_bp.route("/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    # Soft delete
    execute_db("UPDATE products SET is_active = False WHERE id = %s", [product_id])
    return jsonify({"success": True}), 200
