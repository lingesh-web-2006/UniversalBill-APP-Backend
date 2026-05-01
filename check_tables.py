import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Postgre@localhost:1508/voiceinvoice")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
    tables = [row[0] for row in cur.fetchall()]
    print(f"Tables in database: {tables}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
