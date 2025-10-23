import streamlit as st
import pandas as pd

st.set_page_config(page_title="VMG Tracker", layout="centered")

st.title("🧭PÍFANO")

# --- Waypoints ---
waypoints = {
    "Rua Norte": (42.5521, -8.9403),
    "Rua Sur": (42.5477, -8.9387),
    "Maño": (42.5701, -8.9247),
    "Ter": (42.5735, -8.8983),
    "Seixo": (42.5855, -8.8469),
    "Moscardiño": (42.5934, -8.8743),
    "Aurora": (42.6021, -8.8064),
    "Ostreira": (42.5946, -8.9134),
    "Castro": (42.5185, -8.9799),
}

# --- Waypoint selector ---
wp_name = st.selectbox("Selecionar Waypoint", list(waypoints.keys()))
wp_lat, wp_lon = waypoints[wp_name]


# --- HTML container for JS output ---
#st.markdown("### Live GPS Data")

# --- Inject JavaScript safely ---
gps_script = f"""
<script>
const ACC_THRESHOLD = 20; // meters
let watchId = null;
const waypoint = {{ lat: {wp_lat}, lon: {wp_lon} }};

// Haversine distance
function haversine(lat1, lon1, lat2, lon2) {{
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2)**2 +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}}

// Bearing calculation
function bearingTo(lat1, lon1, lat2, lon2) {{
  const y = Math.sin((lon2 - lon1) * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180);
  const x = Math.cos(lat1 * Math.PI / 180) * Math.sin(lat2 * Math.PI / 180) -
            Math.sin(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.cos((lon2 - lon1) * Math.PI / 180);
  return (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
}}

function angleDiff(a, b) {{
  let d = Math.abs(a - b) % 360;
  return d > 180 ? 360 - d : d;
}}

function startTracking() {{
  const output = document.getElementById("gps-output");
  output.innerHTML = "📡 Waiting for GPS signal...";

  if (!navigator.geolocation) {{
    output.innerHTML = "❌ Geolocation not supported.";
    return;
  }}

  const MIN_MOVE_DIST = 2;  // meters — ignore smaller movements
  const MAX_JUMP_DIST = 200; // meters — ignore large GPS jumps
  let lastPos = null;

  watchId = navigator.geolocation.watchPosition(
    (pos) => {{
      const lat = pos.coords.latitude;
      const lon = pos.coords.longitude;
      const acc = pos.coords.accuracy;
      const spd = pos.coords.speed;
      const hdg = pos.coords.heading;
      const time = new Date();

      if (acc > ACC_THRESHOLD) {{
        output.innerHTML = `⏳ Waiting for accurate fix (±${{acc.toFixed(1)}} m)...`;
        return;
      }}

      // Reject noisy GPS updates
      if (lastPos) {{
        const distSinceLast = haversine(lat, lon, lastPos.lat, lastPos.lon);
        if (distSinceLast < MIN_MOVE_DIST) {{
          // Too small — likely GPS jitter
          return;
        }}
        if (distSinceLast > MAX_JUMP_DIST) {{
          // Too large — likely GPS glitch
          console.warn("⚠️ Ignored unrealistic GPS jump:", distSinceLast, "m");
          return;
        }}
      }}

      // Update last position after valid move
      lastPos = {{ lat, lon }};

      const speedKn = spd ? (spd * 1.94384) : 0;
      const bearingWP = bearingTo(lat, lon, waypoint.lat, waypoint.lon);
      const distWP = haversine(lat, lon, waypoint.lat, waypoint.lon);
      const angle = (hdg !== null && !isNaN(hdg)) ? angleDiff(hdg, bearingWP) : 0;
      const vmg = speedKn * Math.cos(angle * Math.PI / 180);
      const etaMin = vmg > 0.1 ? (distWP / (vmg * 0.5144) / 60).toFixed(1) : "∞";

      const coursePlus100 = (hdg + 100) % 360;
      const courseMinus100 = (hdg - 100 + 360) % 360;
      const diffPlus100 = angleDiff(coursePlus100, bearingWP);
      const diffMinus100 = angleDiff(courseMinus100, bearingWP);
      const virtualCourse100 = (diffPlus100 < diffMinus100) ? coursePlus100 : courseMinus100;

      const angleVirt100 = angleDiff(virtualCourse100, bearingWP);
      const vmgVirtual100 = speedKn * Math.cos(angleVirt100 * Math.PI / 180);
      const etaVirtual100 = vmgVirtual100 > 0.1 ? (distWP / (vmgVirtual100 * 0.5144) / 60).toFixed(1) : "∞";

      const coursePlus90 = (hdg + 90) % 360;
      const courseMinus90 = (hdg - 90 + 360) % 360;
      const diffPlus90 = angleDiff(coursePlus90, bearingWP);
      const diffMinus90 = angleDiff(courseMinus90, bearingWP);
      const virtualCourse90 = (diffPlus90 < diffMinus90) ? coursePlus90 : courseMinus90;

      const angleVirt90 = angleDiff(virtualCourse90, bearingWP);
      const vmgVirtual90 = speedKn * Math.cos(angleVirt90 * Math.PI / 180);
      const etaVirtual90 = vmgVirtual90 > 0.1 ? (distWP / (vmgVirtual90 * 0.5144) / 60).toFixed(1) : "∞";

      output.innerHTML = `
        <b>${{time.toLocaleTimeString()}}</b><br>
        Rumbo Real: ${{hdg ? hdg.toFixed(0) : "—"}}°| Velocidad: ${{speedKn.toFixed(1)}} kn  <br>
        Rumbo al waypoint: ${{bearingWP.toFixed(0)}}°| Tiempo al waypoint: ${{etaMin}} min<br>
        Rumbo si viramos 90 grados: ${{virtualCourse90.toFixed(0)}}° | Tiempo al waypoint con el nuevo rumbo: ${{etaVirtual90}} min
      `;
    }},
    (err) => {{
      output.innerHTML = "❌ " + err.message;
    }},
    {{ enableHighAccuracy: true, maximumAge: 0, timeout: 10000 }}
  );
}}

function stopTracking() {{
  if (watchId !== null) {{
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
    document.getElementById("gps-output").innerHTML = "<b>Tracking stopped.</b>";
  }}
}}
</script>

<div style="padding:10px;">
  <div id="gps-output">Waiting...</div>
  <button onclick="startTracking()">▶️ Start</button>
  <button onclick="stopTracking()">⏹️ Stop</button>
</div>
"""

st.components.v1.html(gps_script, height=600)



























