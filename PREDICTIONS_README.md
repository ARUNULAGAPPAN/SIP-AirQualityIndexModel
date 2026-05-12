# Real-Time Air Quality Prediction System

## Overview

This system predicts air quality for the next **3–4 hours** using real-time sensor data, weather conditions, and health-based advisories.

### Key Components

- **`src/aqi.py`**: EPA-based AQI calculations for PM2.5 and CO
- **`src/predictor.py`**: 4-hour AQI forecasting + health advisories
- **`src/weather_api.py`**: OpenWeatherMap API integration (with mock fallback)
- **`pages/04_predictions.py`**: Streamlit UI for real-time predictions
- **`scripts/create_sensor_dataset.py`**: Generate synthetic sensor datasets
- **`data/processed/sensor_dataset_generated.csv`**: Pre-generated sensor data with AQI

---

## Sensor Data

### Hardware Sensors
- **MQ135**: Air quality sensor (ADC value)
- **MQ7**: Carbon monoxide sensor (ADC + PPM)
- **Dust Sensor**: Particulate matter detector (ADC + voltage)
- **Temperature Sensor**: Environmental temperature

### Output
- **AQI** (Air Quality Index): Overall air quality score (0–500)
- **PM2.5**: Fine particulate matter (µg/m³)
- **CO**: Carbon monoxide (ppm)

---

## AQI Calculation

### EPA Breakpoints

| Pollutant | Good | Moderate | Unhealthy | Unhealthy | Very | Hazardous |
|-----------|------|----------|-----------|-----------|------|-----------|
| PM2.5 (µg/m³) | 0–12 | 12–35 | 35–55 | 55–150 | 150–250 | 250–500 |
| CO (ppm) | 0–4.4 | 4.5–9.4 | 9.5–12 | 12–15 | 15–30 | 30–50 |

**Overall AQI**: Maximum of all pollutant AQIs (primary pollutant is the worst)

---

## Forecast Model

### Methodology (Current)

Mock heuristic forecast based on:
1. **Current AQI** from sensor + CO measurements
2. **Weather factors**:
   - Wind speed > 5 m/s → 5% AQI reduction (pollutant dispersion)
   - Temperature > 25°C → 2% AQI increase (thermal inversion)
3. **Confidence decay**: 90% at +1h → 70% at +4h

### For Production

Replace `mock_forecast_aqi()` in `src/predictor.py` with:
- Trained LSTM model using historical data
- Multi-pollutant forecasting
- Real weather API integration

---

## Health Advisories

### Advisory Levels

| AQI | Level | Health Impact | Recommendation | Avoid Duration |
|-----|-------|---------------|-----------------|-----------------|
| 0–50 | Good | No health effects | Enjoy outdoor activities | None |
| 51–100 | Moderate | Sensitive groups may be affected | Limit intense outdoor activity | None |
| 101–150 | Unhealthy (Sensitive) | Health effects in sensitive groups | Limit outdoor activity | None |
| 151–200 | Unhealthy | Everyone may experience effects | Reduce outdoor time | 3–4 hours |
| 201–300 | Very Unhealthy | Serious health effects | Avoid outdoor activities | 5+ hours |
| 301–500 | Hazardous | Emergency conditions | Stay indoors | 6+ hours |

---

## Usage

### 1. Streamlit UI (Interactive)

```bash
# Activate venv
.venv\Scripts\Activate.ps1

# Run Streamlit
streamlit run app.py
```

Navigate to **Pages → Real-time Predictions** and enter sensor data.

### 2. Python API (Programmatic)

```python
from src.predictor import SensorReading, WeatherData, generate_full_advisory

sensor = SensorReading(
    mq135_adc=1299,
    air_quality_ppm=1.27,
    mq7_adc=331,
    co_ppm=0.23,
    dust_adc=737,
    dust_voltage=0.59,
    estimated_pm25=0.97,
    temperature=23.68,
)

weather = WeatherData(
    temperature=23.68,
    humidity=65.0,
    wind_speed=3.5,
    pressure=1013.25,
)

advisory = generate_full_advisory(sensor, weather, forecast_hours=4)
print(advisory)
```

### 3. Generate Sensor Dataset

```bash
$env:PYTHONPATH = '.'; .venv\Scripts\python.exe scripts\create_sensor_dataset.py
```

Creates `data/processed/sensor_dataset_generated.csv` (500 rows)

---

## Weather API Integration

### Setup (Optional)

1. Get API key from [OpenWeatherMap](https://openweathermap.org/api)
2. Set environment variable:
   ```bash
   $env:OPENWEATHER_API_KEY = "your_api_key_here"
   ```

### Auto Fallback

If API unavailable, system uses mock weather data:
- Temperature: 23.68°C
- Humidity: 65%
- Wind Speed: 3.5 m/s
- Pressure: 1013.25 hPa

---

## Files Structure

```
project/
├── src/
│   ├── aqi.py                    # AQI calculations
│   ├── predictor.py              # Forecasting + advisories
│   ├── weather_api.py            # Weather integration
│   └── ...
├── pages/
│   ├── 04_predictions.py         # Streamlit UI for predictions
│   └── ...
├── scripts/
│   ├── create_sensor_dataset.py  # Dataset generator
│   └── train_sensor_model.py     # Training script (for TF 3.11–3.12)
├── data/processed/
│   └── sensor_dataset_generated.csv
└── ...
```

---

## Example Output

```json
{
  "current": {
    "aqi": 4,
    "category": "Good",
    "primary_pollutant": "PM2.5",
    "pm25": 0.97,
    "co_ppm": 0.23,
    "temperature": 23.68
  },
  "forecast": [
    {
      "hour_ahead": 1,
      "predicted_aqi": 4,
      "category": "Good",
      "confidence": 0.85
    },
    ...
  ],
  "advisory": {
    "level": "good",
    "message": "Air quality is good. Enjoy outdoor activities!",
    "recommendation": "No restrictions. All outdoor activities are safe.",
    "avoid_duration": null
  }
}
```

---

## Future Enhancements

- [ ] LSTM model training on larger historical datasets
- [ ] Multi-location forecasting
- [ ] Integration with official AirNow / AQI APIs
- [ ] Historical trend analysis
- [ ] Mobile app deployment
- [ ] Email/SMS alerts for high AQI thresholds
- [ ] Integration with Google Calendar for outdoor event planning

---

## License

See root `LICENSE` file.
