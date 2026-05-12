"""Train short-term model on the generated sensor dataset."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from src.model_short_term import train_short_term_model
from config import SHORT_TERM_MODEL_PATH

DATASET_PATH = Path(__file__).parent / "data" / "processed" / "sensor_dataset_generated.csv"

if __name__ == "__main__":
    df = pd.read_csv(DATASET_PATH)
    print(f"Loaded {len(df)} rows from {DATASET_PATH}")
    print(f"Columns: {list(df.columns)}")
    
    feature_cols = [col for col in df.columns if col not in ["AQI", "Primary Pollutant"]]
    target_col = "AQI"
    
    print(f"Training with features: {feature_cols}")
    print(f"Target: {target_col}")
    
    model = train_short_term_model(
        frame=df,
        feature_columns=feature_cols,
        target_column=target_col,
        model_path=str(SHORT_TERM_MODEL_PATH),
        lookback=24,
        horizon=1,
        epochs=10,
        batch_size=32
    )
    print(f"✓ Model saved to {SHORT_TERM_MODEL_PATH}")
