#!/usr/bin/env python
"""Test script: Fetch two sensor locations from database and generate short-term forecasts."""

import json
import sys
from datetime import datetime, timedelta
from src.mongo_storage import (
    init_db,
    insert_sensor_reading,
    get_distinct_locations_and_forecast,
)


def create_sample_reading(lat: float, lon: float, offset_hours: int = 0) -> dict:
    """Create a sample sensor reading for testing."""
    return {
        "mq135_adc": 512 + offset_hours * 10,
        "air_quality_ppm": 15.5 + offset_hours * 0.5,
        "mq7_adc": 450 + offset_hours * 5,
        "co_ppm": 2.1 + offset_hours * 0.1,
        "dust_adc": 200 + offset_hours * 3,
        "dust_voltage": 3.2,
        "estimated_pm25": 25.0 + offset_hours * 1.5,
        "temperature": 22.5 + offset_hours * 0.2,
        "humidity": 55,
        "wind_speed": 3.5,
        "pressure": 1013.25,
        "latitude": lat,
        "longitude": lon,
    }


def main():
    print("=" * 70)
    print("TEST: Two-Location Short-Term Forecasting")
    print("=" * 70)
    
    # Initialize MongoDB
    print("\n1. Initializing MongoDB...")
    init_db()
    print("   ✓ Database initialized")
    
    # Insert sample readings for two distinct locations
    print("\n2. Inserting sample sensor readings for two locations...")
    
    # Location 1: New York
    for hour in range(4):
        reading_ny = create_sample_reading(lat=40.7128, lon=-74.0060, offset_hours=hour)
        doc_id = insert_sensor_reading(reading_ny)
        print(f"   ✓ Location 1 (NYC): Reading {hour+1}/4 inserted - ID: {doc_id}")
    
    # Location 2: Los Angeles
    for hour in range(4):
        reading_la = create_sample_reading(lat=34.0522, lon=-118.2437, offset_hours=hour)
        doc_id = insert_sensor_reading(reading_la)
        print(f"   ✓ Location 2 (LA):  Reading {hour+1}/4 inserted - ID: {doc_id}")
    
    # Fetch the two locations and generate forecasts
    print("\n3. Fetching two locations and generating short-term forecasts...")
    result = get_distinct_locations_and_forecast(forecast_hours=4)
    
    print(f"\n4. Results for {result['count']} locations:\n")
    
    for idx, location_data in enumerate(result["locations"], 1):
        lat = location_data["latitude"]
        lon = location_data["longitude"]
        
        location_name = "New York (NYC)" if abs(lat - 40.7128) < 0.01 else "Los Angeles (LA)"
        
        print(f"\n   Location {idx}: {location_name}")
        print(f"   ├─ Coordinates: ({lat}, {lon})")
        print(f"   ├─ Latest Reading Timestamp: {location_data['latest_reading_timestamp']}")
        print(f"   ├─ Latest Sensor Values:")
        for key, val in location_data["latest_reading"].items():
            print(f"   │  ├─ {key}: {val}")
        
        forecast = location_data["forecast"]
        print(f"   ├─ Current AQI: {forecast['current_aqi']}")
        print(f"   ├─ Sensor Contributions:")
        contrib = forecast["sensor_contributions"]
        print(f"   │  ├─ Primary Pollutant: {contrib.get('primary_pollutant', 'N/A')}")
        print(f"   │  ├─ PM2.5: {contrib.get('pm25', {}).get('aqi', 'N/A')}")
        print(f"   │  ├─ CO: {contrib.get('co', {}).get('aqi', 'N/A')}")
        print(f"   │  └─ MQ135: {contrib.get('mq135', {}).get('aqi', 'N/A')}")
        
        print(f"   ├─ Short-Term Forecast (next 4 hours):")
        for entry in forecast["forecast_entries"]:
            print(f"   │  ├─ Hour {entry['hour_ahead']}: AQI={entry['predicted_aqi']} ({entry['aqi_category']}) - Confidence: {entry['confidence']:.1%}")
        
        advisory = forecast["advisory"]
        print(f"   └─ Advisory:")
        print(f"      ├─ Level: {advisory.get('level', 'N/A')}")
        print(f"      ├─ Message: {advisory.get('message', 'N/A')[:60]}...")
        print(f"      └─ Recommendation: {advisory.get('recommendation', 'N/A')[:60]}...")
    
    print("\n" + "=" * 70)
    print("✓ Test completed successfully!")
    print("=" * 70)
    
    # Print raw JSON for inspection
    print("\nRaw JSON Output:")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
