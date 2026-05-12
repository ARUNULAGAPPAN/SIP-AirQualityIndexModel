# Air Quality Forecasting and Real-Time AQI Prediction

This project combines classic air-quality forecasting with a real-time AQI prediction pipeline for hardware sensor data. The application supports:

- Historical data upload and model training
- Hourly and daily forecast pages
- Real-time sensor-based AQI prediction
- Weather-aware AQI adjustment
- Hosted API usage for hardware-to-app integration

## What This Project Does

The system has two paths:

1. Historical forecasting path
     - Upload CSV data
     - Preprocess and train short-term and long-term models
     - View dashboard and generate forecasts

2. Real-time hardware path
     - Receive live readings from hardware sensors
     - Combine sensor values with weather and location context
     - Return AQI, forecast, primary pollutant, and health guidance
     - Expose the result through a hosted API

## Current Pages

- [app.py](app.py): Landing page and navigation hub
- [pages/01_dashboard.py](pages/01_dashboard.py): Data overview and status
- [pages/02_training.py](pages/02_training.py): Upload, preprocess, and train
- [pages/03_predictions.py](pages/03_predictions.py): Model-based forecasting
- [pages/05_real_time_predictions.py](pages/05_real_time_predictions.py): Real-time sensor AQI dashboard

## Real-Time Architecture

The real-time flow is now:

1. Hardware sends sensor readings and coordinates
2. The API fetches current weather for that location
3. The predictor computes AQI from all available attributes
4. The service returns AQI, forecast, and advisories
5. The Streamlit UI can display the same logic locally

### Inputs Used in the AQI Calculation

- MQ135 ADC
- Air Quality PPM
- MQ7 ADC
- CO PPM
- Dust ADC
- Dust Voltage
- Estimated PM2.5
- Temperature
- Latitude
- Longitude
- Weather Temperature
- Humidity
- Wind Speed
- Pressure

## AQI Logic

The prediction engine uses a weighted multi-feature AQI approach:

- Sensor readings are normalized to comparable ranges
- PM2.5 and CO drive the strongest pollutant signals
- Dust and MQ sensors add additional context
- Weather modifies dispersion and stagnation behavior
- Latitude and longitude are used as location context in the request and prediction response

The current code is in [src/predictor.py](src/predictor.py).

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the app at:

```text
http://localhost:8501
```

## Run the Hosted API Locally

The hosted API is implemented in [api.py](api.py).

```powershell
.venv\Scripts\Activate.ps1
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```text
GET http://localhost:8000/health
```

Prediction endpoint:

```text
POST http://localhost:8000/predict
```

## API Request Example

Send the hardware sensor payload plus the current coordinates:

```json
{
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
    "forecast_hours": 4
}
```

## API Response Example

The response contains:

- `current.aqi`: current AQI value
- `current.category`: AQI category
- `current.location`: latitude, longitude, location factor
- `current.sensor_contributions`: contribution breakdown by sensor
- `forecast`: 1 to 4 hour AQI forecast
- `peak_forecast`: highest forecasted AQI in the window
- `advisory`: message, recommendation, and avoid duration

Example shape:

```json
{
    "current": {
        "aqi": 103,
        "category": "Unhealthy for Sensitive Groups",
        "location": {
            "latitude": 23.0225,
            "longitude": 72.5714,
            "factor": 1.016
        }
    },
    "forecast": [
        {
            "hour_ahead": 1,
            "predicted_aqi": 106,
            "category": "Unhealthy for Sensitive Groups",
            "confidence": 85
        }
    ]
}
```

## How to Use the API From Hardware

1. Read values from your device sensors.
2. Read GPS coordinates from the module or app location.
3. Send a `POST` request to `/predict`.
4. Display the AQI and recommendation on the device, app, or alerting system.

Example Python client:

```python
import requests

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

