import streamlit as st
import pandas as pd
import math
import time
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 Ría Arousa GPS Tracker", layout="centered")

st.title("📡 Real-Time GPS Tracker — Ría Arousa")
st.markdown("""
Tracks your position every second with high GPS accuracy.  
Shows bearing, VMG, and ETA to a selected waypoint.  
Tap **Start Tracking** to begin and **Stop Tracking** to end.
""")

# --- Waypoints (Ría Arousa) ---
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

# --- Helper Functions ---
def haversine(lat1, lon1, lat2, lon2):
    """Distance in meters between two lat/lon points"""
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def bearing_to(lat1, lon1, lat2, lon2):
    """Bearing in degrees from point A to B"""
    y = math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1))*math.sin(math.radians(lat2)) - math.sin(math.radians(lat1))*math.cos(math.radians(lat2))*math.cos(math.radians(lon2 - lon1))
    brng = math.degrees(math.atan2(y, x))
    return (brng + 360) % 360

# --- Session State ---
if "tracking" not in st.session_state:
    st.session_state.tracking = False
if "data" not in st.session_state:
    st.session_state.data = []

# --- UI Controls ---
waypoint_name = st.selectbox("📍 Select Waypoint", list(waypoints.keys()))
waypoint = waypoints[waypoint_name]

col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Start Tracking"):
        st.session_state.tracking = True
        st.session_state.data = []
with col2:
    if st.button("⏹ Stop Tracking"):
        st.session_state.tracking = False

# --- GPS JavaScript Injection ---
if st.session_state.tracking:
    st.success(f"✅ Tracking active — waypoint: **{waypoint_name}**")

    components.html(f"""
    <div id="gps-output" style="
        font-family: monospace;
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 10px;
        margin-top: 10px;
        font-size: 16px;
        color: #222;">
      Waiting for GPS data...
    </div>

    <script>
    let watchId = null;

    function startTracking() {{
      const out = document.getElementById("gps-output");

      if (!navigator.geolocation) {{
        out.innerHTML = "❌ Geolocation is not supported by your device.";
        return;
      }}

      watchId = navigator.geolocation.watchPosition(
        (pos) => {{
          const acc = pos.coords.accuracy;
          if (acc > 20) {{
            console.log("Skipped fix, poor accuracy:", acc);
            return;
          }}
          const lat = pos.coords.latitude.toFixed(6);
          const lon = pos.coords.longitude.toFixed(6);
          const time = new Date().toISOString();

          out.innerHTML = `
            <b>Time:</b> ${{new Date(time).toLocaleTimeString()}}<br>
            <b>Latitude:</b> ${{lat}}<br>
            <b>Longitude:</b> ${{lon}}<br>
            <b>Accuracy:</b> ±${{acc.toFixed(1)}} m
          `;

          window.parent.postMessage(
            {{lat: lat, lon: lon, acc: acc, time: time}},
            "*"
          );
        }},
        (err) => {{
          out.innerHTML = "❌ Error: " + err.message;
        }},
        {{
          enableHighAccuracy: true,
          maximumAge: 0,
          timeout: 5000
        }}
      );
    }}

    function stopTracking() {{
      if (watchId !== null) {{
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
        document.getElementById("gps-output").innerHTML = "<b>Tracking stopped.</b>";
      }}
    }}

    startTracking();
    window.onbeforeunload = stopTracking;
    </script>
    """, height=240)

# --- Receive Data from JS ---
js_listener = """
<script>
window.addEventListener("message", (event) => {
    const data = event.data;
    if (data.lat && data.lon && data.time) {
        const query = new URLSearchParams({
            lat: data.lat,
            lon: data.lon,
            acc: data.acc,
            time: data.time
        });
        fetch(window.location.pathname + "?" + query.toString());
    }
});
</script>
"""
components.html(js_listener, height=0)

# --- Store GPS fixes ---
params = st.query_params
if "lat" in params:
    lat = float(params["lat"][0])
    lon = float(params["lon"][0])
    acc = float(params["acc"][0])
    time_str = params["time"][0]
    now = pd.to_datetime(time_str)
    st.session_state.data.append({"time": now, "lat": lat, "lon": lon, "acc": acc})

# --- Compute Metrics ---
if len(st.session_state.data) > 1:
    df = pd.DataFrame(st.session_state.data)
    df["delta_t"] = df["time"].diff().dt.total_seconds().fillna(1)
    df["dist_m"] = [
        haversine(df.lat[i-1], df.lon[i-1], df.lat[i], df.lon[i]) if i > 0 else 0
        for i in range(len(df))
    ]
    df["speed_kn"] = df["dist_m"] / df["delta_t"] * 1.94384  # m/s → kn
    df["bearing"] = [bearing_to(df.lat[i], df.lon[i], waypoint[0], waypoint[1]) for i in range(len(df))]
    df["dist_to_wp_m"] = [haversine(df.lat[i], df.lon[i], waypoint[0], waypoint[1]) for i in range(len(df))]
    df["vmg_kn"] = df["speed_kn"] * (
        (df["bearing"] - df["bearing"].iloc[-1]).apply(lambda x: math.cos(math.radians(x)))
    )
    df["eta_min"] = df["dist_to_wp_m"] / (df["vmg_kn"] * 0.51444) / 60
    df["eta_min"] = df["eta_min"].replace([math.inf, -math.inf], None).round(1)

    # --- Show Table ---
    st.subheader("📊 Last 10 Records")
    st.dataframe(df[["time", "lat", "lon", "speed_kn", "bearing", "vmg_kn", "eta_min"]].tail(10), use_container_width=True)

    # --- Download ---
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download Track (CSV)", csv, "gps_log.csv", "text/csv")

elif st.session_state.tracking:
    st.info("⏳ Waiting for first GPS fix...")
else:
    st.warning("Tracking stopped. Tap ▶️ **Start Tracking** to begin.")















