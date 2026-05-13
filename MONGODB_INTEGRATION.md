# MongoDB Integration Guide

This document describes the MongoDB storage layer for the Air Quality API, enabling persistent storage of sensor readings and predictions with location-based querying for mobile app backend integration.

## Overview

The Air Quality Prediction API now uses MongoDB for persistent data storage instead of SQLite. This provides:

- **Durability**: Data persists across service restarts and deployments
- **Geo-Spatial Indexing**: Efficient location-based queries for nearby sensors
- **Scalability**: Support for millions of readings from multiple hardware nodes
- **Time-Series Support**: Indexed timestamp queries for temporal analysis
- **Cloud-Ready**: Integrates with MongoDB Atlas for production deployments

## MongoDB Setup

### Option 1: MongoDB Atlas (Cloud - Recommended for Production)

1. Create free account at https://cloud.mongodb.com
2. Create a cluster (free tier available)
3. Create a database user with username/password
4. Get connection string: `mongodb+srv://username:password@cluster.mongodb.net/air_quality?retryWrites=true&w=majority`
5. Set environment variable: `MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/air_quality?retryWrites=true&w=majority`

### Option 2: Local MongoDB (Development)

**Install MongoDB:**
```bash
# macOS (with Homebrew)
brew tap mongodb/brew
brew install mongodb-community

# Ubuntu/Debian
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org

# Windows
# Download from https://www.mongodb.com/try/download/community
```

**Start MongoDB:**
```bash
mongod  # or `brew services start mongodb-community` on macOS
```

**Set environment variable:**
```bash
export MONGODB_URL=mongodb://localhost:27017
```

### Option 3: Docker

```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
export MONGODB_URL=mongodb://localhost:27017
```

## Environment Configuration

### Local Development

```bash
# .env file (add to project root, included in .gitignore)
MONGODB_URL=mongodb://localhost:27017
OPENWEATHER_API_KEY=your_api_key_here
```

### Render Deployment

Set environment variable in Render dashboard:
- **Variable name**: `MONGODB_URL`
- **Value**: Your MongoDB Atlas connection string
- Example: `mongodb+srv://user:pass@cluster.mongodb.net/air_quality?retryWrites=true&w=majority`

## Database Schema

### Collection: `sensor_readings`

Stores raw hardware payloads from IoT devices.

**Schema:**
```json
{
  "_id": ObjectId,
  "timestamp": ISODate("2025-01-15T12:34:56Z"),
  "latitude": 40.7128,
  "longitude": -74.0060,
  "mq135_adc": 512,
  "air_quality_ppm": 15.5,
  "mq7_adc": 450,
  "co_ppm": 2.1,
  "dust_adc": 200,
  "dust_voltage": 3.2,
  "estimated_pm25": 25.0,
  "temperature": 22.5,
  "forecast_hours": 4
}
```

**Indexes:**
- `timestamp` (ascending)
- `[latitude, longitude]` (2dsphere geo-spatial)

### Collection: `predictions`

Stores computed AQI results linked to sensor readings.

**Schema:**
```json
{
  "_id": ObjectId,
  "sensor_reading_id": ObjectId("..."),
  "timestamp": ISODate("2025-01-15T12:34:56Z"),
  "latitude": 40.7128,
  "longitude": -74.0060,
  "aqi": 85,
  "category": "Unhealthy for Sensitive Groups",
  "primary_pollutant": "PM2.5",
  "sensor_payload": { ... },
  "prediction": {
    "current": {
      "aqi": 85,
      "category": "Unhealthy for Sensitive Groups",
      "sensor_contributions": { ... }
    },
    "forecast": [
      { "hours_ahead": 1, "aqi": 82, ... },
      ...
    ],
    ...
  }
}
```

**Indexes:**
- `timestamp` (ascending)
- `[latitude, longitude]` (2dsphere geo-spatial)
- `sensor_reading_id` (ascending)

## API Query Endpoints

### 1. Get Recent Predictions

```http
GET /predictions/recent?limit=50

Response:
{
  "count": 50,
  "predictions": [
    {
      "_id": "...",
      "aqi": 75,
      "category": "Moderate",
      "latitude": 40.7128,
      "longitude": -74.0060,
      "timestamp": "2025-01-15T12:34:56Z",
      ...
    }
  ]
}
```

**Query Parameters:**
- `limit` (integer, 1-1000, default: 100): Maximum predictions to return

### 2. Get Predictions by Location

```http
GET /predictions/location?latitude=40.7128&longitude=-74.0060&radius_km=5&limit=50

Response:
{
  "count": 12,
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060,
    "radius_km": 5
  },
  "predictions": [...]
}
```

