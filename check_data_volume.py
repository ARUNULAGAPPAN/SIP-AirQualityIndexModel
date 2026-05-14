#!/usr/bin/env python
"""Check the volume of sensor readings for the two locations."""

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
            "earliest_timestamp": {"$min": "$timestamp"},
        }
    },
    {"$sort": {"count": -1}},
]

locations = list(sensor_col.aggregate(pipeline))
client.close()

print(f"✓ Sensor readings by location:\n")
total_readings = 0
for idx, loc in enumerate(locations):
    lat = loc["_id"]["lat"]
    lon = loc["_id"]["lon"]
    count = loc["count"]
    latest = loc.get("latest_timestamp")
    earliest = loc.get("earliest_timestamp")
    total_readings += count
    
    print(f"{idx+1}. ({lat:.6f}, {lon:.6f})")
    print(f"   Readings: {count}")
    if latest and earliest:
        duration = latest - earliest
        print(f"   Duration: {duration.total_seconds() / 3600:.1f} hours")
    print()

print(f"✓ Total readings across all locations: {total_readings}")
