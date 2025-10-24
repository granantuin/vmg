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

# --- Inject JavaScript ---
gps_script = f"""
<script>
const ACC_THRESHOLD = 20;
let watchId = null;
const waypoint = {{ lat: {wp_lat}, lon: {wp_lon} }};

// 🎵 Pífano audio setup
let pifanoAudio = new Audio("https://upload.wikimedia.org/wikipedia/commons/8/8a/Fife.ogg"); 
pifanoAudio.loop = true; // constant sound when active
pifanoAudio.volume = 0.6;

// --- Utility functions ---
function haversine(lat1, lon1, lat2, lon2) {{
  const R = 6371000;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2)**2 +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
            Math.sin(dLon / 2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}}

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

  let lastPos = null;
  const MIN_MOVE_DIST = 2;
  const MAX_JUMP_DIST = 200;

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

      if (lastPos) {{
        const distSinceLast = haversine(lat, lon, lastPos.lat, lastPos.lon);
        if (distSinceLast < MIN_MOVE_DIST || distSinceLast > MAX_JUMP_DIST) return;
      }}
      lastPos = {{ lat, lon }};

      const speedKn = spd ? (spd * 1.94384) : 0;
      const bearingWP = bearingTo(lat, lon, waypoint.lat, waypoint.lon);
      const distWP = haversine(lat, lon, waypoint.lat, waypoint.lon);
      const angle = (hdg !== null && !isNaN(hdg)) ? angleDiff(hdg, bearingWP) : 0;
      const vmg = speedKn * Math.cos(angle * Math.PI / 180);
      const etaMin = vmg > 0.1 ? (distWP / (vmg * 0.5144) / 60).toFixed(1) : "∞";

      const coursePlus90 = (hdg + 90) % 360;
      const courseMinus90 = (hdg - 90 + 360) % 360;
      const diffPlus90 = angleDiff(coursePlus90, bearingWP);
      const diffMinus90 = angleDiff(courseMinus90, bearingWP);
      const virtualCourse90 = (diffPlus90 < diffMinus90) ? coursePlus90 : courseMinus90;

      const angleVirt90 = angleDiff(virtualCourse90, bearingWP);
      const vmgVirtual90 = speedKn * Math.cos(angleVirt90 * Math.PI / 180);
      const etaVirtual90 = vmgVirtual90 > 0.1 ? (distWP / (vmgVirtual90 * 0.5144) / 60).toFixed(1) : "∞";

      // 🎶 --- SOUND LOGIC ---
      if (etaMin !== "∞" && etaVirtual90 !== "∞" && parseFloat(etaMin) > parseFloat(etaVirtual90)) {{
          if (pifanoAudio.paused) {{
              pifanoAudio.play().catch(err => console.warn("Audio play failed:", err));
          }}
      }} else {{
          if (!pifanoAudio.paused) {{
              pifanoAudio.pause();
              pifanoAudio.currentTime = 0;
          }}
      }}

      output.innerHTML = `
        <b>${{time.toLocaleTimeString()}}</b><br>
        Rumbo Real: ${{hdg ? hdg.toFixed(0) : "—"}}° | Velocidad: ${{speedKn.toFixed(1)}} kn<br>
        ETA actual: ${{etaMin}} min | ETA si viras 90°: ${{etaVirtual90}} min
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
    pifanoAudio.pause();
    pifanoAudio.currentTime = 0;
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
