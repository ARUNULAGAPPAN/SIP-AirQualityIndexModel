"""MongoDB storage for hardware sensor readings and predictions.

Provides functions to store incoming sensor payloads and their predicted AQI results.
Also supports querying by location (lat/long) and time range for mobile/web app backend.

Environment variable: MONGODB_URL (default: mongodb://localhost:27017)
Database: air_quality
Collections:
  - sensor_readings: raw incoming hardware payloads
  - predictions: computed AQI + advisory results per sensor reading
"""
from __future__ import annotations

import os
from datetime import datetime, timedelta
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


MONGODB_URL = os.getenv("MONGODB_URL", "mongodb+srv://arun:arun%40123@cluster0.dher6tt.mongodb.net/?appName=Cluster0")
DB_NAME = "air_quality"


def get_client() -> MongoClient:
    """Get or create MongoDB client with connection pooling."""
    return MongoClient(
        MONGODB_URL,
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=20000,
        tlsAllowInvalidCertificates=True,
    )


def init_db() -> None:
    """Initialize MongoDB database and collections with indexes."""
    try:
        client = get_client()
        db = client[DB_NAME]
        
        # Create collections if they don't exist
        if "sensor_readings" not in db.list_collection_names():
            db.create_collection("sensor_readings")
        if "predictions" not in db.list_collection_names():
            db.create_collection("predictions")
        
        # Create indexes for fast queries
        sensor_col = db["sensor_readings"]
        sensor_col.create_index("timestamp")
        sensor_col.create_index([("location", "2dsphere")])
        
        prediction_col = db["predictions"]
        prediction_col.create_index("timestamp")
        prediction_col.create_index([("location", "2dsphere")])
        prediction_col.create_index("sensor_reading_id")
        
        client.close()
    except ServerSelectionTimeoutError:
        # MongoDB not available; log and allow app to continue
        pass


def insert_sensor_reading(payload: dict) -> str:
    """Insert raw sensor reading and return document id."""
    try:
        client = get_client()
        db = client[DB_NAME]
        col = db["sensor_readings"]
        
        doc = {
            **payload,
            "timestamp": datetime.utcnow(),
            "location": {
                "type": "Point",
                "coordinates": [payload.get("longitude", 0), payload.get("latitude", 0)],
            },
        }
        result = col.insert_one(doc)
        client.close()
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error inserting sensor reading: {e}")
        raise


def insert_prediction(sensor_reading_id: str, payload: dict, prediction_result: dict) -> str:
    """Insert prediction result linked to sensor reading."""
    try:
        client = get_client()
        db = client[DB_NAME]
        col = db["predictions"]
        
        doc = {
            "sensor_reading_id": sensor_reading_id,
            "sensor_payload": payload,
            "prediction": prediction_result,
            "latitude": payload.get("latitude"),
            "longitude": payload.get("longitude"),
            "location": {
                "type": "Point",
                "coordinates": [payload.get("longitude", 0), payload.get("latitude", 0)],
            },
            "aqi": prediction_result.get("current", {}).get("aqi"),
            "category": prediction_result.get("current", {}).get("category"),
            "primary_pollutant": prediction_result.get("current", {}).get("sensor_contributions", {}).get("primary_pollutant"),
            "timestamp": datetime.utcnow(),
        }
        result = col.insert_one(doc)
        client.close()
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error inserting prediction: {e}")
        raise


def get_recent_predictions(limit: int = 100) -> list[dict]:
    """Get most recent predictions globally."""
    try:
        client = get_client()
        db = client[DB_NAME]
        col = db["predictions"]
        
        docs = list(col.find().sort("timestamp", -1).limit(limit))
        client.close()
        
        # Convert ObjectId to string for JSON serialization
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            doc["sensor_reading_id"] = str(doc["sensor_reading_id"])
        return docs
    except Exception as e:
        print(f"Error querying recent predictions: {e}")
        return []


def get_predictions_by_location(latitude: float, longitude: float, radius_km: float = 10, limit: int = 50) -> list[dict]:
    """Query predictions near a location (within radius_km)."""
    try:
        client = get_client()
        db = client[DB_NAME]
        col = db["predictions"]
        
        # GeoJSON query: find points within radius (in meters)
        query = {
            "location": {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": [longitude, latitude],
                    },
                    "$maxDistance": int(radius_km * 1000),
                }
            }
        }
        docs = list(col.find(query).sort("timestamp", -1).limit(limit))
        client.close()
        
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            doc["sensor_reading_id"] = str(doc["sensor_reading_id"])
        return docs
    except Exception as e:
        print(f"Error querying by location: {e}")
        return []


