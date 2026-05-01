import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Postgre@localhost:1508/voiceinvoice")

def check_columns():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'companies'")
        columns = [row[0] for row in cur.fetchall()]
        print(f"Columns in 'companies': {columns}")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_columns()
