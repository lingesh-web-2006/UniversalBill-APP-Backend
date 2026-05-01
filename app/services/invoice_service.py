"""
Invoice Service — Core business logic for invoice creation.
Handles product lookup, AI price estimation fallback, and tax calculations.
Uses raw psycopg2 for performance and control.
"""

from decimal import Decimal
import json
from ..db import query_db, execute_db
from ..models import Company, Product, Invoice, InvoiceItem
from .ai_service import ai_service
from ..utils.fuzzy_match import find_best_match


class InvoiceService:
    """Orchestrates invoice creation from parsed AI data."""

    def find_product(self, company_id: str, product_name: str) -> Product | None:
        """
        Fuzzy search for a product by name or aliases using raw SQL.
        """
        from flask import g
        db_type = getattr(g, 'db_type', 'postgres')

        # 1. Try full-text search (Postgres only)
        if db_type == 'postgres':
            fts_query = """
                SELECT * FROM products 
                WHERE company_id = %s AND is_active = True
                AND to_tsvector('english', name) @@ plainto_tsquery('english', %s)
                LIMIT 1
            """
            row = query_db(fts_query, [company_id, product_name], one=True)
            if row:
                return Product(**row)

        # 2. Fallback to ILIKE (Postgres) or LIKE (SQLite) on name
        name_op = "ILIKE" if db_type == "postgres" else "LIKE"
        ilike_query = f"""
            SELECT * FROM products 
            WHERE company_id = %s AND is_active = True
            AND name {name_op} %s
            LIMIT 1
        """
        row = query_db(ilike_query, [company_id, f"%{product_name}%"], one=True)
        if row:
            return Product(**row)

        # 3. Check aliases
        from flask import g
        db_type = getattr(g, 'db_type', 'postgres')
        
        if db_type == 'postgres':
            alias_query = """
                SELECT * FROM products 
                WHERE company_id = %s AND is_active = True
                AND aliases @> %s::jsonb
                LIMIT 1
            """
            import json
            row = query_db(alias_query, [company_id, json.dumps([product_name.lower()])], one=True)
        else:
            # SQLite fallback: aliases are stored as a JSON string. We'll use a loose LIKE check.
            alias_query = """
                SELECT * FROM products 
                WHERE company_id = %s AND is_active = True
                AND aliases LIKE %s
                LIMIT 1
            """
            row = query_db(alias_query, [company_id, f'%"{product_name.lower()}"%'], one=True)

        if row:
            return Product(**row)

        # 4. Final Fuzzy Fallback (Python-side)
        all_products_rows = query_db(
            "SELECT * FROM products WHERE company_id = %s AND is_active = True",
            [company_id]
        )
        if not all_products_rows:
            return None

        names = [r['name'] for r in all_products_rows]
        match, score = find_best_match(product_name, names, threshold=0.6)
        
        if match:
            matched_row = next(r for r in all_products_rows if r['name'] == match)
            return Product(**matched_row)

        return None

    def find_customer(self, company_id: str, customer_query: str) -> str | None:
        """
        Fuzzy search for a customer name based on historical invoices.
        """
        if not customer_query or customer_query.lower() in ("none", "null", "customer"):
            return None

        # Fetch unique historical customer names for this company
        rows = query_db(
            "SELECT DISTINCT customer_name FROM invoices WHERE company_id = %s",
            [company_id]
        )
        if not rows:
            return None

        names = [r['customer_name'] for r in rows]
        match, score = find_best_match(customer_query, names, threshold=0.6)
        
        return match if match else None

    def calculate_item_taxes(
        self,
        unit_price: float,
        quantity: float,
        gst_rate: float,
        supply_type: str = "intra",
    ) -> dict:
        """GST breakdown calculation."""
        taxable = round(Decimal(str(unit_price)) * Decimal(str(quantity)), 2)
        gst_decimal = Decimal(str(gst_rate)) / 100
        gst_total = round(taxable * gst_decimal, 2)

        if supply_type == "inter":
            return {
                "taxable_amount": float(taxable),
                "cgst": 0.0,
                "sgst": 0.0,
                "igst": float(gst_total),
                "gst_amount": float(gst_total),
                "total_amount": float(taxable + gst_total),
            }
        else:
            half = round(gst_total / 2, 2)
            return {
                "taxable_amount": float(taxable),
                "cgst": float(half),
                "sgst": float(gst_total - half),
                "igst": 0.0,
                "gst_amount": float(gst_total),
                "total_amount": float(taxable + gst_total),
            }

    def build_invoice_from_ai(self, company_id: str, parsed_data: dict) -> dict:
        """Orchestrates invoice creation from parsed AI data."""
        print(f"DEBUG: Parsed data received for processing: {json.dumps(parsed_data, indent=2)}")
        
        comp_row = query_db("SELECT * FROM companies WHERE id = %s", [company_id], one=True)
        if not comp_row:
            return {"success": False, "error": "Company not found"}
        
        company = Company(**comp_row)
        company_context = f"{company.name} — {company.city}, {company.state}"
        
        try:
            supply_type = parsed_data.get("supply_type", "intra")
            bonus = Decimal(str(parsed_data.get("bonus", 0)))
        except Exception as e:
            print(f"ERROR in invoice extraction: {e}. Data: {parsed_data}")
            raise e
        resolved_items = []
        total_subtotal = Decimal("0")
        total_cgst = Decimal("0")
        total_sgst = Decimal("0")
        total_igst = Decimal("0")

        for raw_item in parsed_data.get("items", []):
            product_name = raw_item.get("product_name", "Unknown Product")
            quantity = float(raw_item.get("quantity", 1))
            unit = raw_item.get("unit", "piece")
            stated_price = raw_item.get("unit_price")

            db_product = self.find_product(company_id, product_name)
            ai_estimated = False
            product_id = None

            if db_product and stated_price is None:
                unit_price = float(db_product.unit_price)
                gst_rate = float(db_product.gst_rate)
                hsn_code = db_product.hsn_code
                product_id = str(db_product.id)
            elif stated_price is not None:
                unit_price = float(stated_price)
                gst_rate = float(db_product.gst_rate) if db_product else 18.0
                hsn_code = db_product.hsn_code if db_product else None
            else:
                estimate_result = ai_service.estimate_product_price(
                    product_name=product_name,
                    company_context=company_context,
                    quantity=quantity,
                    unit=unit,
                )
                if estimate_result["success"]:
                    est = estimate_result["data"]
                    unit_price = float(est["unit_price"])
                    gst_rate = float(est["gst_rate"])
                    hsn_code = est.get("hsn_code")
                else:
                    unit_price = 999.0
                    gst_rate = 18.0
                    hsn_code = None
                ai_estimated = True

            tax = self.calculate_item_taxes(unit_price, quantity, gst_rate, supply_type)
            resolved_items.append({
                "product_id": product_id,
                "product_name": db_product.name if db_product else product_name,
                "quantity": quantity,
                "unit": unit,
                "unit_price": unit_price,
                "gst_rate": gst_rate,
                "hsn_code": hsn_code,
                "taxable_amount": tax["taxable_amount"],
                "gst_amount": tax["gst_amount"],
                "total_amount": tax["total_amount"],
                "ai_estimated": ai_estimated,
                "cgst": tax["cgst"],
                "sgst": tax["sgst"],
                "igst": tax["igst"]
            })

            total_subtotal += Decimal(str(tax["taxable_amount"]))
            total_cgst += Decimal(str(tax["cgst"]))
            total_sgst += Decimal(str(tax["sgst"]))
            total_igst += Decimal(str(tax["igst"]))

        total = total_subtotal + total_cgst + total_sgst + total_igst + bonus

        customer_name = parsed_data.get("customer_name")
        
        # Try fuzzy match for existing customer
        fuzzy_customer = self.find_customer(company_id, customer_name)
        if fuzzy_customer:
            customer_name = fuzzy_customer

        if not customer_name or str(customer_name).strip().lower() in ("", "none", "null", "customer"):
            customer_name = self._get_next_user_name()

        return {
            "success": True,
            "preview": {
                "company": company.to_dict(),
                "customer_name": customer_name,
                "customer_company": parsed_data.get("customer_company"),
                "customer_store": parsed_data.get("customer_store"),
                "customer_gst": parsed_data.get("customer_gst"),
                "customer_address": parsed_data.get("customer_address"),
                "supply_type": supply_type,
                "items": resolved_items,
                "subtotal": float(total_subtotal),
                "cgst_amount": float(total_cgst),
                "sgst_amount": float(total_sgst),
                "igst_amount": float(total_igst),
                "bonus": float(bonus),
                "total_amount": float(total),
                "ai_confidence": parsed_data.get("confidence", 0.8),
            }
        }

    def _get_next_user_name(self) -> str:
        """Helper to get the next sequential 'User N'."""
        # In psycopg2, % must be escaped as %% in strings to avoid being treated as a placeholder
        rows = query_db("SELECT customer_name FROM invoices WHERE customer_name LIKE %s", ["User %"])
        max_num = 0
        for r in rows:
            name = r['customer_name']
            try:
                num_part = name.split("User ")[1]
                num = int(num_part)
                if num > max_num:
                    max_num = num
            except:
                pass
        return f"User {max_num + 1}"

    def save_invoice(self, company_id: str, invoice_data: dict) -> dict:
        """Persist invoice to DB using raw SQL."""
        import uuid
        from flask import g
        from ..db import get_db_connection
        
        invoice_id = str(uuid.uuid4())
        
        # Ensure connection is established so g.db_type is set
        get_db_connection()
        db_type = getattr(g, 'db_type', 'postgres')

        # Get next invoice number
        if db_type == 'postgres':
            # Case company_id to UUID to avoid syntax errors if it's malformed
            company_id = str(company_id)
            inv_num_row = query_db("SELECT next_invoice_number()", one=True)
            inv_num = inv_num_row['next_invoice_number']
        else:
            cnt_row = query_db("SELECT COUNT(*) AS c FROM invoices", one=True)
            inv_num = f"INV-{1001 + cnt_row['c']}"

        # Check for empty customer name
        customer_name = invoice_data.get("customer_name")
        if not customer_name or str(customer_name).strip().lower() in ("", "none", "null", "customer"):
            customer_name = self._get_next_user_name()

        # Insert Invoice
        invoice_insert = """
            INSERT INTO invoices (
                id, invoice_number, company_id, customer_name, customer_company, customer_store, 
                customer_gst, customer_address, subtotal, cgst_amount, sgst_amount, igst_amount, 
                bonus, total_amount, supply_type, status, ai_processed, ai_confidence
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        params = (
            invoice_id, inv_num, company_id, customer_name, 
            invoice_data.get("customer_company"), invoice_data.get("customer_store"),
            invoice_data.get("customer_gst"), invoice_data.get("customer_address"), 
            invoice_data["subtotal"], invoice_data["cgst_amount"], invoice_data["sgst_amount"], 
            invoice_data["igst_amount"], invoice_data.get("bonus", 0), invoice_data["total_amount"],
            invoice_data.get("supply_type", "intra"), "generated", True, 
            invoice_data.get("ai_confidence")
        )
        
        inv_id_row = query_db(invoice_insert, params, one=True)
        # Some SQLite versions might not return RETURNING properly in our db.py setup, so we just use the uuid
        invoice_id = invoice_id

        # Insert Items
        item_insert = """
            INSERT INTO invoice_items (
                invoice_id, product_name, hsn_code, quantity, unit,
                unit_price, gst_rate, taxable_amount, gst_amount, total_amount,
                ai_estimated, sort_order
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for i, item in enumerate(invoice_data.get("items", [])):
            execute_db(item_insert, (
                invoice_id, item["product_name"], item.get("hsn_code"),
                item["quantity"], item.get("unit", "piece"), item["unit_price"],
                item["gst_rate"], item["taxable_amount"], item["gst_amount"],
                item["total_amount"], item.get("ai_estimated", False), i
            ))

        # Re-fetch for return (as a dict)
        full_invoice = query_db("SELECT * FROM invoices WHERE id = %s", [invoice_id], one=True)
        items = query_db("SELECT * FROM invoice_items WHERE invoice_id = %s ORDER BY sort_order", [invoice_id])
        full_invoice['items'] = items
        
        # Fetch company details too
        comp = query_db("SELECT * FROM companies WHERE id = %s", [company_id], one=True)
        full_invoice['company'] = comp
        
        return full_invoice


# Module-level singleton
invoice_service = InvoiceService()
