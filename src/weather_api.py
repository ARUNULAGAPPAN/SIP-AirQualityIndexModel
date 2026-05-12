"""Weather API integration (OpenWeatherMap with fallback mock)."""
from __future__ import annotations

from typing import Optional
import os

from src.predictor import WeatherData


def get_weather_from_api(
    latitude: float,
    longitude: float,
    api_key: Optional[str] = None,
) -> WeatherData:
    """Fetch current weather from OpenWeatherMap API.
    
    Args:
        latitude: Location latitude
        longitude: Location longitude
        api_key: OpenWeatherMap API key (or read from OPENWEATHER_API_KEY env var)
    
    Returns:
        WeatherData with current conditions
    
    Falls back to mock data if API key unavailable or request fails.
    """
    
    if not api_key:
        api_key = os.getenv("OPENWEATHER_API_KEY")
    
    if not api_key:
        return get_weather_mock()
    
    try:
        import requests
    except ImportError:
        return get_weather_mock()
    
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": api_key,
            "units": "metric",
        }
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        
        data = response.json()
        main = data.get("main", {})
        wind = data.get("wind", {})
        
        return WeatherData(
            temperature=float(main.get("temp", 20.0)),
            humidity=float(main.get("humidity", 60.0)),
            wind_speed=float(wind.get("speed", 3.0)),
            pressure=float(main.get("pressure", 1013.0)),
        )
    except Exception as e:
        print(f"Weather API error: {e}. Using mock data.")
        return get_weather_mock()


def get_weather_mock() -> WeatherData:
    """Return mock weather data for demo/fallback."""
    return WeatherData(
        temperature=23.68,
        humidity=65.0,
        wind_speed=3.5,
        pressure=1013.25,
    )
