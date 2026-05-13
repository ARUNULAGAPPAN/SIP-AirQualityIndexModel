# Air Quality Index (AQI) - EPA Standard Formulas

This document details the EPA standard formulas implemented for calculating AQI values in the Air Quality Forecasting project.

## Overview

The project uses three complementary formulas to calculate overall air quality:
1. **PM2.5 AQI** - EPA standard formula (official measurement)
2. **CO AQI** - EPA standard formula (official measurement)  
3. **MQ135 Pollution Index** - Custom sensor-based formula (supporting indicator)

**Final AQI = max(AQI_PM2.5, AQI_CO, AQI_MQ135)**

The final AQI is the maximum of all three indices, representing the worst air quality indicator.

---

## 1. EPA Standard AQI Formula

All EPA pollutant AQI calculations use this linear interpolation formula:

$$AQI = \frac{I_{hi} - I_{lo}}{C_{hi} - C_{lo}} \times (C - C_{lo}) + I_{lo}$$

Where:
- **C** = Pollutant concentration (in specified units)
- **C_lo, C_hi** = Concentration breakpoints (lower and upper)
- **I_lo, I_hi** = AQI index breakpoints (always 0-50, 51-100, etc.)

### Key Concept
The formula maps a pollutant's concentration into the standardized EPA AQI scale (0-500).

---

## 2. PM2.5 AQI Calculation

### EPA Breakpoints for PM2.5 (24-hour average)

| Concentration (µg/m³) | AQI Range | Category |
|---|---|---|
| 0.0 - 12.0 | 0 - 50 | Good |
| 12.1 - 35.4 | 51 - 100 | Moderate |
| 35.5 - 55.4 | 101 - 150 | Unhealthy for Sensitive Groups |
| 55.5 - 150.4 | 151 - 200 | Unhealthy |
| 150.5 - 250.4 | 201 - 300 | Very Unhealthy |
| 250.5 - 350.4 | 301 - 400 | Hazardous |
| 350.5 - 500.4 | 401 - 500 | Hazardous+ |

### Example Calculation

**Given:** PM2.5 = 15.0 µg/m³

1. Find breakpoint: C = 15.0 falls in range [12.1 - 35.4]
   - C_lo = 12.1, C_hi = 35.4
   - I_lo = 51, I_hi = 100

2. Apply formula:
$$AQI = \frac{100 - 51}{35.4 - 12.1} \times (15.0 - 12.1) + 51$$
$$AQI = \frac{49}{23.3} \times 2.9 + 51$$
$$AQI = 2.1 \times 2.9 + 51 = 6.1 + 51 = 57.1 \approx 57$$

**Result:** AQI = 57 (Moderate)

---

## 3. CO AQI Calculation

### EPA Breakpoints for CO (8-hour average)

| Concentration (ppm) | AQI Range | Category |
|---|---|---|
| 0.0 - 4.4 | 0 - 50 | Good |
| 4.5 - 9.4 | 51 - 100 | Moderate |
| 9.5 - 12.4 | 101 - 150 | Unhealthy for Sensitive Groups |
| 12.5 - 15.4 | 151 - 200 | Unhealthy |
| 15.5 - 30.4 | 201 - 300 | Very Unhealthy |
| 30.5 - 40.4 | 301 - 400 | Hazardous |
| 40.5 - 50.4 | 401 - 500 | Hazardous+ |

### Example Calculation

**Given:** CO = 6.0 ppm

1. Find breakpoint: C = 6.0 falls in range [4.5 - 9.4]
   - C_lo = 4.5, C_hi = 9.4
   - I_lo = 51, I_hi = 100

2. Apply formula:
$$AQI = \frac{100 - 51}{9.4 - 4.5} \times (6.0 - 4.5) + 51$$
$$AQI = \frac{49}{4.9} \times 1.5 + 51$$
$$AQI = 10.0 \times 1.5 + 51 = 15.0 + 51 = 66$$

**Result:** AQI = 66 (Moderate)

---

## 4. MQ135 Custom Pollution Index Formula

The MQ135 sensor detects various air pollutants (VOCs, CO₂, NH₃, alcohol, etc.). Since there is no official EPA breakpoint for combined VOC measurements, we use a custom formula:

$$AQI_{MQ135} = \frac{SafeLimit}{MQ135_{ppm}} \times 100$$

Where:
- **SafeLimit** = 20.0 ppm (baseline safe air quality threshold)
- **MQ135_ppm** = MQ135 sensor reading in ppm
- **Result:** Capped at 500 (hazardous level)

### Interpretation

- **AQI_MQ135 = 100**: Air quality at safe limit
- **AQI_MQ135 < 100**: Better air quality (ppm below safe limit)
- **AQI_MQ135 > 100**: Worse air quality (ppm exceeds safe limit)
- **AQI_MQ135 > 200**: Air quality at or above unsafe level

### Example Calculations

**Case 1: Excellent conditions**
- MQ135 = 10 ppm
- AQI = (20 / 10) × 100 = **200**
- Interpretation: Exceeds safe limit, approaching unhealthy

**Case 2: At safe limit**
- MQ135 = 20 ppm
- AQI = (20 / 20) × 100 = **100**
- Interpretation: Moderate air quality

**Case 3: Below safe limit**
- MQ135 = 30 ppm
- AQI = (20 / 30) × 100 = **67**
- Interpretation: Good air quality

