"""
Migration: Add customer_company and customer_store columns to invoices table.
Run once: python migrate_customer_fields.py
"""
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL","postgresql://postgres:Postgre@localhost:1508/voiceinvoice")


def apply_migration():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()

        print("Adding 'customer_company' column to 'invoices'...")
        cur.execute(
            "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS customer_company VARCHAR(255)"
        )

        print("Adding 'customer_store' column to 'invoices'...")
        cur.execute(
            "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS customer_store VARCHAR(255)"
        )

        print("Adding 'bonus' column to 'invoices' (if missing)...")
        cur.execute(
            "ALTER TABLE invoices ADD COLUMN IF NOT EXISTS bonus NUMERIC(14, 2) NOT NULL DEFAULT 0"
        )

        conn.commit()
        print("\n✅ Migration complete! All columns verified/added successfully.")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    apply_migration()
