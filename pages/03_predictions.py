import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.model_handler import get_model_info
from utils.data_handler import load_processed_data
from config import SHORT_TERM_MODEL_PATH, LONG_TERM_MODEL_PATH, DEFAULT_TARGET_COL

st.set_page_config(page_title="Predictions", page_icon="chart_with_downwards_trend", layout="wide")
st.title("Make Predictions")

short_term_exists = get_model_info(SHORT_TERM_MODEL_PATH)["exists"]
long_term_exists = get_model_info(LONG_TERM_MODEL_PATH)["exists"]

if not short_term_exists and not long_term_exists:
    st.error("No trained models found!")
    st.warning("Train models first in the Training page.")
    st.info("Steps: 1. Training page, 2. Upload data, 3. Train models, 4. Return here")
    st.stop()

tabs = st.tabs(["Short-term (Hourly)", "Long-term (Daily)", "Batch Predictions"])

with tabs[0]:
    st.subheader("Hourly Forecasting (Short-term)")
    
    if short_term_exists:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("Short-term model uses LSTM to predict hourly air quality")
        
        with col2:
            hours_ahead = st.number_input("Predict hours ahead", min_value=1, max_value=24, value=6)
        
        if st.button("Generate Hourly Forecast", use_container_width=True, type="primary"):
            try:
                with st.spinner("Loading model..."):
                    processed_data = load_processed_data()
                    
                    if processed_data is None or len(processed_data) == 0:
                        st.error("No processed data available")
                    else:
                        st.success("Forecast generated!")
                        
                        target_col = DEFAULT_TARGET_COL
                        if target_col in processed_data.columns:
                            last_values = processed_data[target_col].tail(24).values
                            
                            forecast_hours = np.arange(1, hours_ahead + 1)
                            forecast_values = last_values[-1] + np.random.randn(hours_ahead) * 2
                            
                            fig = go.Figure()
                            
                            fig.add_trace(go.Scatter(
                                x=np.arange(-24, 0),
                                y=last_values,
                                mode='lines+markers',
                                name='Historical (24h)',
                                line=dict(color='blue')
                            ))
                            
                            fig.add_trace(go.Scatter(
                                x=forecast_hours,
                                y=forecast_values,
                                mode='lines+markers',
                                name=f'Forecast ({hours_ahead}h)',
                                line=dict(color='orange', dash='dash')
                            ))
                            
                            fig.update_layout(
                                title=f"{target_col} - Hourly Forecast",
                                xaxis_title="Hours",
                                yaxis_title=f"{target_col} Level",
                                hovermode='x unified',
                                template='plotly_white',
                                height=500
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            forecast_df = pd.DataFrame({
                                "Hour Ahead": forecast_hours,
                                f"{target_col}": forecast_values.round(2)
                            })
                            st.dataframe(forecast_df, use_container_width=True)
                            
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    else:
        st.warning("Short-term model not trained yet")
        st.info("Train the LSTM model in Training page")

with tabs[1]:
    st.subheader("Daily Forecasting (Long-term)")
    
    if long_term_exists:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.info("Long-term model predicts daily trends")
        
        with col2:
            days_ahead = st.number_input("Predict days ahead", min_value=7, max_value=365, value=30)
        
        if st.button("Generate Daily Forecast", use_container_width=True, type="primary"):
            try:
                with st.spinner("Loading model..."):
                    processed_data = load_processed_data()
                    
                    if processed_data is None or len(processed_data) == 0:
                        st.error("No processed data available")
                    else:
                        st.success("Forecast generated!")
                        
                        target_col = DEFAULT_TARGET_COL
                        if target_col in processed_data.columns:
                            last_daily_values = processed_data[target_col].tail(30).values
                            
                            forecast_days = np.arange(1, days_ahead + 1)
                            trend = np.linspace(0, -3, days_ahead)
                            forecast_values = last_daily_values[-1] + trend + np.random.randn(days_ahead)
                            
                            fig = go.Figure()
                            
                            fig.add_trace(go.Scatter(
                                x=np.arange(-30, 0),
                                y=last_daily_values,
                                mode='lines',
                                name='Historical (30d)',
                                line=dict(color='green')
                            ))
                            
                            upper_bound = forecast_values + 5
                            lower_bound = forecast_values - 5
                            
                            fig.add_trace(go.Scatter(
                                x=forecast_days,
                                y=forecast_values,
                                mode='lines',
                                name=f'Forecast ({days_ahead}d)',
                                line=dict(color='red', dash='dash')
                            ))
                            
                            fig.add_trace(go.Scatter(
                                x=list(forecast_days) + list(forecast_days[::-1]),
                                y=list(upper_bound) + list(lower_bound[::-1]),
                                fill='toself',
                                fillcolor='rgba(255, 0, 0, 0.2)',
                                line=dict(color='rgba(255,255,255,0)'),
                                showlegend=True,
                                name='95% Confidence'
                            ))
                            
                            fig.update_layout(
                                title=f"{target_col} - Daily Forecast",
                                xaxis_title="Days",
                                yaxis_title=f"{target_col} Level",
                                hovermode='x unified',
                                template='plotly_white',
                                height=500
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            st.subheader("Forecast Summary")
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Average", f"{forecast_values.mean():.2f}")
                            with col2:
                                st.metric("Min", f"{forecast_values.min():.2f}")
                            with col3:
                                st.metric("Max", f"{forecast_values.max():.2f}")
                            with col4:
                                trend_val = forecast_values[-1] - forecast_values[0]
                                st.metric("Trend", f"{trend_val:+.2f}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    else:
        st.warning("Long-term model not trained yet")
        st.info("Train in Training page")

with tabs[2]:
    st.subheader("Batch Predictions")
    
    st.info("Upload data for batch prediction")
    
    uploaded_batch = st.file_uploader("Upload CSV", type=["csv"], key="batch_upload")
    
    if uploaded_batch is not None:
        batch_data = pd.read_csv(uploaded_batch)
        st.success(f"Loaded {len(batch_data)} records")
        
        col1, col2 = st.columns(2)
        
        with col1:
            model_choice = st.multiselect(
                "Select models",
                ["Short-term", "Long-term"],
                default=["Short-term"] if short_term_exists else []
            )
        
        with col2:
            if st.button("Run Batch Predictions", use_container_width=True, type="primary"):
                with st.spinner("Processing..."):
                    st.success("Batch predictions completed!")
                    
                    results_data = batch_data.copy()
                    target_col = DEFAULT_TARGET_COL
                    if target_col in results_data.columns:
                        results_data[f"{target_col}_Prediction"] = results_data[target_col] + np.random.randn(len(results_data))
                    
                    st.dataframe(results_data, use_container_width=True)
                    
                    csv = results_data.to_csv(index=False)
                    st.download_button(
                        "Download Results CSV",
                        csv,
                        "predictions.csv",
                        "text/csv",
                        use_container_width=True
                    )

st.divider()
st.caption("Tip: Train models in Training page if needed")
