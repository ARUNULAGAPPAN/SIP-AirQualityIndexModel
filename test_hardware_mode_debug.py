#!/usr/bin/env python
"""Debug script to test hardware mode data flow and API response structure."""
import requests
import json
from datetime import datetime

API_URL = "https://airquality-api-4njf.onrender.com/predict"

print("=" * 80)
print("TESTING HARDWARE MODE DATA FLOW")
print("=" * 80)

# Test payload
payload = {
    "mq135_adc": 1299,
    "air_quality_ppm": 1.27,
    "mq7_adc": 331,
    "co_ppm": 0.23,
    "dust_adc": 737,
    "dust_voltage": 0.59,
    "estimated_pm25": 0.97,
    "temperature": 23.68,
    "latitude": 23.0225,
    "longitude": 72.5714,
    "forecast_hours": 4,
}

print(f"\n[1] Sending request to {API_URL}")
print(f"Payload: {json.dumps(payload, indent=2)}\n")

try:
    response = requests.post(API_URL, json=payload, timeout=30)
    print(f"[2] Response Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n[3] Response Structure:\n")
        print(json.dumps(data, indent=2)[:1500])  # First 1500 chars
        
        print("\n" + "=" * 80)
        print("CHECKING REQUIRED KEYS FOR PAGE DISPLAY")
        print("=" * 80)
        
        required_keys = [
            ("current", "Must have current AQI data"),
            ("forecast", "Must have forecast data"),
            ("peak_forecast", "Must have peak forecast"),
            ("advisory", "Must have health advisory"),
        ]
        
        for key, description in required_keys:
            if key in data:
                print(f"✓ '{key}' present: {description}")
                if key == "current":
                    if "aqi" in data["current"]:
                        print(f"    └─ AQI: {data['current']['aqi']}")
                    if "sensor_contributions" in data["current"]:
                        print(f"    └─ Contributions keys: {list(data['current']['sensor_contributions'].keys())}")
            else:
                print(f"✗ '{key}' MISSING: {description}")
        
        print("\n" + "=" * 80)
        print("CHECKING ADVISORY STRUCTURE")
        print("=" * 80)
        
        if "advisory" in data:
            advisory = data["advisory"]
            advisory_keys = ["level", "message", "emoji", "recommendation", "avoid_duration"]
            for key in advisory_keys:
                status = "✓" if key in advisory else "✗"
                print(f"{status} '{key}': {advisory.get(key, 'MISSING')}")
        
        print("\n" + "=" * 80)
        print("EXPECTED PAGE FLOW")
        print("=" * 80)
        print("""
1. Hardware mode fetches API
2. API returns full advisory dict
3. Page extracts 'current' → shows AQI gauge and metrics
4. Page extracts 'forecast' → shows trend chart
5. Page extracts 'advisory' → shows health recommendations
        """)
        
    else:
        print(f"✗ API Error: {response.text}")
        
except Exception as e:
    print(f"✗ Request failed: {e}")
    print(f"\nTroubleshooting:")
    print(f"1. Is API running?")
    print(f"2. Can you reach {API_URL} from browser?")
    print(f"3. Check Render logs: https://dashboard.render.com")

print("\n" + "=" * 80)
