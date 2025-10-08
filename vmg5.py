# ======================================
# 📡 Real-Time GPS Tracker – Ría Arousa (Virtual Course)
# ======================================

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 GPS Tracker + Virtual Course", layout="centered")
st.title("📡 Real-Time GPS Tracker – Virtual Course")

st.markdown("""
Tracks your live GPS position and calculates:
- **Speed**, **Course**, **Bearing to waypoint**, **VMG**, **ETA**
- Adds a **Virtual Course** ±100° from actual heading, and computes **VMGvirtual** & **ETAvirtual**
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

# --- Session state ---
if "tracking" not in st.session_state:
    st.session_state.tracking = False
if "data" not in st.session_state:
    st.session_state.data = []

# --- Control buttons ---
col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Start Tracking"):
        st.session_state.tracking = True
with col2:
    if st.button("⏹ Stop Tracking"):
        st.session_state.tracking = False

# --- Status ---
if st.session_state.tracking:
    st.success("✅ Tracking active — receiving GPS data...")
else:
    st.warning("⏹ Tracking stopped. Tap ▶️ to start.")

# --- JavaScript GPS logic ---
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
let tracking = {str(st.session_state.tracking).lower()};
let lastPos = null;
let lastTime = null;
const MOVE_THRESHOLD = 5;  // meters
const waypoint = {{lat: {wp_lat}, lon: {wp_lon}}};  // target waypoint

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

let watchId = null;

function startTracking() {{
  if (!navigator.geolocation) {{
    document.getElementById("gps-output").innerHTML = "❌ Geolocation not supported.";
    return;
  }}
  watchId = navigator.geolocation.watchPosition((pos) => {{
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    const acc = pos.coords.accuracy;
    const time = new Date();

    if (acc > 30) {{
      document.getElementById("gps-output").innerHTML =
        "📡 Waiting for accurate fix (±" + acc.toFixed(1) + " m)";
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

        // --- VMG & ETA (actual) ---
        const angleDiff = Math.abs(course - bearingWP);
        vmg = speedKn * Math.cos(angleDiff * Math.PI / 180);
        etaMin = (vmg > 0.1) ? (distToWP / (vmg * 0.5144) / 60).toFixed(1) : "∞";

        // --- Virtual Course logic ---
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
    document.getElementById("gps-output").innerHTML = "<b>Tracking stopped.</b>";
  }}
}}

if (tracking) startTracking();
else stopTracking();
</script>
"""

components.html(html_code, height=300)

# --- Handle updates ---
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
    eta = params.get("etaMin", ["—"])[0]
    course_virtual = float(params.get("courseVirtual", [0])[0])
    vmg_virtual = float(params.get("vmgVirtual", [0])[0])
    eta_virtual = params.get("etaVirtual", ["—"])[0]

    st.session_state.data.append({
        "time": time,
        "lat": lat,
        "lon": lon,
        "acc_m": acc,
        "speed_kn": round(speed, 2),
        "course_deg": round(course, 1),
        "bearing_deg": round(bearing, 1),
        "vmg_kn": round(vmg, 2),
        "eta_min": eta,
        "course_virtual": round(course_virtual, 1),
        "vmg_virtual": round(vmg_virtual, 2),
        "eta_virtual": eta_virtual
    })

# --- Show table ---
if len(st.session_state.data) > 0:
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df.tail(10), use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download CSV Log", csv, "gps_log.csv", "text/csv")
else:
    st.info("📡 Waiting for GPS fix...")












