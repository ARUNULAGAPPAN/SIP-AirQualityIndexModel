import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.predictor import LocationContext, SensorReading, WeatherData, generate_full_advisory, get_aqi_category_name, AQI_CATEGORIES

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="Real-time Sensor Predictions", page_icon="📡", layout="wide")

# Professional header
col_header_left, col_header_right = st.columns([3, 1])
with col_header_left:
    st.title("📡 Real-Time Air Quality Prediction")
    st.caption("Live hardware sensor data → Multi-feature AQI → Health advisories")
with col_header_right:
    st.metric("Last Updated", datetime.now().strftime("%H:%M:%S"), label_visibility="collapsed")

st.divider()

# ==================== DATA INPUT SECTION ====================
# Demo mode toggle
use_demo = st.toggle("🎮 Use Demo Mode (Simulated Hardware)", value=True, help="Toggle to switch between simulated and real hardware data")

st.sidebar.header("📍 Location")
latitude = st.sidebar.number_input("Latitude", value=23.0225, format="%.5f")
longitude = st.sidebar.number_input("Longitude", value=72.5714, format="%.5f")

location = LocationContext(latitude=latitude, longitude=longitude)

if use_demo:
    # Demo/simulated sensor data
    sensor = SensorReading(
        mq135_adc=1299,
        air_quality_ppm=1.27,
        mq7_adc=331,
        co_ppm=0.23,
        dust_adc=737,
        dust_voltage=0.59,
        estimated_pm25=0.97,
        temperature=23.68,
    )
    
    weather = WeatherData(
        temperature=23.68,
        humidity=65.0,
        wind_speed=3.5,
        pressure=1013.25,
    )
    
    st.info("🎮 **Demo Mode**: Using simulated sensor data. For real hardware, toggle off and integrate API endpoint.")
else:
    st.warning("⚠️ **Hardware Mode**: Connect your hardware API endpoint. See PREDICTIONS_README.md for integration guide.")
    # Placeholder for real hardware data
    sensor = SensorReading(
        mq135_adc=1299,
        air_quality_ppm=1.27,
        mq7_adc=331,
        co_ppm=0.23,
        dust_adc=737,
        dust_voltage=0.59,
        estimated_pm25=0.97,
        temperature=23.68,
    )
    weather = WeatherData(
        temperature=23.68,
        humidity=65.0,
        wind_speed=3.5,
        pressure=1013.25,
    )

# Generate advisory from sensor data
advisory = generate_full_advisory(sensor, weather, location=location, forecast_hours=4)

st.divider()

# ==================== CURRENT AQI SECTION ====================
st.header("📊 Current Air Quality Index")

current = advisory["current"]
aqi = current["aqi"]
category = current["category"]

# Color coding for AQI
if aqi <= 50:
    color, emoji = "#90EE90", "🟢"
elif aqi <= 100:
    color, emoji = "#FFFF00", "🟡"
elif aqi <= 150:
    color, emoji = "#FF8C00", "🟠"
elif aqi <= 200:
    color, emoji = "#FF0000", "🔴"
elif aqi <= 300:
    color, emoji = "#800080", "🟣"
else:
    color, emoji = "#8B0000", "⛔"

# Main AQI display
col_aqi_main, col_aqi_details = st.columns([2, 1])

