import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import sys
from datetime import datetime
import requests
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import API_INGEST_URL, API_PREDICT_URL
from src.predictor import LocationContext, SensorReading, WeatherData, generate_full_advisory, get_aqi_category_name, AQI_CATEGORIES
from src.mongo_storage import get_distinct_locations_and_forecast, get_aggregated_readings_for_location

# ==================== SESSION STATE ====================
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()
if "auto_refresh_enabled" not in st.session_state:
    st.session_state.auto_refresh_enabled = True
if "selected_sensor_index" not in st.session_state:
    st.session_state.selected_sensor_index = 0

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

# ==================== FETCH SENSOR LOCATIONS ====================
@st.cache_data(ttl=30)  # Cache for 30 seconds
def fetch_available_sensors() -> list[dict]:
    """Fetch the two distinct sensor locations from database."""
    try:
        from src.mongo_storage import get_distinct_locations_and_forecast
        result = get_distinct_locations_and_forecast(forecast_hours=4)
        return result.get("locations", [])
    except Exception as e:
        st.error(f"Error fetching sensor locations: {e}")
        return []

# ==================== LIVE DATA FETCH ====================
def fetch_live_prediction_from_reading(latitude: float, longitude: float, forecast_hours: int = 4) -> dict | None:
    """Fetch aggregated readings (20 latest) and predict using actual data."""
    try:
        # Get the 20 latest readings for this location from database, aggregated
        aggregated_reading = get_aggregated_readings_for_location(latitude, longitude, count=20)
        
        if not aggregated_reading:
            st.warning(f"No readings found for location ({latitude:.4f}, {longitude:.4f})")
            return None
        
        # Use aggregated sensor data from the database
        payload = {
            "mq135_adc": aggregated_reading.get("mq135_adc", 0),
            "air_quality_ppm": aggregated_reading.get("air_quality_ppm", 0),
            "mq7_adc": aggregated_reading.get("mq7_adc", 0),
            "co_ppm": aggregated_reading.get("co_ppm", 0),
            "dust_adc": aggregated_reading.get("dust_adc", 0),
            "dust_voltage": aggregated_reading.get("dust_voltage", 0),
            "estimated_pm25": aggregated_reading.get("estimated_pm25", 0),
            "temperature": aggregated_reading.get("temperature", 22),
            "latitude": latitude,
            "longitude": longitude,
            "forecast_hours": forecast_hours,
        }
        
        response = requests.post(
            API_PREDICT_URL,
            json=payload,
            timeout=15,
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"API returned {response.status_code}: {response.text[:100]}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to API. Is the server running?")
        return None
    except requests.exceptions.Timeout:
        st.error("❌ API request timed out. Server may be slow.")
        return None
    except Exception as e:
        st.error(f"❌ Error fetching live data: {str(e)}")
        return None


def advisory_from_api_response(response: dict) -> dict:
    """Convert API response to advisory format."""
    return response


# ==================== DATA INPUT SECTION ====================

# Demo mode toggle
use_demo = st.toggle("🎮 Use Demo Mode (Simulated Hardware)", value=True, help="Toggle to switch between simulated and real hardware data")

if use_demo:
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
    
    st.sidebar.header("📍 Location")
    latitude = st.sidebar.number_input("Latitude", value=23.0225, format="%.5f")
    longitude = st.sidebar.number_input("Longitude", value=72.5714, format="%.5f")
    location = LocationContext(latitude=latitude, longitude=longitude)
