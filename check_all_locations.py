#!/usr/bin/env python
"""Check all distinct locations in database."""

from src.mongo_storage import get_client

client = get_client()
db = client["air_quality"]
sensor_col = db["sensor_readings"]

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
    {"$sort": {"latest_timestamp": -1}},
]

locations = list(sensor_col.aggregate(pipeline))
client.close()

print(f"✓ Found {len(locations)} distinct sensor locations:\n")
for idx, loc in enumerate(locations):
    lat = loc["_id"]["lat"]
    lon = loc["_id"]["lon"]
    count = loc["count"]
    print(f"{idx+1}. ({lat:.6f}, {lon:.6f}) - {count} reading(s)")

print("\n✓ Expected to see your two locations:")
print("  - (12.942556, 80.136284)")
print("  - (12.947448, 80.140701)")
