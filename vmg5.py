import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 GPS Logger", layout="centered")

st.title("📡 Real-Time GPS Logger")
st.markdown("""
This app records your live GPS position every second.  
Tap **Start Tracking** to begin and **Stop Tracking** to end.  
When you stop, you’ll still see your recorded positions and can download them as a CSV.
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

# --- HTML + JS for geolocation tracking ---
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
  {'Tracking active...' if tracking else 'Tracking stopped.'}
</div>

<script>
let watchId = null;
let tracking = {str(tracking).lower()};

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

      // Send data directly to Streamlit via postMessage
      const payload = {{lat, lon, acc, time}};
      window.parent.postMessage({type: "streamlit:setComponentValue", value: payload}, "*");
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
}} else {{
  stopTracking();
}}
</script>
"""

# --- Create component with real-time value ---
value = components.html(html_code, height=220)

# --- Append incoming data to DataFrame ---
if isinstance(value, dict) and "lat" in value:
    st.session_state.data.append({
        "time": value["time"],
        "latitude": float(value["lat"]),
        "longitude": float(value["lon"]),
        "accuracy_m": float(value["acc"]),
    })

# --- Show the data (even after stop) ---
if len(st.session_state.data) > 0:
    df = pd.DataFrame(st.session_state.data)
    st.subheader("📊 Recorded Positions")
    st.dataframe(df.tail(10), use_container_width=True)

    # Download CSV
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download CSV Log", csv, "gps_log.csv", "text/csv")

if tracking:
    st.success("✅ Tracking active — updating every second...")
else:
    st.info("Tracking stopped. Tap ▶️ **Start Tracking** to begin again.")








