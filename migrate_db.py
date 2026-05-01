import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Postgre@localhost:1508/voiceinvoice")

def apply_migration():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        print("Checking/Adding 'is_active' column to 'companies'...")
        cur.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE")
        conn.commit()
        print("Migration complete!")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    apply_migration()
