import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 GPS Logger", layout="centered")

st.title("📡 Real-Time GPS Logger")
st.markdown("""
This app records your live GPS position every second.  
Tap **Start Tracking** to begin and **Stop Tracking** to end.  
When you stop, you’ll still see the recorded results and can **download them as CSV**.
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

# --- HTML/JS for GPS tracking ---
html_code = f"""
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
let tracking = {str(tracking).lower()};
let watchId = null;

function startTracking() {{
  const out = document.getElementById("gps-output");

  if (!navigator.geolocation) {{
    out.innerHTML = "❌ Geolocation not supported.";
    return;
  }}

  watchId = navigator.geolocation.watchPosition(
    (pos) => {{
      const lat = pos.coords.latitude.toFixed(6);
      const lon = pos.coords.longitude.toFixed(6);
      const acc = pos.coords.accuracy.toFixed(1);
      const time = new Date().toISOString();

      out.innerHTML =
        `<b>Time:</b> ${{new Date(time).toLocaleTimeString()}}<br>` +
        `<b>Latitude:</b> ${{lat}}<br>` +
        `<b>Longitude:</b> ${{lon}}<br>` +
        `<b>Accuracy:</b> ±${{acc}} m`;

      const query = new URLSearchParams({{lat, lon, acc, time}});
      fetch(window.location.pathname + "?" + query.toString());
    }},
    (err) => {{
      out.innerHTML = "❌ " + err.message;
    }},
    {{ enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }}
  );
}}

function stopTracking() {{
  if (watchId !== null) {{
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
    document.getElementById("gps-output").innerHTML = "<b>Tracking stopped.</b>";
  }}
}}

if (tracking) {{
  startTracking();
  setTimeout(() => window.location.reload(), 1000);  // Auto-refresh while tracking
}} else {{
  stopTracking();
}}
</script>
"""

components.html(html_code, height=220)

# --- Capture data from URL parameters ---
params = st.query_params
if "lat" in params:
    try:
        lat = float(params["lat"][0])
        lon = float(params["lon"][0])
        acc = float(params["acc"][0])
        time = params["time"][0]
        if len(st.session_state.data) == 0 or st.session_state.data[-1]["time"] != time:
            st.session_state.data.append({
                "time": time,
                "latitude": lat,
                "longitude": lon,
                "accuracy_m": acc
            })
    except Exception:
        pass

# --- Show results table ---
if len(st.session_state.data) > 0:
    df = pd.DataFrame(st.session_state.data)
    st.subheader("📊 Logged Positions")
    st.dataframe(df.tail(10), use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download CSV Log", csv, "gps_log.csv", "text/csv")

if not tracking:
    st.info("Tracking stopped. Tap ▶️ **Start Tracking** to begin again.")






