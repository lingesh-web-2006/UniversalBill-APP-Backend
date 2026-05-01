import sqlite3
import os
from flask import g, current_app
from datetime import datetime

_db_migrated = False

def get_db_connection():
    """Get a database connection, with automatic fallback to SQLite if Postgres is unavailable."""
    global _db_migrated
    if 'db_conn' not in g:
        db_url = current_app.config['SQLALCHEMY_DATABASE_URI']
        
        try:
            # Try PostgreSQL
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            g.db_conn = psycopg2.connect(db_url)
            g.db_type = 'postgres'
            
            # Simple lazy migration for Postgres
            if not _db_migrated:
                try:
                    with g.db_conn.cursor() as cur:
                        # Add missing columns to Postgres
                        cur.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE")
                        cur.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE")
                        cur.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS bonus DECIMAL DEFAULT 0")
                        cur.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS customer_company TEXT")
                        cur.execute("ALTER TABLE invoices ADD COLUMN IF NOT EXISTS customer_store TEXT")
                        
                        # Add customers table if not exists
                        cur.execute("""
                            CREATE TABLE IF NOT EXISTS customers (
                                id TEXT PRIMARY KEY,
                                name TEXT NOT NULL,
                                company_id TEXT,
                                gst_number TEXT,
                                address TEXT,
                                city TEXT,
                                state TEXT,
                                pincode TEXT,
                                phone TEXT,
                                email TEXT,
                                is_active BOOLEAN DEFAULT TRUE,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        g.db_conn.commit()
                        _db_migrated = True
                except:
                    g.db_conn.rollback()
                    
        except (Exception, ImportError) as e:
            # Fallback to SQLite
            db_path = os.path.join(current_app.root_path, '..', 'voiceinvoice.db')
            if not os.path.exists(db_path):
                print(f"Creating SQLite database at {db_path}")
            
            g.db_conn = sqlite3.connect(db_path)
            g.db_conn.row_factory = sqlite3.Row
            g.db_type = 'sqlite'
            
            # Initialize SQLite if needed
            _init_sqlite(g.db_conn)
            
            # Lazy migration for SQLite columns
            try:
                cursor = g.db_conn.cursor()
                # SQLite doesn't support IF NOT EXISTS for ADD COLUMN in older versions, 
                # so we catch the error if they already exist
                try:
                    cursor.execute("ALTER TABLE invoices ADD COLUMN customer_company TEXT")
                except sqlite3.OperationalError: pass
                try:
                    cursor.execute("ALTER TABLE invoices ADD COLUMN customer_store TEXT")
                except sqlite3.OperationalError: pass
                g.db_conn.commit()
            except:
                pass
            
    return g.db_conn

def close_db_connection(e=None):
    """Closes the database connection at the end of a request."""
    conn = g.pop('db_conn', None)
    if conn is not None:
        conn.close()

def _init_sqlite(conn):
    """Basic schema initialization for SQLite fallback."""
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS companies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            gst_number TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            phone TEXT,
            email TEXT,
            template TEXT DEFAULT 'default',
            brand_color TEXT DEFAULT '#2563eb',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id TEXT,
            name TEXT NOT NULL,
            aliases TEXT,
            unit_price DECIMAL,
            unit TEXT,
            gst_rate DECIMAL DEFAULT 18.0,
            hsn_code TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        );
        CREATE TABLE IF NOT EXISTS invoices (
            id TEXT PRIMARY KEY,
            invoice_number TEXT NOT NULL,
            company_id TEXT,
            customer_name TEXT,
            customer_company TEXT,
            customer_store TEXT,
            customer_gst TEXT,
            customer_address TEXT,
            subtotal DECIMAL,
            cgst_amount DECIMAL,
            sgst_amount DECIMAL,
            igst_amount DECIMAL,
            bonus DECIMAL DEFAULT 0,
            total_amount DECIMAL,
            supply_type TEXT DEFAULT 'intra',
            status TEXT DEFAULT 'generated',
            ai_processed BOOLEAN DEFAULT TRUE,
            ai_confidence DECIMAL,
            invoice_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        );
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id TEXT,
            product_name TEXT,
            hsn_code TEXT,
            quantity DECIMAL,
            unit TEXT,
            unit_price DECIMAL,
            gst_rate DECIMAL,
            taxable_amount DECIMAL,
            gst_amount DECIMAL,
            total_amount DECIMAL,
            ai_estimated BOOLEAN DEFAULT FALSE,
            sort_order INTEGER,
            FOREIGN KEY (invoice_id) REFERENCES invoices (id)
        );
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            company_id TEXT,
            gst_number TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            pincode TEXT,
            phone TEXT,
            email TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        );
    """)
    conn.commit()

def query_db(query, args=(), one=False):
    """Execute a query and return results as dictionaries."""
    conn = get_db_connection()
    db_type = getattr(g, 'db_type', 'postgres')
    
    # Handle placeholder syntax (Postgres uses %s, SQLite uses ?)
    if db_type == 'sqlite':
        query = query.replace('%s', '?')
        
    try:
        if db_type == 'postgres':
            # Dynamic import for Postgres
            from psycopg2.extras import RealDictCursor
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, args)
                rv = cur.fetchall()
            conn.commit()
        else:
            # SQLite specific
            cur = conn.cursor()
            cur.execute(query, args)
            rv = [dict(row) for row in cur.fetchall()]
            cur.close()
            conn.commit()
            
        return (rv[0] if rv else None) if one else rv
    except Exception as e:
        conn.rollback()
        print(f"DATABASE QUERY ERROR: {e}")
        print(f"QUERY: {query}")
        print(f"ARGS: {args}")
        # Log to file for deep debugging
        with open("crash_debug.txt", "a") as f:
            f.write(f"\n\n--- ERROR AT {datetime.now()} ---\n")
            f.write(f"Query: {query}\nArgs: {args}\nError: {e}\n")
        raise e

def execute_db(query, args=()):
    """Execute a query without returning results."""
    conn = get_db_connection()
    db_type = getattr(g, 'db_type', 'postgres')
    
    if db_type == 'sqlite':
        query = query.replace('%s', '?')
        
    try:
        cur = conn.cursor()
        cur.execute(query, args)
        conn.commit()
        cur.close()
    except Exception as e:
        conn.rollback()
        raise e
