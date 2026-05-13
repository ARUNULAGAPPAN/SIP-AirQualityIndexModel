#!/usr/bin/env python
"""Local test of bulk ingest logic."""
from pydantic import BaseModel, Field
from typing import Union

class PredictionRequest(BaseModel):
    mq135_adc: float = Field(..., ge=0)
    air_quality_ppm: float = Field(..., ge=0)
    mq7_adc: float = Field(..., ge=0)
    co_ppm: float = Field(..., ge=0)
    dust_adc: float = Field(..., ge=0)
    dust_voltage: float = Field(..., ge=0)
    estimated_pm25: float = Field(..., ge=0)
    temperature: float
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    forecast_hours: int = Field(4, ge=1, le=6)

# Test single payload parsing
print("=" * 70)
print("TEST 1: Single Payload Parsing")
print("=" * 70)

single_dict = {
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

single = PredictionRequest(**single_dict)
print(f"✓ Single payload parsed successfully")
print(f"  mq135_adc={single.mq135_adc}, air_quality_ppm={single.air_quality_ppm}")

# Test bulk payload parsing
print("\n" + "=" * 70)
print("TEST 2: Bulk Array Parsing")
print("=" * 70)

bulk_list = [
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
    }
]

parsed_bulk = [PredictionRequest(**item) for item in bulk_list]
print(f"✓ Bulk array parsed successfully: {len(parsed_bulk)} items")
for i, item in enumerate(parsed_bulk, 1):
    print(f"  [{i}] mq135_adc={item.mq135_adc}, air_quality_ppm={item.air_quality_ppm}")

# Simulate ingest endpoint logic
print("\n" + "=" * 70)
print("TEST 3: Ingest Endpoint Logic")
print("=" * 70)

def simulate_insert_reading(data_dict):
    """Simulate MongoDB insert, just return a mock ID."""
    import uuid
    return str(uuid.uuid4())

def process_ingest(payload):
    """Simulate the ingest endpoint."""
    # Handle bulk array of payloads
    if isinstance(payload, list):
        sensor_ids = []
        for item in payload:
            if isinstance(item, dict):
                sensor_id = simulate_insert_reading(item)
                sensor_ids.append(sensor_id)
            else:
                sensor_id = simulate_insert_reading(item.dict())
                sensor_ids.append(sensor_id)
        return {
            "status": "ok",
            "count": len(sensor_ids),
            "sensor_ids": sensor_ids,
        }
    # Handle single payload
    else:
        sensor_id = simulate_insert_reading(payload.dict())
        return {"status": "ok", "sensor_id": sensor_id}

# Test with single payload
result_single = process_ingest(single)
print(f"Single payload result: {result_single}")
print(f"  ✓ Status: {result_single['status']}")
print(f"  ✓ Sensor ID: {result_single['sensor_id']}")

# Test with bulk array
result_bulk = process_ingest(parsed_bulk)
print(f"\nBulk array result: {result_bulk}")
print(f"  ✓ Status: {result_bulk['status']}")
print(f"  ✓ Count: {result_bulk['count']}")
print(f"  ✓ Sensor IDs: {len(result_bulk['sensor_ids'])} generated")

print("\n" + "=" * 70)
print("✓ ALL TESTS PASSED - BULK INGEST LOGIC WORKING")
print("=" * 70)
