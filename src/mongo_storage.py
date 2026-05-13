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


MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = "air_quality"


def get_client() -> MongoClient:
    """Get or create MongoDB client with connection pooling."""
    return MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)


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
        sensor_col.create_index([("latitude", "2dsphere"), ("longitude", "2dsphere")])
        
        prediction_col = db["predictions"]
        prediction_col.create_index("timestamp")
        prediction_col.create_index([("latitude", "2dsphere"), ("longitude", "2dsphere")])
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
                    "$maxDistance": radius_km * 1000,
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
        
        # Find predictions near this node
        pipeline = [
            {
                "$match": {
                    "timestamp": {"$gte": cutoff_time},
                    "latitude": {"$gte": latitude - 0.1, "$lte": latitude + 0.1},
                    "longitude": {"$gte": longitude - 0.1, "$lte": longitude + 0.1},
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
