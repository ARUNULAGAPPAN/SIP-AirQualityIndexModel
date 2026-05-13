"""
AQI Formula Quick Reference - Usage Guide

This guide provides copy-paste code examples for using EPA standard AQI formulas
in the Air Quality Forecasting project.
"""

# =============================================================================
# OPTION 1: Single Pollutant AQI (EPA Formula)
# =============================================================================

from src.aqi import pollutant_aqi

# PM2.5 AQI (micrograms/m³)
aqi_pm25, category_pm25 = pollutant_aqi(15.0, "PM2.5")
print(f"PM2.5: {aqi_pm25} ({category_pm25})")  # Output: PM2.5: 57 (Moderate)

# CO AQI (ppm)
aqi_co, category_co = pollutant_aqi(6.0, "CO")
print(f"CO: {aqi_co} ({category_co})")  # Output: CO: 66 (Moderate)

# MQ135 Custom Index
from src.aqi import mq135_pollution_index
aqi_mq135 = mq135_pollution_index(25.0)
print(f"MQ135: {aqi_mq135}")  # Output: MQ135: 80


# =============================================================================
# OPTION 2: Overall AQI from Dataset (Maximum Method)
# =============================================================================

from src.aqi import overall_aqi
import pandas as pd

# From a single row/dictionary
row = {
    "Estimated PM2.5": 15.0,    # µg/m³
    "CO PPM": 6.0,              # ppm
    "Air Quality PPM": 25.0     # MQ135 ppm
}

aqi_overall, primary = overall_aqi(row)
print(f"Overall AQI: {aqi_overall}, Primary Pollutant: {primary}")
# Output: Overall AQI: 80, Primary Pollutant: MQ135

# From a dataset (pandas Series or dict per row)
df = pd.read_csv("data/processed/air_quality_data.csv")
aqi_values = []
primary_pollutants = []

for _, row in df.iterrows():
    aqi, primary = overall_aqi(row)
    aqi_values.append(aqi)
    primary_pollutants.append(primary)

df["AQI"] = aqi_values
df["Primary Pollutant"] = primary_pollutants


# =============================================================================
# OPTION 3: Hardware Real-Time AQI (with Weather Adjustment)
# =============================================================================

from src.predictor import compute_aqi_from_sensors, SensorReading, WeatherData

# Create sensor reading from hardware input
sensor = SensorReading(
    mq135_adc=1299,           # MQ135 ADC value (0-4095)
    air_quality_ppm=1.27,     # MQ135 PPM (from calibration)
    mq7_adc=331,              # MQ7 ADC value
    co_ppm=0.23,              # CO in ppm
    dust_adc=737,             # Dust sensor ADC
    dust_voltage=0.59,        # Dust sensor voltage
    estimated_pm25=0.97,      # PM2.5 in µg/m³
    temperature=23.68,        # Temperature in °C
)

# Add weather data
weather = WeatherData(
    temperature=23.68,    # °C
    humidity=65.0,        # % RH
    wind_speed=3.5,       # m/s
    pressure=1013.0,      # hPa
)

# Calculate AQI with weather adjustment
aqi, contributions = compute_aqi_from_sensors(sensor, weather)

print(f"Final AQI: {aqi}")
print(f"Primary Pollutant: {contributions['primary_pollutant']}")
print(f"PM2.5: {contributions['PM2.5_value_ug_m3']} µg/m³ → AQI {contributions['PM2.5_aqi']}")
print(f"CO: {contributions['CO_value_ppm']} ppm → AQI {contributions['CO_aqi']}")
print(f"MQ135: {contributions['MQ135_value_ppm']} ppm → Index {contributions['MQ135_aqi']}")
print(f"Weather Adjustment: {contributions['weather_adjustment_factor']:.3f}x")


# =============================================================================
# OPTION 4: Training Dataset Generation with EPA AQI
# =============================================================================

# Already done in scripts/create_sensor_dataset.py
# Just run:
# python -m scripts.create_sensor_dataset

# Verify the generated dataset
import pandas as pd

df = pd.read_csv("data/processed/sensor_dataset_generated.csv")
print(f"Dataset shape: {df.shape}")
print(f"\nAQI Range: {df['AQI'].min()} - {df['AQI'].max()}")
print(f"Average AQI: {df['AQI'].mean():.1f}")
print(f"\nPrimary Pollutant Distribution:")
print(df['Primary Pollutant'].value_counts())


# =============================================================================
# OPTION 5: Training Models with EPA AQI Labels
# =============================================================================

from scripts.train_sensor_model import train_short_term_model

df = pd.read_csv("data/processed/sensor_dataset_generated.csv")

# Features include all sensor readings
feature_cols = [col for col in df.columns if col not in ["AQI", "Primary Pollutant"]]
target_col = "AQI"  # EPA-calculated values

print(f"Training with {len(feature_cols)} features")
print(f"Target: EPA-calculated {target_col}")

model = train_short_term_model(
    frame=df,
    feature_columns=feature_cols,
    target_column=target_col,
    model_path="models/hourly_model.keras",
    lookback=24,
    horizon=1,
    epochs=10,
    batch_size=32
)

