import streamlit as st
import pandas as pd
import math
from datetime import datetime
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 GPS Tracker — Ría Arousa", layout="centered")

st.title("📡 Real-Time GPS Tracker — Ría Arousa")
st.markdown("""
Tracks your GPS position live (updates when accuracy ≤ 50 m).  
Computes **Speed (knots)**, **Bearing**, **VMG**, and **ETA** to a selected waypoint.
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

# ---------------- Helper Functions ---------------- #
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

# ---------------- JavaScript for GPS ---------------- #
if st.session_state.tracking:
    st.success("✅ Tracking active — waiting for GPS fix ≤ 50 m...")

    components.html(
        """
        <div id="gps-output" style="font-family:monospace;background:#f7f7f7;
             padding:12px;border-radius:10px;margin-top:10px;">Waiting for GPS...</div>
        <script>
        let watchId = null;
        if (navigator.geolocation) {
          watchId = navigator.geolocation.watchPosition(
            (pos) => {
              const acc = pos.coords.accuracy;
              if (acc > 50) return;
              const lat = pos.coords.latitude;
              const lon = pos.coords.longitude;
              const time = new Date().toISOString();
              const payload = {lat: lat, lon: lon, acc: acc, time: time};
              document.getElementById("gps-output").innerHTML =
                `<b>${new Date(time).toLocaleTimeString()}</b><br>
                 Lat: ${lat.toFixed(6)} | Lon: ${lon.toFixed(6)} | ±${acc.toFixed(1)} m`;
              window.parent.postMessage(payload, "*");
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

# ---------------- Browser → Streamlit Bridge ---------------- #
components.html(
    """
    <script>
    window.addEventListener("message", (event) => {
        const d = event.data;
        if (!d.lat || !d.lon) return;
        const query = new URLSearchParams(d).toString();
        const url = window.location.pathname + "?" + query;
        window.history.replaceState(null, "", url);
    });
    </script>
    """,
    height=0,
)

# ---------------- Capture Parameters ---------------- #
params = st.query_params
if "lat" in params and "lon" in params:
    try:
        lat = float(params["lat"])
        lon = float(params["lon"])
        acc = float(params["acc"])
        t = params["time"]
        if not st.session_state.data or st.session_state.data[-1]["time"] != t:
            st.session_state.data.append({"time": t, "lat": lat, "lon": lon, "acc": acc})
    except Exception:
        pass

# ---------------- Compute + Display ---------------- #
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

    # After computing df and before showing dataframe:
    latest = df.iloc[-1]
    st.markdown(f"""
    <div style="background:#eef; padding:10px; border-radius:10px; font-family:monospace;">
    <b>Last Fix:</b> {latest['time'].strftime('%H:%M:%S')}<br>
    Lat: {latest['lat']:.6f} | Lon: {latest['lon']:.6f} | ±{latest['acc']:.1f} m<br>
    Speed: {latest['speed_kn']:.2f} kn | Bearing→WP: {latest['bearing_wp']:.1f}°<br>
    VMG: {latest['vmg_kn']:.2f} kn | ETA: {latest['eta_min'] if latest['eta_min'] else '—'} min
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader(f"📊 Live Data — Target: {waypoint_name}")
    st.dataframe(df[["time", "lat", "lon", "acc", "speed_kn", "bearing_wp", "vmg_kn", "eta_min"]].tail(10),
                 use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download CSV", csv, "gps_log.csv", "text/csv")

elif st.session_state.tracking:
    st.info("⏳ Waiting for accurate GPS fix (≤ 50 m)...")
else:
    st.warning("Tracking stopped. Tap ▶️ Start Tracking to begin.")







