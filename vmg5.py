import streamlit as st
import pandas as pd
import math
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 GPS Tracker — Ría Arousa", layout="centered")

st.title("📡 Real-Time GPS Tracker — Ría Arousa")
st.markdown("""
Tracks your live GPS position when accuracy ≤ 50 m.  
Shows **Speed (knots)**, **Bearing**, **VMG**, and **ETA** to a selected waypoint.
""")

# ---------------- Waypoints ---------------- #
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

# ---------------- Helper functions ---------------- #
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def bearing_to(lat1, lon1, lat2, lon2):
    y = math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
        math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(lon2 - lon1))
    return (math.degrees(math.atan2(y, x)) + 360) % 360

# ---------------- Session State ---------------- #
if "tracking" not in st.session_state:
    st.session_state.tracking = False
if "data" not in st.session_state:
    st.session_state.data = []

# ---------------- Controls ---------------- #
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

# ---------------- JavaScript GPS Code ---------------- #
if st.session_state.tracking:
    components.html(
        """
        <div id="gps-output" style="font-family: monospace; background:#f5f5f5; padding:10px; border-radius:10px;">
          ⏳ Waiting for GPS fix...
        </div>
        <script>
        let lastSent = 0;
        if (navigator.geolocation) {
          navigator.geolocation.watchPosition(
            (pos) => {
              const acc = pos.coords.accuracy;
              if (acc > 50) return;
              const now = Date.now();
              if (now - lastSent < 1000) return;  // 1-second throttle
              lastSent = now;

              const data = {
                lat: pos.coords.latitude,
                lon: pos.coords.longitude,
                acc: acc,
                time: new Date().toISOString()
              };

              document.getElementById("gps-output").innerHTML =
                `<b>${new Date(data.time).toLocaleTimeString()}</b><br>
                 Lat: ${data.lat.toFixed(6)} | Lon: ${data.lon.toFixed(6)} | ±${acc.toFixed(1)} m`;

              const params = new URLSearchParams(data).toString();
              window.location.search = params; // sends data to Streamlit via query params
            },
            (err) => { document.getElementById("gps-output").innerHTML = "❌ " + err.message; },
            { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
          );
        } else {
          document.getElementById("gps-output").innerHTML = "❌ Geolocation not supported.";
        }
        </script>
        """,
        height=180,
    )

# ---------------- Query Params Handler ---------------- #
params = st.query_params
if "lat" in params and st.session_state.tracking:
    lat = float(params["lat"][0])
    lon = float(params["lon"][0])
    acc = float(params["acc"][0])
    t = params["time"][0]

    # Avoid duplicates
    if not st.session_state.data or st.session_state.data[-1]["time"] != t:
        st.session_state.data.append({"time": t, "lat": lat, "lon": lon, "acc": acc})

# ---------------- Data Processing ---------------- #
if len(st.session_state.data) > 1:
    df = pd.DataFrame(st.session_state.data)
    df["time"] = pd.to_datetime(df["time"])
    df["dt"] = df["time"].diff().dt.total_seconds().fillna(1)
    df["dist_m"] = [haversine(df.lat[i-1], df.lon[i-1], df.lat[i], df.lon[i]) if i > 0 else 0 for i in range(len(df))]
    df["speed_kn"] = (df["dist_m"] / df["dt"] * 1.94384).round(2)
    df["bearing_wp"] = [bearing_to(df.lat[i], df.lon[i], waypoint[0], waypoint[1]) for i in range(len(df))]
    df["dist_wp_m"] = [haversine(df.lat[i], df.lon[i], waypoint[0], waypoint[1]) for i in range(len(df))]
    df["course"] = [bearing_to(df.lat[i-1], df.lon[i-1], df.lat[i], df.lon[i]) if i > 0 else 0 for i in range(len(df))]
    df["vmg_kn"] = (df["speed_kn"] * [
        math.cos(math.radians(df["bearing_wp"].iloc[i] - df["course"].iloc[i])) if i > 0 else 0
        for i in range(len(df))
    ]).round(2)
    df["eta_min"] = [
        round(df["dist_wp_m"].iloc[i] / (df["vmg_kn"].iloc[i] * 0.51444) / 60, 1)
        if df["vmg_kn"].iloc[i] > 0 else None
        for i in range(len(df))
    ]

    st.subheader(f"📊 Live Data — Target: {waypoint_name}")
    st.dataframe(df[["time", "lat", "lon", "acc", "speed_kn", "bearing_wp", "vmg_kn", "eta_min"]].tail(10),
                 use_container_width=True)
    st.map(df[["lat", "lon"]])

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download CSV", csv, "gps_log.csv", "text/csv")

elif st.session_state.tracking:
    st.info("⏳ Waiting for first accurate GPS fix (≤ 50 m)...")
else:
    st.warning("Tracking stopped. Tap ▶️ Start Tracking to begin.")











