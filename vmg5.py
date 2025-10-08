# ==============================
# 📡 Real-Time GPS Tracker (Streamlit)
# Filters out GPS noise — updates only on real movement
# ==============================

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 Ría Arousa GPS Tracker", layout="centered")
st.title("📡 Real-Time GPS Tracker – Ría Arousa")

st.markdown("""
This app records your live GPS position and shows:
- **Speed (knots)**, **Course (°)**, **Bearing**, **VMG**, **ETA**
- Updates only when movement exceeds a threshold (ignores GPS jitter)
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
selected_wp = st.selectbox("🎯 Select waypoint", list(waypoints.keys()))
wp_lat, wp_lon = waypoints[selected_wp]

# --- Data storage ---
if "data" not in st.session_state:
    st.session_state.data = []

# --- JavaScript for GPS tracking ---
html_code = f"""
<div id="gps-output" style="
  font-family: monospace;
  background-color: #eef;
  padding: 10px;
  border-radius: 10px;
  margin-top: 10px;
  color: #000;">
  Waiting for GPS fix...
</div>

<script>
let lastPos = null;
let lastTime = null;
const MOVE_THRESHOLD = 5; // meters — minimum to consider real movement

// --- Haversine (m) ---
function haversine(lat1, lon1, lat2, lon2) {{
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 +
            Math.cos(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) *
            Math.sin(dLon/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}}

// --- Bearing (°) ---
function bearingTo(lat1, lon1, lat2, lon2) {{
  const y = Math.sin((lon2 - lon1) * Math.PI/180) * Math.cos(lat2 * Math.PI/180);
  const x = Math.cos(lat1 * Math.PI/180) * Math.sin(lat2 * Math.PI/180) -
            Math.sin(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) *
            Math.cos((lon2 - lon1) * Math.PI/180);
  return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
}}

const waypoint = {{lat: {wp_lat}, lon: {wp_lon}}};

navigator.geolocation.watchPosition((pos) => {{
  const lat = pos.coords.latitude;
  const lon = pos.coords.longitude;
  const acc = pos.coords.accuracy;
  const time = new Date();

  if (acc > 30) {{
    document.getElementById("gps-output").innerHTML = "📡 Waiting for accurate fix (±" + acc.toFixed(1) + " m)";
    return;
  }}

  if (lastPos) {{
    const dist = haversine(lastPos.lat, lastPos.lon, lat, lon);
    const dt = (time - lastTime) / 1000;

    if (dist < MOVE_THRESHOLD || dt < 1) {{
      return; // Ignore small jitter or too frequent updates
    }}

    const speedKn = (dist / dt) * 1.94384; // knots
    const course = bearingTo(lastPos.lat, lastPos.lon, lat, lon);
    const bearingWP = bearingTo(lat, lon, waypoint.lat, waypoint.lon);
    const distToWP = haversine(lat, lon, waypoint.lat, waypoint.lon);
    const angleDiff = Math.abs(course - bearingWP);
    const vmg = speedKn * Math.cos(angleDiff * Math.PI / 180);
    const etaMin = (vmg > 0.1) ? (distToWP / (vmg * 0.5144) / 60).toFixed(1) : "∞";

    document.getElementById("gps-output").innerHTML = `
      <b>${{time.toLocaleTimeString()}}</b><br>
      Lat: ${{lat.toFixed(6)}} | Lon: ${{lon.toFixed(6)}} | ±${{acc.toFixed(1)}} m<br>
      Speed: ${{speedKn.toFixed(2)}} kn | Course: ${{course.toFixed(1)}}°<br>
      Bearing→{selected_wp}: ${{bearingWP.toFixed(1)}}° | VMG: ${{vmg.toFixed(2)}} kn<br>
      ETA: ${{etaMin}} min
    `;

    window.parent.postMessage({{
      lat, lon, acc, time: time.toISOString(),
      speedKn, course, bearingWP, vmg, eta: etaMin
    }}, "*");
  }}

  lastPos = {{lat, lon}};
  lastTime = time;

}}, err => {{
  document.getElementById("gps-output").innerHTML = "❌ " + err.message;
}}, {{
  enableHighAccuracy: true,
  maximumAge: 0,
  timeout: 10000
}});
</script>
"""

components.html(html_code, height=240)

# --- Get updates from JS ---
params = st.query_params
if "lat" in params:
    lat = float(params["lat"][0])
    lon = float(params["lon"][0])
    acc = float(params["acc"][0])
    time = params["time"][0]
    speed = float(params.get("speedKn", [0])[0])
    course = float(params.get("course", [0])[0])
    bearing = float(params.get("bearingWP", [0])[0])
    vmg = float(params.get("vmg", [0])[0])
    eta = params.get("eta", ["—"])[0]
    st.session_state.data.append({
        "time": time,
        "lat": lat,
        "lon": lon,
        "acc_m": acc,
        "speed_kn": round(speed, 2),
        "course_deg": round(course, 1),
        "bearing_deg": round(bearing, 1),
        "vmg_kn": round(vmg, 2),
        "eta_min": eta
    })

# --- Display dataframe ---
if len(st.session_state.data) > 0:
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df.tail(10), use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download CSV Log", csv, "gps_log.csv", "text/csv")
else:
    st.info("📡 Waiting for movement or accurate GPS fix...")











