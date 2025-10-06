import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="📡 GPS Logger", layout="centered")

st.title("📡 Real-Time GPS Logger")
st.markdown("""
This app records your live GPS position every second.  
Tap **Start Tracking** to begin and **Stop Tracking** to end.  
You can download your logged positions as a CSV file.
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

# --- Enable auto-refresh when tracking ---
if st.session_state.tracking:
    count = st_autorefresh(interval=1000, limit=None, key="gps_refresh")

# --- HTML GPS tracker ---
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
if (navigator.geolocation) {
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude.toFixed(6);
      const lon = pos.coords.longitude.toFixed(6);
      const acc = pos.coords.accuracy.toFixed(1);
      const time = new Date().toISOString();
      document.getElementById("gps-output").innerHTML =
        `<b>Time:</b> ${new Date(time).toLocaleTimeString()}<br>` +
        `<b>Latitude:</b> ${lat}<br>` +
        `<b>Longitude:</b> ${lon}<br>` +
        `<b>Accuracy:</b> ±${acc} m`;
      // Send coordinates to Streamlit via URL params
      const query = new URLSearchParams({
        lat: lat, lon: lon, acc: acc, time: time
      });
      fetch(window.location.pathname + "?" + query.toString());
    },
    (err) => {
      document.getElementById("gps-output").innerHTML = "❌ Error: " + err.message;
    },
    { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
  );
} else {
  document.getElementById("gps-output").innerHTML = "❌ Geolocation not supported.";
}
</script>
"""
components.html(html_code, height=220)

# --- Capture GPS data from browser ---
params = st.query_params
if "lat" in params:
    try:
        lat = float(params["lat"][0])
        lon = float(params["lon"][0])
        acc = float(params["acc"][0])
        time = params["time"][0]
        # Avoid duplicates (only append new timestamp)
        if len(st.session_state.data) == 0 or st.session_state.data[-1]["time"] != time:
            st.session_state.data.append({
                "time": time, "latitude": lat, "longitude": lon, "accuracy_m": acc
            })
    except Exception:
        pass

# --- Display live table ---
if len(st.session_state.data) > 0:
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df.tail(10), use_container_width=True)
    
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download CSV Log", csv, "gps_log.csv", "text/csv")

if not st.session_state.tracking:
    st.info("Tracking stopped. Tap ▶️ **Start Tracking** to begin.")





