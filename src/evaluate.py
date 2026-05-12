"""Model evaluation helpers."""

from __future__ import annotations

from typing import Iterable


def _require_numpy() -> object:
    try:
        import numpy as np
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise ImportError("numpy is required for metric calculation. Install requirements.txt first.") from exc
    return np


def calculate_metrics(y_true: Iterable[float], y_pred: Iterable[float]) -> dict[str, float]:
    """Return RMSE and MAE for a set of predictions."""

    np = _require_numpy()

    y_true_array = np.asarray(list(y_true), dtype=float)
    y_pred_array = np.asarray(list(y_pred), dtype=float)

    if y_true_array.shape != y_pred_array.shape:
        raise ValueError("y_true and y_pred must have the same shape.")

    rmse = float(np.sqrt(np.mean((y_true_array - y_pred_array) ** 2)))
    mae = float(np.mean(np.abs(y_true_array - y_pred_array)))
    return {"rmse": rmse, "mae": mae}
