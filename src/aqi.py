"""AQI calculation helpers using EPA standard formulas.

This module implements:
1. PM2.5 AQI - EPA standard formula
2. CO AQI - EPA standard formula
3. MQ135 Custom Pollution Index - sensor-based formula
4. Overall AQI - maximum of all three pollutants

Functions:
- pollutant_aqi(conc, pollutant): returns (aqi, category_name)
- mq135_pollution_index(mq135_ppm, safe_limit=20.0): returns MQ135 AQI index
- overall_aqi(row): accept dict/Series with keys and returns (aqi, primary_pollutant)

Formulas:
EPA AQI Formula: AQI = ((I_hi - I_lo) / (C_hi - C_lo)) * (C - C_lo) + I_lo
Where:
  - C = pollutant concentration
  - C_lo, C_hi = concentration breakpoints
  - I_lo, I_hi = AQI index breakpoints

MQ135 Index: AQI_MQ135 = (SafeLimit / MQ135_ppm) * 100
"""
from __future__ import annotations
from typing import Tuple

# Breakpoints: list of tuples (BP_lo, BP_hi, I_lo, I_hi)
# PM2.5 (24-hr average) in micrograms/m3 (µg/m³) - EPA Standard
PM25_BREAKPOINTS = [
    (0.0, 12.0, 0, 50),      # Good
    (12.1, 35.4, 51, 100),   # Moderate
    (35.5, 55.4, 101, 150),  # Unhealthy for Sensitive Groups
    (55.5, 150.4, 151, 200), # Unhealthy
    (150.5, 250.4, 201, 300),# Very Unhealthy
    (250.5, 350.4, 301, 400),# Hazardous (1)
    (350.5, 500.4, 401, 500),# Hazardous (2)
]

# CO (8-hour average) in ppm - EPA Standard
CO_BREAKPOINTS = [
    (0.0, 4.4, 0, 50),       # Good
    (4.5, 9.4, 51, 100),     # Moderate
    (9.5, 12.4, 101, 150),   # Unhealthy for Sensitive Groups
    (12.5, 15.4, 151, 200),  # Unhealthy
    (15.5, 30.4, 201, 300),  # Very Unhealthy
    (30.5, 40.4, 301, 400),  # Hazardous (1)
    (40.5, 50.4, 401, 500),  # Hazardous (2)
]

AQI_CATEGORIES = [
    (0, 50, "Good"),
    (51, 100, "Moderate"),
    (101, 150, "Unhealthy for Sensitive Groups"),
    (151, 200, "Unhealthy"),
    (201, 300, "Very Unhealthy"),
    (301, 500, "Hazardous"),
]

# Safe limit for MQ135 in ppm (baseline reference)
MQ135_SAFE_LIMIT = 20.0


def _linear_interpolate(C: float, BP_lo: float, BP_hi: float, I_lo: int, I_hi: int) -> float:
    """EPA Standard AQI interpolation formula.
    
    AQI = ((I_hi - I_lo) / (C_hi - C_lo)) * (C - C_lo) + I_lo
    
    Args:
        C: Concentration of pollutant
        BP_lo: Lower concentration breakpoint
        BP_hi: Upper concentration breakpoint
        I_lo: Lower AQI index breakpoint
        I_hi: Upper AQI index breakpoint
    
    Returns:
        Interpolated AQI value
    """
    return (I_hi - I_lo) / (BP_hi - BP_lo) * (C - BP_lo) + I_lo


def _find_bp_and_compute(conc: float, breakpoints) -> float:
    """Find the correct breakpoint range and compute AQI.
    
    Args:
        conc: Pollutant concentration
        breakpoints: List of (BP_lo, BP_hi, I_lo, I_hi) tuples
    
    Returns:
        Computed AQI value
    """
    for BP_lo, BP_hi, I_lo, I_hi in breakpoints:
        if BP_lo <= conc <= BP_hi:
            return _linear_interpolate(conc, BP_lo, BP_hi, I_lo, I_hi)
    # If concentration beyond defined breakpoints, use the highest breakpoint
    BP_lo, BP_hi, I_lo, I_hi = breakpoints[-1]
    return _linear_interpolate(min(conc, BP_hi), BP_lo, BP_hi, I_lo, I_hi)