def get_predictions_by_time_range(start_time: datetime, end_time: datetime, limit: int = 100) -> list[dict]:
    """Query predictions within a time range."""
    try:
        client = get_client()
        db = client[DB_NAME]
        col = db["predictions"]
        
        docs = list(col.find({
            "timestamp": {
                "$gte": start_time,
                "$lte": end_time,
            }
        }).sort("timestamp", -1).limit(limit))
        client.close()
        
        for doc in docs:
            doc["_id"] = str(doc["_id"])
            doc["sensor_reading_id"] = str(doc["sensor_reading_id"])
        return docs
    except Exception as e:
        print(f"Error querying by time range: {e}")
        return []


def get_node_stats(latitude: float, longitude: float, hours: int = 24) -> dict:
    """Get aggregated stats for a node (location) over last N hours."""
    try:
        client = get_client()
        db = client[DB_NAME]
        col = db["predictions"]
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Find predictions near this node using geo-spatial query
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": cutoff_time},
                    "location": {
                        "$near": {
                            "$geometry": {
                                "type": "Point",
                                "coordinates": [longitude, latitude],
                            },
                            "$maxDistance": 1000,  # 1km radius for node stats
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "avg_aqi": {"$avg": "$aqi"},
                    "max_aqi": {"$max": "$aqi"},
                    "min_aqi": {"$min": "$aqi"},
                    "latest_timestamp": {"$max": "$timestamp"},
                }
            },
        ]
        result = list(col.aggregate(pipeline))
        client.close()
        
        if result:
            stats = result[0]
            stats.pop("_id", None)
            return stats
        return {"count": 0, "avg_aqi": None, "max_aqi": None, "min_aqi": None}
    except Exception as e:
        print(f"Error computing node stats: {e}")
        return {}


def get_distinct_locations_and_forecast(forecast_hours: int = 4) -> dict:
    """Fetch the two distinct sensor locations from database and generate short-term forecasts.
    
    Returns:
        {
            "locations": [
                {
                    "latitude": float,
                    "longitude": float,
                    "latest_reading": {...},
                    "forecast": {
                        "current_aqi": int,
                        "forecast_entries": [...],
                        "advisory": {...}
                    }
                },
                ...
            ]
        }
    """
    try:
        from src.predictor import compute_aqi_from_sensors, forecast_aqi, generate_full_advisory
        from src.predictor import SensorReading, WeatherData, LocationContext
        
        client = get_client()
        db = client[DB_NAME]
        sensor_col = db["sensor_readings"]
        
        # Get distinct locations with their record counts, sorted by count descending (most active)
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "lat": "$latitude",
                        "lon": "$longitude",
                    },
                    "count": {"$sum": 1},
                    "latest_timestamp": {"$max": "$timestamp"},
                }
            },
            {"$sort": {"count": -1}},  # Sort by number of readings (highest first)
            {"$limit": 2},  # Get the top 2 most active locations
        ]
        
        location_groups = list(sensor_col.aggregate(pipeline))
        
        results = {"locations": []}
        
        for group in location_groups:
            lat = group["_id"]["lat"]
            lon = group["_id"]["lon"]
            
            # Fetch the full latest document for this location
            latest_reading = sensor_col.find_one(
                {"latitude": lat, "longitude": lon},
                sort=[("timestamp", -1)]
            )
            
            if not latest_reading:
                continue
            
            # Extract sensor data
            sensor = SensorReading(
                mq135_adc=latest_reading.get("mq135_adc", 0),
                air_quality_ppm=latest_reading.get("air_quality_ppm", 0),
                mq7_adc=latest_reading.get("mq7_adc", 0),
                co_ppm=latest_reading.get("co_ppm", 0),
                dust_adc=latest_reading.get("dust_adc", 0),
                dust_voltage=latest_reading.get("dust_voltage", 0),
                estimated_pm25=latest_reading.get("estimated_pm25", 0),
                temperature=latest_reading.get("temperature", 22),
            )
            
            # Use weather if available, otherwise use defaults
            weather = WeatherData(
                temperature=latest_reading.get("temperature", 22),
                humidity=latest_reading.get("humidity", 50),
                wind_speed=latest_reading.get("wind_speed", 2),
                pressure=latest_reading.get("pressure", 1013),
            )
            
            location = LocationContext(latitude=lat, longitude=lon)
            
            # Compute current AQI
            current_aqi, sensor_contrib = compute_aqi_from_sensors(sensor, weather, location)
            
            # Generate forecast
            forecast_entries = forecast_aqi(sensor, weather, location, hours_ahead=forecast_hours)
            
            # Generate advisory
            advisory = generate_full_advisory(sensor, weather, location, forecast_hours=forecast_hours)
            
            results["locations"].append({
                "latitude": lat,
                "longitude": lon,
                "reading_count": group["count"],
                "latest_reading_timestamp": latest_reading.get("timestamp"),
                "latest_reading": {
                    "mq135_ppm": latest_reading.get("air_quality_ppm"),
                    "co_ppm": latest_reading.get("co_ppm"),
                    "pm25": latest_reading.get("estimated_pm25"),
                    "temperature": latest_reading.get("temperature"),
                },
                "forecast": {
                    "current_aqi": current_aqi,
                    "sensor_contributions": sensor_contrib,
                    "forecast_entries": [
                        {
                            "hour_ahead": entry.hour_ahead,
                            "predicted_aqi": entry.predicted_aqi,
                            "aqi_category": entry.aqi_category,
                            "confidence": entry.confidence,
                        }
                        for entry in forecast_entries
                    ],
                    "advisory": advisory,
                }
            })
        
        client.close()
        return results
    except Exception as e:
        print(f"Error fetching distinct locations and forecasting: {e}")
        import traceback
        traceback.print_exc()
        return {"locations": []}