**Query Parameters:**
- `latitude` (float, -90 to 90, required): Center latitude
- `longitude` (float, -180 to 180, required): Center longitude
- `radius_km` (float, 0.1-100, default: 10): Search radius in kilometers
- `limit` (integer, 1-500, default: 50): Maximum predictions to return

### 3. Get Node Statistics

```http
GET /predictions/stats?latitude=40.7128&longitude=-74.0060&hours=24

Response:
{
  "location": {
    "latitude": 40.7128,
    "longitude": -74.0060
  },
  "time_window_hours": 24,
  "stats": {
    "count": 48,
    "avg_aqi": 72.5,
    "max_aqi": 95,
    "min_aqi": 55,
    "latest_timestamp": "2025-01-15T12:34:56Z"
  }
}
```

**Query Parameters:**
- `latitude` (float, -90 to 90, required): Node latitude
- `longitude` (float, -180 to 180, required): Node longitude
- `hours` (integer, 1-720, default: 24): Time window in hours

### 4. Get Predictions by Time Range

```http
GET /predictions/time-range?start_hours_ago=24&end_hours_ago=0&limit=100

Response:
{
  "count": 48,
  "time_range": {
    "start": "2025-01-14T12:34:56Z",
    "end": "2025-01-15T12:34:56Z"
  },
  "predictions": [...]
}
```

**Query Parameters:**
- `start_hours_ago` (integer, 0-720, default: 24): Start time (hours from now)
- `end_hours_ago` (integer, 0-720, default: 0): End time (hours from now)
- `limit` (integer, 1-500, default: 100): Maximum predictions to return

## Integration with API Endpoints

### POST /predict

Accepts sensor readings, computes AQI, and stores both reading and prediction:

```bash
curl -X POST https://api.example.com/predict \
  -H "Content-Type: application/json" \
  -d '{
    "mq135_adc": 512,
    "air_quality_ppm": 15.5,
    "mq7_adc": 450,
    "co_ppm": 2.1,
    "dust_adc": 200,
    "dust_voltage": 3.2,
    "estimated_pm25": 25.0,
    "temperature": 22.5,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "forecast_hours": 4
  }'

Response includes:
{
  "current": { ... },
  "forecast": [ ... ],
  "stored": {
    "sensor_id": "507f1f77bcf86cd799439011",
    "prediction_id": "507f1f77bcf86cd799439012"
  }
}
```

### POST /ingest

Stores a sensor reading without computing prediction:

```bash
curl -X POST https://api.example.com/ingest \
  -H "Content-Type: application/json" \
  -d '{ ... sensor payload ... }'

Response:
{
  "status": "ok",
  "sensor_id": "507f1f77bcf86cd799439011"
}
```

## Usage Examples

### Python Client (for mobile app backend)

```python
import requests

API_BASE = "https://airquality-api-4njf.onrender.com"

# Get recent predictions (dashboard)
response = requests.get(f"{API_BASE}/predictions/recent?limit=10")
predictions = response.json()["predictions"]

# Get predictions near user location
lat, lon = 40.7128, -74.0060
response = requests.get(
    f"{API_BASE}/predictions/location",
    params={"latitude": lat, "longitude": lon, "radius_km": 5}
)
nearby = response.json()["predictions"]

# Get stats for monitoring a specific node
response = requests.get(
    f"{API_BASE}/predictions/stats",
    params={"latitude": lat, "longitude": lon, "hours": 24}
)
stats = response.json()["stats"]
print(f"24-hour avg AQI: {stats.get('avg_aqi'):.1f}")

# Get historical data (last 7 days)
response = requests.get(
    f"{API_BASE}/predictions/time-range",
    params={"start_hours_ago": 168, "end_hours_ago": 0}
)
history = response.json()["predictions"]
```

### JavaScript Client

```javascript
const API_BASE = "https://airquality-api-4njf.onrender.com";

// Fetch nearby predictions
async function getNearbyPredictions(lat, lon, radiusKm = 5) {
  const response = await fetch(
    `${API_BASE}/predictions/location?latitude=${lat}&longitude=${lon}&radius_km=${radiusKm}`
  );
  return response.json();
}

// Fetch stats for a location
async function getLocationStats(lat, lon, hours = 24) {
  const response = await fetch(
    `${API_BASE}/predictions/stats?latitude=${lat}&longitude=${lon}&hours=${hours}`
  );
  return response.json();
}

// Usage
const { predictions } = await getNearbyPredictions(40.7128, -74.0060);
const { stats } = await getLocationStats(40.7128, -74.0060);
console.log(`Average AQI: ${stats.avg_aqi}`);
```

