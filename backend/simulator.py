# simulator.py
import time
import random
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime

# ===== Konfigurasi koneksi ke PostgreSQL (samakan dengan docker-compose / .env) =====
DB_NAME = "trackingdb"
DB_USER = "tracking"
DB_PASS = "tracking123"
DB_HOST = "localhost"   # jika di dalam compose network dan simulator di container lain: pakai 'postgres'
DB_PORT = 5432

VEHICLE_ID = "vhc01"
VEHICLE_SEED = {
    "vehicle_id": VEHICLE_ID,
    "name": "Demo Truck",
    "type": "truck",
    "plate_no": "B 1234 XX",
    "capacity": 18.0,
    "owner": "ACME",
}

def get_conn():
    return psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS,
        host=DB_HOST, port=DB_PORT
    )

def ensure_vehicle_exists(conn):
    with conn.cursor(cursor_factory=DictCursor) as cur:
        cur.execute("""
            INSERT INTO vehicles (vehicle_id, name, type, plate_no, capacity, owner)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (vehicle_id) DO NOTHING
        """, (
            VEHICLE_SEED["vehicle_id"],
            VEHICLE_SEED["name"],
            VEHICLE_SEED["type"],
            VEHICLE_SEED["plate_no"],
            VEHICLE_SEED["capacity"],
            VEHICLE_SEED["owner"],
        ))
        conn.commit()

def insert_position(conn, vehicle_id: str):
    # Contoh koordinat sekitar Jakarta; silakan ganti pusat area sesuai kebutuhan
    lat = -6.2 + random.uniform(-0.01, 0.01)   # ~±1.1 km lat
    lon = 106.81 + random.uniform(-0.01, 0.01) # ~±1.1 km lon (di ekuator)
    sog = random.uniform(0, 60)                # speed (km/h) mock; pakai m/s kalau perlu
    cog = random.uniform(0, 360)               # course over ground (derajat)
    heading = random.uniform(0, 360)           # heading (derajat)
    status = random.choice(["Moving", "Idle", "Stopped"])
    ts = datetime.now()                         # timestamp server

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO positions (vehicle_id, lat, lon, sog, cog, heading, status, ts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (vehicle_id, lat, lon, sog, cog, heading, status, ts))
    conn.commit()
    print(f"[{ts}] Inserted position for {vehicle_id}: lat={lat:.5f}, lon={lon:.5f}, sog={sog:.2f} km/h, status={status}")

def main():
    conn = None
    try:
        conn = get_conn()
        ensure_vehicle_exists(conn)  # pastikan kendaraan ada

        while True:
            insert_position(conn, VEHICLE_ID)
            time.sleep(5)  # jeda 5 detik
    except KeyboardInterrupt:
        print("Simulator stopped by user.")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
