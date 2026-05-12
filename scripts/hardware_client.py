"""Example client for sending live hardware readings to the hosted AQI API.

Usage:
    .venv\\Scripts\\python.exe scripts\\hardware_client.py --base-url http://localhost:8000

You can also pass your own sensor readings and coordinates.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import requests


DEFAULT_PAYLOAD: dict[str, Any] = {
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Send hardware AQI readings to the hosted API.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Hosted API base URL")
    parser.add_argument("--latitude", type=float, default=DEFAULT_PAYLOAD["latitude"], help="Latitude")
    parser.add_argument("--longitude", type=float, default=DEFAULT_PAYLOAD["longitude"], help="Longitude")
    parser.add_argument("--forecast-hours", type=int, default=4, help="Forecast horizon")
    parser.add_argument("--mq135-adc", type=float, default=DEFAULT_PAYLOAD["mq135_adc"], help="MQ135 ADC")
    parser.add_argument("--air-quality-ppm", type=float, default=DEFAULT_PAYLOAD["air_quality_ppm"], help="Air quality ppm")
    parser.add_argument("--mq7-adc", type=float, default=DEFAULT_PAYLOAD["mq7_adc"], help="MQ7 ADC")
    parser.add_argument("--co-ppm", type=float, default=DEFAULT_PAYLOAD["co_ppm"], help="CO ppm")
    parser.add_argument("--dust-adc", type=float, default=DEFAULT_PAYLOAD["dust_adc"], help="Dust ADC")
    parser.add_argument("--dust-voltage", type=float, default=DEFAULT_PAYLOAD["dust_voltage"], help="Dust voltage")
    parser.add_argument("--estimated-pm25", type=float, default=DEFAULT_PAYLOAD["estimated_pm25"], help="Estimated PM2.5")
    parser.add_argument("--temperature", type=float, default=DEFAULT_PAYLOAD["temperature"], help="Temperature")
    return parser


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "mq135_adc": args.mq135_adc,
        "air_quality_ppm": args.air_quality_ppm,
        "mq7_adc": args.mq7_adc,
        "co_ppm": args.co_ppm,
        "dust_adc": args.dust_adc,
        "dust_voltage": args.dust_voltage,
        "estimated_pm25": args.estimated_pm25,
        "temperature": args.temperature,
        "latitude": args.latitude,
        "longitude": args.longitude,
        "forecast_hours": args.forecast_hours,
    }


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    payload = build_payload(args)

    try:
        response = requests.post(f"{args.base_url.rstrip('/')}/predict", json=payload, timeout=15)
        response.raise_for_status()
        data = response.json()
        print(json.dumps(data, indent=2))
    except requests.exceptions.ConnectionError:
        print(f"Could not connect to API at {args.base_url}. Start the server with: uvicorn api:app --reload --host 0.0.0.0 --port 8000")
    except requests.exceptions.HTTPError as exc:
        print(f"API returned an error: {exc}")
        if exc.response is not None:
            print(exc.response.text)


if __name__ == "__main__":
    main()