# simulators/producer_ship.py
"""
Producer posisi untuk kapal/vehicle apapun (contoh SHIP01).
Mendukung 2 mode:
- circle: mengitari titik pusat dalam radius tertentu (km)
- route : mengikuti serangkaian waypoint (lat, lon) berurutan

Contoh pakai:
  python simulators/producer_ship.py --vehicle-id SHIP01 --mode circle \
    --center -6.2 106.8167 --radius-km 10 --interval 5

  python simulators/producer_ship.py --vehicle-id SHIP01 --mode route \
    --waypoint -6.20 106.82 --waypoint -6.05 107.00 --waypoint -6.50 110.40 \
    --speed-kmh 30 --interval 5
"""

import os
import time
import math
import random
import argparse
from datetime import datetime
import psycopg2

# Gunakan DATABASE_URL dari environment kalau ada.
# Saat menjalankan dari host (bukan container), ini default ke localhost.
DATABASE_URL_DEFAULT = "postgresql://tracking:tracking123@localhost:5432/trackingdb"
DATABASE_URL = os.getenv("DATABASE_URL", DATABASE_URL_DEFAULT)


def connect_db():
    return psycopg2.connect(DATABASE_URL)


def insert_position(conn, vehicle_id, lat, lon, sog, cog, heading, status):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO positions (vehicle_id, lat, lon, sog, cog, heading, status, ts)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
            """,
            (vehicle_id, lat, lon, sog, cog, heading, status),
        )
    conn.commit()


# ---------- util geometri sederhana (cukup untuk simulasi) ----------
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.asin(math.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2):
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(dlambda)
    brng = (math.degrees(math.atan2(y, x)) + 360) % 360
    return brng


def move_towards(lat, lon, target_lat, target_lon, step_km):
    """Gerak lurus menuju target sejauh step_km (linear di lat/lon)."""
    dist = haversine_km(lat, lon, target_lat, target_lon)
    if dist == 0 or step_km >= dist:
        return target_lat, target_lon, dist
    f = step_km / dist  # fraksi perpindahan
    new_lat = lat + (target_lat - lat) * f
    new_lon = lon + (target_lon - lon) * f
    return new_lat, new_lon, dist - step_km
# -------------------------------------------------------------------


def status_from_speed(sog):
    if sog < 1:
        return "Stopped"
    elif sog < 5:
        return "Idle"
    else:
        return "Moving"


def run_circle(conn, args):
    # titik awal = sedikit offset dari center
    lat = args.center[0] + random.uniform(-0.01, 0.01)
    lon = args.center[1] + random.uniform(-0.01, 0.01)

    radius_km = args.radius_km
    interval = args.interval
    speed_kmh = args.speed_kmh

    while True:
        # pilih titik tujuan acak dalam radius
        ang = random.uniform(0, 2*math.pi)
        r_km = random.uniform(0.1, radius_km)
        # konversi "pergeseran" km ke derajat (aproksimasi)
        dlat = (r_km / 111.0) * math.cos(ang)
        dlon = (r_km / (111.0 * math.cos(math.radians(lat)))) * math.sin(ang)
        tgt_lat = args.center[0] + dlat
        tgt_lon = args.center[1] + dlon

        # bergerak menuju target beberapa langkah (biar mulus)
        while True:
            step_km = (speed_kmh * interval) / 3600.0
            new_lat, new_lon, remaining = move_towards(lat, lon, tgt_lat, tgt_lon, step_km)
            sog = speed_kmh + random.uniform(-2, 2)
            sog = max(0.0, sog)
            cog = heading = bearing_deg(lat, lon, new_lat, new_lon)
            st = status_from_speed(sog)

            insert_position(conn, args.vehicle_id, new_lat, new_lon, sog, cog, heading, st)
            print(f"[{datetime.now()}] {args.vehicle_id} lat={new_lat:.5f}, lon={new_lon:.5f}, sog={sog:.2f} km/h, status={st}")

            lat, lon = new_lat, new_lon
            time.sleep(interval)
            if remaining <= 0.01:  # km
                break


def run_route(conn, args):
    waypoints = args.waypoint[:]  # list of (lat, lon)
    if len(waypoints) < 2:
        raise ValueError("Mode 'route' butuh minimal 2 --waypoint")

    interval = args.interval
    speed_kmh = args.speed_kmh

    # mulai dari titik pertama
    idx = 0
    lat, lon = waypoints[0]

    while True:
        tgt_lat, tgt_lon = waypoints[idx + 1]
        step_km = (speed_kmh * interval) / 3600.0

        new_lat, new_lon, remaining = move_towards(lat, lon, tgt_lat, tgt_lon, step_km)
        sog = speed_kmh + random.uniform(-2, 2)
        sog = max(0.0, sog)
        cog = heading = bearing_deg(lat, lon, new_lat, new_lon)
        st = status_from_speed(sog)

        insert_position(conn, args.vehicle_id, new_lat, new_lon, sog, cog, heading, st)
        print(f"[{datetime.now()}] {args.vehicle_id} lat={new_lat:.5f}, lon={new_lon:.5f}, sog={sog:.2f} km/h, status={st}")

        lat, lon = new_lat, new_lon
        time.sleep(interval)

        if remaining <= 0.01:  # capai waypoint berikutnya
            idx += 1
            if idx >= len(waypoints) - 1:
                # selesai: ulang dari awal rute (loop)
                idx = 0
                lat, lon = waypoints[0]


def main():
    p = argparse.ArgumentParser(description="Producer posisi untuk kapal/vehicle (contoh SHIP01)")
    p.add_argument("--vehicle-id", required=True, help="ID kendaraan, mis. SHIP01")
    p.add_argument("--mode", choices=["circle", "route"], default="circle")
    p.add_argument("--interval", type=int, default=5, help="detik antar titik (default: 5)")
    p.add_argument("--speed-kmh", type=float, default=25.0, help="kecepatan rata-rata (km/h)")

    # mode circle
    p.add_argument("--center", nargs=2, type=float, metavar=("LAT", "LON"),
                   default=[-6.2, 106.8167], help="pusat lingkaran (lat lon)")
    p.add_argument("--radius-km", type=float, default=10.0, help="radius km untuk circle")

    # mode route
    p.add_argument("--waypoint", nargs=2, type=float, action="append",
                   metavar=("LAT", "LON"), help="tambah waypoint berurutan (pakai berulang kali)")

    args = p.parse_args()

    conn = connect_db()
    try:
        if args.mode == "circle":
            args.center = (float(args.center[0]), float(args.center[1]))
            run_circle(conn, args)
        else:
            # pastikan list berisi pasangan (lat,lon)
            args.waypoint = [(float(a), float(b)) for a, b in (args.waypoint or [])]
            run_route(conn, args)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
