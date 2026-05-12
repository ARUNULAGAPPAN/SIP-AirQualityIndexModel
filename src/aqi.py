"""AQI calculation helpers for PM2.5 and CO using EPA breakpoints.

Functions:
- pollutant_aqi(conc, pollutant): returns (aqi, category_name)
- overall_aqi(row): accept dict/Series with keys 'Estimated PM2.5' (ug/m3) and 'CO PPM' and returns (aqi, primary_pollutant)

"""
from __future__ import annotations
from typing import Tuple

# Breakpoints: list of tuples (BP_lo, BP_hi, I_lo, I_hi)
# PM2.5 (24-hr) in micrograms/m3 (ug/m3) - EPA
PM25_BREAKPOINTS = [
    (0.0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 350.4, 301, 400),
    (350.5, 500.4, 401, 500),
]

# CO (8-hr) in ppm - EPA
CO_BREAKPOINTS = [
    (0.0, 4.4, 0, 50),
    (4.5, 9.4, 51, 100),
    (9.5, 12.4, 101, 150),
    (12.5, 15.4, 151, 200),
    (15.5, 30.4, 201, 300),
    (30.5, 40.4, 301, 400),
    (40.5, 50.4, 401, 500),
]

AQI_CATEGORIES = [
    (0, 50, "Good"),
    (51, 100, "Moderate"),
    (101, 150, "Unhealthy for Sensitive Groups"),
    (151, 200, "Unhealthy"),
    (201, 300, "Very Unhealthy"),
    (301, 500, "Hazardous"),
]


def _linear_interpolate(C: float, BP_lo: float, BP_hi: float, I_lo: int, I_hi: int) -> float:
    return (I_hi - I_lo) / (BP_hi - BP_lo) * (C - BP_lo) + I_lo


def _find_bp_and_compute(conc: float, breakpoints) -> float:
    for BP_lo, BP_hi, I_lo, I_hi in breakpoints:
        if BP_lo <= conc <= BP_hi:
            return _linear_interpolate(conc, BP_lo, BP_hi, I_lo, I_hi)
    # If concentration beyond defined breakpoints, cap to max index
    BP_lo, BP_hi, I_lo, I_hi = breakpoints[-1]
    return _linear_interpolate(min(conc, BP_hi), BP_lo, BP_hi, I_lo, I_hi)


def pollutant_aqi(conc: float, pollutant: str) -> Tuple[int, str]:
    """Compute AQI for a single pollutant.

    pollutant: 'PM2.5' or 'CO' (case-insensitive)
    Returns: (aqi_int, category_name)
    """
    if conc is None:
        return (0, "Unknown")
    p = pollutant.lower()
    if p in ("pm2.5", "pm25", "pm"):
        aqi = _find_bp_and_compute(float(conc), PM25_BREAKPOINTS)
    elif p == "co":
        aqi = _find_bp_and_compute(float(conc), CO_BREAKPOINTS)
    else:
        raise ValueError(f"Unsupported pollutant: {pollutant}")

    aqi_int = int(round(aqi))
    category = "Unknown"
    for lo, hi, name in AQI_CATEGORIES:
        if lo <= aqi_int <= hi:
            category = name
            break
    return aqi_int, category


def overall_aqi(row) -> Tuple[int, str]:
    """Given a mapping/Series with keys for PM2.5 and CO, compute overall AQI.

    Expected keys (case-sensitive as used in generator):
    - 'Estimated PM2.5' (ug/m3)
    - 'CO PPM' (ppm)

    Returns: (aqi_value, primary_pollutant)
    """
    pm25_key = "Estimated PM2.5"
    co_key = "CO PPM"

    pm25_conc = None
    co_conc = None
    if pm25_key in row:
        pm25_conc = row[pm25_key]
    if co_key in row:
        co_conc = row[co_key]

    scores = []
    if pm25_conc is not None:
        aqi_pm25, _ = pollutant_aqi(pm25_conc, "PM2.5")
        scores.append((aqi_pm25, "PM2.5"))
    if co_conc is not None:
        aqi_co, _ = pollutant_aqi(co_conc, "CO")
        scores.append((aqi_co, "CO"))

    if not scores:
        return (0, "Unknown")

    # Overall AQI is the maximum
    best = max(scores, key=lambda t: t[0])
    return best
