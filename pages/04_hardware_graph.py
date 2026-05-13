"""
Hardware Input Graph Visualization
Shows sensor hardware architecture as interactive network graph
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.predictor import LocationContext, SensorReading, WeatherData, generate_full_advisory

# ==================== PAGE CONFIG ====================
st.set_page_config(page_title="Hardware Architecture", page_icon="🏗️", layout="wide")

col_header_left, col_header_right = st.columns([3, 1])
with col_header_left:
    st.title("🏗️ Hardware Input Architecture")
    st.caption("Interactive sensor network visualization with parameter details")
with col_header_right:
    st.metric("Last Updated", datetime.now().strftime("%H:%M:%S"), label_visibility="collapsed")

st.divider()

# ==================== DEMO DATA ====================
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

location = LocationContext(latitude=23.0225, longitude=72.5714)

# ==================== HARDWARE GRAPH STRUCTURE ====================
# Define the hardware architecture as nodes and edges
hardware_nodes = {
    "ESP32": {
        "label": "ESP32 Microcontroller",
        "type": "controller",
        "color": "#1f77b4",
        "params": {
            "Device": "ESP32",
            "Function": "Main Control Unit",
            "Protocol": "WiFi/Serial",
        }
    },
    "MQ135": {
        "label": "MQ135 Sensor",
        "type": "sensor",
        "color": "#ff7f0e",
        "params": {
            "Sensor": "MQ135",
            "Measurement": "Air Quality (PPM)",
            "ADC Value": f"{sensor.mq135_adc}",
            "PPM": f"{sensor.air_quality_ppm:.2f}",
            "Range": "0-1000 ppm",
            "Protocol": "Analog (ADC)",
        }
    },
    "MQ7": {
        "label": "MQ7 Sensor",
        "type": "sensor",
        "color": "#ff7f0e",
        "params": {
            "Sensor": "MQ7",
            "Measurement": "CO (PPM)",
            "ADC Value": f"{sensor.mq7_adc}",
            "PPM": f"{sensor.co_ppm:.3f}",
            "Range": "0-1000 ppm",
            "Protocol": "Analog (ADC)",
        }
    },
    "Dust": {
        "label": "Dust Sensor",
        "type": "sensor",
        "color": "#ff7f0e",
        "params": {
            "Sensor": "Dust Density",
            "Measurement": "PM2.5 (µg/m³)",
            "ADC Value": f"{sensor.dust_adc}",
            "Voltage": f"{sensor.dust_voltage:.2f}V",
            "Estimated PM2.5": f"{sensor.estimated_pm25:.2f}",
            "Formula": "(170V - 0.1) µg/m³",
        }
    },
    "DHT": {
        "label": "DHT Sensor",
        "type": "sensor",
        "color": "#ff7f0e",
        "params": {
            "Sensor": "DHT22",
            "Measurement": "Temperature & Humidity",
            "Temperature": f"{sensor.temperature:.2f}°C",
            "Range": "-40 to 80°C",
            "Protocol": "Digital (1-Wire)",
        }
    },
    "GPS": {
        "label": "GPS Module",
        "type": "sensor",
        "color": "#2ca02c",
        "params": {
            "Module": "GPS Receiver",
            "Latitude": f"{location.latitude:.5f}",
            "Longitude": f"{location.longitude:.5f}",
            "Accuracy": "±5m",
            "Protocol": "UART/Serial",
        }
    },
    "MongoDB": {
        "label": "MongoDB Cloud",
        "type": "database",
        "color": "#13aa52",
        "params": {
            "Database": "MongoDB Atlas",
            "Collection": "sensor_readings",
            "Index": "GeoJSON (2dsphere)",
            "Backup": "Automatic",
        }
    },
    "API": {
        "label": "Render API",
        "type": "backend",
        "color": "#d62728",
        "params": {
            "Service": "Render FastAPI",
            "Endpoint": "/ingest, /predict",
            "Protocol": "HTTPS REST",
            "Status": "Active",
        }
    },
}

# Define edges (connections between nodes)
edges = [
    ("MQ135", "ESP32"),
    ("MQ7", "ESP32"),
    ("Dust", "ESP32"),
    ("DHT", "ESP32"),
    ("GPS", "ESP32"),
    ("ESP32", "API"),
    ("API", "MongoDB"),
]

# ==================== GRAPH LAYOUT ====================
# Position nodes in a hierarchical layout
positions = {
    # Sensors at bottom
    "MQ135": (0, 0),
    "MQ7": (1, 0),
    "Dust": (2, 0),
    "DHT": (3, 0),
    "GPS": (4, 0),
    
    # ESP32 in middle
    "ESP32": (2, 1.5),
    
    # Backend services
    "API": (2, 3),
    "MongoDB": (2, 4.5),
}

# ==================== BUILD PLOTLY GRAPH ====================
fig = go.Figure()

# Add edges as lines
edge_x = []
edge_y = []
for start, end in edges:
    x0, y0 = positions[start]
    x1, y1 = positions[end]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

fig.add_trace(go.Scatter(
    x=edge_x, y=edge_y,
    mode='lines',
    line=dict(width=2, color='#888'),
    hoverinfo='none',
    showlegend=False,
    name='Connections',
))

# Add nodes
node_x = []
node_y = []
node_text = []
node_color = []
node_size = []
node_label = []

for node_id, pos in positions.items():
    node_x.append(pos[0])
    node_y.append(pos[1])
    node_info = hardware_nodes[node_id]
    node_label.append(node_id)
    node_color.append(node_info["color"])
    node_text.append(node_info["label"])
    node_size.append(40 if node_info["type"] == "controller" else 35 if node_info["type"] == "sensor" else 38)

fig.add_trace(go.Scatter(
    x=node_x, y=node_y,
    mode='markers+text',
    text=node_label,
    textposition="middle center",
    textfont=dict(size=10, color='white', family='Arial Black'),
    hovertext=node_text,
    hoverinfo='text',
    marker=dict(
        size=node_size,
        color=node_color,
        line=dict(width=2, color='white'),
    ),
    name='Hardware Nodes',
))

fig.update_layout(
    title='Hardware Architecture Graph',
    showlegend=False,
    hovermode='closest',
    margin=dict(b=20, l=5, r=5, t=40),
    annotations=[
        dict(
            text="Click/hover on nodes to view details →",
            x=0, y=-0.15,
            xref='paper', yref='paper',
            showarrow=False,
            font=dict(size=12, color='gray')
        )
    ],
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    plot_bgcolor='rgba(240, 240, 240, 0.5)',
    height=500,
)

st.plotly_chart(fig, use_container_width=True, key="hardware_graph")

st.divider()

# ==================== NODE DETAILS SECTION ====================
st.header("📋 Node Parameters")

col1, col2 = st.columns([1, 3])

with col1:
    selected_node = st.selectbox(
        "Select Hardware Component",
        options=list(hardware_nodes.keys()),
        format_func=lambda x: f"{x} - {hardware_nodes[x]['label']}"
    )

with col2:
    node_info = hardware_nodes[selected_node]
    st.subheader(f"🔹 {node_info['label']}")
    
    # Display parameters as a table
    params_df = pd.DataFrame(
        list(node_info['params'].items()),
        columns=["Parameter", "Value"]
    )
    
    st.dataframe(
        params_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Parameter": st.column_config.TextColumn("Parameter", width="medium"),
            "Value": st.column_config.TextColumn("Value", width="large"),
        }
    )

st.divider()

# ==================== SENSOR DATA TABLE ====================
st.header("📊 Current Sensor Readings")

sensor_table_data = {
    "Sensor": ["MQ135", "MQ7", "Dust", "DHT22", "GPS"],
    "Measurement": [
        f"{sensor.air_quality_ppm:.2f} PPM",
        f"{sensor.co_ppm:.3f} PPM",
        f"{sensor.estimated_pm25:.2f} µg/m³",
        f"{sensor.temperature:.2f}°C",
        f"Lat: {location.latitude:.5f}°",
    ],
    "Status": ["✅ Active", "✅ Active", "✅ Active", "✅ Active", "✅ Active"],
}

sensor_df = pd.DataFrame(sensor_table_data)
st.dataframe(sensor_df, use_container_width=True, hide_index=True)

st.divider()

# ==================== DATA FLOW SECTION ====================
st.header("🔄 Data Flow Path")

flow_steps = [
    ("🔌 **Sensors**", "MQ135, MQ7, Dust, DHT22, GPS collect raw data"),
    ("🎮 **ESP32**", "Processes analog signals, performs calibration"),
    ("📡 **WiFi/Serial**", "Transmits data via HTTPS to cloud"),
    ("☁️ **Render API**", "/ingest endpoint receives batch sensor data"),
    ("📀 **MongoDB**", "Stores with GeoJSON for location-based queries"),
    ("📊 **Dashboard**", "Real-time visualization & analytics"),
]

for i, (step, description) in enumerate(flow_steps, 1):
    col_step, col_desc = st.columns([0.15, 0.85])
    with col_step:
        st.write(f"**{i}**")
    with col_desc:
        st.write(f"{step}  \n*{description}*")
    if i < len(flow_steps):
        st.write("**↓**")

st.divider()

# ==================== SPECIFICATIONS ====================
st.header("⚙️ Hardware Specifications")

spec_cols = st.columns(3)

with spec_cols[0]:
    st.subheader("Air Quality Sensors")
    st.write("""
    - **MQ135**: VOC/NH₃/CO₂ detector (0-1000 ppm)
    - **MQ7**: CO detector (0-1000 ppm)
    - **Dust Sensor**: PM2.5 (0-500 µg/m³)
    """)

with spec_cols[1]:
    st.subheader("Environmental Sensors")
    st.write("""
    - **DHT22**: Temperature (-40 to 80°C)
    - **DHT22**: Humidity (0-100%)
    - **GPS**: Location ±5m accuracy
    """)

with spec_cols[2]:
    st.subheader("Connectivity")
    st.write("""
    - **Protocol**: WiFi 802.11 b/g/n
    - **Baud Rate**: 115200
    - **Cloud**: MongoDB Atlas
    - **API**: Render FastAPI
    """)