else:
    # Hardware mode: Select from two real sensor nodes
    st.sidebar.header("⚙️ Hardware Settings")
    
    # Fetch available sensor locations
    available_sensors = fetch_available_sensors()
    
    if not available_sensors:
        st.error("❌ No sensor readings found in database. Please ensure hardware is sending data via `/ingest` endpoint.")
        st.stop()
    
    # Create sensor selector
    sensor_options = []
    for idx, sensor_data in enumerate(available_sensors):
        lat = sensor_data.get("latitude", 0)
        lon = sensor_data.get("longitude", 0)
        latest_reading = sensor_data.get("latest_reading", {})
        aqi_current = sensor_data.get("forecast", {}).get("current_aqi", "N/A")
        sensor_options.append(f"Sensor {idx+1}: ({lat:.4f}, {lon:.4f}) - AQI: {aqi_current}")
    
    selected_sensor_label = st.sidebar.selectbox(
        "Select Sensor Node",
        options=sensor_options,
        index=st.session_state.selected_sensor_index,
        help="Choose which sensor node to display predictions for"
    )
    
    # Extract selected sensor index
    selected_index = sensor_options.index(selected_sensor_label)
    st.session_state.selected_sensor_index = selected_index
    selected_sensor = available_sensors[selected_index]
    
    latitude = selected_sensor["latitude"]
    longitude = selected_sensor["longitude"]
    location = LocationContext(latitude=latitude, longitude=longitude)
    
    # Auto-refresh control
    auto_refresh = st.sidebar.checkbox("🔄 Auto-Refresh (every 10s)", value=True, help="Automatically refresh live data from API")
    if st.sidebar.button("🔄 Refresh Now", key="manual_refresh"):
        st.cache_data.clear()
    
    st.warning(
        f"⚠️ **Hardware Mode Active**: Fetching live predictions for Sensor at ({latitude:.4f}, {longitude:.4f})"
    )
    
    # Fetch live prediction using actual sensor data
    api_response = fetch_live_prediction_from_reading(latitude, longitude, forecast_hours=4)

    if api_response:
        advisory = advisory_from_api_response(api_response)
        st.session_state.last_refresh = time.time()
        st.success("✅ Connected to API - showing live predictions")

        # Populate local sensor/weather variables from API so all UI widgets reflect live values
        try:
            current_api = advisory.get("current", {})
            sensors_api = current_api.get("sensors", {})
            weather_api = current_api.get("weather", {})

            sensor = SensorReading(
                mq135_adc=float(sensors_api.get("mq135_adc", 0)),
                air_quality_ppm=float(sensors_api.get("air_quality_ppm", 0)),
                mq7_adc=float(sensors_api.get("mq7_adc", 0)),
                co_ppm=float(sensors_api.get("co_ppm", 0)),
                dust_adc=float(sensors_api.get("dust_adc", 0)),
                dust_voltage=float(sensors_api.get("dust_voltage", 0)),
                estimated_pm25=float(sensors_api.get("pm25", 0)),
                temperature=float(sensors_api.get("temperature", 0)),
            )

            weather = WeatherData(
                temperature=float(weather_api.get("temperature", 0)),
                humidity=float(weather_api.get("humidity", 0)),
                wind_speed=float(weather_api.get("wind_speed", 0)),
                pressure=float(weather_api.get("pressure", 0)),
            )
        except Exception:
            # If mapping fails, silently continue and rely on advisory values
            pass
    else:
        st.error(
            "❌ Failed to fetch live data from API. Please check:\n"
            f"1. API is running at `{API_PREDICT_URL}`\n"
            "2. Hardware is sending data to the API\n"
            "3. Network connectivity is available"
        )
        # Fallback to demo data on API failure
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
        # Generate advisory locally as fallback
        advisory = generate_full_advisory(sensor, weather, location=location, forecast_hours=4)



# Forecast horizon selector for the weather-style trend view
forecast_hours = st.radio(
    "Forecast Horizon",
    options=[4, 12, 24],
    index=0,
    horizontal=True,
    format_func=lambda hours: f"{hours}-hour view" if hours < 24 else "24-hour day view",
    help="Choose a shorter or day-style AQI forecast",
)

# Generate advisory (demo mode only; hardware mode already has advisory from API)
if use_demo:
    advisory = generate_full_advisory(sensor, weather, location=location, forecast_hours=forecast_hours)



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
    
    # Sensor contributions breakdown (numeric values only)
    st.caption("**Sensor Contributions**")
    contributions = current["sensor_contributions"]
    
    # Filter only numeric contributions for sorting
    numeric_contributions = {
        k: v for k, v in contributions.items() 
        if isinstance(v, (int, float)) and "_aqi" in k
    }
    contrib_sorted = sorted(numeric_contributions.items(), key=lambda x: x[1], reverse=True)
    
    for sensor_name, contrib_value in contrib_sorted:
        sensor_label = sensor_name.replace("_aqi", "").replace("_", " ").title()
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

# ==================== AQI FORECAST SECTION ====================
st.header(f"⏰ {forecast_hours}-Hour AQI Forecast")
st.caption("Weather-style AQI trend view with colored risk bands and forecast cards.")

forecast_data = advisory["forecast"]
peak_forecast = advisory["peak_forecast"]
forecast_df = pd.DataFrame(forecast_data)

# Add presentation helpers
forecast_df["hour_label"] = forecast_df["hour_ahead"].apply(lambda h: f"+{h}h")
forecast_df["aqi_color"] = forecast_df["predicted_aqi"].apply(
    lambda aqi_value: "#2e7d32" if aqi_value <= 50 else
    "#f9a825" if aqi_value <= 100 else
    "#ef6c00" if aqi_value <= 150 else
    "#d32f2f" if aqi_value <= 200 else
    "#6a1b9a"
)
forecast_df["category_short"] = forecast_df["category"].replace({
    "Good": "Good",
    "Moderate": "Moderate",
    "Unhealthy for Sensitive Groups": "Sensitive",
    "Unhealthy": "Unhealthy",
    "Very Unhealthy": "Very Unhealthy",
    "Hazardous": "Hazardous",
})

current_style = (
    "#2e7d32" if aqi <= 50 else
    "#f9a825" if aqi <= 100 else
    "#ef6c00" if aqi <= 150 else
    "#d32f2f" if aqi <= 200 else
    "#6a1b9a"
)

summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
with summary_col1:
    st.metric("Now", f"{aqi}", f"{category}")
with summary_col2:
    st.metric("Peak", f"{peak_forecast['aqi']}", f"+{peak_forecast['hour_ahead']}h")
with summary_col3:
    st.metric("Average", f"{int(forecast_df['predicted_aqi'].mean())}", f"{forecast_hours}h trend")
