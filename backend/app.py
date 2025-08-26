from fastapi import FastAPI
from app_sea import router as sea_router  # Pastikan impor router dari app_sea.py

app = FastAPI()

# Daftarkan router untuk data cuaca dan laut
app.include_router(sea_router)
