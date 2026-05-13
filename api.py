"""Hosted prediction API for hardware sensor payloads with MongoDB persistence.

Run locally:
    export MONGODB_URL=mongodb://localhost:27017  # optional, default shown
    uvicorn api:app --reload

The `/predict` endpoint accepts sensor readings plus latitude/longitude,
fetches weather, computes AQI, and stores both payload + prediction in MongoDB.

The `/ingest` endpoint stores sensor payloads for later processing.

Query endpoints (/predictions/recent, /predictions/location, etc.) allow
mobile app backend to retrieve stored data.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from src.predictor import LocationContext, SensorReading, generate_full_advisory
from src.weather_api import get_weather_from_api
from src import mongo_storage


app = FastAPI(title="Air Quality Prediction API", version="1.0.0")


@app.on_event("startup")
def _startup() -> None:
    """Initialize MongoDB on app startup."""
    try:
        mongo_storage.init_db()
    except Exception as e:
        print(f"Warning: MongoDB init failed: {e}. App will continue; storage may fail.")


@app.get("/")
def root() -> dict:
    return {
        "service": "Air Quality Prediction API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "predict": "/predict (POST)",
            "ingest": "/ingest (POST)",
            "predictions_recent": "/predictions/recent (GET)",
            "predictions_location": "/predictions/location (GET)",
            "predictions_stats": "/predictions/stats (GET)",
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
    """Predict AQI from sensor readings and store results to MongoDB."""
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
        
        # Generate prediction
        result = generate_full_advisory(
            current_sensor=sensor,
            weather=weather,
            location=location,
            forecast_hours=payload.forecast_hours,
        )
        
        # Store sensor reading and prediction to MongoDB
        try:
            sensor_id = mongo_storage.insert_sensor_reading(payload.dict())
            prediction_id = mongo_storage.insert_prediction(sensor_id, payload.dict(), result)
            result["stored"] = {
                "sensor_id": sensor_id,
                "prediction_id": prediction_id,
            }
        except Exception as e:
            # Non-fatal: storage failures should not prevent predictions
            print(f"Warning: MongoDB storage failed: {e}")
        
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/ingest")
def ingest(payload: PredictionRequest) -> dict:
    """Store a hardware payload to MongoDB for later processing."""
    try:
        sensor_id = mongo_storage.insert_sensor_reading(payload.dict())
        return {"status": "ok", "sensor_id": sensor_id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/predictions/recent")
def predictions_recent(limit: int = Query(100, ge=1, le=1000)) -> dict:
    """Get the most recent predictions globally (for dashboard/app)."""
    try:
        predictions = mongo_storage.get_recent_predictions(limit=limit)
        return {"count": len(predictions), "predictions": predictions}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/predictions/location")
def predictions_by_location(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10, ge=0.1, le=100),
    limit: int = Query(50, ge=1, le=500),
) -> dict:
    """Query predictions near a specific location within radius_km."""
    try:
        predictions = mongo_storage.get_predictions_by_location(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            limit=limit,
        )
        return {
            "count": len(predictions),
            "location": {"latitude": latitude, "longitude": longitude, "radius_km": radius_km},
            "predictions": predictions,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/predictions/stats")
def predictions_stats(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    hours: int = Query(24, ge=1, le=720),
) -> dict:
    """Get aggregated AQI stats for a node (location) over last N hours."""
    try:
        stats = mongo_storage.get_node_stats(
            latitude=latitude,
            longitude=longitude,
            hours=hours,
        )
        return {
            "location": {"latitude": latitude, "longitude": longitude},
            "time_window_hours": hours,
            "stats": stats,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/predictions/time-range")
def predictions_by_time(
    start_hours_ago: int = Query(24, ge=0, le=720),
    end_hours_ago: int = Query(0, ge=0, le=720),
    limit: int = Query(100, ge=1, le=500),
) -> dict:
    """Query predictions within a time range (in hours ago from now)."""
    try:
        now = datetime.utcnow()
        start_time = now - timedelta(hours=start_hours_ago)
        end_time = now - timedelta(hours=end_hours_ago)
        
        predictions = mongo_storage.get_predictions_by_time_range(
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        return {
            "count": len(predictions),
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
            },
            "predictions": predictions,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
