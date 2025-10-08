import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 FANPI Project", layout="centered")
st.title("📡FANPI Project ")

st.markdown("""
This app reads live GPS data, calculates:
- **Speed (knots)**, **Course (°)**, **Bearing to waypoint (°)**, **VMG**, **ETA**
- Adds a **Virtual Course** (±100° from course) with **VMGv** and **ETAv**
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

# --- Session storage ---
if "data" not in st.session_state:
    st.session_state.data = []

# --- JS HTML Block ---
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

<button id="start-btn" style="margin:5px; padding:8px;">▶️ Start Tracking</button>
<button id="stop-btn" style="margin:5px; padding:8px;">⏹ Stop Tracking</button>

<script>
let tracking = false;
let watchId = null;
let lastPos = null;
let lastTime = null;
const MOVE_THRESHOLD = 3; // meters
const ACC_THRESHOLD = 20; // meters
const waypoint = {{lat: {wp_lat}, lon: {wp_lon}}};

function haversine(lat1, lon1, lat2, lon2) {{
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 +
            Math.cos(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) *
            Math.sin(dLon/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}}

function bearingTo(lat1, lon1, lat2, lon2) {{
  const y = Math.sin((lon2 - lon1) * Math.PI/180) * Math.cos(lat2 * Math.PI/180);
  const x = Math.cos(lat1 * Math.PI/180) * Math.sin(lat2 * Math.PI/180) -
            Math.sin(lat1 * Math.PI/180) * Math.cos(lat2 * Math.PI/180) *
            Math.cos((lon2 - lon1) * Math.PI/180);
  return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
}}

function startTracking() {{
  if (!navigator.geolocation) {{
    document.getElementById("gps-output").innerHTML = "❌ Geolocation not supported.";
    return;
  }}

  tracking = true;
  document.getElementById("gps-output").innerHTML = "📡 Waiting for GPS fix...";

  watchId = navigator.geolocation.watchPosition((pos) => {{
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    const acc = pos.coords.accuracy;
    const time = new Date();

    if (acc > ACC_THRESHOLD) {{
      document.getElementById("gps-output").innerHTML =
        "⏳ Waiting for accurate fix (±" + acc.toFixed(1) + " m)";
      return;
    }}

    let speedKn = 0, course = 0, vmg = 0, etaMin = "∞";
    let vmgVirtual = 0, etaVirtual = "∞", courseVirtual = 0;
    let bearingWP = bearingTo(lat, lon, waypoint.lat, waypoint.lon);
    let distToWP = haversine(lat, lon, waypoint.lat, waypoint.lon);

    if (lastPos) {{
      const dist = haversine(lastPos.lat, lastPos.lon, lat, lon);
      const dt = (time - lastTime) / 1000;
      if (dist >= MOVE_THRESHOLD && dt > 0) {{
        speedKn = (dist / dt) * 1.94384;
        course = bearingTo(lastPos.lat, lastPos.lon, lat, lon);

        const angleDiff = Math.abs(course - bearingWP);
        vmg = speedKn * Math.cos(angleDiff * Math.PI / 180);
        etaMin = (vmg > 0.1) ? (distToWP / (vmg * 0.5144) / 60).toFixed(1) : "∞";

        // Virtual course ±100°
        const left = (course - 100 + 360) % 360;
        const right = (course + 100) % 360;
        const diffL = Math.abs(((bearingWP - left + 540) % 360) - 180);
        const diffR = Math.abs(((bearingWP - right + 540) % 360) - 180);
        courseVirtual = (diffL < diffR) ? left : right;

        const angleDiffVirtual = Math.abs(courseVirtual - bearingWP);
        vmgVirtual = speedKn * Math.cos(angleDiffVirtual * Math.PI / 180);
        etaVirtual = (vmgVirtual > 0.1)
          ? (distToWP / (vmgVirtual * 0.5144) / 60).toFixed(1)
          : "∞";
      }}
    }}

    document.getElementById("gps-output").innerHTML = `
      <b>${{time.toLocaleTimeString()}}</b><br>
      Lat: ${{lat.toFixed(6)}} | Lon: ${{lon.toFixed(6)}} | ±${{acc.toFixed(1)}} m<br>
      Speed: ${{speedKn.toFixed(2)}} kn | Course: ${{course.toFixed(1)}}°<br>
      Bearing→{selected_wp}: ${{bearingWP.toFixed(1)}}° | VMG: ${{vmg.toFixed(2)}} kn | ETA: ${{etaMin}} min<br>
      🧭 Virtual course: ${{courseVirtual.toFixed(1)}}° | VMGv: ${{vmgVirtual.toFixed(2)}} kn | ETAv: ${{etaVirtual}} min
    `;

    // send data to Streamlit
    window.parent.postMessage({{
      lat, lon, acc, time: time.toISOString(),
      speedKn, course, bearingWP, vmg, etaMin,
      courseVirtual, vmgVirtual, etaVirtual
    }}, "*");

    lastPos = {{lat, lon}};
    lastTime = time;
  }},
  (err) => {{
    document.getElementById("gps-output").innerHTML = "❌ " + err.message;
  }},
  {{
    enableHighAccuracy: true,
    maximumAge: 0,
    timeout: 10000
  }});
}}

function stopTracking() {{
  if (watchId) {{
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
  }}
  tracking = false;
  document.getElementById("gps-output").innerHTML = "⏹ Tracking stopped.";
}}

document.getElementById("start-btn").onclick = startTracking;
document.getElementById("stop-btn").onclick = stopTracking;
</script>
"""
components.html(html_code, height=330)












