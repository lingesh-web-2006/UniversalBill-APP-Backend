"""
Data models — Plain Python classes for type safety and serialization.
Replaces SQLAlchemy ORM classes.
"""
from datetime import date, datetime

class Company:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.gst_number = kwargs.get('gst_number')
        self.address = kwargs.get('address')
        self.city = kwargs.get('city')
        self.state = kwargs.get('state')
        self.pincode = kwargs.get('pincode')
        self.phone = kwargs.get('phone')
        self.email = kwargs.get('email')
        self.logo_url = kwargs.get('logo_url')
        self.template = kwargs.get('template', 'default')
        self.brand_color = kwargs.get('brand_color', '#1a56db')
        self.is_active = kwargs.get('is_active', True)

    def to_dict(self):
        return {
            "id": str(self.id) if self.id else None,
            "name": self.name,
            "gst_number": self.gst_number,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "pincode": self.pincode,
            "phone": self.phone,
            "email": self.email,
            "logo_url": self.logo_url,
            "template": self.template,
            "brand_color": self.brand_color,
        }

class Product:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.company_id = kwargs.get('company_id')
        self.name = kwargs.get('name')
        self.aliases = kwargs.get('aliases', [])
        self.unit_price = kwargs.get('unit_price')
        self.unit = kwargs.get('unit', 'piece')
        self.gst_rate = kwargs.get('gst_rate', 18.00)
        self.hsn_code = kwargs.get('hsn_code')
        self.ai_estimated = kwargs.get('ai_estimated', False)

    def to_dict(self):
        return {
            "id": str(self.id) if self.id else None,
            "name": self.name,
            "aliases": self.aliases or [],
            "unit_price": float(self.unit_price) if self.unit_price else 0,
            "unit": self.unit,
            "gst_rate": float(self.gst_rate),
            "hsn_code": self.hsn_code,
            "ai_estimated": self.ai_estimated,
        }

class Invoice:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.invoice_number = kwargs.get('invoice_number')
        self.company_id = kwargs.get('company_id')
        self.customer_name = kwargs.get('customer_name')
        self.customer_company = kwargs.get('customer_company')
        self.customer_store = kwargs.get('customer_store')
        self.customer_gst = kwargs.get('customer_gst')
        self.customer_address = kwargs.get('customer_address')
        self.subtotal = kwargs.get('subtotal', 0)
        self.cgst_amount = kwargs.get('cgst_amount', 0)
        self.sgst_amount = kwargs.get('sgst_amount', 0)
        self.igst_amount = kwargs.get('igst_amount', 0)
        self.bonus = kwargs.get('bonus', 0)
        self.total_amount = kwargs.get('total_amount', 0)
        self.supply_type = kwargs.get('supply_type', 'intra')
        self.status = kwargs.get('status', 'draft')
        self.invoice_date = kwargs.get('invoice_date', date.today())
        self.items = kwargs.get('items', [])
        self.company = kwargs.get('company') # Populated during serialization if needed

    def to_dict(self):
        return {
            "id": str(self.id) if self.id else None,
            "invoice_number": self.invoice_number,
            "company": self.company.to_dict() if self.company else None,
            "customer_name": self.customer_name,
            "customer_company": self.customer_company,
            "customer_store": self.customer_store,
            "customer_gst": self.customer_gst,
            "customer_address": self.customer_address,
            "subtotal": float(self.subtotal),
            "cgst_amount": float(self.cgst_amount),
            "sgst_amount": float(self.sgst_amount),
            "igst_amount": float(self.igst_amount),
            "bonus": float(self.bonus),
            "total_amount": float(self.total_amount),
            "supply_type": self.supply_type,
            "status": self.status,
            "invoice_date": self.invoice_date.isoformat() if hasattr(self.invoice_date, 'isoformat') else str(self.invoice_date),
            "items": [item.to_dict() if hasattr(item, 'to_dict') else item for item in self.items],
        }

class InvoiceItem:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.invoice_id = kwargs.get('invoice_id')
        self.product_name = kwargs.get('product_name')
        self.hsn_code = kwargs.get('hsn_code')
        self.quantity = kwargs.get('quantity', 1)
        self.unit = kwargs.get('unit', 'piece')
        self.unit_price = kwargs.get('unit_price')
        self.gst_rate = kwargs.get('gst_rate', 18.00)
        self.taxable_amount = kwargs.get('taxable_amount')
        self.gst_amount = kwargs.get('gst_amount')
        self.total_amount = kwargs.get('total_amount')
        self.ai_estimated = kwargs.get('ai_estimated', False)

    def to_dict(self):
        return {
            "id": str(self.id) if self.id else None,
            "product_name": self.product_name,
            "hsn_code": self.hsn_code,
            "quantity": float(self.quantity),
            "unit": self.unit,
            "unit_price": float(self.unit_price),
            "gst_rate": float(self.gst_rate),
            "taxable_amount": float(self.taxable_amount),
            "gst_amount": float(self.gst_amount),
            "total_amount": float(self.total_amount),
            "ai_estimated": self.ai_estimated,
        }

class Customer:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.name = kwargs.get('name')
        self.company_id = kwargs.get('company_id')
        self.gst_number = kwargs.get('gst_number')
        self.address = kwargs.get('address')
        self.city = kwargs.get('city')
        self.state = kwargs.get('state')
        self.pincode = kwargs.get('pincode')
        self.phone = kwargs.get('phone')
        self.email = kwargs.get('email')
        self.is_active = kwargs.get('is_active', True)

    def to_dict(self):
        return {
            "id": str(self.id) if self.id else None,
            "name": self.name,
            "company_id": self.company_id,
            "gst_number": self.gst_number,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "pincode": self.pincode,
            "phone": self.phone,
            "email": self.email,
            "is_active": self.is_active,
        }
