"""Real-time predictions: sensor data + weather + 3-4 hour AQI forecast with advisories.

Uses multi-feature AQI correlation:
- All 8 hardware sensor readings (MQ135, MQ7, Dust, Temperature)
- Weather conditions (Temperature, Humidity, Wind, Pressure)
- Weighted combination for robust AQI calculation
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple
import json

from src.aqi import AQI_CATEGORIES


@dataclass(slots=True)
class SensorReading:
    """All 8 hardware sensor measurements."""
    mq135_adc: float          # Air quality sensor ADC
    air_quality_ppm: float    # Air quality PPM
    mq7_adc: float            # CO sensor ADC
    co_ppm: float             # CO concentration (ppm)
    dust_adc: float           # Dust sensor ADC
    dust_voltage: float       # Dust sensor voltage
    estimated_pm25: float     # PM2.5 (µg/m³)
    temperature: float        # Temperature (°C)


@dataclass(slots=True)
class WeatherData:
    """Weather conditions affecting pollutant dispersion."""
    temperature: float        # Temperature (°C)
    humidity: float           # Relative humidity (%)
    wind_speed: float         # Wind speed (m/s)
    pressure: float           # Atmospheric pressure (hPa)


@dataclass(slots=True)
class LocationContext:
    """Geographic context for the prediction request."""
    latitude: float
    longitude: float


@dataclass(slots=True)
class AQIForecast:
    """3-4 hour AQI forecast for a single hour ahead."""
    hour_ahead: int
    predicted_aqi: int
    aqi_category: str
    confidence: float


def _location_factor(location: Optional[LocationContext]) -> float:
    """Convert location context into a small stabilizing factor.

    Latitude and longitude are not direct air-quality inputs, so we keep the
    adjustment modest and use them only as location context.
    """

    if location is None:
        return 1.0

    lat_component = abs(location.latitude) / 90.0 * 0.03
    lon_component = abs(location.longitude) / 180.0 * 0.02
    return min(1.08, 1.0 + lat_component + lon_component)


def compute_aqi_from_sensors(
    sensor: SensorReading,
    weather: WeatherData,
    location: Optional[LocationContext] = None,
) -> Tuple[int, dict]:
    """Compute AQI using all 8 sensor attributes + weather (multi-feature correlation).
    
    Returns:
        (aqi_value, sensor_contributions) where contributions show which sensors influenced AQI most
    """
    
    # Normalize sensor readings to 0-100 scale
    # ADC values typically 0-4095; PPM 0-10+; voltage 0-5V
    
    # MQ135: Air quality (maps to AQI-like scale)
    mq135_normalized = min(100, (sensor.mq135_adc / 4095) * 150)
    
    # Air Quality PPM: Direct pollution indicator
    aq_ppm_normalized = min(100, sensor.air_quality_ppm * 30)
    
    # MQ7/CO: Carbon monoxide (0-10 ppm typical)
    co_normalized = min(100, (sensor.co_ppm / 10) * 100)
    
    # Dust sensor: Particulate matter
    dust_normalized = min(100, (sensor.dust_adc / 4095) * 120)
    dust_voltage_normalized = min(100, (sensor.dust_voltage / 5) * 100)
    
    # PM2.5: Direct particulate (0-35 is "good", >250 is hazardous)
    pm25_normalized = min(100, (sensor.estimated_pm25 / 35) * 50)
    
    # Temperature effect: Heat can worsen air stagnation (affects pollutant concentration)
    # Optimal ~20°C; worse at extremes
    temp_effect = 1.0
    if sensor.temperature > 30:
        temp_effect = 1.1 + (sensor.temperature - 30) * 0.02
    elif sensor.temperature < 10:
        temp_effect = 1.05 + (10 - sensor.temperature) * 0.01
    
    # Weather mitigating factors
    # Wind speed: >5 m/s helps dispersion (reduces AQI effect by 10%)
    wind_mitigation = 0.9 if weather.wind_speed > 5 else 1.0
    
    # Humidity: Very high (>80%) or very low (<20%) can worsen readings
    humidity_factor = 1.0
    if weather.humidity > 80 or weather.humidity < 20:
        humidity_factor = 1.05
    
    # Atmospheric pressure: Low pressure (bad weather) can trap pollutants
    pressure_factor = 1.0
    if weather.pressure < 1000:
        pressure_factor = 1.08

    location_factor = _location_factor(location)
    
    # Weighted AQI calculation
    weights = {
        "mq135": 0.20,
        "aq_ppm": 0.15,
        "co": 0.25,
        "dust_adc": 0.15,
        "dust_voltage": 0.10,
        "pm25": 0.15,
    }
    
    base_aqi = (
        weights["mq135"] * mq135_normalized +
        weights["aq_ppm"] * aq_ppm_normalized +
        weights["co"] * co_normalized +
        weights["dust_adc"] * dust_normalized +
        weights["dust_voltage"] * dust_voltage_normalized +
        weights["pm25"] * pm25_normalized
    )
    
    # Apply weather and temperature factors
    adjusted_aqi = base_aqi * temp_effect * wind_mitigation * humidity_factor * pressure_factor * location_factor
    
    # Scale to EPA AQI range (0-500+)
    final_aqi = int(max(0, min(500, adjusted_aqi * 5)))
    
    contributions = {
        "mq135": round(mq135_normalized * weights["mq135"], 1),
        "air_quality_ppm": round(aq_ppm_normalized * weights["aq_ppm"], 1),
        "co": round(co_normalized * weights["co"], 1),
        "dust_adc": round(dust_normalized * weights["dust_adc"], 1),
        "dust_voltage": round(dust_voltage_normalized * weights["dust_voltage"], 1),
        "pm25": round(pm25_normalized * weights["pm25"], 1),
        "location": round((location_factor - 1.0) * 100, 1),
    }
    
    return final_aqi, contributions


def get_aqi_category_name(aqi_value: int) -> str:
    """Map AQI value to health category."""
    for lo, hi, name in AQI_CATEGORIES:
        if lo <= aqi_value <= hi:
            return name
    return "Hazardous"


def get_advisory(aqi_value: int, forecast_hours: int) -> dict:
    """Generate health advisory based on AQI."""
    
    if aqi_value <= 50:
        return {
            "level": "good",
            "emoji": "✅",
            "message": "Air quality is Good",
            "recommendation": "No restrictions. All outdoor activities are safe.",
            "avoid_duration": None,
        }
    elif aqi_value <= 100:
        return {
            "level": "moderate",
            "emoji": "ℹ️",
            "message": "Air quality is Moderate",
            "recommendation": "Sensitive groups should consider limiting intense outdoor activities.",
            "avoid_duration": None,
        }
    elif aqi_value <= 150:
        return {
            "level": "unhealthy_sensitive",
            "emoji": "⚠️",
            "message": "Unhealthy for Sensitive Groups",
            "recommendation": "Sensitive individuals should limit outdoor activities.",
            "avoid_duration": None,
        }
    elif aqi_value <= 200:
        return {
            "level": "unhealthy",
            "emoji": "⚠️⚠️",
            "message": "Unhealthy Air Quality",
            "recommendation": "Everyone should limit outdoor activities. Use N95 masks if outside.",
            "avoid_duration": forecast_hours,
        }
    elif aqi_value <= 300:
        return {
            "level": "very_unhealthy",
            "emoji": "🚫",
            "message": "Very Unhealthy Air Quality",
            "recommendation": "Avoid outdoor activities. Remain indoors with air filtration.",
            "avoid_duration": forecast_hours + 1,
        }
    else:
        return {
            "level": "hazardous",
            "emoji": "🚨",
            "message": "Hazardous Air Quality",
            "recommendation": "Stay indoors. Keep windows closed. Use air purifiers.",
            "avoid_duration": forecast_hours + 2,
        }


def forecast_aqi(
    current_sensor: SensorReading,
    weather: WeatherData,
    location: Optional[LocationContext] = None,
    hours_ahead: int = 4,
) -> list[AQIForecast]:
    """Generate 3-4 hour AQI forecast using weather trends."""
    
    forecasts = []
    
    # Current AQI
    current_aqi, _ = compute_aqi_from_sensors(current_sensor, weather, location=location)
    
    # Weather-based trend factors
    wind_factor = 0.95 if weather.wind_speed > 5 else 1.05
    temp_factor = 1.02 if weather.temperature > 25 else 0.98
    location_factor = _location_factor(location)
    
    for h in range(1, hours_ahead + 1):
        # Simple exponential decay/growth based on weather
        trend_factor = (wind_factor * temp_factor * location_factor) ** h
        projected_aqi = int(max(0, current_aqi * trend_factor))
        
        confidence = 0.90 - (h * 0.05)
        
        forecasts.append(AQIForecast(
            hour_ahead=h,
            predicted_aqi=projected_aqi,
            aqi_category=get_aqi_category_name(projected_aqi),
            confidence=max(0.5, confidence),
        ))
    
    return forecasts


def generate_full_advisory(
    current_sensor: SensorReading,
    weather: WeatherData,
    location: Optional[LocationContext] = None,
    forecast_hours: int = 4,
) -> dict:
    """Generate complete real-time advisory from hardware sensor data."""
    
    # Compute current AQI from all sensor attributes
    current_aqi, contributions = compute_aqi_from_sensors(current_sensor, weather, location=location)
    current_category = get_aqi_category_name(current_aqi)
    
    # Get forecast
    forecasts = forecast_aqi(current_sensor, weather, location=location, hours_ahead=forecast_hours)
    peak_forecast = max(forecasts, key=lambda f: f.predicted_aqi)
    
    # Get advisory based on peak
    advisory = get_advisory(peak_forecast.predicted_aqi, forecast_hours)
    
    return {
        "current": {
            "aqi": current_aqi,
            "category": current_category,
            "sensor_contributions": contributions,
            "location": {
                "latitude": round(location.latitude, 5) if location else None,
                "longitude": round(location.longitude, 5) if location else None,
                "factor": round(_location_factor(location), 3),
            },
            "sensors": {
                "mq135_adc": round(current_sensor.mq135_adc, 0),
                "air_quality_ppm": round(current_sensor.air_quality_ppm, 2),
                "mq7_adc": round(current_sensor.mq7_adc, 0),
                "co_ppm": round(current_sensor.co_ppm, 3),
                "dust_adc": round(current_sensor.dust_adc, 0),
                "dust_voltage": round(current_sensor.dust_voltage, 2),
                "pm25": round(current_sensor.estimated_pm25, 2),
                "temperature": round(current_sensor.temperature, 1),
            },
            "weather": {
                "temperature": round(weather.temperature, 1),
                "humidity": round(weather.humidity, 0),
                "wind_speed": round(weather.wind_speed, 1),
                "pressure": round(weather.pressure, 0),
            },
        },
        "forecast": [
            {
                "hour_ahead": f.hour_ahead,
                "predicted_aqi": f.predicted_aqi,
                "category": f.aqi_category,
                "confidence": round(f.confidence * 100, 0),
            }
            for f in forecasts
        ],
        "peak_forecast": {
            "hour_ahead": peak_forecast.hour_ahead,
            "aqi": peak_forecast.predicted_aqi,
            "category": peak_forecast.aqi_category,
        },
        "advisory": advisory,
    }


# Example usage
if __name__ == "__main__":
    # Sample sensor reading
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
    
    # Sample weather
    weather = WeatherData(
        temperature=23.68,
        humidity=65.0,
        wind_speed=3.5,
        pressure=1013.25,
    )
    
    location = LocationContext(latitude=23.0225, longitude=72.5714)

    result = generate_full_advisory(sensor, weather, location=location, forecast_hours=4)
    print(json.dumps(result, indent=2))
