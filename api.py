"""Hosted prediction API for hardware sensor payloads.

Run locally:
    uvicorn api:app --reload

The `/predict` endpoint accepts sensor readings plus latitude/longitude,
fetches weather for the location, and returns AQI forecast + advisories.
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.predictor import LocationContext, SensorReading, generate_full_advisory
from src.weather_api import get_weather_from_api
from src import storage


app = FastAPI(title="Air Quality Prediction API", version="1.0.0")


@app.on_event("startup")
def _startup() -> None:
    try:
        storage.init_db()
    except Exception:
        # If DB initialization fails, startup should continue; ingestion will error later
        pass


@app.get("/")
def root() -> dict:
    return {
        "service": "Air Quality Prediction API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
        },
    }


class PredictionRequest(BaseModel):
    mq135_adc: float = Field(..., ge=0)
    air_quality_ppm: float = Field(..., ge=0)
    mq7_adc: float = Field(..., ge=0)
    co_ppm: float = Field(..., ge=0)
    dust_adc: float = Field(..., ge=0)
    dust_voltage: float = Field(..., ge=0)
    estimated_pm25: float = Field(..., ge=0)
    temperature: float
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    forecast_hours: int = Field(4, ge=1, le=6)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/predict")
def predict(payload: PredictionRequest) -> dict:
    try:
        sensor = SensorReading(
            mq135_adc=payload.mq135_adc,
            air_quality_ppm=payload.air_quality_ppm,
            mq7_adc=payload.mq7_adc,
            co_ppm=payload.co_ppm,
            dust_adc=payload.dust_adc,
            dust_voltage=payload.dust_voltage,
            estimated_pm25=payload.estimated_pm25,
            temperature=payload.temperature,
        )
        location = LocationContext(latitude=payload.latitude, longitude=payload.longitude)
        weather = get_weather_from_api(payload.latitude, payload.longitude)
        # Persist incoming hardware reading for later rendering/analysis
        try:
            storage.insert_reading(payload.dict())
        except Exception:
            # Non-fatal: storage failures should not prevent predictions
            pass
        return generate_full_advisory(
            current_sensor=sensor,
            weather=weather,
            location=location,
            forecast_hours=payload.forecast_hours,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ingest")
def ingest(payload: PredictionRequest) -> dict:
    """Store a hardware payload and return stored id for later retrieval by mobile clients."""
    try:
        rowid = storage.insert_reading(payload.dict())
        return {"status": "ok", "id": rowid}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/readings")
def readings(limit: int = 100) -> dict:
    """Return the most recent hardware readings for rendering on mobile apps."""
    try:
        rows = storage.get_recent(limit=limit)
        return {"count": len(rows), "rows": rows}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
