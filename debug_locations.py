#!/usr/bin/env python
"""Debug the get_distinct_locations_and_forecast function."""

from src.mongo_storage import get_distinct_locations_and_forecast, get_client

# First check if data exists
client = get_client()
db = client["airquality"]
sensor_col = db["sensor_readings"]

# Check raw data
count = sensor_col.count_documents({})
print(f"Total documents in sensor_readings: {count}")

# Get sample documents
sample = sensor_col.find_one()
if sample:
    print(f"\nSample document keys: {list(sample.keys())}")
    print(f"Sample lat: {sample.get('latitude')}, lon: {sample.get('longitude')}")

# Try the aggregation manually
pipeline = [
    {
        "$group": {
            "_id": {
                "lat": "$latitude",
                "lon": "$longitude",
            },
            "count": {"$sum": 1},
        }
    },
    {"$sort": {"count": -1}},
    {"$limit": 2},
]

results = list(sensor_col.aggregate(pipeline))
print(f"\nAggregation results: {len(results)} locations")
for loc in results:
    print(f"  - ({loc['_id']['lat']}, {loc['_id']['lon']}): {loc['count']} readings")

client.close()

# Now try the function
print("\n\nCalling get_distinct_locations_and_forecast()...")
result = get_distinct_locations_and_forecast(forecast_hours=4)
print(f"Result: {len(result.get('locations', []))} locations found")
for loc in result.get('locations', []):
    print(f"  - ({loc['latitude']}, {loc['longitude']}): AQI={loc['forecast']['current_aqi']}")
