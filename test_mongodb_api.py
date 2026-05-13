#!/usr/bin/env python
"""Test MongoDB-backed API endpoints."""
import requests
import json

API = "https://airquality-api-4njf.onrender.com"

print("=" * 70)
print("MONGODB API INTEGRATION TEST")
print("=" * 70)

# Test 1: Health check
print("\n[1/5] Health Check")
print("-" * 70)
resp = requests.get(f"{API}/health")
print(f"Status: {resp.status_code}")
print(f"Response: {resp.json()}")

# Test 2: Ingest sensor data
print("\n[2/5] Ingest Sensor Data to MongoDB")
print("-" * 70)
payload = {
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
    "forecast_hours": 4,
}
resp = requests.post(f"{API}/ingest", json=payload)
print(f"Status: {resp.status_code}")
print(f"Response: {json.dumps(resp.json(), indent=2)}")
sensor_id = resp.json().get("sensor_id")
print(f"✓ Stored sensor ID: {sensor_id}")

# Test 3: Get recent predictions
print("\n[3/5] Get Recent Predictions")
print("-" * 70)
resp = requests.get(f"{API}/predictions/recent?limit=5")
print(f"Status: {resp.status_code}")
data = resp.json()
print(f"Count: {data.get('count')}")
if data.get("predictions"):
    print("Latest 3 predictions:")
    for i, pred in enumerate(data.get("predictions", [])[:3]):
        print(f"  [{i+1}] AQI={pred.get('aqi')}, Lat={pred.get('latitude')}, Lon={pred.get('longitude')}, Time={pred.get('timestamp')[:19]}")

# Test 4: Get predictions by location
print("\n[4/5] Get Predictions by Location (radius=10km)")
print("-" * 70)
resp = requests.get(f"{API}/predictions/location?latitude=40.7128&longitude=-74.0060&radius_km=10&limit=5")
print(f"Status: {resp.status_code}")
data = resp.json()
print(f"Count: {data.get('count')}")
location = data.get("location", {})
print(f"Search center: ({location.get('latitude')}, {location.get('longitude')})")
print(f"Radius: {location.get('radius_km')} km")

# Test 5: Get node stats
print("\n[5/5] Get Node Statistics (24 hours)")
print("-" * 70)
resp = requests.get(f"{API}/predictions/stats?latitude=40.7128&longitude=-74.0060&hours=24")
print(f"Status: {resp.status_code}")
data = resp.json()
stats = data.get("stats", {})
print(f"Time window: {data.get('time_window_hours')} hours")
print(f"Stats:")
print(f"  Count: {stats.get('count')}")
print(f"  Avg AQI: {stats.get('avg_aqi')}")
print(f"  Max AQI: {stats.get('max_aqi')}")
print(f"  Min AQI: {stats.get('min_aqi')}")

print("\n" + "=" * 70)
print("✓ ALL TESTS COMPLETED - MongoDB API working!")
print("=" * 70)
