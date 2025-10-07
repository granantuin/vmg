import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 GPS Tracker with Waypoints", layout="centered")

st.title("📡 Real-Time GPS Tracker (1 record/s with Waypoints)")
st.markdown("""
This app records your **position every second** and computes:
- Speed (knots)
- Bearing to selected waypoint
- VMG (Velocity Made Good)
- ETA (minutes)

Select a waypoint from the table below, tap **Start** to begin, and **Stop** to finish.
""")

# --- Define waypoints ---
waypoints = {
    "Rua Norte": (42.5521, -8.9403),
    "Rua Sur": (42.5477, -8.9387),
    "Maño": (42.5701, -8.9247),
    "Ter": (42.5737, -8.8982),
    "Seixo": (42.5855, -8.8469),
    "Moscardiño": (42.5934, -8.8743),
    "Aurora":(42.6021,-8.8064),
    "Ostreira":(42.5946,-8.9134),
    "Capitán":(42.5185,-89799),
}

st.subheader("📍 Select Waypoint")
selected_wp = st.selectbox("Choose a destination:", list(waypoints.keys()))
lat_wp, lon_wp = waypoints[selected_wp]
st.write(f"**Selected waypoint:** {selected_wp} — 🌍 Lat: {lat_wp:.5f}, Lon: {lon_wp:.5f}")

# --- Convert to JS for HTML component ---
html_code = f"""
<div id="status" style="font-weight:bold;color:#006400;margin-top:10px;">
  Waiting to start...
</div>

<div style="margin-top:10px;">
  <button onclick="startTracking()" style="background-color:#4CAF50;color:white;padding:10px 20px;border:none;border-radius:8px;">▶️ Start</button>
  <button onclick="stopTracking()" style="background-color:#d9534f;color:white;padding:10px 20px;border:none;border-radius:8px;">⏹ Stop</button>
</div>

<div id="table" style="margin-top:15px;font-family:monospace;font-size:15px;"></div>

<script>
let intervalID = null;
let tracking = false;
let data = [];
let lastPos = null;
let lastLoggedSecond = null;

// Waypoint selected from Streamlit
let waypoint = {{lat: {lat_wp}, lon: {lon_wp}}};

function haversine(lat1, lon1, lat2, lon2){{
  const R = 6371000;
  const φ1 = lat1*Math.PI/180, φ2 = lat2*Math.PI/180;
  const dφ = (lat2-lat1)*Math.PI/180, dλ = (lon2-lon1)*Math.PI/180;
  const a = Math.sin(dφ/2)**2 + Math.cos(φ1)*Math.cos(φ2)*Math.sin(dλ/2)**2;
  return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
}}
function bearing(lat1, lon1, lat2, lon2){{
  const φ1=lat1*Math.PI/180, φ2=lat2*Math.PI/180, Δλ=(lon2-lon1)*Math.PI/180;
  const x=Math.sin(Δλ)*Math.cos(φ2);
  const y=Math.cos(φ1)*Math.sin(φ2)-Math.sin(φ1)*Math.cos(φ2)*Math.cos(Δλ);
  return (Math.atan2(x,y)*180/Math.PI+360)%360;
}}

function updateTable(){{
  let html = "<b>Last 10 records</b><br><table border='1' cellspacing='0' cellpadding='3'><tr><th>Time</th><th>Lat</th><th>Lon</th><th>Speed(kn)</th><th>Bearing</th><th>VMG</th><th>ETA(min)</th></tr>";
  const last = data.slice(-10);
  last.forEach(r=>{{
    html += `<tr><td>${{r.time}}</td><td>${{r.lat.toFixed(5)}}</td><td>${{r.lon.toFixed(5)}}</td>
             <td>${{r.spd ? r.spd.toFixed(2) : "—"}}</td><td>${{r.brg.toFixed(1)}}</td>
             <td>${{r.vmg ? r.vmg.toFixed(2) : "—"}}</td><td>${{r.eta ? r.eta.toFixed(1) : "—"}}</td></tr>`;
  }});
  html += "</table>";
  document.getElementById("table").innerHTML = html;
}}

function recordPosition(){{
  if(!tracking) return;
  navigator.geolocation.getCurrentPosition((pos)=>{{
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    const now = new Date();
    const thisSecond = now.getSeconds();
    if(thisSecond === lastLoggedSecond) return;
    lastLoggedSecond = thisSecond;

    let spd=0, brg=0, vmg=0, eta=null;
    if(lastPos){{
      const dt = (now - lastPos.time)/1000;
      const dist = haversine(lastPos.lat,lastPos.lon,lat,lon);
      const speed_ms = dist/dt;
      spd = speed_ms * 1.94384;
      brg = bearing(lat,lon,waypoint.lat,waypoint.lon);
      const distWP = haversine(lat,lon,waypoint.lat,waypoint.lon);
      vmg = spd * Math.cos((brg*Math.PI)/180);
      eta = speed_ms>0 ? (distWP/(speed_ms*60)) : null;
    }}
    lastPos = {{lat, lon, time: now}};
    data.push({{time: now.toLocaleTimeString(), lat, lon, spd, brg, vmg, eta}});
    updateTable();
  }},(err)=>{{
    document.getElementById("status").innerText="❌ "+err.message;
  }},{{enableHighAccuracy:true}});
}}

function startTracking(){{
  if(!navigator.geolocation){{
    document.getElementById("status").innerText="❌ Geolocation not supported.";
    return;
  }}
  document.getElementById("status").innerText="✅ Tracking started toward {selected_wp}";
  tracking = true;
  lastLoggedSecond = null;
  intervalID = setInterval(recordPosition, 1000);
}}

function stopTracking(){{
  tracking = false;
  clearInterval(intervalID);
  document.getElementById("status").innerText="⏹ Tracking stopped.";
  const csv = "data:text/csv;charset=utf-8," +
              ["time,lat,lon,speed_knots,bearing,vmg,eta_min"].concat(
                data.map(d=>[d.time,d.lat,d.lon,
                             (d.spd||0).toFixed(2),
                             d.brg.toFixed(1),
                             (d.vmg||0).toFixed(2),
                             (d.eta||0).toFixed(1)].join(","))
              ).join("\\n");
  const link = document.createElement("a");
  link.href = encodeURI(csv);
  link.download = "gps_track.csv";
  link.innerText="💾 Download CSV";
  document.getElementById("table").appendChild(document.createElement("br"));
  document.getElementById("table").appendChild(link);
}}
</script>
"""

components.html(html_code, height=600)
