response = requests.post("http://localhost:8000/predict", json=payload, timeout=10)
print(response.json())
```

You can also use the included client script:

```powershell
.venv\Scripts\python.exe scripts\hardware_client.py --base-url http://localhost:8000
```

Pass your own values when testing against a live device or a different location:

```powershell
.venv\Scripts\python.exe scripts\hardware_client.py --base-url https://your-host.example --latitude 23.0225 --longitude 72.5714
```

## How to Host It

### Option 1: Host the API on a VM or container

Use the FastAPI app from [api.py](api.py) and run it with Uvicorn.

Typical deployment command:

```powershell
uvicorn api:app --host 0.0.0.0 --port 8000
```

If you deploy to a cloud VM, expose port `8000` or place it behind Nginx / a cloud load balancer.

### Option 2: Host Streamlit separately

Use Streamlit for the dashboard UI:

```powershell
streamlit run app.py
```

For public hosting, put Streamlit and the API on separate services if you want independent scaling.

### Option 3: Single-host deployment

If you want one machine to do both jobs:

1. Run the API with Uvicorn on one port.
2. Run Streamlit on another port.
3. Let Streamlit call the API endpoint for live data.

## Deploy To Render

This repository now includes [render.yaml](render.yaml) so you can deploy the API and UI as two web services.

### What gets deployed

- `airquality-api`: FastAPI service for `POST /predict` and `GET /health`
- `airquality-ui`: Streamlit dashboard for manual viewing and real-time visualization

### Deploy steps

1. Push this repository to GitHub.
2. Create a new Render Blueprint from the repo root.
3. Render will detect [render.yaml](render.yaml).
4. Set `OPENWEATHER_API_KEY` in the API service environment if you want live weather.
5. Deploy both services.

### Service URLs

- API: `https://<your-api-service>.onrender.com`
- UI: `https://<your-ui-service>.onrender.com`

### Call the deployed API

Use the deployed API URL in your hardware client:

```powershell
.venv\Scripts\python.exe scripts\hardware_client.py --base-url https://<your-api-service>.onrender.com
```

Example raw request:

```bash
curl -X POST "https://<your-api-service>.onrender.com/predict" \
    -H "Content-Type: application/json" \
    -d '{"mq135_adc":1299,"air_quality_ppm":1.27,"mq7_adc":331,"co_ppm":0.23,"dust_adc":737,"dust_voltage":0.59,"estimated_pm25":0.97,"temperature":23.68,"latitude":23.0225,"longitude":72.5714,"forecast_hours":4}'
```

### Important note

The Streamlit UI and the API are intentionally separated so each can scale independently. The UI can still be used locally or deployed on its own, but the hardware integration should call the API service directly.

## Real Hardware Mode

The real-time page [pages/05_real_time_predictions.py](pages/05_real_time_predictions.py) is designed for this flow:

- Demo mode: uses sample sensor values
- Hardware mode: replace the demo payload with real sensor data from your hardware API
- Location is included through latitude and longitude

## Weather Integration

Weather is fetched in [src/weather_api.py](src/weather_api.py).

- If `OPENWEATHER_API_KEY` is set, the app can fetch weather from OpenWeatherMap
- If not, it falls back to mock weather values so the app still works

Set the API key like this:

```powershell
$env:OPENWEATHER_API_KEY = "your_api_key_here"
```

## Dataset Generator

The project includes a synthetic sensor dataset generator:

```powershell
$env:PYTHONPATH = '.'; .venv\Scripts\python.exe scripts\create_sensor_dataset.py
```

Output file:

- [data/processed/sensor_dataset_generated.csv](data/processed/sensor_dataset_generated.csv)

## Training Notes

The short-term model utilities are in [src/model_short_term.py](src/model_short_term.py).

Important note:

- TensorFlow is not available for Python 3.14 on this environment
- If you want to train the LSTM model, use Python 3.11 or 3.12

Suggested training flow:

1. Prepare a compatible Python environment
2. Install dependencies
3. Generate or load processed data
4. Train from the Training page or from a script

## Project Structure

```text
AirQuality_Forecasting/
├── app.py
├── api.py
├── config.py
├── README.md
├── requirements.txt
├── pages/
│   ├── 01_dashboard.py
│   ├── 02_training.py
│   ├── 03_predictions.py
│   └── 05_real_time_predictions.py
├── src/
│   ├── aqi.py
│   ├── predictor.py
│   ├── preprocess.py
│   ├── model_short_term.py
│   ├── model_long_term.py
│   └── weather_api.py
├── utils/
│   ├── data_handler.py
│   └── model_handler.py
├── scripts/
│   ├── create_sensor_dataset.py
│   └── train_sensor_model.py
├── data/
│   ├── raw/
│   └── processed/
└── models/
```

## Typical Workflow

1. Train with historical data if you want the classical forecasting pages.
2. Use the real-time page for sensor input plus weather-aware AQI.
3. Deploy [api.py](api.py) for hosted hardware-to-cloud communication.
4. Call the API from your device or front end.

## Troubleshooting

- If the API fails to start, make sure `fastapi`, `uvicorn`, and `requests` are installed.
- If Streamlit shows multiple page name conflicts, ensure page filenames are unique.
- If TensorFlow installation fails on Python 3.14, switch to Python 3.11 or 3.12 for model training.

## License

See the repository license if one is added later.