print("✓ Model trained with EPA AQI labels")


# =============================================================================
# OPTION 6: Batch Processing Many Sensors
# =============================================================================

from src.aqi import overall_aqi
import pandas as pd
from typing import List, Tuple

def process_sensor_batch(readings: List[dict]) -> List[Tuple[int, str]]:
    """Process multiple sensor readings and return AQI values."""
    results = []
    for reading in readings:
        aqi, primary = overall_aqi(reading)
        results.append((aqi, primary))
    return results

# Example batch
readings = [
    {
        "Estimated PM2.5": 10.0,
        "CO PPM": 2.0,
        "Air Quality PPM": 15.0,
    },
    {
        "Estimated PM2.5": 50.0,
        "CO PPM": 8.0,
        "Air Quality PPM": 45.0,
    },
    {
        "Estimated PM2.5": 200.0,
        "CO PPM": 20.0,
        "Air Quality PPM": 150.0,
    },
]

results = process_sensor_batch(readings)
for i, (aqi, primary) in enumerate(results):
    print(f"Reading {i+1}: AQI = {aqi} (Primary: {primary})")


# =============================================================================
# OPTION 7: Forecast with EPA AQI (4-hour ahead)
# =============================================================================

from src.predictor import SensorReading, WeatherData, compute_aqi_from_sensors
from src.model_short_term import predict_short_term

# Current sensor reading
current_sensor = SensorReading(
    mq135_adc=1299,
    air_quality_ppm=1.27,
    mq7_adc=331,
    co_ppm=0.23,
    dust_adc=737,
    dust_voltage=0.59,
    estimated_pm25=0.97,
    temperature=23.68,
)

# Current weather
current_weather = WeatherData(
    temperature=23.68,
    humidity=65.0,
    wind_speed=3.5,
    pressure=1013.0,
)

# Calculate current AQI
current_aqi, _ = compute_aqi_from_sensors(current_sensor, current_weather)
print(f"Current AQI: {current_aqi}")

# Predict future AQI (4-hour forecast)
# Load trained model
import tensorflow as tf
model = tf.keras.models.load_model("models/hourly_model.keras")

# Prepare historical data (24-hour lookback window)
# ...prepare_historical_data...

# Make predictions
forecasts = predict_short_term(
    model=model,
    historical_data=prepared_data,
    forecast_hours=4,
)

print("\nAQI Forecast (Next 4 Hours):")
for hour, predicted_aqi in enumerate(forecasts, 1):
    print(f"  +{hour}h: AQI {int(predicted_aqi)}")


# =============================================================================
# OPTION 8: Health Advisories Based on EPA AQI
# =============================================================================

from src.predictor import get_aqi_category_name, get_advisory

aqi_value = 123

category = get_aqi_category_name(aqi_value)
advisory = get_advisory(aqi_value, forecast_hours=4)

print(f"AQI: {aqi_value}")
print(f"Category: {category}")
print(f"Advisory Level: {advisory['level']}")
print(f"Message: {advisory['message']}")
print(f"Recommendation: {advisory['recommendation']}")


# =============================================================================
# TESTING & VALIDATION
# =============================================================================

# Run comprehensive AQI formula tests
# python -m scripts.test_aqi_formulas_fixed

# Expected output: ✓ ALL TESTS PASSED!


# =============================================================================
# FORMULA REFERENCE
# =============================================================================

"""
EPA Standard Formula:
    AQI = ((I_hi - I_lo) / (C_hi - C_lo)) * (C - C_lo) + I_lo
    
    Where:
    - C = Pollutant concentration
    - C_lo, C_hi = Concentration breakpoints
    - I_lo, I_hi = AQI index breakpoints

PM2.5 Breakpoints (24-hour average, µg/m³):
    0.0-12.0        → AQI 0-50 (Good)
    12.1-35.4       → AQI 51-100 (Moderate)
    35.5-55.4       → AQI 101-150 (Unhealthy for Sensitive)
    55.5-150.4      → AQI 151-200 (Unhealthy)
    150.5-250.4     → AQI 201-300 (Very Unhealthy)
    250.5-350.4     → AQI 301-400 (Hazardous)
    350.5-500.4     → AQI 401-500 (Hazardous+)

CO Breakpoints (8-hour average, ppm):
    0.0-4.4         → AQI 0-50 (Good)
    4.5-9.4         → AQI 51-100 (Moderate)
    9.5-12.4        → AQI 101-150 (Unhealthy for Sensitive)
    12.5-15.4       → AQI 151-200 (Unhealthy)
    15.5-30.4       → AQI 201-300 (Very Unhealthy)
    30.5-40.4       → AQI 301-400 (Hazardous)
    40.5-50.4       → AQI 401-500 (Hazardous+)

MQ135 Custom Formula:
    AQI_MQ135 = (SafeLimit / MQ135_ppm) * 100
    SafeLimit = 20.0 ppm (baseline reference)
    Result capped at 500 (hazardous level)

Overall AQI:
    AQI_Overall = max(AQI_PM2.5, AQI_CO, AQI_MQ135)
"""