with summary_col4:
    st.metric("Confidence", f"{int(forecast_df['confidence'].mean())}%", "Model estimate")

forecast_tabs = st.tabs(["Trend", "Forecast Cards", "Table View"])

with forecast_tabs[0]:
    fig_forecast = go.Figure()

    fig_forecast.add_trace(
        go.Scatter(
            x=forecast_df["hour_ahead"],
            y=forecast_df["predicted_aqi"],
            mode="lines+markers+text",
            name="Forecasted AQI",
            line=dict(color=current_style, width=4, shape="spline"),
            marker=dict(size=13, color=forecast_df["aqi_color"], line=dict(width=2, color="white")),
            text=forecast_df["predicted_aqi"],
            textposition="top center",
            hovertemplate="Hour +%{x}<br>AQI: %{y}<extra></extra>",
            fill="tozeroy",
            fillcolor="rgba(33, 150, 243, 0.10)",
        )
    )

    # Add threshold zones for interpretation
    threshold_bands = [
        (0, 50, "rgba(46, 125, 50, 0.08)", "Good"),
        (50, 100, "rgba(249, 168, 37, 0.08)", "Moderate"),
        (100, 150, "rgba(239, 108, 0, 0.08)", "Sensitive"),
        (150, 200, "rgba(211, 47, 47, 0.08)", "Unhealthy"),
        (200, 500, "rgba(106, 27, 154, 0.08)", "Hazardous"),
    ]
    for y0, y1, fillcolor, label in threshold_bands:
        fig_forecast.add_hrect(y0=y0, y1=y1, fillcolor=fillcolor, opacity=1.0, layer="below", line_width=0)
        fig_forecast.add_annotation(x=0.15, xref="paper", y=(y0 + y1) / 2, yref="y", text=label, showarrow=False, font=dict(size=10, color="#6b7280"), xanchor="left")

    fig_forecast.update_layout(
        title=None,
        xaxis=dict(
            title="Hours Ahead",
            tickmode="array",
            tickvals=forecast_df["hour_ahead"],
            ticktext=forecast_df["hour_label"],
            showgrid=False,
            zeroline=False,
        ),
        yaxis=dict(
            title="AQI",
            range=[0, max(150, int(forecast_df["predicted_aqi"].max() * 1.25))],
            showgrid=True,
            gridcolor="rgba(0,0,0,0.07)",
            zeroline=False,
        ),
        template="plotly_white",
        height=390,
        hovermode="x unified",
        showlegend=False,
        margin=dict(l=20, r=20, t=20, b=20),
    )

    st.plotly_chart(fig_forecast, use_container_width=True)

with forecast_tabs[1]:
    step = max(1, len(forecast_df) // 8)
    card_df = forecast_df.iloc[::step].head(8).copy()

    card_cols = st.columns(len(card_df))
    for idx, (_, row) in enumerate(card_df.iterrows()):
        with card_cols[idx]:
            st.markdown(
                f"""
                <div style='padding:1rem;border-radius:1rem;background:linear-gradient(180deg, rgba(255,255,255,0.96), rgba(248,250,252,0.96));border:1px solid rgba(148,163,184,0.18);box-shadow:0 8px 24px rgba(15,23,42,0.06);min-height:170px;'>
                    <div style='font-size:0.9rem;color:#64748b;margin-bottom:0.35rem;'>{row['hour_label']}</div>
                    <div style='font-size:1.8rem;font-weight:700;color:{row['aqi_color']};line-height:1;'>{int(row['predicted_aqi'])}</div>
                    <div style='font-size:0.95rem;font-weight:600;color:#0f172a;margin-top:0.45rem;'>{row['category_short']}</div>
                    <div style='font-size:0.8rem;color:#64748b;margin-top:0.25rem;'>Confidence: {int(row['confidence'])}%</div>
                    <div style='margin-top:0.75rem;height:8px;border-radius:999px;background:rgba(148,163,184,0.18);overflow:hidden;'>
                        <div style='width:{min(100, int(row['predicted_aqi'] / 5 * 100))}%;height:100%;border-radius:999px;background:{row['aqi_color']};'></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

with forecast_tabs[2]:
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


# ==================== AUTO-REFRESH FOOTER ====================
if not use_demo:
    # Hardware mode: show auto-refresh status
    st.divider()
    
    col_refresh_status, col_refresh_time = st.columns([3, 1])
    
    with col_refresh_status:
        refresh_badge = "🟢 Auto-refreshing every 10s" if auto_refresh else "⚪ Manual refresh only"
        st.caption(refresh_badge)
    
    with col_refresh_time:
        time_since_refresh = time.time() - st.session_state.last_refresh
        time_until_next = max(0, 10 - int(time_since_refresh))
        st.caption(f"Next refresh in: {time_until_next}s")
    
    # Auto-rerun after 10 seconds if enabled
    if auto_refresh and time_since_refresh > 10:
        st.session_state.last_refresh = time.time()
        st.cache_data.clear()
        st.rerun()
    elif auto_refresh:
        # Schedule rerun using Streamlit's built-in mechanism
        st.session_state.auto_refresh_enabled = True
