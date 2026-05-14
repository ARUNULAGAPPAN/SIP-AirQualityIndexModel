import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"

PROCESSED_DATA_PATH = PROCESSED_DATA_DIR / "air_quality_processed.csv"
SHORT_TERM_MODEL_PATH = MODELS_DIR / "hourly_model.keras"
LONG_TERM_MODEL_PATH = MODELS_DIR / "daily_model.pkl"
TRAINING_LOG_PATH = MODELS_DIR / "training_log.json"

SHORT_TERM_LOOKBACK = 24
SHORT_TERM_HORIZON = 1
LONG_TERM_MODEL_TYPE = "prophet"

DEFAULT_FEATURE_COLS = ["PM2.5", "PM10", "Temp", "Humidity", "NO2", "CO"]
DEFAULT_TARGET_COL = "PM2.5"

THEME_COLOR = "#1f77b4"
ACCENT_COLOR = "#ff7f0e"

API_BASE_URL = os.getenv("AIRQUALITY_API_BASE_URL", "https://airquality-api-4njf.onrender.com").rstrip("/")
API_PREDICT_URL = f"{API_BASE_URL}/predict"
API_INGEST_URL = f"{API_BASE_URL}/ingest"

RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
