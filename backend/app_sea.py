import requests
from fastapi import APIRouter, HTTPException, Query
from datetime import datetime
from dotenv import load_dotenv
import os
import numpy as np

# Muat variabel lingkungan dari file .env
load_dotenv()

# Ambil kredensial dari .env
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
STORMGLASS_API_KEY = os.getenv("STORMGLASS_API_KEY")

# Inisialisasi APIRouter
router = APIRouter()

# Function untuk mengambil data cuaca dari OpenWeather API
def get_weather_data(lat: float, lon: float):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()

        # Ambil suhu udara (temp)
        temperature = data["main"]["temp"]  # Suhu dalam derajat Celsius
        weather_description = data["weather"][0]["description"]
        humidity = data["main"]["humidity"]  # Kelembapan
        pressure = data["main"]["pressure"]  # Tekanan udara
        wind_speed = data["wind"]["speed"]  # Kecepatan angin
        wind_deg = data["wind"]["deg"]  # Arah angin dalam derajat

        return {
            "temperature": temperature,
            "weather_description": weather_description,
            "humidity": humidity,
            "pressure": pressure,
            "wind_speed": wind_speed,
            "wind_deg": wind_deg
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather data: {e}")

# Function untuk mengambil data cuaca laut dari StormGlass API
def get_ocean_weather_data(lat: float, lon: float, time: str):
    try:
        url = f"https://api.stormglass.io/v2/weather/point"
        params = {
            "lat": lat,
            "lng": lon,
            "start": time,
            "end": time,
            "params": "waveHeight,swellHeight,swellDirection,windSpeed,windDirection,airTemperature"
        }
        headers = {
            "Authorization": STORMGLASS_API_KEY
        }
        response = requests.get(url, params=params, headers=headers)
        data = response.json()

        # Ambil data dari Stormglass
        wave_height = data["hours"][0]["waveHeight"] if "waveHeight" in data["hours"][0] else None
        swell_height = data["hours"][0]["swellHeight"] if "swellHeight" in data["hours"][0] else None
        wind_speed_ocean = data["hours"][0]["windSpeed"] if "windSpeed" in data["hours"][0] else None
        wind_direction = data["hours"][0]["windDirection"] if "windDirection" in data["hours"][0] else None
        air_temperature = data["hours"][0]["airTemperature"] if "airTemperature" in data["hours"][0] else None

        return {
            "wave_height": wave_height,
            "swell_height": swell_height,
            "wind_speed": wind_speed_ocean,
            "wind_direction": wind_direction,
            "air_temperature": air_temperature
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching ocean weather data: {e}")

# Daftarkan endpoint API
@router.get("/get_full_weather_data")
async def get_full_weather_data(
    lat: float = Query(..., description="Latitude of the location"),
    lon: float = Query(..., description="Longitude of the location"),
    time: str = Query(..., description="Time in ISO format (e.g., '2025-08-25T00:00:00')")
):
    weather = get_weather_data(lat, lon)
    ocean_weather = get_ocean_weather_data(lat, lon, time)
    
    return {
        "weather": weather,
        "ocean_weather": ocean_weather
    }