def get_latest_reading_for_location(latitude: float, longitude: float, tolerance_km: float = 0.5) -> dict | None:
    """Fetch the latest sensor reading for a specific location.
    
    Args:
        latitude: Target latitude
        longitude: Target longitude
        tolerance_km: Radius to search for readings (default 0.5 km for exact location match)
    
    Returns:
        Latest sensor reading document or None if not found.
    """
    try:
        client = get_client()
        db = client[DB_NAME]
        sensor_col = db["sensor_readings"]
        
        # Query for readings near this exact location
        latest_reading = sensor_col.find_one(
            {"latitude": latitude, "longitude": longitude},
            sort=[("timestamp", -1)]
        )
        
        client.close()
        
        if latest_reading:
            latest_reading["_id"] = str(latest_reading["_id"])
        
        return latest_reading
    except Exception as e:
        print(f"Error fetching latest reading for location ({latitude}, {longitude}): {e}")
        return None


def get_aggregated_readings_for_location(latitude: float, longitude: float, count: int = 20) -> dict | None:
    """Fetch the latest N readings and aggregate them for robust prediction.
    
    Args:
        latitude: Target latitude
        longitude: Target longitude
        count: Number of latest readings to aggregate (default 20)
    
    Returns:
        Aggregated sensor readings dict with averaged values, or None if not found.
    """
    try:
        client = get_client()
        db = client[DB_NAME]
        sensor_col = db["sensor_readings"]
        
        # Fetch the latest N readings
        readings = list(sensor_col.find(
            {"latitude": latitude, "longitude": longitude},
            sort=[("timestamp", -1)],
            limit=count
        ))
        
        client.close()
        
        if not readings:
            return None
        
        # Average all sensor values
        aggregated = {
            "mq135_adc": sum(r.get("mq135_adc", 0) for r in readings) / len(readings),
            "air_quality_ppm": sum(r.get("air_quality_ppm", 0) for r in readings) / len(readings),
            "mq7_adc": sum(r.get("mq7_adc", 0) for r in readings) / len(readings),
            "co_ppm": sum(r.get("co_ppm", 0) for r in readings) / len(readings),
            "dust_adc": sum(r.get("dust_adc", 0) for r in readings) / len(readings),
            "dust_voltage": sum(r.get("dust_voltage", 0) for r in readings) / len(readings),
            "estimated_pm25": sum(r.get("estimated_pm25", 0) for r in readings) / len(readings),
            "temperature": sum(r.get("temperature", 22) for r in readings) / len(readings),
            "humidity": sum(r.get("humidity", 50) for r in readings) / len(readings),
            "wind_speed": sum(r.get("wind_speed", 2) for r in readings) / len(readings),
            "pressure": sum(r.get("pressure", 1013) for r in readings) / len(readings),
            "latitude": latitude,
            "longitude": longitude,
            "reading_count": len(readings),
            "timestamp": readings[0].get("timestamp"),  # Latest timestamp
        }
        
        return aggregated
    except Exception as e:
        print(f"Error fetching aggregated readings for location ({latitude}, {longitude}): {e}")
        return None