## Testing

### Local Testing

```bash
# Start MongoDB
mongod

# Start API server
export MONGODB_URL=mongodb://localhost:27017
uvicorn api:app --reload

# Test /ingest endpoint
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "mq135_adc": 512,
    "air_quality_ppm": 15.5,
    "mq7_adc": 450,
    "co_ppm": 2.1,
    "dust_adc": 200,
    "dust_voltage": 3.2,
    "estimated_pm25": 25.0,
    "temperature": 22.5,
    "latitude": 40.7128,
    "longitude": -74.0060,
    "forecast_hours": 4
  }'

# Test /predictions/recent endpoint
curl http://localhost:8000/predictions/recent?limit=5

# Test /predictions/location endpoint
curl "http://localhost:8000/predictions/location?latitude=40.7128&longitude=-74.0060&radius_km=10"
```

### Debugging MongoDB Connection

```bash
# Check connection
mongosh "mongodb+srv://username:password@cluster.mongodb.net/air_quality"

# List collections
show collections

# Check recent documents
db.predictions.find().limit(5)

# Check indexes
db.predictions.getIndexes()
```

## Performance Tuning

### Index Best Practices

- **Geo-spatial queries**: 2dsphere indexes on [latitude, longitude] enable efficient distance calculations
- **Time-series**: Compound index on (timestamp, location) optimizes temporal + spatial queries
- **Read-heavy**: TTL indexes auto-delete old data (optional)

### Query Optimization

```python
# Efficient: Uses geo-spatial index
predictions = get_predictions_by_location(lat=40.7128, lon=-74.0060, radius_km=5)

# Efficient: Uses timestamp index
predictions = get_predictions_by_time_range(start, end, limit=100)

# Avoid: Full collection scan
predictions = db.predictions.find({"aqi": {"$gt": 100}})  # No index on aqi
```

## Deployment Checklist

- [ ] Created MongoDB Atlas account and cluster
- [ ] Created database user with strong password
- [ ] Set `MONGODB_URL` environment variable in Render dashboard
- [ ] Updated `requirements-render.txt` with `pymongo`
- [ ] Tested local connection with `mongosh` or Python client
- [ ] Deployed updated code to GitHub
- [ ] Verified Render deployment (check logs for MongoDB connection)
- [ ] Tested `/ingest` endpoint on deployed API
- [ ] Tested `/predictions/recent` endpoint
- [ ] Tested `/predictions/location` with sample coordinates
- [ ] Monitored API logs for MongoDB errors

## Troubleshooting

### "Connection timeout" error

**Cause**: MongoDB not running or network unreachable
**Solution**:
- Check MongoDB is running: `ps aux | grep mongod`
- Verify `MONGODB_URL` is correct
- Check firewall/network rules
- On Render: Verify `MONGODB_URL` env var is set in dashboard

### "Authentication failed" error

**Cause**: Incorrect username/password in connection string
**Solution**:
- Reset MongoDB password in Atlas dashboard
- Update `MONGODB_URL` with correct credentials
- Ensure special characters are URL-encoded

### Slow queries

**Cause**: Missing indexes
**Solution**:
- Run `init_db()` to create indexes
- Check index status: `db.predictions.getIndexes()`
- Monitor query execution: Enable MongoDB profiler

### Data not persisting

**Cause**: Using ephemeral file system (old SQLite approach)
**Solution**:
- Verify `MONGODB_URL` points to persistent database
- Check database connection on startup
- Verify storage functions don't catch exceptions silently

## Migration from SQLite

The storage layer automatically switches to MongoDB. No manual data migration needed for new deployments, but existing SQLite data can be migrated if needed:

```python
import sqlite3
from src.mongo_storage import insert_sensor_reading, insert_prediction

# Read from SQLite
conn = sqlite3.connect("data/hardware.db")
cursor = conn.cursor()
cursor.execute("SELECT payload FROM sensor_readings ORDER BY id DESC LIMIT 100")

# Write to MongoDB
for (payload_json,) in cursor.fetchall():
    insert_sensor_reading(json.loads(payload_json))

conn.close()
```

## References

- [MongoDB Official Documentation](https://docs.mongodb.com)
- [PyMongo Documentation](https://pymongo.readthedocs.io)
- [MongoDB Atlas Getting Started](https://docs.mongodb.com/manual/tutorial/getting-started/)
- [Geo-Spatial Queries](https://docs.mongodb.com/manual/geospatial-queries/)
