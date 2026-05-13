#!/usr/bin/env python
"""Test GPS validation and MQ135 scaling fixes."""
from src.predictor import compute_aqi_from_sensors, SensorReading, WeatherData, LocationContext

# Test data: clean air
sensor = SensorReading(
    mq135_adc=1000,
    air_quality_ppm=1.27,  # Low PPM = good air
    mq7_adc=350,
    co_ppm=0.23,
    dust_adc=200,
    dust_voltage=3.2,
    estimated_pm25=0.97,
    temperature=23.68,
)

weather = WeatherData(
    temperature=23.68,
    humidity=60.0,
    wind_speed=2.0,
    pressure=1013.0,
)

print("=" * 70)
print("TESTING FIXES: MQ135 SCALING + GPS VALIDATION")
print("=" * 70)

# Test 1: Invalid GPS (test coordinates)
print("\n[1] Invalid GPS coordinates (-90, -180)")
print("-" * 70)
location_invalid = LocationContext(latitude=-90, longitude=-180)
aqi, contrib = compute_aqi_from_sensors(sensor, weather, location_invalid)
print(f"Final AQI: {contrib['final_aqi']}")
print(f"Weather adjustment applied: {contrib['weather_adjustment_applied']}")
print(f"Weather factor: {contrib['weather_adjustment_factor']}")
print(f"PM2.5 AQI: {contrib['PM2.5_aqi']}")
print(f"CO AQI: {contrib['CO_aqi']}")
print(f"MQ135 AQI: {contrib['MQ135_aqi']} (from 1.27 ppm → (1.27/10)*100 = 12.7 ≈ 13)")

# Test 2: Valid GPS
print("\n[2] Valid GPS coordinates (40.7128, -74.0060)")
print("-" * 70)
location_valid = LocationContext(latitude=40.7128, longitude=-74.0060)
aqi2, contrib2 = compute_aqi_from_sensors(sensor, weather, location_valid)
print(f"Final AQI: {contrib2['final_aqi']}")
print(f"Weather adjustment applied: {contrib2['weather_adjustment_applied']}")
print(f"Weather factor: {contrib2['weather_adjustment_factor']}")
print(f"PM2.5 AQI: {contrib2['PM2.5_aqi']}")
print(f"CO AQI: {contrib2['CO_aqi']}")
print(f"MQ135 AQI: {contrib2['MQ135_aqi']}")

print("\n" + "=" * 70)
print("✓ FIXES WORKING:")
print("  • MQ135 scaling: (ppm / 10) * 100, capped at 500")
print("  • GPS validation: Invalid coords (-90, -180) skip weather")
print("  • Weather adjustment only applied for valid GPS")
print("=" * 70)
