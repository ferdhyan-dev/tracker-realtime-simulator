FROM python:3.11-slim
WORKDIR /app

COPY backend/requirements.txt requirements.txt
RUN pip install -r requirements.txt

# salin semua kode backend ke image
COPY backend/ ./

ENV PYTHONUNBUFFERED=1
CMD ["uvicorn", "app_db:app", "--host", "0.0.0.0", "--port", "8000"]
