import pandas as pd
import json
from pathlib import Path
from typing import Optional, List
from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, PROCESSED_DATA_PATH


def load_raw_data(file_path: str) -> pd.DataFrame:
    return pd.read_csv(file_path)


def save_raw_data(uploaded_file, filename: str) -> Path:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_path = RAW_DATA_DIR / filename
    file_path.write_bytes(uploaded_file.getvalue())
    return file_path


def load_processed_data() -> Optional[pd.DataFrame]:
    if PROCESSED_DATA_PATH.exists():
        return pd.read_csv(PROCESSED_DATA_PATH)
    return None


def get_data_summary(df: pd.DataFrame) -> dict:
    return {
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": df.dtypes.to_dict(),
        "missing": df.isnull().sum().to_dict(),
        "numerical_summary": df.describe().to_dict(),
    }


def get_file_size(file_path: Path) -> str:
    size = file_path.stat().st_size
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def list_data_files() -> List[Path]:
    return list(RAW_DATA_DIR.glob("*.csv"))


def save_training_metadata(metadata: dict, log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(metadata, f, indent=4, default=str)


def load_training_metadata(log_path: Path) -> Optional[dict]:
    if log_path.exists():
        with open(log_path, "r") as f:
            return json.load(f)
    return None
