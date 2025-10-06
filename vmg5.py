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

# --- Fixed waypoint (example: Vilagarcía buoy) ---
WAYPOINT = {"lat": 42.5608, "lon": -8.9406}

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
        st.session_state.data = []  # reset log
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

# --- Tracking section ---
if st.session_state.tracking:
    st.success("✅ Tracking active — updates every second.")
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
    if (navigator.geolocation) {
        navigator.geolocation.watchPosition((pos) => {
            const lat = pos.coords.latitude;
            const lon = pos.coords.longitude;
            const t = new Date().toISOString();
            const acc = pos.coords.accuracy;
            window.parent.postMessage({lat, lon, acc, time: t}, "*");
        }, (err) => {
            document.getElementById("gps-data").innerHTML = "❌ " + err.message;
        }, {enableHighAccuracy: true, maximumAge: 0, timeout: 5000});
    } else {
        document.getElementById("gps-data").innerHTML = "❌ Geolocation not supported.";
    }
    </script>
    """
    components.html(html_code, height=160)

    # Listen for messages
    js_listener = """
    <script>
    window.addEventListener("message", (event) => {
        const d = event.data;
        if (d.lat && d.lon && d.time) {
            const query = new URLSearchParams({
                lat: d.lat,
                lon: d.lon,
                time: d.time,
                acc: d.acc
            });
            window.location.search = query.toString();
        }
    });
    </script>
    """
    components.html(js_listener, height=0)

# --- Capture new GPS updates from URL ---
params = st.query_params
if "lat" in params:
    lat = float(params["lat"][0])
    lon = float(params["lon"][0])
    time_iso = params["time"][0]
    acc = float(params["acc"][0]) if "acc" in params else None

    # Compute velocity and metrics
    if len(st.session_state.data) > 0:
        last = st.session_state.data[-1]
        dt = (pd.to_datetime(time_iso) - pd.to_datetime(last["time"])).total_seconds()
        if dt > 0:
            dist = haversine(last["lat"], last["lon"], lat, lon)
            speed_ms = dist / dt
            speed_knots = speed_ms * 1.94384
            brg = bearing(lat, lon, WAYPOINT["lat"], WAYPOINT["lon"])
            dist_wp = haversine(lat, lon, WAYPOINT["lat"], WAYPOINT["lon"])
            vmg = speed_knots * math.cos(math.radians(brg))
            ttr_min = dist_wp / (speed_ms * 60) if speed_ms > 0 else None
        else:
            speed_knots = brg = vmg = ttr_min = 0
    else:
        speed_knots = brg = vmg = ttr_min = 0

    st.session_state.data.append({
        "time": time_iso,
        "lat": lat,
        "lon": lon,
        "speed_knots": round(speed_knots, 2),
        "bearing_to_wp": round(brg, 1),
        "vmg": round(vmg, 2),
        "eta_min": round(ttr_min, 1) if ttr_min else None,
        "accuracy_m": acc
    })

    st.rerun()

# --- Display results ---
if len(st.session_state.data) > 0:
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df.tail(10), use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download CSV Log", csv, "track_log.csv", "text/csv")















