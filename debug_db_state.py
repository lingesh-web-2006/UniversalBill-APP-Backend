import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Postgre@localhost:1508/voiceinvoice")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    print("Checking tables...")
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = cur.fetchall()
    print(f"Tables: {[t[0] for t in tables]}")
    
    print("\nChecking companies...")
    cur.execute("SELECT id, name, is_active FROM companies")
    for row in cur.fetchall():
        print(f"Company Profile: {row}")
        
    print("\nChecking invoices count...")
    cur.execute("SELECT COUNT(*) FROM invoices")
    print(f"Invoices: {cur.fetchone()[0]}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
