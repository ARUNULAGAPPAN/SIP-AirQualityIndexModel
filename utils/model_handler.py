import pickle
import json
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
from config import (
    SHORT_TERM_MODEL_PATH,
    LONG_TERM_MODEL_PATH,
    TRAINING_LOG_PATH,
)


def model_exists(model_path: Path) -> bool:
    return model_path.exists()


def get_model_info(model_path: Path) -> dict:
    if not model_path.exists():
        return {"exists": False, "message": "Model not found"}
    
    stat = model_path.stat()
    return {
        "exists": True,
        "path": str(model_path),
        "size": f"{stat.st_size / 1024 / 1024:.2f} MB",
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


def save_model(model: Any, model_path: Path) -> bool:
    try:
        model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(model_path, "wb") as f:
            pickle.dump(model, f)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def load_model(model_path: Path) -> Optional[Any]:
    try:
        if not model_path.exists():
            return None
        if str(model_path).endswith('.keras'):
            from tensorflow import keras
            return keras.models.load_model(str(model_path))
        else:
            with open(model_path, "rb") as f:
                return pickle.load(f)
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_training_history() -> Optional[dict]:
    if TRAINING_LOG_PATH.exists():
        try:
            with open(TRAINING_LOG_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error: {e}")
            return None
    return None


def save_training_log(training_info: dict) -> bool:
    try:
        TRAINING_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        training_info["timestamp"] = datetime.now().isoformat()
        with open(TRAINING_LOG_PATH, "w") as f:
            json.dump(training_info, f, indent=4, default=str)
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def delete_model(model_path: Path) -> bool:
    try:
        if model_path.exists():
            model_path.unlink()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def get_short_term_model_path() -> Path:
    return SHORT_TERM_MODEL_PATH


def get_long_term_model_path() -> Path:
    return LONG_TERM_MODEL_PATH


def format_metrics(metrics: dict) -> dict:
    return {
        key: f"{value:.4f}" if isinstance(value, float) else value
        for key, value in metrics.items()
    }
