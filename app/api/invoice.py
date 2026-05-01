"""
Invoice API
  POST /api/invoice/generate  — Save a confirmed invoice
  POST /api/invoice/pdf       — Generate PDF for an invoice
  GET  /api/invoice/          — List invoices
  GET  /api/invoice/<id>      — Get single invoice
"""
import base64
from flask import Blueprint, request, jsonify, send_file
import io
from ..services.invoice_service import invoice_service
from ..services.pdf_service import generate_invoice_pdf
from ..models import Invoice, Company, InvoiceItem
from ..db import query_db, execute_db
from ..utils.validators import validate_required

invoice_bp = Blueprint("invoice", __name__)


@invoice_bp.route("/generate", methods=["POST"])
def generate_invoice():
    """Body: company_id, invoice_data"""
    data = request.get_json(force=True)
    error = validate_required(data, ["company_id", "invoice_data"])
    if error:
        return jsonify({"error": error}), 400

    try:
        # save_invoice now returns a dictionary
        invoice_dict = invoice_service.save_invoice(
            company_id=data["company_id"],
            invoice_data=data["invoice_data"],
        )
        return jsonify({
            "success": True,
            "invoice": invoice_dict,
            "invoice_id": str(invoice_dict["id"]),
            "invoice_number": invoice_dict["invoice_number"],
        }), 201
    except Exception as e:
        return jsonify({"error": f"Failed to save invoice: {str(e)}"}), 500


@invoice_bp.route("/pdf", methods=["POST"])
def download_pdf():
    """Body: invoice_id OR invoice_data"""
    data = request.get_json(force=True)

    if "invoice_id" in data:
        row = query_db("SELECT * FROM invoices WHERE id = %s", [data["invoice_id"]], one=True)
        if not row:
            return jsonify({"error": "Invoice not found"}), 404
        
        # Hydrate with items and company for PDF
        invoice_obj = Invoice(**row)
        items = query_db("SELECT * FROM invoice_items WHERE invoice_id = %s ORDER BY sort_order", [row['id']])
        invoice_obj.items = [InvoiceItem(**itm) for itm in items]
        
        comp_row = query_db("SELECT * FROM companies WHERE id = %s", [row['company_id']], one=True)
        invoice_obj.company = Company(**comp_row)
        
        invoice_dict = invoice_obj.to_dict()
    elif "invoice_data" in data:
        invoice_dict = data["invoice_data"]
    else:
        return jsonify({"error": "Provide invoice_id or invoice_data"}), 400

    try:
        pdf_bytes = generate_invoice_pdf(invoice_dict)
        encoded = base64.b64encode(pdf_bytes).decode("utf-8")
        filename = f"{invoice_dict.get('invoice_number', 'invoice')}.pdf"
        return jsonify({
            "success": True,
            "filename": filename,
            "pdf_base64": encoded,
        }), 200
    except Exception as e:
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500


@invoice_bp.route("/", methods=["GET"])
def list_invoices():
    """List invoices with manual pagination."""
    company_id = request.args.get("company_id")
    status = request.args.get("status")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    offset = (page - 1) * per_page

    sql = "SELECT * FROM invoices WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = %s"
        params.append(company_id)
    if status:
        sql += " AND status = %s"
        params.append(status)

    # Get total count for pagination
    count_sql = sql.replace("SELECT *", "SELECT COUNT(*) AS cnt")
    count_row = query_db(count_sql, params, one=True)
    total_count = count_row['cnt']

    # Get page items
    sql += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
    page_params = params + [per_page, offset]
    rows = query_db(sql, page_params)
    
    invoices = []
    for r in rows:
        inv = Invoice(**r)
        # Fetch items for each (inefficient but matches old behavior)
        # In a real app we'd join, but keeping it simple for now
        item_rows = query_db("SELECT * FROM invoice_items WHERE invoice_id = %s", [r['id']])
        inv.items = [InvoiceItem(**ir) for ir in item_rows]
        invoices.append(inv.to_dict())

    pages = (total_count + per_page - 1) // per_page

    return jsonify({
        "invoices": invoices,
        "total": total_count,
        "page": page,
        "pages": pages,
    }), 200


@invoice_bp.route("/<invoice_id>", methods=["GET"])
def get_invoice(invoice_id):
    row = query_db("SELECT * FROM invoices WHERE id = %s", [invoice_id], one=True)
    if not row:
        return jsonify({"error": "Invoice not found"}), 404
    
    inv = Invoice(**row)
    item_rows = query_db("SELECT * FROM invoice_items WHERE invoice_id = %s ORDER BY sort_order", [row['id']])
    inv.items = [InvoiceItem(**ir) for ir in item_rows]
    
    comp_row = query_db("SELECT * FROM companies WHERE id = %s", [row['company_id']], one=True)
    inv.company = Company(**comp_row)
    
    return jsonify(inv.to_dict()), 200

@invoice_bp.route("/<invoice_id>", methods=["DELETE"])
def delete_invoice(invoice_id):
    row = query_db("SELECT * FROM invoices WHERE id = %s", [invoice_id], one=True)
    if not row:
        return jsonify({"error": "Invoice not found"}), 404
        
    try:
        # Delete invoice items first to respect foreign key constraints
        execute_db("DELETE FROM invoice_items WHERE invoice_id = %s", [invoice_id])
        # Delete the invoice itself
        execute_db("DELETE FROM invoices WHERE id = %s", [invoice_id])
        return jsonify({"success": True, "message": "Invoice deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to delete invoice: {str(e)}"}), 500
