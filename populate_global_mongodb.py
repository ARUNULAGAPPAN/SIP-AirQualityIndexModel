#!/usr/bin/env python
"""Populate the global MongoDB with sensor readings for the two locations."""

from src.mongo_storage import insert_sensor_reading, get_latest_reading_for_location
from datetime import datetime, timedelta
import random

# Two sensor locations
locations = [
    {
        "name": "Sensor 1",
        "latitude": 12.942556,
        "longitude": 80.136284,
        "readings_count": 2445,
    },
    {
        "name": "Sensor 2",
        "latitude": 12.947448,
        "longitude": 80.140701,
        "readings_count": 2383,
    }
]

print("Populating global MongoDB with sensor readings...\n")

for loc in locations:
    print(f"Generating {loc['readings_count']} readings for {loc['name']} ({loc['latitude']}, {loc['longitude']})...")
    
    # Generate readings spread over the past 24 hours
    base_time = datetime.utcnow() - timedelta(hours=24)
    
    for i in range(loc['readings_count']):
        # Spread readings evenly over 24 hours
        timestamp = base_time + timedelta(seconds=(i * 86400 / loc['readings_count']))
        
        # Realistic sensor data with some variation
        payload = {
            'mq135_adc': random.randint(400, 600),
            'air_quality_ppm': random.uniform(10, 20),
            'mq7_adc': random.randint(300, 500),
            'co_ppm': random.uniform(1.5, 3.0),
            'dust_adc': random.randint(150, 300),
            'dust_voltage': random.uniform(2.5, 3.5),
            'estimated_pm25': random.uniform(15, 35),
            'temperature': random.uniform(20, 30),
            'latitude': loc['latitude'],
            'longitude': loc['longitude'],
        }
        
        try:
            insert_sensor_reading(payload)
            if (i + 1) % 500 == 0:
                print(f"  ✓ Inserted {i + 1} / {loc['readings_count']}")
        except Exception as e:
            print(f"  ✗ Error inserting reading {i}: {e}")
            break
    
    print(f"  ✓ Completed {loc['name']}\n")

# Verify
print("Verifying data...")
for loc in locations:
    reading = get_latest_reading_for_location(loc['latitude'], loc['longitude'])
    if reading:
        print(f"✓ {loc['name']}: Retrieved latest reading")
    else:
        print(f"✗ {loc['name']}: Could not retrieve reading")

print("\n✓ Global MongoDB is now populated!")
