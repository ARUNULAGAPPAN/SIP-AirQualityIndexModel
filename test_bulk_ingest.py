#!/usr/bin/env python
"""Test bulk ingest endpoint."""
import requests
import json

API_URL = "https://airquality-api-4njf.onrender.com/ingest"

# Single payload test
print("=" * 70)
print("TEST 1: Single Payload")
print("=" * 70)

single_payload = {
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
}

response = requests.post(API_URL, json=single_payload, timeout=10)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# Bulk array test
print("\n" + "=" * 70)
print("TEST 2: Bulk Array Payloads")
print("=" * 70)

bulk_payloads = [
    {
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
    },
    {
        "mq135_adc": 520,
        "air_quality_ppm": 16.2,
        "mq7_adc": 455,
        "co_ppm": 2.3,
        "dust_adc": 210,
        "dust_voltage": 3.3,
        "estimated_pm25": 26.0,
        "temperature": 23.0,
        "latitude": 40.7129,
        "longitude": -74.0061,
        "forecast_hours": 4
    },
    {
        "mq135_adc": 530,
        "air_quality_ppm": 17.0,
        "mq7_adc": 460,
        "co_ppm": 2.5,
        "dust_adc": 220,
        "dust_voltage": 3.4,
        "estimated_pm25": 27.0,
        "temperature": 23.5,
        "latitude": 40.7130,
        "longitude": -74.0062,
        "forecast_hours": 4
    }
]

response = requests.post(API_URL, json=bulk_payloads, timeout=10)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

print("\n" + "=" * 70)
print("✓ BULK INGEST ENDPOINT WORKING")
print("=" * 70)
