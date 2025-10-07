import streamlit as st
import pandas as pd
import math
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 GPS Tracker — Ría Arousa", layout="centered")

st.title("📡 Real-Time GPS Tracker — Ría Arousa")
st.markdown("""
Track your GPS position every second (with high accuracy).  
Select a waypoint to compute bearing, VMG, and ETA.
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

# --- Helpers ---
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def bearing_to(lat1, lon1, lat2, lon2):
    y = math.sin(math.radians(lon2 - lon1)) * math.cos(math.radians(lat2))
    x = math.cos(math.radians(lat1))*math.sin(math.radians(lat2)) - math.sin(math.radians(lat1))*math.cos(math.radians(lat2))*math.cos(math.radians(lon2 - lon1))
    return (math.degrees(math.atan2(y, x)) + 360) % 360

# --- Session state ---
if "tracking" not in st.session_state:
    st.session_state.tracking = False
if "data" not in st.session_state:
    st.session_state.data = []

# --- UI ---
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

# --- Live JS ---
if st.session_state.tracking:
    st.success("✅ Tracking active (waiting for GPS fix...)")

    components.html(
        """
        <div id="gps-output" style="font-family: monospace; background:#f0f0f0; padding:10px; border-radius:10px;">
          Waiting for GPS data...
        </div>
        <script>
        let watchId = null;
        if (navigator.geolocation) {
          watchId = navigator.geolocation.watchPosition(
            (pos) => {
              const acc = pos.coords.accuracy;
              if (acc > 20) return;  // skip poor accuracy
              const lat = pos.coords.latitude.toFixed(6);
              const lon = pos.coords.longitude.toFixed(6);
              const time = new Date().toISOString();
              document.getElementById("gps-output").innerHTML = `
                <b>Time:</b> ${new Date(time).toLocaleTimeString()}<br>
                <b>Lat:</b> ${lat}<br>
                <b>Lon:</b> ${lon}<br>
                <b>Accuracy:</b> ±${acc.toFixed(1)} m
              `;
              window.parent.postMessage(
                {type: "streamlit:setComponentValue", value: JSON.stringify({lat: lat, lon: lon, acc: acc, time: time})},
                "*"
              );
            },
            (err) => {
              document.getElementById("gps-output").innerHTML = "❌ " + err.message;
            },
            { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
          );
        } else {
          document.getElementById("gps-output").innerHTML = "❌ Geolocation not supported.";
        }
        </script>
        """,
        height=220,
    )

# --- Receive position updates ---
pos = st.experimental_get_query_params()
if "lat" in pos:
    lat = float(pos["lat"][0])
    lon = float(pos["lon"][0])
    acc = float(pos["acc"][0])
    time = pos["time"][0]
    st.session_state.data.append({"time": time, "lat": lat, "lon": lon, "acc": acc})

# --- Show Data ---
if len(st.session_state.data) > 1:
    df = pd.DataFrame(st.session_state.data)
    df["time"] = pd.to_datetime(df["time"])
    df["delta_t"] = df["time"].diff().dt.total_seconds().fillna(1)
    df["dist_m"] = [
        haversine(df.lat[i-1], df.lon[i-1], df.lat[i], df.lon[i]) if i > 0 else 0
        for i in range(len(df))
    ]
    df["speed_kn"] = df["dist_m"] / df["delta_t"] * 1.94384
    df["bearing"] = [bearing_to(df.lat[i], df.lon[i], waypoint[0], waypoint[1]) for i in range(len(df))]
    df["dist_to_wp_m"] = [haversine(df.lat[i], df.lon[i], waypoint[0], waypoint[1]) for i in range(len(df))]
    df["vmg_kn"] = df["speed_kn"] * [
        math.cos(math.radians(df["bearing"].iloc[i] - df["bearing"].iloc[-1])) for i in range(len(df))
    ]
    df["eta_min"] = df["dist_to_wp_m"] / (df["vmg_kn"] * 0.51444) / 60
    df["eta_min"] = df["eta_min"].replace([math.inf, -math.inf], None).round(1)

    st.subheader("📊 Last 10 Records")
    st.dataframe(df[["time", "lat", "lon", "acc", "speed_kn", "bearing", "vmg_kn", "eta_min"]].tail(10))

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download CSV", csv, "gps_log.csv", "text/csv")

elif st.session_state.tracking:
    st.info("⏳ Waiting for GPS fix...")
else:
    st.warning("Tracking stopped. Tap ▶️ **Start Tracking** to begin.")















