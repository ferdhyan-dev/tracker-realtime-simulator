# backend/app_db.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from datetime import datetime
import os
import logging

# ===== Logging =====
logging.basicConfig(level=logging.INFO)

# ===== FastAPI app =====
app = FastAPI(title="Realtime Tracking API (with DB)")

# CORS (bebas di-dev; boleh dipersempit saat prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== Database =====
# Default host 'postgres' (nama service di docker-compose). Bisa dioverride via env DATABASE_URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://tracking:tracking123@postgres:5432/trackingdb"
)
# future=True opsional; pool_pre_ping mencegah koneksi stale
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)


def _rows_to_dict_list(rows):
    """Ubah list RowMapping -> list dict, konversi datetime -> ISO string."""
    out = []
    for r in rows:
        d = dict(r)  # RowMapping immutable, jadi copy dulu
        ts = d.get("ts")
        if isinstance(ts, datetime):
            d["ts"] = ts.isoformat()
        out.append(d)
    return out


@app.get("/health")
def health():
    """Healthcheck sederhana."""
    return {"status": "ok"}


@app.get("/vehicles")
def get_vehicles():
    """
    Kembalikan daftar kendaraan + posisi terakhir (jika ada).
    Otomatis handle skema dengan / tanpa tabel owners (owner_id).
    """
    try:
        with engine.begin() as conn:
            # Deteksi ketersediaan tabel owners & kolom owner_id
            owners_table_exists = conn.execute(text("""
                SELECT EXISTS (
                  SELECT 1 FROM information_schema.tables
                  WHERE table_schema='public' AND table_name='owners'
                );
            """)).scalar_one()

            vehicles_has_owner_id = conn.execute(text("""
                SELECT EXISTS (
                  SELECT 1 FROM information_schema.columns
                  WHERE table_name='vehicles' AND column_name='owner_id'
                );
            """)).scalar_one()

            if owners_table_exists and vehicles_has_owner_id:
                sql = text("""
                    SELECT v.vehicle_id, v.name, v.type, v.capacity,
                           o.name AS owner,
                           p.lat, p.lon, p.sog, p.cog, p.heading, p.status, p.ts
                    FROM vehicles v
                    LEFT JOIN owners o ON o.owner_id = v.owner_id
                    LEFT JOIN LATERAL (
                        SELECT lat, lon, sog, cog, heading, status, ts
                        FROM positions p2
                        WHERE p2.vehicle_id = v.vehicle_id
                        ORDER BY ts DESC
                        LIMIT 1
                    ) p ON TRUE
                    ORDER BY v.vehicle_id;
                """)
            else:
                # Fallback: skema lama (tanpa owners); owner dikosongkan
                sql = text("""
                    SELECT v.vehicle_id, v.name, v.type, v.capacity,
                           NULL::text AS owner,
                           p.lat, p.lon, p.sog, p.cog, p.heading, p.status, p.ts
                    FROM vehicles v
                    LEFT JOIN LATERAL (
                        SELECT lat, lon, sog, cog, heading, status, ts
                        FROM positions p2
                        WHERE p2.vehicle_id = v.vehicle_id
                        ORDER BY ts DESC
                        LIMIT 1
                    ) p ON TRUE
                    ORDER BY v.vehicle_id;
                """)

            rows = conn.execute(sql).mappings().all()
            return _rows_to_dict_list(rows)

    except Exception as e:
        logging.exception("Error in /vehicles")
        return {"error": str(e)}


@app.get("/positions/latest")
def latest_positions():
    """
    Satu titik terakhir per vehicle: vehicle_id, lat, lon, sog, status, ts.
    """
    try:
        with engine.begin() as conn:
            rows = conn.execute(text("""
                SELECT p.vehicle_id, p.lat, p.lon, p.sog, p.status, p.ts
                FROM positions p
                JOIN (
                  SELECT vehicle_id, MAX(ts) AS max_ts
                  FROM positions
                  GROUP BY vehicle_id
                ) last
                  ON last.vehicle_id = p.vehicle_id AND last.max_ts = p.ts
                ORDER BY p.vehicle_id;
            """)).mappings().all()

            return _rows_to_dict_list(rows)

    except Exception as e:
        logging.exception("Error in /positions/latest")
        return {"error": str(e)}
