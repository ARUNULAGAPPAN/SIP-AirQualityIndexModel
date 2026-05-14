#!/usr/bin/env python
"""Test aggregated readings for the two sensor locations."""

from src.mongo_storage import get_aggregated_readings_for_location

# Test aggregated readings
lat1, lon1 = 12.942556, 80.136284
lat2, lon2 = 12.947448, 80.140701

agg1 = get_aggregated_readings_for_location(lat1, lon1, count=20)
agg2 = get_aggregated_readings_for_location(lat2, lon2, count=20)

print(f'Location 1 ({lat1}, {lon1}):')
if agg1:
    print(f'  ✓ Aggregated {agg1["reading_count"]} readings')
    print(f'  mq135_adc avg: {agg1["mq135_adc"]:.1f}')
    print(f'  air_quality_ppm avg: {agg1["air_quality_ppm"]:.2f}')
    print(f'  temperature avg: {agg1["temperature"]:.1f}')
else:
    print(f'  ✗ No data found')

print(f'\nLocation 2 ({lat2}, {lon2}):')
if agg2:
    print(f'  ✓ Aggregated {agg2["reading_count"]} readings')
    print(f'  mq135_adc avg: {agg2["mq135_adc"]:.1f}')
    print(f'  air_quality_ppm avg: {agg2["air_quality_ppm"]:.2f}')
    print(f'  temperature avg: {agg2["temperature"]:.1f}')
else:
    print(f'  ✗ No data found')

print("\n✓ Aggregated readings test complete!")