with col_aqi_main:
    # Large AQI Gauge
    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=aqi,
            number={"suffix": "", "font": {"size": 60}},
            gauge={
                "axis": {"range": [0, 500]},
                "bar": {"color": color, "thickness": 0.2},
                "steps": [
                    {"range": [0, 50], "color": "rgba(144, 238, 144, 0.25)"},
                    {"range": [51, 100], "color": "rgba(255, 255, 0, 0.25)"},
                    {"range": [101, 150], "color": "rgba(255, 140, 0, 0.25)"},
                    {"range": [151, 200], "color": "rgba(255, 0, 0, 0.25)"},
                    {"range": [201, 300], "color": "rgba(128, 0, 128, 0.25)"},
                    {"range": [301, 500], "color": "rgba(139, 0, 0, 0.25)"},
                ],
            },
        )
    )
    fig_gauge.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_aqi_details:
    st.metric("AQI Category", f"{emoji} {category}")
    st.markdown("---")

    location_data = current["location"]
    st.caption("**Location Context**")
    st.metric("Latitude", f"{location_data['latitude']}")
    st.metric("Longitude", f"{location_data['longitude']}")
    st.metric("Location Factor", f"{location_data['factor']}")
    
    # Sensor contributions breakdown
    st.caption("**Sensor Contributions**")
    contributions = current["sensor_contributions"]
    contrib_sorted = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    
    for sensor_name, contrib_value in contrib_sorted:
        sensor_label = sensor_name.replace("_", " ").title()
        st.metric(sensor_label, f"{contrib_value:.1f}", label_visibility="collapsed")


st.divider()

# ==================== SENSOR READINGS SECTION ====================
st.header("🔌 Live Sensor Readings")

col1, col2, col3, col4 = st.columns(4)

sensors_data = current["sensors"]

with col1:
    st.subheader("Air Quality Sensors")
    st.metric("MQ135 ADC", f"{sensors_data['mq135_adc']:.0f}")
    st.metric("Air Quality PPM", f"{sensors_data['air_quality_ppm']:.2f}")

with col2:
    st.subheader("CO Sensor")
    st.metric("MQ7 ADC", f"{sensors_data['mq7_adc']:.0f}")
    st.metric("CO PPM", f"{sensors_data['co_ppm']:.3f}")

with col3:
    st.subheader("Dust Sensor")
    st.metric("Dust ADC", f"{sensors_data['dust_adc']:.0f}")
    st.metric("Dust Voltage", f"{sensors_data['dust_voltage']:.2f}V")

with col4:
    st.subheader("Environmental")
    st.metric("PM2.5", f"{sensors_data['pm25']:.2f} µg/m³")
    st.metric("Temperature", f"{sensors_data['temperature']:.1f}°C")

st.divider()

# ==================== WEATHER CONDITIONS SECTION ====================
st.header("🌤️ Weather Conditions")

col_w1, col_w2, col_w3, col_w4 = st.columns(4)

weather_data = current["weather"]

with col_w1:
    st.metric("Temperature", f"{weather_data['temperature']:.1f}°C")
with col_w2:
    st.metric("Humidity", f"{weather_data['humidity']:.0f}%")
with col_w3:
    st.metric("Wind Speed", f"{weather_data['wind_speed']:.1f} m/s")
with col_w4:
    st.metric("Pressure", f"{weather_data['pressure']:.0f} hPa")

st.divider()

# ==================== 4-HOUR FORECAST SECTION ====================
st.header("⏰ 4-Hour AQI Forecast")

forecast_data = advisory["forecast"]
peak_forecast = advisory["peak_forecast"]

# Forecast line chart
forecast_df = pd.DataFrame(forecast_data)

fig_forecast = go.Figure()

fig_forecast.add_trace(
    go.Scatter(
        x=forecast_df["hour_ahead"],
        y=forecast_df["predicted_aqi"],
        mode="lines+markers+text",
        name="Forecasted AQI",
        line=dict(color="steelblue", width=4),
        marker=dict(size=14, symbol="circle"),
        text=forecast_df["predicted_aqi"],
        textposition="top center",
        fill="tozeroy",
        fillcolor="rgba(70, 130, 180, 0.15)",
    )
)

# Add threshold zones
fig_forecast.add_hrect(y0=0, y1=50, fillcolor="green", opacity=0.1, layer="below", annotation_text="Good", annotation_position="left")
fig_forecast.add_hrect(y0=51, y1=100, fillcolor="yellow", opacity=0.1, layer="below", annotation_text="Moderate", annotation_position="left")
fig_forecast.add_hrect(y0=101, y1=150, fillcolor="orange", opacity=0.1, layer="below", annotation_text="Unhealthy", annotation_position="left")
fig_forecast.add_hrect(y0=151, y1=200, fillcolor="red", opacity=0.1, layer="below", annotation_text="Very Unhealthy", annotation_position="left")
fig_forecast.add_hrect(y0=201, y1=500, fillcolor="purple", opacity=0.1, layer="below", annotation_text="Hazardous", annotation_position="left")

