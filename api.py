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


app = FastAPI(title="Air Quality Prediction API", version="1.0.0")


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
        return generate_full_advisory(
            current_sensor=sensor,
            weather=weather,
            location=location,
            forecast_hours=payload.forecast_hours,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
