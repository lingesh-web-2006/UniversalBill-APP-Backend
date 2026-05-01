import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:Postgre@localhost:1508/voiceinvoice")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # Check if companies already exist
    cur.execute("SELECT COUNT(*) FROM companies")
    count = cur.fetchone()[0]
    print(f"Existing companies: {count}")

    if count == 0:
        print("Seeding companies...")
        cur.execute("""
            INSERT INTO companies (id, name, gst_number, address, city, state, pincode, phone, email, template, brand_color)
            VALUES
                ('11111111-1111-1111-1111-111111111111',
                 'VIPS TECH',
                 '29ABCDE1234F1Z5',
                 'redhill chennai 52',
                 'Chennai', 'tamilnadu', '600052',
                 '+91-7695924565', 'contact@vipstech.com',
                 'modern', '#2563eb'),
                ('22222222-2222-2222-2222-222222222222',
                 'VIPS TECH',
                 '27FGHIJ5678K2Z3',
                 'redhill chennai 52',
                 'Chennai', 'tamilnadu', '600052',
                 '+91-7695924565', 'contact@vipstech.com',
                 'default', '#059669'),
                ('33333333-3333-3333-3333-333333333333',
                 'VIPS TECH',
                 '33KLMNO9012P3Z7',
                 'redhill chennai 52',
                 'Chennai', 'tamilnadu', '600052',
                 '+91-7695924565', 'contact@vipstech.com',
                 'minimal', '#7c3aed')
            ON CONFLICT (id) DO NOTHING
        """)

        print("Seeding products for TechBridge...")
        cur.execute("""
            INSERT INTO products (company_id, name, aliases, unit_price, unit, gst_rate, hsn_code)
            VALUES
                ('11111111-1111-1111-1111-111111111111', 'Laptop Stand', '["laptop holder","stand"]', 1499.00, 'piece', 18, '8473'),
                ('11111111-1111-1111-1111-111111111111', 'USB-C Hub', '["usb hub","type c hub"]', 2299.00, 'piece', 18, '8471'),
                ('11111111-1111-1111-1111-111111111111', 'Mechanical Keyboard', '["keyboard","mech keyboard"]', 4999.00, 'piece', 18, '8471'),
                ('11111111-1111-1111-1111-111111111111', 'Wireless Mouse', '["mouse","bluetooth mouse"]', 1799.00, 'piece', 18, '8471'),
                ('11111111-1111-1111-1111-111111111111', 'Web Development', '["web dev","website"]', 25000.00, 'project', 18, '998314'),
                ('11111111-1111-1111-1111-111111111111', 'Cloud Hosting Annual', '["hosting","server"]', 8400.00, 'year', 18, '998315')
        """)

        print("Seeding products for Sunrise Traders...")
        cur.execute("""
            INSERT INTO products (company_id, name, aliases, unit_price, unit, gst_rate, hsn_code)
            VALUES
                ('22222222-2222-2222-2222-222222222222', 'Basmati Rice 5kg', '["rice","basmati"]', 350.00, 'bag', 5, '1006'),
                ('22222222-2222-2222-2222-222222222222', 'Refined Oil 5L', '["oil","sunflower oil"]', 420.00, 'can', 5, '1512'),
                ('22222222-2222-2222-2222-222222222222', 'Wheat Flour 10kg', '["atta","flour"]', 280.00, 'bag', 0, '1101'),
                ('22222222-2222-2222-2222-222222222222', 'Sugar 5kg', '["sugar","chini"]', 210.00, 'bag', 5, '1701'),
                ('22222222-2222-2222-2222-222222222222', 'Toor Dal 1kg', '["dal","lentils","toor"]', 95.00, 'kg', 5, '0713')
        """)

        print("Seeding products for CloudMart...")
        cur.execute("""
            INSERT INTO products (company_id, name, aliases, unit_price, unit, gst_rate, hsn_code)
            VALUES
                ('33333333-3333-3333-3333-333333333333', 'Smart TV 43"', '["tv","television","smart tv"]', 28999.00, 'piece', 18, '8528'),
                ('33333333-3333-3333-3333-333333333333', 'Refrigerator 350L', '["fridge","refrigerator"]', 32500.00, 'piece', 18, '8418'),
                ('33333333-3333-3333-3333-333333333333', 'Washing Machine 7kg', '["washing machine","washer"]', 18750.00, 'piece', 28, '8450'),
                ('33333333-3333-3333-3333-333333333333', 'Air Conditioner 1.5T', '["ac","air conditioner"]', 34999.00, 'piece', 28, '8415')
        """)

        conn.commit()
        print("Seed data inserted successfully!")
    else:
        print("Companies already exist, checking counts...")
        cur.execute("SELECT name FROM companies")
        companies = [r[0] for r in cur.fetchall()]
        print(f"Companies: {companies}")

    conn.close()
except Exception as e:
    print(f"Error: {e}")
