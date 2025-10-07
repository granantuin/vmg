import streamlit as st
import pandas as pd
import math
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 GPS Tracker — Ría Arousa", layout="centered")

st.title("📡 Real-Time GPS Tracker — Ría Arousa")
st.markdown("""
Track your GPS position every second (with high accuracy).  
Select a waypoint to compute bearing, VMG, and ETA.
""")

# --- Waypoints ---
waypoints = {
    "Rua Norte": (42.5521, -8.9403),
    "Rua Sur": (42.5477, -8.9387),
    "Maño": (42.5701, -8.9247),
    "Ter": (42.5737, -8.8982),
    "Seixo": (42.5855, -8.8469),
    "Moscardiño": (42.5934, -8.8743),
    "Aurora": (42.6021, -8.8064),
    "Ostreira": (42.5946, -8.9134),
    "Capitán": (42.5185, -8.9799),
}

# --- Helper functions ---
def haversine(lat1, lon1, lat2, lon2):
    """Distance (m) between two lat/lon points"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def bearing_to(lat1, lon1, lat2, lon2):
    """Bearing in degrees from point A to point B"""
    y = math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1))*math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1))*math.cos(math.radians(lat2))*math.cos(math.radians(lon2 - lon1))
    return (math.degrees(math.atan2(y, x)) + 360) % 360

# --- Session state ---
if "tracking" not in st.session_state:
    st.session_state.tracking = False
if "data" not in st.session_state:
    st.session_state.data = []

# --- UI Controls ---
waypoint_name = st.selectbox("📍 Select Waypoint", list(waypoints.keys()))
waypoint = waypoints[waypoint_name]

col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Start Tracking"):
        st.session_state.tracking = True
        st.session_state.data = []
with col2:
    if st.button("⏹ Stop Tracking"):
        st.session_state.tracking = False

# --- JavaScript for geolocation tracking ---
if st.session_state.tracking:
    st.success("✅ Tracking active (waiting for GPS fix...)")

    components.html(
        """
        <div id="gps-output" style="font-family: monospace; background:#f0f0f0; padding:10px; border-radius:10px;">
          Waiting for GPS data...
        </div>
        <script>
        let watchId = null;
        if (navigator.geolocation) {
          watchId = navigator.geolocation.watchPosition(
            (pos) => {
              const acc = pos.coords.accuracy;

















