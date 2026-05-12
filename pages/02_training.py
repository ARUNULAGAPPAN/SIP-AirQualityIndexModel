import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.data_handler import save_raw_data, load_processed_data, list_data_files
from utils.model_handler import get_model_info, save_training_log, get_training_history
from config import RAW_DATA_DIR, PROCESSED_DATA_PATH, SHORT_TERM_MODEL_PATH, LONG_TERM_MODEL_PATH

st.set_page_config(page_title="Training", page_icon="arrow_forward", layout="wide")
st.title("Model Training Pipeline")

if "training_complete" not in st.session_state:
    st.session_state.training_complete = False
if "training_progress" not in st.session_state:
    st.session_state.training_progress = 0

tabs = st.tabs(["Upload Data", "Configure Training", "Train Models", "Results"])

with tabs[0]:
    st.subheader("Upload Your Air Quality Dataset")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Expected Data Format
        Your CSV should contain:
        - datetime column
        - PM2.5 (target variable)
        - PM10, NO2, CO (pollutants)
        - Temp, Humidity (weather data)
        """)
    
    with col2:
        st.markdown("""
        ### Recommended Data Sources
        - OpenAQ
        - UCI Air Quality Dataset
        - Kaggle Air Quality
        - EPA AirNow
        
        ### Requirements
        - Minimum 1000 records
        - Regular time intervals (hourly)
        - Less than 30% missing values
        """)
    
    st.divider()
    
    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])
    
    if uploaded_file is not None:
        file_path = save_raw_data(uploaded_file, uploaded_file.name)
        st.success(f"File uploaded: {uploaded_file.name}")
        
        st.subheader("Data Preview")
        df = pd.read_csv(file_path)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rows", len(df))
        with col2:
            st.metric("Columns", len(df.columns))
        with col3:
            missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            st.metric("Missing Data", f"{missing_pct:.1f}%")
        
        st.dataframe(df.head(10), use_container_width=True)
        st.info("File ready for preprocessing!")
    
    st.subheader("Existing Data Files")
    existing_files = list_data_files()
    if existing_files:
        st.caption(f"Found {len(existing_files)} file(s)")
        for file in existing_files:
            st.text(f"{file.name} ({file.stat().st_size / 1024 / 1024:.2f} MB)")
    else:
        st.caption("No existing files")

with tabs[1]:
    st.subheader("Training Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Short-term Model (LSTM - Hourly)")
        st.markdown("""
        - Algorithm: LSTM Neural Network
        - Frequency: Hourly predictions
        - Use Case: Near-term forecasting
        - Features: Time series sequences
        """)
        
        lookback = st.number_input(
            "Lookback window (hours)",
            min_value=6,
            max_value=168,
            value=24,
            help="Past hours to use for prediction"
        )
        
        horizon = st.number_input(
            "Forecast horizon (hours)",
            min_value=1,
            max_value=6,
            value=1,
            help="Hours ahead to forecast"
        )
        
        st.info(f"Using {lookback}h history to predict {horizon}h ahead")
    
    with col2:
        st.markdown("### Long-term Model (Daily)")
        st.markdown("""
        - Algorithms: Prophet or XGBoost
        - Frequency: Daily predictions
        - Use Case: Long-term trends
        - Features: Seasonality, trend
        """)
        
        long_term_model = st.selectbox(
            "Select long-term model type",
            ["prophet", "xgboost"],
            help="Prophet for seasonality, XGBoost for complex patterns"
        )
        
        st.info(f"Using {long_term_model.upper()}")
    
    st.divider()
    st.subheader("Training Modes")
    
    training_mode = st.radio(
        "Select what to train",
        ["Short-term only", "Long-term only", "Both models"],
        horizontal=True
    )
    
    st.session_state.training_config = {
        "lookback": lookback,
        "horizon": horizon,
        "long_term_model": long_term_model,
        "mode": training_mode
    }
    
    st.success("Configuration ready!")

with tabs[2]:
    st.subheader("Train Models")
    
    if load_processed_data() is None:
        st.warning("No processed data found.")
        st.info("Steps: 1. Go to Upload Data, 2. Upload CSV, 3. Complete preprocessing")
    else:
        processed_data = load_processed_data()
        
        st.success(f"Processed data: {len(processed_data)} records")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Pre-training")
            if st.button("Preprocess Data", use_container_width=True):
                with st.spinner("Preprocessing..."):
                    try:
                        from src.preprocess import preprocess_data
                        raw_files = list(RAW_DATA_DIR.glob("*.csv"))
                        if raw_files:
                            latest_file = max(raw_files, key=lambda p: p.stat().st_mtime)
                            df = preprocess_data(str(latest_file), str(PROCESSED_DATA_PATH))
                            st.success(f"Data preprocessed! {len(df)} records")
                        else:
                            st.error("No CSV files in data/raw/")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with col2:
            st.markdown("### Data Summary")
            if processed_data is not None:
                st.metric("Records", len(processed_data))
                st.metric("Features", len(processed_data.columns))
        
        st.divider()
        
        st.subheader("Start Training")
        
        training_col1, training_col2 = st.columns([2, 1])
        
        with training_col1:
            mode = st.selectbox(
                "Training mode",
                ["Short-term (LSTM)", "Long-term (Prophet/XGBoost)", "Both models"]
            )
        
        with training_col2:
            train_button = st.button("START TRAINING", use_container_width=True, type="primary")
        
        if train_button:
            try:
                processed_df = load_processed_data()
                if processed_df is not None:
                    progress_bar = st.progress(0)
                    status_container = st.container()
                    
                    training_log = {
                        "start_time": datetime.now().isoformat(),
                        "mode": mode,
                        "records": len(processed_df),
                        "features": list(processed_df.columns),
                    }
                    
                    if "Short-term" in mode or "Both" in mode:
                        with status_container:
                            st.info("Training short-term model...")
                        try:
                            from src.model_short_term import train_short_term_model
                            
                            target_col = "PM2.5" if "PM2.5" in processed_df.columns else processed_df.columns[0]
                            feature_cols = [col for col in processed_df.columns if col != "datetime"]
                            
                            lookback = st.session_state.training_config.get("lookback", 24)
                            horizon = st.session_state.training_config.get("horizon", 1)
                            
                            train_short_term_model(
                                frame=processed_df,
                                feature_columns=feature_cols,
                                target_column=target_col,
                                model_path=str(SHORT_TERM_MODEL_PATH),
                                lookback=lookback,
                                horizon=horizon
                            )
                            
                            with status_container:
                                st.success("Short-term model trained!")
                            progress_bar.progress(50)
                            training_log["short_term_status"] = "completed"
                        except Exception as e:
                            st.error(f"Short-term training failed: {str(e)}")
                            training_log["short_term_status"] = f"failed: {str(e)}"
                    
                    if "Long-term" in mode or "Both" in mode:
                        with status_container:
                            st.info("Training long-term model...")
                        try:
                            from src.model_long_term import train_long_term_model
                            
                            target_col = "PM2.5" if "PM2.5" in processed_df.columns else processed_df.columns[0]
                            long_term_model_type = st.session_state.training_config.get("long_term_model", "prophet")
                            
                            train_long_term_model(
                                frame=processed_df,
                                target_column=target_col,
                                model_path=str(LONG_TERM_MODEL_PATH),
                                model_type=long_term_model_type
                            )
                            
                            with status_container:
                                st.success("Long-term model trained!")
                            progress_bar.progress(100)
                            training_log["long_term_status"] = "completed"
                        except Exception as e:
                            st.error(f"Long-term training failed: {str(e)}")
                            training_log["long_term_status"] = f"failed: {str(e)}"
                    
                    training_log["end_time"] = datetime.now().isoformat()
                    save_training_log(training_log)
                    
                    st.session_state.training_complete = True
                    st.balloons()
                    
            except Exception as e:
                st.error(f"Training error: {str(e)}")

with tabs[3]:
    st.subheader("Training Results")
    
    short_term_info = get_model_info(SHORT_TERM_MODEL_PATH)
    long_term_info = get_model_info(LONG_TERM_MODEL_PATH)
    training_history = get_training_history()

    short_ready = short_term_info["exists"]
    long_ready = long_term_info["exists"]
    models_ready = int(short_ready) + int(long_ready)
    records_value = training_history.get("records", 0) if training_history else 0
    features_value = len(training_history.get("features", [])) if training_history else 0
    training_mode = training_history.get("mode", "N/A") if training_history else "N/A"

    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    with metric_col1:
        st.metric("Short-term", "Ready" if short_ready else "Missing")
    with metric_col2:
        st.metric("Long-term", "Ready" if long_ready else "Missing")
    with metric_col3:
        st.metric("Training Mode", training_mode)
    with metric_col4:
        st.metric("Models Ready", f"{models_ready}/2")

    chart_col1, chart_col2 = st.columns([1.4, 1])

    with chart_col1:
        readiness_fig = go.Figure()
        readiness_fig.add_trace(
            go.Bar(
                x=["Short-term", "Long-term"],
                y=[1 if short_ready else 0, 1 if long_ready else 0],
                text=["Ready" if short_ready else "Missing", "Ready" if long_ready else "Missing"],
                textposition="auto",
                marker_color=["#2ca02c" if short_ready else "#d62728", "#2ca02c" if long_ready else "#d62728"],
            )
        )
        readiness_fig.update_layout(
            title="Model Readiness",
            yaxis=dict(range=[0, 1.2], tickvals=[0, 1], ticktext=["Missing", "Ready"]),
            xaxis_title="Model",
            template="plotly_white",
            height=340,
            margin=dict(l=10, r=10, t=50, b=10),
        )
        st.plotly_chart(readiness_fig, use_container_width=True)

    with chart_col2:
        coverage_fig = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=models_ready * 50,
                number={"suffix": "%"},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": "#1f77b4"},
                    "steps": [
                        {"range": [0, 50], "color": "#fde0dd"},
                        {"range": [50, 100], "color": "#e5f5e0"},
                    ],
                },
            )
        )
        coverage_fig.update_layout(title="Training Coverage", height=340, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(coverage_fig, use_container_width=True)

    detail_col1, detail_col2 = st.columns(2)
    
    with detail_col1:
        st.markdown("### Short-term Model")
        if short_term_info["exists"]:
            st.success("Ready")
            st.caption(f"Size: {short_term_info['size']}")
            st.caption(f"Created: {short_term_info['created']}")
            st.caption(f"Modified: {short_term_info['modified']}")
        else:
            st.info("Not trained yet")
    
    with detail_col2:
        st.markdown("### Long-term Model")
        if long_term_info["exists"]:
            st.success("Ready")
            st.caption(f"Size: {long_term_info['size']}")
            st.caption(f"Created: {long_term_info['created']}")
            st.caption(f"Modified: {long_term_info['modified']}")
        else:
            st.info("Not trained yet")

    st.markdown("### Interpretation")
    if short_ready and long_ready:
        st.success(
            "Both models are trained and ready. The hourly model captures short-term variation, and the daily model is ready for trend forecasting."
        )
    elif short_ready or long_ready:
        st.warning(
            "Only one model is ready. You can generate forecasts for that horizon, but the full forecasting set is not complete yet."
        )
    else:
        st.info(
            "No trained models are available yet. Upload data and run training to generate forecast results here."
        )

    if training_history:
        history_col1, history_col2, history_col3 = st.columns(3)
        with history_col1:
            st.metric("Records Trained", records_value)
        with history_col2:
            st.metric("Feature Count", features_value)
        with history_col3:
            st.metric("Last Run", training_history.get("timestamp", "N/A")[:10])

        st.caption(
            f"Last training status: {training_history.get('short_term_status', 'N/A')} | {training_history.get('long_term_status', 'N/A')}"
        )
    
    st.divider()

    with st.expander("Model Management"):
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Delete Short-term Model", use_container_width=True):
                try:
                    SHORT_TERM_MODEL_PATH.unlink(missing_ok=True)
                    st.success("Model deleted")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        with col2:
            if st.button("Delete Long-term Model", use_container_width=True):
                try:
                    LONG_TERM_MODEL_PATH.unlink(missing_ok=True)
                    st.success("Model deleted")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        with col3:
            if st.button("Delete All Models", use_container_width=True):
                try:
                    SHORT_TERM_MODEL_PATH.unlink(missing_ok=True)
                    LONG_TERM_MODEL_PATH.unlink(missing_ok=True)
                    st.success("Models deleted")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
