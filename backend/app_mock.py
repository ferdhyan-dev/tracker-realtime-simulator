from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone

app = FastAPI(title="Realtime Tracking API (MOCK)")

# Allow all origins (biar frontend bisa fetch API tanpa cors error)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data mock kendaraan
VEHICLES = {
    "SHIP01": {
        "vehicle_id": "SHIP01",
        "name": "Sun Flower",
        "plate_imo": "IMO1234567",
        "type": "passenger",
        "owner": "OAR",
        "capacity": 200,
    },
    "TRK01": {
        "vehicle_id": "TRK01",
        "name": "Logistic-01",
        "plate_no": "B 1234 XX",
        "type": "truck",
        "owner": "ACME",
        "capacity": 18.0,
    },
}

LATEST_POS = {
    "SHIP01": {
        "lat": -7.2575,
        "lon": 112.7521,
        "sog": 0.0,
        "cog": 0.0,
        "heading": 0.0,
        "status": "anchored",
        "ts": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
    },
    "TRK01": {
        "lat": -6.1754,
        "lon": 106.8272,
        "sog": 42.0,
        "cog": 89.0,
        "heading": 88.0,
        "status": "moving",
        "ts": datetime.utcnow().replace(tzinfo=timezone.utc).isoformat(),
    },
}

TRACKS = {
    "TRK01": [
        {
            "lat": -6.20,
            "lon": 106.80,
            "ts": (datetime.utcnow() - timedelta(minutes=20)).replace(tzinfo=timezone.utc).isoformat()
        },
        {
            "lat": -6.19,
            "lon": 106.81,
            "ts": (datetime.utcnow() - timedelta(minutes=15)).replace(tzinfo=timezone.utc).isoformat()
        },
        {
            "lat": -6.18,
            "lon": 106.82,
            "ts": (datetime.utcnow() - timedelta(minutes=10)).replace(tzinfo=timezone.utc).isoformat()
        },
        {
            "lat": -6.1754,
            "lon": 106.8272,
            "ts": (datetime.utcnow() - timedelta(minutes=2)).replace(tzinfo=timezone.utc).isoformat()
        },
    ]
}

# ==== API ENDPOINTS ====

@app.get("/vehicles")
def get_vehicles():
    """List semua kendaraan dengan posisi terakhir"""
    result = []
    for vid, vdata in VEHICLES.items():
        pos = LATEST_POS.get(vid)
        result.append({
            **vdata,
            "position": pos
        })
    return result

@app.get("/vehicles/{vehicle_id}")
def get_vehicle(vehicle_id: str):
    """Detail satu kendaraan"""
    if vehicle_id in VEHICLES:
        return {
            **VEHICLES[vehicle_id],
            "position": LATEST_POS.get(vehicle_id),
            "tracks": TRACKS.get(vehicle_id, [])
        }
    return {"error": "Vehicle not found"}
