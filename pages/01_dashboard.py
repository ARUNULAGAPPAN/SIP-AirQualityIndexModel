import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.data_handler import load_processed_data
from utils.model_handler import get_model_info
from config import SHORT_TERM_MODEL_PATH, LONG_TERM_MODEL_PATH, DEFAULT_TARGET_COL

st.set_page_config(page_title="Dashboard", page_icon="chart_with_upwards_trend", layout="wide")
st.title("Air Quality Forecasting Dashboard")

st.sidebar.header("Dashboard Settings")
time_range = st.sidebar.selectbox("Time Range", ["Last 7 days", "Last 30 days", "Last 90 days", "All"])

col1, col2, col3 = st.columns(3)

processed_data = load_processed_data()

if processed_data is not None and len(processed_data) > 0:
    with col1:
        st.metric(
            "Total Records",
            f"{len(processed_data):,}",
            delta="records loaded",
        )
    
    with col2:
        target_col = DEFAULT_TARGET_COL
        if target_col in processed_data.columns:
            latest_value = processed_data[target_col].iloc[-1]
            avg_value = processed_data[target_col].mean()
            st.metric(
                f"Latest {target_col}",
                f"{latest_value:.2f}",
                delta=f"{latest_value - avg_value:+.2f} vs avg",
            )
    
    with col3:
        missing_pct = (processed_data.isnull().sum().sum() / (len(processed_data) * len(processed_data.columns))) * 100
        st.metric(
            "Data Quality",
            f"{100 - missing_pct:.1f}%",
            delta=f"{missing_pct:.1f}% missing",
        )
    
    st.divider()
    
    st.subheader("Model Status")
    model_col1, model_col2 = st.columns(2)
    
    with model_col1:
        st.markdown("#### Short-term Model (LSTM - Hourly)")
        short_term_info = get_model_info(SHORT_TERM_MODEL_PATH)
        if short_term_info["exists"]:
            st.success("Model Ready")
            st.caption(f"Size: {short_term_info['size']}")
            st.caption(f"Last updated: {short_term_info['modified']}")
        else:
            st.warning("Not trained yet")
    
    with model_col2:
        st.markdown("#### Long-term Model (Daily)")
        long_term_info = get_model_info(LONG_TERM_MODEL_PATH)
        if long_term_info["exists"]:
            st.success("Model Ready")
            st.caption(f"Size: {long_term_info['size']}")
            st.caption(f"Last updated: {long_term_info['modified']}")
        else:
            st.warning("Not trained yet")
    
    st.divider()
    
    st.subheader("Data Overview")
    
    viz_col1, viz_col2 = st.columns(2)
    
    with viz_col1:
        numeric_cols = processed_data.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            selected_col = st.selectbox("Select column to visualize", numeric_cols, key="viz_col")
            if selected_col:
                fig = px.line(
                    processed_data,
                    y=selected_col,
                    title=f"{selected_col} Over Time",
                    labels={selected_col: "Value"},
                    template="plotly_white"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    with viz_col2:
        if numeric_cols:
            dist_col = st.selectbox("Select column for distribution", numeric_cols, key="dist_col")
            if dist_col:
                fig = px.histogram(
                    processed_data,
                    x=dist_col,
                    nbins=50,
                    title=f"Distribution of {dist_col}",
                    template="plotly_white"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Feature Correlation")
    numeric_cols = processed_data.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) > 1:
        corr_matrix = processed_data[numeric_cols].corr()
        fig = px.imshow(
            corr_matrix,
            labels=dict(x="Features", y="Features", color="Correlation"),
            title="Feature Correlation Matrix",
            color_continuous_scale="RdBu",
            template="plotly_white",
            zmin=-1, zmax=1
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Data Preview")
    st.dataframe(processed_data.tail(20), use_container_width=True)
    
    st.subheader("Data Statistics")
    st.dataframe(processed_data.describe(), use_container_width=True)

else:
    st.info("No processed data available. Please upload and process data in the Training page.")
    st.warning("Steps: 1. Go to Training page, 2. Upload your CSV file, 3. Run preprocessing, 4. Return here")
