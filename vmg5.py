import streamlit as st
import pandas as pd
import time
import json
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="📡 GPS Logger", layout="centered")

st.title("📡 Real-Time GPS Logger")
st.markdown("""
This app records your live GPS position every second.  
Tap **Start Tracking** to begin and **Stop Tracking** to end.  
When you stop, you’ll see your recorded positions and can download them as CSV.
""")

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
    if st.button("⏹ Stop Tracking"):
        st.session_state.tracking = False

tracking = st.session_state.tracking

# --- Auto-refresh every second only when tracking ---
if tracking:
    st_autorefresh(interval=1000, key="gps_refresh")

# --- Geolocation script (runs in browser) ---
html_code = """
<div id="gps-output" style="
    font-family: monospace;
    background-color: #f8f9fa;
    padding: 12px;
    border-radius: 10px;
    font-size: 16px;
    color: #222;
    border: 1px solid #ccc;
    margin-top: 10px;">
  Waiting for GPS data...
</div>

<script>
function updatePosition() {
  if (!navigator.geolocation) {
    document.getElementById("gps-output").innerHTML = "❌ Geolocation not supported.";
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude.toFixed(6);
      const lon = pos.coords.longitude.toFixed(6);
      const acc = pos.coords.accuracy.toFixed(1);
      const time = new Date().toISOString();
      const payload = {lat, lon, acc, time};
      window.localStorage.setItem("gps_data", JSON.stringify(payload));

      document.getElementById("gps-output").innerHTML =
        `<b>Time:</b> ${new Date(time).toLocaleTimeString()}<br>` +
        `<b>Latitude:</b> ${lat}<br>` +
        `<b>Longitude:</b> ${lon}<br>` +
        `<b>Accuracy:</b> ±${acc} m`;
    },
    (err) => {
      document.getElementById("gps-output").innerHTML = "❌ " + err.message;
    },
    { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
  );
}

updatePosition();
</script>
"""

components.html(html_code, height=200)

# --- Read from browser's localStorage (persistent JS → Streamlit bridge) ---
gps_raw = st.experimental_get_query_params().get("gps_data", [None])[0]

# Try to read latest location from localStorage using a hidden iframe trick
# (works in browser after reload)
components.html("""
<script>
const data = localStorage.getItem("gps_data");
if (data) {
  const url = new URL(window.location);
  url.searchParams.set("gps_data", data);
  window.history.replaceState({}, "", url);
}
</script>
""", height=0)

# --- Process new position data ---
if gps_raw:
    try:
        gps = json.loads(gps_raw)
        lat, lon, acc, t = gps["lat"], gps["lon"], gps["acc"], gps["time"]

        if len(st.session_state.data) == 0 or st.session_state.data[-1]["time"] != t:
            st.session_state.data.append({
                "time": t,
                "latitude": float(lat),
                "longitude": float(lon),
                "accuracy_m": float(acc)
            })
    except Exception:
        pass

# --- Display results ---
if len(st.session_state.data) > 0:
    df = pd.DataFrame(st.session_state.data)
    st.subheader("📊 Recorded Positions")
    st.dataframe(df.tail(10), use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download CSV Log", csv, "gps_log.csv", "text/csv")

if tracking:
    st.success("✅ Tracking active — updating every second...")
else:
    st.info("Tracking stopped. Tap ▶️ **Start Tracking** to begin again.")










