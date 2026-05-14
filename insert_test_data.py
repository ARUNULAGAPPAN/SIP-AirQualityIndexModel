#!/usr/bin/env python
"""Insert sensor readings directly into MongoDB for the two locations."""

from src.mongo_storage import insert_sensor_reading, get_latest_reading_for_location

# Location 1
payload1 = {
    'mq135_adc': 512,
    'air_quality_ppm': 15.5,
    'mq7_adc': 450,
    'co_ppm': 2.1,
    'dust_adc': 200,
    'dust_voltage': 3.2,
    'estimated_pm25': 25.0,
    'temperature': 22.5,
    'latitude': 12.942556,
    'longitude': 80.136284,
}

# Location 2
payload2 = {
    'mq135_adc': 450,
    'air_quality_ppm': 12.3,
    'mq7_adc': 380,
    'co_ppm': 1.8,
    'dust_adc': 180,
    'dust_voltage': 2.9,
    'estimated_pm25': 18.0,
    'temperature': 24.0,
    'latitude': 12.947448,
    'longitude': 80.140701,
}

try:
    id1 = insert_sensor_reading(payload1)
    print(f"✓ Inserted Location 1 (12.942556, 80.136284): {id1}")
    
    id2 = insert_sensor_reading(payload2)
    print(f"✓ Inserted Location 2 (12.947448, 80.140701): {id2}")
    
    # Verify they're retrievable
    reading1 = get_latest_reading_for_location(12.942556, 80.136284)
    print(f"✓ Retrieved Location 1: mq135_adc={reading1.get('mq135_adc')}")
    
    reading2 = get_latest_reading_for_location(12.947448, 80.140701)
    print(f"✓ Retrieved Location 2: mq135_adc={reading2.get('mq135_adc')}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
