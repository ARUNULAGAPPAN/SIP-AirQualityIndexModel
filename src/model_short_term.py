"""Short-term hourly forecasting model utilities."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class ShortTermDataset:
    """Container for scaled training arrays."""

    x_train: Any
    y_train: Any
    x_test: Any
    y_test: Any
    scaler: Any


def _require_numpy() -> object:
    try:
        return import_module("numpy")
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("numpy is required for sequence creation. Install requirements.txt first.") from exc


def _require_sklearn_scaler() -> object:
    try:
        sklearn_preprocessing = import_module("sklearn.preprocessing")
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("scikit-learn is required for scaling. Install requirements.txt first.") from exc
    return sklearn_preprocessing.MinMaxScaler


def _require_keras() -> object:
    try:
        tensorflow_module = import_module("tensorflow")
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("TensorFlow is required for the LSTM model. Install requirements.txt first.") from exc
    return tensorflow_module.keras


def create_sequences(
    series: Any,
    lookback: int = 24,
    horizon: int = 1,
) -> tuple[Any, Any]:
    """Convert a 2D feature array into LSTM sequences."""

    np = _require_numpy()

    x_values: list[Any] = []
    y_values: list[Any] = []

    for index in range(lookback, len(series) - horizon + 1):
        x_values.append(series[index - lookback : index])
        y_values.append(series[index : index + horizon, 0])

    return np.asarray(x_values), np.asarray(y_values)


def build_short_term_model(
    lookback: int = 24,
    feature_count: int = 4,
    horizon: int = 1,
) -> Any:
    """Build an LSTM for 1-6 hour ahead forecasting."""

    keras = _require_keras()

    model = keras.Sequential(
        [
            keras.layers.Input(shape=(lookback, feature_count)),
            keras.layers.LSTM(64, return_sequences=True),
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(32),
            keras.layers.Dense(32, activation="relu"),
            keras.layers.Dense(horizon),
        ]
    )
    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    return model


def prepare_short_term_dataset(
    frame,
    feature_columns: list[str],
    target_column: str,
    lookback: int = 24,
    horizon: int = 1,
    train_split: float = 0.8,
) -> ShortTermDataset:
    """Scale the data and create lookback sequences for training."""

    np = _require_numpy()
    MinMaxScaler = _require_sklearn_scaler()

    ordered_columns = [target_column] + [column_name for column_name in feature_columns if column_name != target_column]
    values = frame[ordered_columns].astype(float).to_numpy()
    scaler = MinMaxScaler()
    scaled_values = scaler.fit_transform(values)
    x_values, y_values = create_sequences(scaled_values, lookback=lookback, horizon=horizon)

    split_index = max(int(len(x_values) * train_split), 1)
    return ShortTermDataset(
        x_train=x_values[:split_index],
        y_train=y_values[:split_index],
        x_test=x_values[split_index:],
        y_test=y_values[split_index:],
        scaler=scaler,
    )


def train_short_term_model(
    frame,
    feature_columns: list[str],
    target_column: str,
    model_path: str,
    lookback: int = 24,
    horizon: int = 1,
    epochs: int = 6,
    batch_size: int = 32,
) -> Any:
    """Train the hourly LSTM and save it to disk."""

    keras = _require_keras()

    ordered_columns = [target_column] + [column_name for column_name in feature_columns if column_name != target_column]
    dataset = prepare_short_term_dataset(
        frame,
        feature_columns=feature_columns,
        target_column=target_column,
        lookback=lookback,
        horizon=horizon,
    )
    # Ensure training arrays are proper numpy arrays with correct ranks.
    np = _require_numpy()
    x_train = np.asarray(dataset.x_train)
    y_train = np.asarray(dataset.y_train)
    x_test = np.asarray(dataset.x_test)
    y_test = np.asarray(dataset.y_test)

    # If sequences were created as a 1-D object array of arrays, stack into 3-D array.
    if x_train.ndim == 1 and len(x_train) > 0 and isinstance(x_train[0], (list, tuple, np.ndarray)):
        x_train = np.stack(x_train)
    if x_test.ndim == 1 and len(x_test) > 0 and isinstance(x_test[0], (list, tuple, np.ndarray)):
        x_test = np.stack(x_test)

    # Ensure y has shape (n_samples, horizon)
    if y_train.ndim == 1:
        y_train = y_train.reshape(-1, horizon)
    if y_test.ndim == 1 and y_test.size > 0:
        y_test = y_test.reshape(-1, horizon)
    model = build_short_term_model(lookback=lookback, feature_count=len(ordered_columns), horizon=horizon)
    fit_kwargs = {
        "epochs": epochs,
        "batch_size": batch_size,
    }
    if x_test.size > 0:
        fit_kwargs["validation_data"] = (x_test, y_test)
    model.fit(x_train, y_train, **fit_kwargs)
    Path(model_path).parent.mkdir(parents=True, exist_ok=True)
    model.save(model_path)
    return model