fig_forecast.update_layout(
    title=None,
    xaxis_title="Hours Ahead",
    yaxis_title="Air Quality Index (AQI)",
    template="plotly_white",
    height=350,
    hovermode="x unified",
    showlegend=False,
)

st.plotly_chart(fig_forecast, use_container_width=True)

# Forecast table
col_table_left, col_table_right = st.columns([3, 1])

with col_table_left:
    st.caption("**Hourly Breakdown**")
    forecast_display = forecast_df.copy()
    forecast_display["Confidence"] = forecast_display["confidence"].apply(lambda x: f"{int(x)}%")
    forecast_display = forecast_display.rename(columns={
        "hour_ahead": "Hours Ahead",
        "predicted_aqi": "AQI",
        "category": "Health Impact",
    })
    
    st.dataframe(
        forecast_display[["Hours Ahead", "AQI", "Health Impact", "Confidence"]],
        use_container_width=True,
        hide_index=True,
    )

with col_table_right:
    st.caption("**Peak Forecast**")
    st.metric("Peak AQI", peak_forecast["aqi"])
    st.metric("At Hour", f"+{peak_forecast['hour_ahead']}h")
    st.metric("Category", peak_forecast["category"])

st.divider()

# ==================== HEALTH ADVISORY SECTION ====================
st.header("⚠️ Health Advisory & Recommendations")

advisory_data = advisory["advisory"]
level = advisory_data["level"]
emoji_icon = advisory_data["emoji"]

# Professional advisory box
if level == "good":
    st.success(f"{emoji_icon} **{advisory_data['message']}** — All outdoor activities are safe.")
elif level == "moderate":
    st.info(f"{emoji_icon} **{advisory_data['message']}** — Check sensitivity before outdoor activities.")
elif level == "unhealthy_sensitive":
    st.warning(f"{emoji_icon} **{advisory_data['message']}** — Sensitive groups should limit outdoor exposure.")
elif level == "unhealthy":
    st.error(f"{emoji_icon} **{advisory_data['message']}** — Limit outdoor activities for everyone.")
elif level == "very_unhealthy":
    st.error(f"{emoji_icon} **{advisory_data['message']}** — Avoid outdoor activities.")
else:
    st.error(f"{emoji_icon} **{advisory_data['message']}** — Emergency conditions. Stay indoors.")

st.subheader("📋 Recommendation")
st.markdown(f"> {advisory_data['recommendation']}")

# Avoid duration callout
if advisory_data["avoid_duration"]:
    st.error(f"🚫 **Avoid this area for: {advisory_data['avoid_duration']} hours** (or until AQI improves)")

st.divider()

# ==================== FOOTER SECTION ====================
st.markdown("""
---
### ℹ️ About This System

- **Data Source**: 8 hardware sensors + 4 weather factors (multi-feature correlation)
- **Sensor Attributes**: MQ135, Air Quality PPM, MQ7, CO, Dust ADC, Dust Voltage, PM2.5, Temperature
- **Weather Factors**: Temperature, Humidity, Wind Speed, Pressure
- **Forecast Horizon**: 4 hours ahead
- **Update Frequency**: Real-time (API endpoint integration ready)
- **Accuracy**: Confidence decreases with time (90% at +1h, 70% at +4h)

### 🔗 Integration

To connect real hardware:
1. Configure API endpoint in `src/weather_api.py`
2. Send sensor data via POST request (see PREDICTIONS_README.md)
3. Toggle "Hardware Mode" above

---
*🛡️ Stay informed. Make safe decisions. Check before going out.*
""", unsafe_allow_html=False)
