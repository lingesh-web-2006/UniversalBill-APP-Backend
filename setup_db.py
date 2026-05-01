import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Postgre@localhost:1508/voiceinvoice")

schema_sql = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS companies (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name        VARCHAR(255) NOT NULL,
    gst_numb er  VARCHAR(20) UNIQUE NOT NULL,
    address     TEXT NOT NULL,
    city        VARCHAR(100) NOT NULL,
    state       VARCHAR(100) NOT NULL,
    pincode     VARCHAR(10) NOT NULL,
    phone       VARCHAR(20),
    email       VARCHAR(255),
    logo_url    TEXT,
    template    VARCHAR(50) DEFAULT 'default',
    brand_color VARCHAR(7) DEFAULT '#1a56db',
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id      UUID REFERENCES companies(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    aliases         JSONB DEFAULT '[]',
    unit_price      NUMERIC(12, 2) NOT NULL,
    unit            VARCHAR(50) DEFAULT 'piece',
    gst_rate        NUMERIC(5, 2) DEFAULT 18.00,
    hsn_code        VARCHAR(20),
    description     TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    ai_estimated    BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_company ON products(company_id);

CREATE TABLE IF NOT EXISTS invoices (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_number  VARCHAR(50) UNIQUE NOT NULL,
    company_id      UUID REFERENCES companies(id) ON DELETE RESTRICT,
    customer_name   VARCHAR(255) NOT NULL,
    customer_gst    VARCHAR(20),
    customer_address TEXT,
    customer_phone  VARCHAR(20),
    customer_email  VARCHAR(255),
    subtotal        NUMERIC(14, 2) NOT NULL DEFAULT 0,
    cgst_amount     NUMERIC(14, 2) NOT NULL DEFAULT 0,
    sgst_amount     NUMERIC(14, 2) NOT NULL DEFAULT 0,
    igst_amount     NUMERIC(14, 2) NOT NULL DEFAULT 0,
    bonus           NUMERIC(14, 2) DEFAULT 0,
    total_amount    NUMERIC(14, 2) NOT NULL DEFAULT 0,
    supply_type     VARCHAR(10) DEFAULT 'intra',
    status          VARCHAR(20) DEFAULT 'draft',
    voice_transcript TEXT,
    ai_processed    BOOLEAN DEFAULT FALSE,
    ai_confidence   NUMERIC(5, 2),
    notes           TEXT,
    invoice_date    DATE DEFAULT CURRENT_DATE,
    due_date        DATE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoices_company ON invoices(company_id);
CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);

CREATE TABLE IF NOT EXISTS invoice_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    invoice_id      UUID REFERENCES invoices(id) ON DELETE CASCADE,
    product_id      UUID REFERENCES products(id) ON DELETE SET NULL,
    product_name    VARCHAR(255) NOT NULL,
    hsn_code        VARCHAR(20),
    quantity        NUMERIC(10, 3) NOT NULL DEFAULT 1,
    unit            VARCHAR(50) DEFAULT 'piece',
    unit_price      NUMERIC(12, 2) NOT NULL,
    gst_rate        NUMERIC(5, 2) DEFAULT 18.00,
    taxable_amount  NUMERIC(14, 2) NOT NULL,
    gst_amount      NUMERIC(14, 2) NOT NULL,
    total_amount    NUMERIC(14, 2) NOT NULL,
    ai_estimated    BOOLEAN DEFAULT FALSE,
    sort_order      INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoice_items_invoice ON invoice_items(invoice_id);

CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    company_ids     JSONB DEFAULT '[]',
    role            VARCHAR(20) DEFAULT 'operator',
    is_active       BOOLEAN DEFAULT TRUE,
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_companies_updated ON companies;
CREATE TRIGGER trg_companies_updated BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trg_products_updated ON products;
CREATE TRIGGER trg_products_updated BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trg_invoices_updated ON invoices;
CREATE TRIGGER trg_invoices_updated BEFORE UPDATE ON invoices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE SEQUENCE IF NOT EXISTS invoice_seq START 1000;

CREATE OR REPLACE FUNCTION next_invoice_number()
RETURNS VARCHAR AS $$
BEGIN
    RETURN 'INV-' || TO_CHAR(NOW(), 'YYYYMM') || '-' || LPAD(nextval('invoice_seq')::TEXT, 4, '0');
END;
$$ LANGUAGE plpgsql;
"""

try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    print("Applying schema...")
    cur.execute(schema_sql)
    print("Schema applied successfully!")
    
    # Check tables now
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = [row[0] for row in cur.fetchall()]
    print(f"Tables now: {tables}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
