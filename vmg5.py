import streamlit as st
import math
import time
import pandas as pd
import streamlit.components.v1 as components

# --- Streamlit setup ---
st.set_page_config(page_title="⛵ Real-Time Marine Tracker", layout="centered")
st.title("⛵ Real-Time Marine Tracker")

st.markdown("""
This app shows your GPS position, speed (knots), bearing, VMG,  
and estimated time to reach a target waypoint.  
Tap **Start Tracking** to begin and **Stop** to end.
""")

# --- Fixed waypoint (change this to your destination) ---
WAYPOINT = {"lat": 42.5608, "lon": -8.9406}  # Example: Vilagarcía buoy

# --- Session state ---
if "tracking" not in st.session_state:
    st.session_state.tracking = False
if "data" not in st.session_state:
    st.session_state.data = []

# --- Buttons ---
col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Start Tracking"):
        st.session_state.tracking = True
with col2:
    if st.button("⏹ Stop"):
        st.session_state.tracking = False

# --- Utility functions ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ, Δλ = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(Δφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(Δλ/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def bearing(lat1, lon1, lat2, lon2):
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δλ = math.radians(lon2 - lon1)
    x = math.sin(Δλ) * math.cos(φ2)
    y = math.cos(φ1)*math.sin(φ2) - math.sin(φ1)*math.cos(φ2)*math.cos(Δλ)
    θ = math.atan2(x, y)
    return (math.degrees(θ) + 360) % 360

# --- Main tracking ---
if st.session_state.tracking:
    st.success("✅ Tracking active — updating every second.")
    st.markdown(f"**Waypoint:** {WAYPOINT['lat']:.5f}, {WAYPOINT['lon']:.5f}")

    html_code = """
    <div id="gps-data" style="
        font-family: monospace;
        background-color: #eef;
        padding: 15px;
        border-radius: 10px;
        font-size: 16px;">
      Waiting for GPS data...
    </div>

    <script>
    let lastTime = null, lastLat = null, lastLon = null;
    let watchId = null;

    function toRad(deg){ return deg * Math.PI / 180; }
    function haversine(lat1, lon1, lat2, lon2){
        const R = 6371000;
        const φ1 = toRad(lat1), φ2 = toRad(lat2);
        const Δφ = toRad(lat2-lat1), Δλ = toRad(lon2-lon1);
        const a = Math.sin(Δφ/2)**2 + Math.cos(φ1)*Math.cos(φ2)*Math.sin(Δλ/2)**2;
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    }

    watchId = navigator.geolocation.watchPosition((pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        const time = pos.timestamp;

        let speed = 0;
        if (lastLat !== null){
            const dt = (time - lastTime)/1000;
            if (dt > 0){
                const dist = haversine(lastLat, lastLon, lat, lon);
                speed = dist / dt; // m/s
            }
        }

        lastLat = lat;
        lastLon = lon;
        lastTime = time;

        window.parent.postMessage({lat: lat, lon: lon, speed: speed}, "*");
    }, 
    (err) => { 
        document.getElementById("gps-data").innerHTML = "❌ " + err.message; 
    },
    {enableHighAccuracy:true, maximumAge:0, timeout:5000});
    </script>
    """
    components.html(html_code, height=180)

    # Placeholder for live data
    placeholder = st.empty()

    while st.session_state.tracking:
        params = st.query_params
        if "lat" in params and "lon" in params and "speed" in params:
            lat = float(params["lat"][0])
            lon = float(params["lon"][0])
            speed_ms = float(params["speed"][0])
            speed_knots = speed_ms * 1.94384  # 1 m/s = 1.94384 knots

            brg = bearing(lat, lon, WAYPOINT["lat"], WAYPOINT["lon"])
            dist = haversine(lat, lon, WAYPOINT["lat"], WAYPOINT["lon"])
            vmg = speed_knots * math.cos(math.radians(brg))
            ttr_min = dist / (speed_ms * 60) if speed_ms > 0 else None

            # Display info
            placeholder.markdown(f"""
            **Time:** {time.strftime('%H:%M:%S')}  
            **Latitude:** {lat:.5f}  
            **Longitude:** {lon:.5f}  
            **Speed:** {speed_knots:.2f} kn  
            **Bearing to WP:** {brg:.1f}°  
            **VMG:** {vmg:.2f} kn  
            **ETA:** {ttr_min:.1f} min
            """)
        time.sleep(1)
        st.experimental_rerun()

else:
    st.warning("Tracking stopped. Tap ▶️ **Start Tracking** to begin.")












