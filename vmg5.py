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
const ACC_THRESHOLD = 20; // meters
let watchId = null;

// --- Waypoint (example: Moscardiño) ---
const waypoint = { lat: 42.5934, lon: -8.8743 };

// --- Haversine distance (m) ---
function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// --- Bearing (°) from point 1 to point 2 ---
function bearingTo(lat1, lon1, lat2, lon2) {
  const y = Math.sin((lon2 - lon1) * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180);
  const x = Math.cos(lat1 * Math.PI / 180) * Math.sin(lat2 * Math.PI / 180) -
            Math.sin(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.cos((lon2 - lon1) * Math.PI / 180);
  return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
}

// --- Angle difference helper (0–180°) ---
function angleDiff(a, b) {
  let d = Math.abs(a - b) % 360;
  return d > 180 ? 360 - d : d;
}

// --- Start tracking ---
function startTracking() {
  const output = document.getElementById("gps-output");
  output.innerHTML = "📡 Waiting for GPS signal...";

  if (!navigator.geolocation) {
    output.innerHTML = "❌ Geolocation not supported.";
    return;
  }

  watchId = navigator.geolocation.watchPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      const acc = pos.coords.accuracy;
      const spd = pos.coords.speed;   // m/s
      const hdg = pos.coords.heading; // degrees
      const time = new Date();

      // --- Ignore poor accuracy ---
      if (acc > ACC_THRESHOLD) {
        output.innerHTML = `⏳ Waiting for accurate fix (±${acc.toFixed(1)} m)...`;
        return;
      }

      const speedKn = spd ? (spd * 1.94384) : 0; // m/s → kn
      const bearingWP = bearingTo(lat, lon, waypoint.lat, waypoint.lon);
      const distWP = haversine(lat, lon, waypoint.lat, waypoint.lon);

      // --- Actual VMG & ETA ---
      const angle = (hdg !== null && !isNaN(hdg)) ? angleDiff(hdg, bearingWP) : 0;
      const vmg = speedKn * Math.cos(angle * Math.PI / 180);
      const etaMin = vmg > 0.1 ? (distWP / (vmg * 0.5144) / 60).toFixed(1) : "∞";

      // --- Virtual courses: +100° and -100° ---
      const coursePlus = (hdg + 100) % 360;
      const courseMinus = (hdg - 100 + 360) % 360;

      // --- Pick nearest to bearing ---
      const diffPlus = angleDiff(coursePlus, bearingWP);
      const diffMinus = angleDiff(courseMinus, bearingWP);
      const virtualCourse = (diffPlus < diffMinus) ? coursePlus : courseMinus;

      // --- Compute VMGvirtual ---
      const angleVirt = angleDiff(virtualCourse, bearingWP);
      const vmgVirtual = speedKn * Math.cos(angleVirt * Math.PI / 180);
      const etaVirtual = vmgVirtual > 0.1 ? (distWP / (vmgVirtual * 0.5144) / 60).toFixed(1) : "∞";

      // --- Display ---
      output.innerHTML = `
        <b>${time.toLocaleTimeString()}</b><br>
        Lat: ${lat.toFixed(6)} | Lon: ${lon.toFixed(6)} | ±${acc.toFixed(1)} m<br>
        Speed: ${speedKn.toFixed(2)} kn | Course: ${hdg ? hdg.toFixed(1) : "—"}°<br>
        Bearing→WP: ${bearingWP.toFixed(1)}° | VMG: ${vmg.toFixed(2)} kn | ETA: ${etaMin} min<br>
        🧭 Virtual Course: ${virtualCourse.toFixed(1)}° | VMGvirtual: ${vmgVirtual.toFixed(2)} kn | ETAvirtual: ${etaVirtual} min
      `;

      // --- Send to Streamlit backend (if needed) ---
      window.parent.postMessage({
        lat, lon, acc, time: time.toISOString(),
        speedKn, course: hdg, bearingWP, vmg, eta: etaMin,
        virtualCourse, vmgVirtual, etaVirtual
      }, "*");
    },
    (err) => {
      output.innerHTML = "❌ " + err.message;
    },
    { enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }
  );
}

// --- Stop tracking ---
function stopTracking() {
  if (watchId !== null) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
    document.getElementById("gps-output").innerHTML = "<b>Tracking stopped.</b>";
  }
}
</script>

"""
components.html(html_code, height=330)