**Case 4: Poor conditions**
- MQ135 = 5 ppm
- AQI = (20 / 5) × 100 = **400**
- Interpretation: Hazardous air quality

---

## 5. Overall AQI Calculation

### Method: Maximum of All Pollutants

The overall AQI is computed as:

$$AQI_{Overall} = \max(AQI_{PM2.5}, AQI_{CO}, AQI_{MQ135})$$

The primary pollutant is identified as the one contributing the highest AQI value.

### Example

Given sensor reading:
- PM2.5 = 15.0 µg/m³ → AQI_PM2.5 = 57 (Moderate)
- CO = 6.0 ppm → AQI_CO = 66 (Moderate)
- MQ135 = 25 ppm → AQI_MQ135 = 80 (Moderate)

**Overall AQI = max(57, 66, 80) = 80**
**Primary Pollutant = CO** (caused highest AQI)

---

## 6. Weather Adjustment Factor

After computing the EPA AQI values, a weather adjustment factor is applied to account for meteorological conditions:

$$AQI_{adjusted} = AQI_{Overall} \times WeatherFactor$$

### Weather Adjustments

| Condition | Adjustment | Effect |
|---|---|---|
| Wind speed > 5 m/s | × 0.95 | Wind helps disperse pollutants (-5%) |
| Humidity > 80% or < 20% | × 1.05 | Extreme humidity traps pollutants (+5%) |
| Pressure < 1000 hPa | × 1.08 | Low pressure traps pollutants (+8%) |
| Temperature > 35°C | × 1.05 | Heat amplifies pollution (+5%) |
| Temperature < 5°C | × 1.03 | Cold can trap pollutants (+3%) |

**Example:**
- Base EPA AQI = 80
- Wind = 3 m/s, Humidity = 75%, Pressure = 1010 hPa, Temp = 28°C
- WeatherFactor = 1.0 (no adjustments apply)
- **Adjusted AQI = 80 × 1.0 = 80**

---

## 7. AQI Categories

All AQI values map to health categories:

| AQI Range | Category | Health Impact |
|---|---|---|
| 0 - 50 | Good | No health concerns |
| 51 - 100 | Moderate | Sensitive groups may experience effects |
| 101 - 150 | Unhealthy for Sensitive Groups | Sensitive groups should limit outdoor exposure |
| 151 - 200 | Unhealthy | General population may experience effects |
| 201 - 300 | Very Unhealthy | Everyone should limit outdoor exposure |
| 301 - 500 | Hazardous | Everyone should avoid outdoor exposure |

---

## 8. Implementation in Code

### Python Functions

```python
# Calculate individual pollutant AQI
from src.aqi import pollutant_aqi, mq135_pollution_index

# PM2.5 AQI (EPA formula)
aqi_pm25, category = pollutant_aqi(15.0, "PM2.5")  # Returns (57, "Moderate")

# CO AQI (EPA formula)
aqi_co, category = pollutant_aqi(6.0, "CO")  # Returns (66, "Moderate")

# MQ135 Custom Index
aqi_mq135 = mq135_pollution_index(25.0)  # Returns 80

# Overall AQI (maximum)
from src.aqi import overall_aqi
aqi_overall, primary_pollutant = overall_aqi({
    "Estimated PM2.5": 15.0,
    "CO PPM": 6.0,
    "Air Quality PPM": 25.0
})
# Returns (80, "MQ135")
```

### Hardware Real-Time Prediction

```python
from src.predictor import compute_aqi_from_sensors, SensorReading, WeatherData

sensor = SensorReading(
    mq135_adc=1299,
    air_quality_ppm=1.27,
    mq7_adc=331,
    co_ppm=0.23,
    dust_adc=737,
    dust_voltage=0.59,
    estimated_pm25=0.97,
    temperature=23.68
)

weather = WeatherData(
    temperature=23.68,
    humidity=65.0,
    wind_speed=3.5,
    pressure=1013.0
)

aqi_value, contributions = compute_aqi_from_sensors(sensor, weather)
print(f"AQI: {aqi_value}")
print(f"Primary Pollutant: {contributions['primary_pollutant']}")
```

---

## 9. Training & Dataset Generation

During dataset generation and model training:

1. **Raw sensor data** is loaded or synthesized
2. **EPA AQI formulas** are applied to compute ground truth AQI values
3. **Dataset** includes computed AQI labels for supervised learning
4. **Model** learns to predict future AQI based on historical patterns

```python
from scripts.create_sensor_dataset import synthesize_rows

# Generates synthetic sensor data with calculated EPA AQI values
df = synthesize_rows(base_reading, n=1000)
# df["AQI"] contains EPA-calculated values
# df["Primary Pollutant"] identifies the dominant pollutant
```

---

## References

- [EPA AQI Technical Assistance Document](https://www.airnow.gov/sites/default/files/2020-05/aqi-technical-assistance-document-sept2018.pdf)
- [EPA Air Quality Index](https://www.airnow.gov/)
- [MQ135 Datasheet](https://datasheetspdf.com/pdf/1217815/Henan/MQ-135/1)

---

## Verification

To verify the AQI calculations:

```bash
python scripts/test_aqi_formulas.py
```

This will test all three formulas against known EPA examples and sensor readings.
