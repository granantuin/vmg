import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(page_title="⛵ Real-Time Marine Tracker", layout="centered")

st.title("⛵ Real-Time Marine Tracker")
st.markdown("""
Records and displays your GPS position every second (client-side).  
Shows speed [knots], bearing, VMG, and ETA to waypoint.  
When you stop, you can download the recorded log.
""")

# --- Fixed waypoint (Vilagarcía buoy example) ---
WAYPOINT = {"lat": 42.5608, "lon": -8.9406}

# --- Session state ---
if "data" not in st.session_state:
    st.session_state.data = []

# --- Utility JS/HTML ---
html_code = f"""
<div id="status" style="background:#eef;padding:10px;border-radius:10px;margin-bottom:10px;font-family:monospace;"></div>
<div id="table" style="font-family:monospace;font-size:14px;"></div>

<script>
let tracking = false;
let data = [];
let lastTime = null;
let waypoint = {{lat:{WAYPOINT['lat']}, lon:{WAYPOINT['lon']}}};

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
             <td>${{r.spd.toFixed(2)}}</td><td>${{r.brg.toFixed(1)}}</td>
             <td>${{r.vmg.toFixed(2)}}</td><td>${{r.eta.toFixed(1)}}</td></tr>`;
  }});
  html += "</table>";
  document.getElementById("table").innerHTML = html;
}}

function start(){{
  if(!navigator.geolocation){{
    document.getElementById("status").innerText="❌ Geolocation not supported.";
    return;
  }}
  document.getElementById("status").innerText="✅ Tracking started...";
  tracking = true;
  navigator.geolocation.watchPosition((pos)=>{{
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    const now = new Date();
    let spd=0, brg=0, vmg=0, eta=0;
    if(data.length>0){{
      const last=data[data.length-1];
      const dt=(now-last.jsTime)/1000;
      if(dt>0){{
        const dist=haversine(last.lat,last.lon,lat,lon);
        spd = dist/dt*1.94384; // knots
        brg = bearing(lat,lon,waypoint.lat,waypoint.lon);
        const distWP = haversine(lat,lon,waypoint.lat,waypoint.lon);
        vmg = spd*Math.cos((brg*Math.PI)/180);
        eta = (distWP/(spd*0.5144))/60; // min
      }}
    }}
    data.push({{time: now.toLocaleTimeString(), lat, lon, spd, brg, vmg, eta, jsTime: now}});
    updateTable();
  }},(err)=>{{
    document.getElementById("status").innerText="❌ "+err.message;
  }},{{enableHighAccuracy:true}});
}}

function stop(){{
  tracking=false;
  document.getElementById("status").innerText="⏹ Tracking stopped.";
  const csv = "data:text/csv;charset=utf-8," + 
              ["time,lat,lon,speed_knots,bearing,vmg,eta_min"].concat(
                data.map(d=>[d.time,d.lat,d.lon,d.spd.toFixed(2),d.brg.toFixed(1),d.vmg.toFixed(2),d.eta.toFixed(1)].join(","))
              ).join("\\n");
  const link = document.createElement("a");
  link.href = encodeURI(csv);
  link.download = "gps_track.csv";
  link.innerText="💾 Download CSV";
  document.getElementById("table").appendChild(document.createElement("br"));
  document.getElementById("table").appendChild(link);
}}

</script>

<button onclick="start()" style="margin:5px;font-size:16px;">▶️ Start</button>
<button onclick="stop()" style="margin:5px;font-size:16px;">⏹ Stop</button>
"""

components.html(html_code, height=500)



















