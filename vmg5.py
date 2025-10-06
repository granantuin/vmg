import streamlit as st
import math
import time
import pandas as pd
import streamlit.components.v1 as components

# --- Streamlit setup ---
st.set_page_config(page_title="⛵ Real-Time Marine Tracker", layout="centered")
st.title("⛵ Real-Time Marine Tracker")

st.markdown("""
This app shows your GPS position, speed (knots), bearing, VMG,  
and estimated time to reach a target waypoint.  
Tap **Start Tracking** to begin and **Stop** to end.
""")

# --- Fixed waypoint (example: Vilagarcía buoy) ---
WAYPOINT = {"lat": 42.5608, "lon": -8.9406}

# --- Session state ---
if "tracking" not in st.session_state:
    st.session_state.tracking = False
if "data" not in st.session_state:
    st.session_state.data = []

# --- Buttons ---
col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Start Tracking"):
        st.session_state.tracking = True
        st.session_state.data = []  # reset log
with col2:
    if st.button("⏹ Stop"):
        st.session_state.tracking = False

# --- Utility functions ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ, Δλ = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(Δφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(Δλ/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def bearing(lat1, lon1, lat2, lon2):
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δλ = math.radians(lon2 - lon1)
    x = math.sin(Δλ) * math.cos(φ2)
    y = math.cos(φ1)*math.sin(φ2) - math.sin(φ1)*math.cos(φ2)*math.cos(Δλ)
    θ = math.atan2(x, y)
    return (math.degrees(θ) + 360) % 360

# --- Tracking section ---
if st.session_state.tracking:
    st.success("✅ Tracking active — updates every second.")
    st.markdown(f"**Waypoint:** {WAYPOINT['lat']:.5f}, {WAYPOINT['lon']:.5f}")

    html_code = """
    <div id="gps-data" style="
        font-family: monospace;
        background-color: #eef;
        padding: 15px;
        border-radius: 10px;
        font-size: 16px;">
      Waiting for GPS data...
    </div>

    <script>
    let lastTime = null, lastLat =













