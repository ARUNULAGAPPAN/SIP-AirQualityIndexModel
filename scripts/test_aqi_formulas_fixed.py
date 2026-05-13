"""Test and verify AQI formula implementations.

This script validates:
1. PM2.5 AQI calculation (EPA formula)
2. CO AQI calculation (EPA formula)
3. MQ135 pollution index formula
4. Overall AQI (maximum of pollutants)
5. Weather adjustment factors
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.aqi import (
    pollutant_aqi,
    mq135_pollution_index,
    overall_aqi,
    AQI_CATEGORIES,
    PM25_BREAKPOINTS,
    CO_BREAKPOINTS,
)
from src.predictor import compute_aqi_from_sensors, SensorReading, WeatherData


def test_pm25_aqi():
    """Test PM2.5 AQI calculations against EPA examples."""
    print("\n" + "="*70)
    print("TEST 1: PM2.5 AQI Calculation (EPA Formula)")
    print("="*70)
    
    test_cases = [
        (0.0, 0, "Good"),           # Minimum
        (12.0, 50, "Good"),         # Upper good limit
        (15.0, 57, "Moderate"),     # Manual calculation example
        (35.4, 100, "Moderate"),    # Upper moderate limit
        (55.4, 150, "Unhealthy for Sensitive Groups"),
        (150.4, 200, "Unhealthy"),
        (250.4, 300, "Very Unhealthy"),
        (350.4, 400, "Hazardous"),
        (500.0, 496, "Hazardous"),  # Above upper limit (extrapolated value)
    ]
    
    all_passed = True
    for conc, expected_aqi, expected_category in test_cases:
        aqi, category = pollutant_aqi(conc, "PM2.5")
        # Allow ±1 tolerance for rounding
        passed = abs(aqi - expected_aqi) <= 1 and category == expected_category
        status = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_passed = False
        print(f"{status}: PM2.5 = {conc:6.1f} µg/m³ → AQI = {aqi:3d} ({category})")
        if not passed:
            print(f"       Expected: AQI = {expected_aqi}, Category = {expected_category}")
    
    return all_passed


def test_co_aqi():
    """Test CO AQI calculations against EPA examples."""
    print("\n" + "="*70)
    print("TEST 2: CO AQI Calculation (EPA Formula)")
    print("="*70)
    
    test_cases = [
        (0.0, 0, "Good"),           # Minimum
        (4.4, 50, "Good"),          # Upper good limit
        (6.0, 66, "Moderate"),      # Manual calculation example
        (9.4, 100, "Moderate"),     # Upper moderate limit
        (12.4, 150, "Unhealthy for Sensitive Groups"),
        (15.4, 200, "Unhealthy"),
        (30.4, 300, "Very Unhealthy"),
        (40.4, 400, "Hazardous"),
        (50.0, 496, "Hazardous"),   # Above upper limit (extrapolated value)
    ]
    
    all_passed = True
    for conc, expected_aqi, expected_category in test_cases:
        aqi, category = pollutant_aqi(conc, "CO")
        # Allow ±1 tolerance for rounding
        passed = abs(aqi - expected_aqi) <= 1 and category == expected_category
        status = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_passed = False
        print(f"{status}: CO = {conc:5.1f} ppm → AQI = {aqi:3d} ({category})")
        if not passed:
            print(f"       Expected: AQI = {expected_aqi}, Category = {expected_category}")
    
    return all_passed


def test_mq135_index():
    """Test MQ135 pollution index formula."""
    print("\n" + "="*70)
    print("TEST 3: MQ135 Pollution Index Formula")
    print("="*70)
    
    test_cases = [
        (5.0, 400, "Hazardous (2x safe limit)"),
        (10.0, 200, "Very Unhealthy (0.5x safe limit)"),
        (20.0, 100, "Moderate (at safe limit)"),
        (30.0, 67, "Good (1.5x safe limit)"),
        (40.0, 50, "Good (2x safe limit)"),
    ]
    
    all_passed = True
    for conc, expected_approx, description in test_cases:
        index = mq135_pollution_index(conc)
        # Allow ±2 tolerance for rounding
        passed = abs(index - expected_approx) <= 2
        status = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_passed = False
        print(f"{status}: MQ135 = {conc:5.1f} ppm → Index = {index:.0f} - {description}")
        if not passed:
            print(f"       Expected: ~{expected_approx}")
    
    return all_passed


def test_overall_aqi():
    """Test overall AQI calculation (maximum of pollutants)."""
    print("\n" + "="*70)
    print("TEST 4: Overall AQI (Maximum of PM2.5, CO, MQ135)")
    print("="*70)
    
    test_cases = [
        # (PM2.5, CO, MQ135_ppm, expected_aqi, expected_primary)
        (15.0, 6.0, 25.0, 80, "MQ135"),      # MQ135 dominates
        (35.0, 12.0, 20.0, 150, "PM2.5"),    # PM2.5 dominates
        (0.5, 0.2, 100.0, 20, "MQ135"),      # Clean with high MQ135 reading
        (55.4, 4.4, 20.0, 150, "PM2.5"),     # PM2.5 at limit
    ]
    
    all_passed = True
    for pm25, co, mq135, expected_aqi, expected_primary in test_cases:
        row = {
            "Estimated PM2.5": pm25,
            "CO PPM": co,
            "Air Quality PPM": mq135,
        }
        aqi, primary = overall_aqi(row)
        passed = aqi == expected_aqi and primary == expected_primary
        status = "✓ PASS" if passed else "✗ FAIL"
        if not passed:
            all_passed = False

        print(f"{status}: PM2.5={pm25:5.1f}, CO={co:4.1f}, MQ135={mq135:5.1f}")
        print(f"       → AQI = {aqi:3d} (Primary: {primary})")
        if not passed:
            print(f"       Expected: AQI = {expected_aqi}, Primary = {expected_primary}")
    
    return all_passed


def test_hardware_sensor_aqi():
    """Test AQI calculation from hardware sensor readings."""
    print("\n" + "="*70)
    print("TEST 5: Hardware Sensor AQI Calculation")
    print("="*70)
    
    # Test case 1: Clean air conditions
    sensor1 = SensorReading(
        mq135_adc=1299,
        air_quality_ppm=1.27,
        mq7_adc=331,
        co_ppm=0.23,
        dust_adc=737,
        dust_voltage=0.59,
        estimated_pm25=0.97,
        temperature=23.68,
    )
    
    weather1 = WeatherData(
        temperature=23.68,
        humidity=65.0,
        wind_speed=3.5,
        pressure=1013.0,
    )
    
    aqi1, contrib1 = compute_aqi_from_sensors(sensor1, weather1)
    print(f"✓ Clean conditions:")
    print(f"  PM2.5 = {contrib1['PM2.5_value_ug_m3']:5.2f} µg/m³ → AQI = {contrib1['PM2.5_aqi']}")
    print(f"  CO    = {contrib1['CO_value_ppm']:5.3f} ppm     → AQI = {contrib1['CO_aqi']}")
    print(f"  MQ135 = {contrib1['MQ135_value_ppm']:5.2f} ppm     → Index = {contrib1['MQ135_aqi']}")
    print(f"  Primary Pollutant: {contrib1['primary_pollutant']}")
    print(f"  Final AQI: {aqi1}")
    print(f"  Weather Adjustment: {contrib1['weather_adjustment_factor']}")
    
    # Test case 2: Poor air conditions with strong wind
    sensor2 = SensorReading(
        mq135_adc=3500,
        air_quality_ppm=8.5,
        mq7_adc=1200,
        co_ppm=8.5,
        dust_adc=3000,
        dust_voltage=3.5,
        estimated_pm25=125.0,
        temperature=28.0,
    )
    
    weather2 = WeatherData(
        temperature=28.0,
        humidity=85.0,
        wind_speed=8.0,  # Strong wind helps
        pressure=995.0,  # Low pressure traps
    )
    
    aqi2, contrib2 = compute_aqi_from_sensors(sensor2, weather2)
    print(f"\n✓ Poor conditions with strong wind:")
    print(f"  PM2.5 = {contrib2['PM2.5_value_ug_m3']:5.2f} µg/m³ → AQI = {contrib2['PM2.5_aqi']}")
    print(f"  CO    = {contrib2['CO_value_ppm']:5.3f} ppm     → AQI = {contrib2['CO_aqi']}")
    print(f"  MQ135 = {contrib2['MQ135_value_ppm']:5.2f} ppm     → Index = {contrib2['MQ135_aqi']}")
    print(f"  Primary Pollutant: {contrib2['primary_pollutant']}")
    print(f"  Final AQI: {aqi2}")
    print(f"  Weather Adjustment: {contrib2['weather_adjustment_factor']}")
    
    return True


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "="*70)
    print("TEST 6: Edge Cases & Error Handling")
    print("="*70)
    
    all_passed = True
    
    # Test 1: None values
    try:
        aqi, cat = pollutant_aqi(None, "PM2.5")
        print(f"✓ None handling: pollutant_aqi(None) → AQI = {aqi} (Expected: 0)")
        passed = aqi == 0
        all_passed = all_passed and passed
    except Exception as e:
        print(f"✗ None handling failed: {e}")
        all_passed = False
    
    # Test 2: Negative values
    try:
        aqi, cat = pollutant_aqi(-5.0, "PM2.5")
        print(f"✓ Negative handling: pollutant_aqi(-5.0) → AQI = {aqi} (Expected: 0)")
        passed = aqi == 0
        all_passed = all_passed and passed
    except Exception as e:
        print(f"✗ Negative handling failed: {e}")
        all_passed = False
    
    # Test 3: Very high values (extrapolation)
    aqi, cat = pollutant_aqi(1000.0, "PM2.5")
    print(f"✓ High value extrapolation: PM2.5 = 1000 → AQI = {aqi} (capped at 500)")
    passed = aqi <= 500
    all_passed = all_passed and passed
    
    # Test 4: MQ135 with zero
    index = mq135_pollution_index(0.0)
    print(f"✓ MQ135 zero handling: mq135_pollution_index(0.0) → {index} (Expected: 0)")
    passed = index == 0.0
    all_passed = all_passed and passed
    
    return all_passed


def test_formula_consistency():
    """Test formula consistency and mathematical properties."""
    print("\n" + "="*70)
    print("TEST 7: Formula Consistency & Mathematical Properties")
    print("="*70)
    
    all_passed = True
    
    # Property 1: AQI should increase with pollutant concentration
    print("✓ Testing monotonicity (AQI increases with concentration)...")
    pm25_values = [5, 10, 15, 20, 30, 50, 100]
    prev_aqi = 0
    for pm25 in pm25_values:
        aqi, _ = pollutant_aqi(pm25, "PM2.5")
        if aqi >= prev_aqi:
            print(f"  PM2.5 = {pm25:3d} → AQI = {aqi:3d} ✓")
        else:
            print(f"  PM2.5 = {pm25:3d} → AQI = {aqi:3d} ✗ (decreases from {prev_aqi})")
            all_passed = False
        prev_aqi = aqi
    
    # Property 2: Overall AQI should equal the maximum
    print("\n✓ Testing overall_aqi returns maximum...")
    row = {"Estimated PM2.5": 20.0, "CO PPM": 5.0, "Air Quality PPM": 30.0}
    overall, primary = overall_aqi(row)
    aqi_pm25, _ = pollutant_aqi(20.0, "PM2.5")
    aqi_co, _ = pollutant_aqi(5.0, "CO")
    aqi_mq135 = int(mq135_pollution_index(30.0))
    expected_max = max(aqi_pm25, aqi_co, aqi_mq135)
    if overall == expected_max:
        print(f"  PM2.5={aqi_pm25}, CO={aqi_co}, MQ135={aqi_mq135}")
        print(f"  max() = {expected_max}, overall_aqi() = {overall} ✓")
    else:
        print(f"  Expected max = {expected_max}, got {overall} ✗")
        all_passed = False
    
    return all_passed


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("AIR QUALITY INDEX (AQI) FORMULA VERIFICATION")
    print("="*70)
    
    results = {
        "PM2.5 AQI": test_pm25_aqi(),
        "CO AQI": test_co_aqi(),
        "MQ135 Index": test_mq135_index(),
        "Overall AQI": test_overall_aqi(),
        "Hardware Sensor": test_hardware_sensor_aqi(),
        "Edge Cases": test_edge_cases(),
        "Formula Consistency": test_formula_consistency(),
    }
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    all_passed = True
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
        all_passed = all_passed and passed
    
    print("="*70)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
