"""Long-term daily forecasting model utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import pickle


@dataclass(slots=True)
class LongTermModelBundle:
    """Container for a long-term model and its training columns."""

    model: object
    feature_columns: list[str]
    target_column: str
    model_type: str


def _require_pandas() -> object:
    try:
        import pandas as pd
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("pandas is required for daily aggregation. Install requirements.txt first.") from exc
    return pd


def _require_prophet() -> object:
    try:
        from prophet import Prophet
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError("prophet is not installed. Use model_type='xgboost' or install requirements.txt.") from exc
    return Prophet


def _require_xgboost() -> object:
    try:
        from xgboost import XGBRegressor
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError("xgboost is not installed. Install requirements.txt first.") from exc
    return XGBRegressor


def build_long_term_model(model_type: str = "prophet") -> object:
    """Build a daily forecasting model using Prophet or XGBoost."""

    normalized = model_type.lower()
    if normalized == "prophet":
        Prophet = _require_prophet()
        return Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
    if normalized == "xgboost":
        XGBRegressor = _require_xgboost()
        return XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="reg:squarederror",
            random_state=42,
        )
    raise ValueError("model_type must be either 'prophet' or 'xgboost'.")


def prepare_daily_features(frame: pd.DataFrame, datetime_column: str = "datetime") -> pd.DataFrame:
    """Aggregate hourly air quality data into daily averages and calendar features."""

    pd = _require_pandas()

    daily_frame = frame.copy()
    daily_frame[datetime_column] = pd.to_datetime(daily_frame[datetime_column], errors="coerce")
    daily_frame = daily_frame.dropna(subset=[datetime_column])
    daily_frame = daily_frame.set_index(datetime_column).sort_index()
    daily_frame = daily_frame.resample("D").mean(numeric_only=True).reset_index()
    daily_frame["Day_of_Week"] = daily_frame[datetime_column].dt.dayofweek
    daily_frame["Month"] = daily_frame[datetime_column].dt.month
    return daily_frame


def train_long_term_model(
    frame: pd.DataFrame,
    target_column: str,
    model_path: str,
    model_type: str = "prophet",
) -> LongTermModelBundle:
    """Train and persist a daily forecasting model."""

    pd = _require_pandas()

    daily_frame = frame.copy()
    daily_frame["datetime"] = pd.to_datetime(daily_frame["datetime"], errors="coerce")
    daily_frame = daily_frame.dropna(subset=["datetime", target_column])
    daily_frame = daily_frame.sort_values("datetime")

    model = build_long_term_model(model_type=model_type)
    normalized = model_type.lower()

    feature_columns: list[str] = []
    if normalized == "prophet":
        training_frame = daily_frame[["datetime", target_column]].rename(columns={"datetime": "ds", target_column: "y"})
        model.fit(training_frame)
    else:
        training_frame = prepare_daily_features(daily_frame, datetime_column="datetime")
        feature_columns = [column_name for column_name in training_frame.columns if column_name not in {"datetime", target_column}]
        model.fit(training_frame[feature_columns], training_frame[target_column])

    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    with open(model_path, "wb") as file_handle:
        pickle.dump(model, file_handle)

    return LongTermModelBundle(
        model=model,
        feature_columns=feature_columns,
        target_column=target_column,
        model_type=normalized,
    )
