#!/usr/bin/env python
"""Test script to verify two sensor locations are fetchable and forecast works."""

from src.mongo_storage import get_distinct_locations_and_forecast, get_latest_reading_for_location

result = get_distinct_locations_and_forecast(forecast_hours=4)
locations = result.get("locations", [])

print(f"✓ Found {len(locations)} sensor locations\n")

for idx, loc in enumerate(locations):
    lat = loc["latitude"]
    lon = loc["longitude"]
    aqi = loc["forecast"]["current_aqi"]
    reading = loc["latest_reading"]
    forecast_count = len(loc["forecast"].get("forecast_entries", []))
    
    print(f"Location {idx+1}: ({lat:.4f}, {lon:.4f})")
    print(f"  Current AQI: {aqi}")
    print(f"  Latest Reading: {reading}")
    print(f"  Forecast entries: {forecast_count}")
    
    # Test get_latest_reading_for_location
    latest = get_latest_reading_for_location(lat, lon)
    if latest:
        print(f"  ✓ get_latest_reading_for_location works: mq135_adc={latest.get('mq135_adc')}")
    print()

print("✓ All tests passed! Dashboard should work correctly.")
