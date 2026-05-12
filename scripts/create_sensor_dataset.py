"""Generate a sensor dataset CSV from a single sample reading.

Usage:
    python scripts/create_sensor_dataset.py

This creates `data/processed/sensor_dataset_generated.csv` with an `AQI` column computed
from `Estimated PM2.5` and `CO PPM` using `src/aqi.py`.
"""
from __future__ import annotations
import os
from pathlib import Path
import numpy as np
import pandas as pd

from src.aqi import overall_aqi

OUT_PATH = Path(__file__).parent.parent / "data" / "processed" / "sensor_dataset_generated.csv"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Base sample provided by user
base = {
    "MQ135 ADC": 1299,
    "Air Quality PPM": 1.27,
    "MQ7 ADC": 331,
    "CO PPM": 0.23,
    "Dust ADC": 737,
    "Dust Voltage": 0.59,
    "Estimated PM2.5": 0.97,  # ug/m3
    "Temperature": 23.68,
}

def synthesize_rows(base_row: dict, n: int = 1000, seed: int | None = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        factor = 1 + rng.normal(0, 0.02)
        row = {
            "MQ135 ADC": int(base_row["MQ135 ADC"] * rng.normal(1, 0.01)),
            "Air Quality PPM": round(base_row["Air Quality PPM"] * factor, 2),
            "MQ7 ADC": int(base_row["MQ7 ADC"] * rng.normal(1, 0.02)),
            "CO PPM": round(max(0.0, base_row["CO PPM"] * rng.normal(1, 0.02)), 3),
            "Dust ADC": int(base_row["Dust ADC"] * rng.normal(1, 0.02)),
            "Dust Voltage": round(max(0.0, base_row["Dust Voltage"] * rng.normal(1, 0.02)), 3),
            "Estimated PM2.5": round(max(0.0, base_row["Estimated PM2.5"] * rng.normal(1, 0.03)), 3),
            "Temperature": round(base_row["Temperature"] * rng.normal(1, 0.01), 2),
        }
        rows.append(row)
    df = pd.DataFrame(rows)

    # Compute AQI and primary pollutant
    aqi_vals = []
    primary = []
    for _, r in df.iterrows():
        aqi_val, pollutant = overall_aqi(r)
        aqi_vals.append(aqi_val)
        primary.append(pollutant)
    df["AQI"] = aqi_vals
    df["Primary Pollutant"] = primary
    return df

if __name__ == "__main__":
    df = synthesize_rows(base, n=500)
    df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(df)} rows to {OUT_PATH}")