def pollutant_aqi(conc: float, pollutant: str) -> Tuple[int, str]:
    """Compute AQI for a single pollutant using EPA standard formula.

    Args:
        conc: Pollutant concentration
        pollutant: 'PM2.5', 'CO', or 'MQ135' (case-insensitive)
    
    Returns:
        (aqi_int, category_name)
    
    EPA Formula: AQI = ((I_hi - I_lo) / (C_hi - C_lo)) * (C - C_lo) + I_lo
    """
    if conc is None or conc < 0:
        return (0, "Unknown")
    
    p = pollutant.lower()
    
    if p in ("pm2.5", "pm25", "pm"):
        aqi = _find_bp_and_compute(float(conc), PM25_BREAKPOINTS)
    elif p == "co":
        aqi = _find_bp_and_compute(float(conc), CO_BREAKPOINTS)
    elif p == "mq135":
        aqi = mq135_pollution_index(float(conc))
    else:
        raise ValueError(f"Unsupported pollutant: {pollutant}")

    aqi_int = int(round(aqi))
    category = "Unknown"
    for lo, hi, name in AQI_CATEGORIES:
        if lo <= aqi_int <= hi:
            category = name
            break
    return aqi_int, category


def mq135_pollution_index(mq135_ppm: float, safe_limit: float = MQ135_SAFE_LIMIT) -> float:
    """Calculate MQ135 custom pollution index using sensor formula.
    
    MQ135 measures overall air quality based on VOCs and other pollutants.
    Formula: AQI_MQ135 = (SafeLimit / MQ135_ppm) * 100
    
    Args:
        mq135_ppm: MQ135 sensor reading in ppm
        safe_limit: Safe limit baseline (default 20.0 ppm)
    
    Returns:
        MQ135 pollution index (0-500+)
    
    Examples:
        - mq135_ppm = 20 (at safe limit) → index = 100
        - mq135_ppm = 10 (half of limit) → index = 200 (worse)
        - mq135_ppm = 40 (twice limit) → index = 50 (better)
    """
    if mq135_ppm is None or mq135_ppm < 0:
        return 0.0
    
    # Formula: (MQ135_ppm / 10) * 100, capped at 500
    # Scaling: 0 ppm → 0, 10 ppm → 100, 50+ ppm → 500
    index = (float(mq135_ppm) / 10.0) * 100
    
    return min(500, index)  # Cap at hazardous level


def overall_aqi(row) -> Tuple[int, str]:
    """Compute overall AQI from multiple pollutants using EPA formulas.

    Expected keys in row (case-sensitive):
    - 'Estimated PM2.5' (µg/m³) - EPA PM2.5 standard
    - 'CO PPM' (ppm) - EPA CO standard
    - 'Air Quality PPM' or 'air_quality_ppm' (ppm) - MQ135 sensor reading

    Overall AQI = max(AQI_PM2.5, AQI_CO, AQI_MQ135)

    Returns:
        (aqi_value, primary_pollutant)
        where aqi_value is 0-500+ and primary_pollutant is the pollutant causing highest AQI
    """
    pm25_key = "Estimated PM2.5"
    co_key = "CO PPM"
    mq135_key = None
    
    # Try multiple key variants for MQ135
    for key in ["Air Quality PPM", "air_quality_ppm", "MQ135 PPM", "mq135_ppm"]:
        if key in row:
            mq135_key = key
            break

    pm25_conc = None
    co_conc = None
    mq135_conc = None
    
    if pm25_key in row:
        pm25_conc = row[pm25_key]
    if co_key in row:
        co_conc = row[co_key]
    if mq135_key:
        mq135_conc = row[mq135_key]

    scores = []
    
    # Calculate PM2.5 AQI using EPA formula
    if pm25_conc is not None and pm25_conc > 0:
        aqi_pm25, _ = pollutant_aqi(pm25_conc, "PM2.5")
        scores.append((aqi_pm25, "PM2.5", pm25_conc))
    
    # Calculate CO AQI using EPA formula
    if co_conc is not None and co_conc > 0:
        aqi_co, _ = pollutant_aqi(co_conc, "CO")
        scores.append((aqi_co, "CO", co_conc))
    
    # Calculate MQ135 AQI using custom formula
    if mq135_conc is not None and mq135_conc > 0:
        aqi_mq135 = mq135_pollution_index(mq135_conc)
        scores.append((int(aqi_mq135), "MQ135", mq135_conc))

    if not scores:
        return (0, "Unknown")

    # Overall AQI is the maximum of all pollutant indices
    # This represents the worst air quality indicator
    best = max(scores, key=lambda t: t[0])
    return (best[0], best[1])
