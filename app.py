import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

st.set_page_config(
    page_title="Air Quality Forecasting",
    page_icon="chart_with_upwards_trend",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 3em;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5em;
    }
    .subtitle {
        font-size: 1.2em;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Air Quality Forecasting")
    st.markdown("---")
    
    st.markdown("""
    ### Quick Links
    - Dashboard: View data and metrics
    - Training: Train models with your data
    - Predictions: Make forecasts
    """)
    
    st.markdown("---")
    
    st.markdown("""
    ### About
    Air-Powered Air Quality Forecasting
    
    Predict air pollutant levels using:
    - LSTM: Hourly forecasting
    - Prophet/XGBoost: Daily trends
    """)
    
    st.markdown("---")
    
    with st.expander("Getting Started"):
        st.markdown("""
        1. Upload Data: Start in the Training page
        2. Preprocess: Clean and prepare data
        3. Train Models: Build LSTM and daily models
        4. Dashboard: View data insights
        5. Predict: Make forecasts on new data
        """)
    
    st.markdown("---")
    st.caption("Made with Streamlit")

col1, col2 = st.columns([3, 1])

with col1:
    st.markdown("""
    # Air Quality Forecasting System
    ### Predict air pollutant levels with machine learning
    """)

with col2:
    st.markdown("""
    ##### Version 2.0
    Multi-page UI
    """)

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### Dashboard
    View your data and model performance metrics at a glance.
    - Data overview
    - Model status
    - Visualizations
    - Statistics
    """)

with col2:
    st.markdown("""
    ### Training
    Train machine learning models on your dataset.
    - Upload CSV files
    - Configure parameters
    - Train LSTM & daily models
    - Monitor progress
    """)

with col3:
    st.markdown("""
    ### Predictions
    Generate forecasts for future air quality.
    - Hourly predictions
    - Daily trends
    - Batch forecasting
    - Confidence intervals
    """)

st.divider()

st.markdown("## Quick Start")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Step 1: Upload Data
    - Go to Training page
    - Click upload and select your CSV file
    - Expected columns: datetime, PM2.5, PM10, Temp, Humidity
    - Supported data sources: OpenAQ, UCI, Kaggle, EPA
    """)

with col2:
    st.markdown("""
    ### Step 2: Train Models
    - Review data preview
    - Configure model parameters
    - Choose training mode (short-term, long-term, or both)
    - Click "START TRAINING"
    """)

col3, col4 = st.columns(2)

with col3:
    st.markdown("""
    ### Step 3: View Dashboard
    - Go to Dashboard page
    - See data insights and visualizations
    - Check model status
    - Monitor data quality metrics
    """)

with col4:
    st.markdown("""
    ### Step 4: Make Predictions
    - Go to Predictions page
    - Generate hourly or daily forecasts
    - View confidence intervals
    - Download predictions as CSV
    """)

st.divider()

st.markdown("## Features")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    ### Advanced Models
    - LSTM Neural Network: Sequence-to-sequence learning for hourly patterns
    - Prophet: Facebook's forecasting tool with seasonality
    - XGBoost: Gradient boosting for complex patterns
    """)
    
    st.markdown("""
    ### Data Processing
    - Automatic column mapping and normalization
    - Missing value handling
    - Feature engineering
    - Time-based features (hour, day, month)
    """)

with col2:
    st.markdown("""
    ### Flexible Training
    - Train individual or combined models
    - Customize lookback windows and horizons
    - Choose between daily forecast methods
    - Monitor training progress in real-time
    """)
    
    st.markdown("""
    ### Comprehensive Forecasting
    - Hourly predictions (next 6-24 hours)
    - Daily trends (30-365 days ahead)
    - Confidence intervals
    - Batch prediction support
    """)

st.divider()

st.markdown("## Data Sources")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    ### OpenAQ
    Real-time air quality data
    [openaq.org](https://openaq.org)
    """)

with col2:
    st.markdown("""
    ### UCI Dataset
    Air Quality ML datasets
    [archive.ics.uci.edu](https://archive.ics.uci.edu)
    """)

with col3:
    st.markdown("""
    ### Kaggle
    Community datasets
    [kaggle.com](https://www.kaggle.com)
    """)

with col4:
    st.markdown("""
    ### EPA AirNow
    US Environmental Protection
    [airnow.gov](https://www.airnow.gov)
    """)

st.divider()

st.markdown("""
---
## Ready to Start?
Use the sidebar to navigate to the Training page and upload your first dataset!

### Expected CSV Format
Your data should include:
- datetime: Timestamp or date column
- PM2.5: Fine particulate matter (target variable)
- PM10: Coarse particulate matter
- NO2, CO: Pollutant levels
- Temp, Humidity: Weather variables

Other column names are automatically mapped to standard names.

---
""")

st.markdown("""
<hr style="margin: 2em 0;">
<p style="text-align: center; color: #999;">
    Air Quality Forecasting System v2.0 | Built with Streamlit
</p>
""", unsafe_allow_html=True)
