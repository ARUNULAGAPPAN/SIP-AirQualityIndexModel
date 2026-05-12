"""Data cleaning and feature engineering utilities."""

from __future__ import annotations

import pandas as pd
from pathlib import Path
from typing import Iterable


COLUMN_ALIASES = {
    "datetime": ["datetime", "date_time", "timestamp", "date", "time"],
    "PM2.5": ["PM2.5", "PM2.5_value", "pm2.5", "pm25", "PM25", "PM 2.5"],
    "PM10": ["PM10", "PM10_value", "pm 10"],
    "NO2": ["NO2", "NO2_value"],
    "CO": ["CO", "CO_value"],
    "Temp": ["Temp", "Temperature", "temp", "temperature", "temp_c", "temperature_c"],
    "Humidity": ["Humidity", "Hum", "humidity", "relative_humidity"],
}


DEFAULT_TARGET_COLUMN = "PM2.5"


def _normalize_column_name(column_name: str) -> str:
    return column_name.strip().lower().replace(" ", "").replace("_", "").replace(".", "")


def _canonicalize_columns(frame):
    lookup = {_normalize_column_name(column_name): column_name for column_name in frame.columns}
    rename_map: dict[str, str] = {}
    for canonical_name, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            actual = lookup.get(_normalize_column_name(alias))
            if actual:
                rename_map[actual] = canonical_name
                break
    return frame.rename(columns=rename_map)


def _resolve_requested_column(frame, requested_name: str) -> str | None:
    if requested_name in frame.columns:
        return requested_name

    normalized_lookup = {_normalize_column_name(column_name): column_name for column_name in frame.columns}
    return normalized_lookup.get(_normalize_column_name(requested_name))


def _find_datetime_column(frame: pd.DataFrame) -> str:
    candidates = COLUMN_ALIASES["datetime"]
    for column_name in candidates:
        if column_name in frame.columns:
            return column_name
    normalized_lookup = {_normalize_column_name(column_name): column_name for column_name in frame.columns}
    for candidate in candidates:
        actual = normalized_lookup.get(_normalize_column_name(candidate))
        if actual:
            return actual
    raise ValueError("No datetime column found. Expected one of: datetime, date_time, timestamp, date, time.")


def _infer_target_column(frame: pd.DataFrame, target_column: str | None) -> str:
    if target_column:
        resolved = _resolve_requested_column(frame, target_column)
        if resolved:
            return resolved

    candidate_names = COLUMN_ALIASES[DEFAULT_TARGET_COLUMN]
    for column_name in candidate_names:
        if column_name in frame.columns:
            return column_name

    normalized_lookup = {_normalize_column_name(column_name): column_name for column_name in frame.columns}
    for candidate in candidate_names:
        actual = normalized_lookup.get(_normalize_column_name(candidate))
        if actual:
            return actual
    
    raise ValueError(
        "No PM2.5 target column found. Provide target_column explicitly or include a PM2.5-like column."
    )


def _safe_numeric_columns(frame: pd.DataFrame, exclude: Iterable[str]) -> list[str]:
    excluded = set(exclude)
    return [
        column_name
        for column_name in frame.columns
        if column_name not in excluded and pd.api.types.is_numeric_dtype(frame[column_name])
    ]


def preprocess_data(
    input_path: str,
    output_path: str,
    *,
    target_column: str | None = None,
    lag_hours: tuple[int, ...] = (1, 2),
) -> pd.DataFrame:
    """Load raw air quality data, fill gaps, and add time-based features.

    The output is saved as CSV and also returned as a DataFrame.
    """

    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("pandas is required to preprocess data. Install requirements.txt first.") from exc

    source_path = Path(input_path)
    destination_path = Path(output_path)

    frame = pd.read_csv(source_path)
    frame = _canonicalize_columns(frame)
    datetime_column = _find_datetime_column(frame)
    target_column_name = _infer_target_column(frame, target_column)

    frame[datetime_column] = pd.to_datetime(frame[datetime_column], errors="coerce")
    frame = frame.sort_values(datetime_column).reset_index(drop=True)
    frame = frame.ffill()

    frame["Hour"] = frame[datetime_column].dt.hour
    frame["Day_of_Week"] = frame[datetime_column].dt.dayofweek
    frame["Month"] = frame[datetime_column].dt.month

    _safe_numeric_columns(frame, exclude=[datetime_column])
    for lag in lag_hours:
        frame[f"{target_column_name}_value_{lag}hr_ago"] = frame[target_column_name].shift(lag)

    frame = frame.dropna(subset=[target_column_name])
    frame = frame.dropna().reset_index(drop=True)

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(destination_path, index=False)
    return frame


def prepare_daily_frame(frame: pd.DataFrame, datetime_column: str | None = None) -> pd.DataFrame:
    """Aggregate an hourly frame into a daily average frame for long-term models."""

    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("pandas is required to aggregate daily data. Install requirements.txt first.") from exc

    if datetime_column is None:
        datetime_column = _find_datetime_column(frame)

    daily = frame.copy()
    daily = _canonicalize_columns(daily)
    if datetime_column is not None:
        resolved = _resolve_requested_column(daily, datetime_column)
        datetime_column = resolved or datetime_column
    datetime_column = _find_datetime_column(daily)
    daily[datetime_column] = pd.to_datetime(daily[datetime_column], errors="coerce")
    daily = daily.dropna(subset=[datetime_column])
    daily = daily.set_index(datetime_column).sort_index()
    daily = daily.resample("D").mean(numeric_only=True).reset_index()
    daily["Day_of_Week"] = daily[datetime_column].dt.dayofweek
    daily["Month"] = daily[datetime_column].dt.month
    return daily
