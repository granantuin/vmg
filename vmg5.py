import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

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
let tracking = %s;
let watchId = null;

function startTracking() {
  const out = document.getElementById("gps-output");

  if (!navigator.geolocation) {
    out.innerHTML = "❌ Geolocation not supported.";
    return;
  }

  watchId = navigator.geolocation.watchPosition(
    (pos) => {
      const lat = pos.coords.latitude.toFixed(6);
      const lon = pos.coords.longitude.toFixed(6);
      const acc = pos.coords.accuracy.toFixed(1);
      const time = new Date().toISOString();
      out.innerHTML =
        `<b>Time:</b> ${new Date(time).toLocaleTimeString()}<br>` +
        `<b>Latitude:</b> ${lat}<br>` +
        `<b>Longitude:</b> ${lon}<br>` +
        `<b>Accuracy:</b> ±${acc} m`;

      // Send to Streamlit via URL
      const query = new URLSearchParams({lat, lon, acc, time});
      fetch(window.location.pathname + "?" + query.toString());
    },
    (err) => {
      out.innerHTML = "❌ " + err.message;
    },
    { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
  );
}

function stopTracking() {
  if (watchId !== null) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
    document.getElementById("gps-output").innerHTML = "<b>Tracking stopped.</b>";
  }
}

if (tracking) startTracking(); else stopTracking();

// Auto-refresh every second if tracking is active
if (tracking) {
  setTimeout(() => window.location.reload(), 1000);
}
</script>
""" % ("true" if st.session_state.tracking else "false")

components.html(html_code, height=220)

# --- Capture GPS data ---
params = st.query_params
if "lat" in params:
    try:
        lat = float(params["lat"][0])
        lon = float(params["lon"][0])
        acc = float(params["acc"][0])
        time = params["time"][0]
        if len(st.session_state.data) == 0 or st.session_state.data[-1]["time"] != time:
            st.session_state.data.append({"time": time, "latitude": lat, "longitude": lon, "accuracy_m": acc})
    except Exception:
        pass

# --- Show results ---
if len(st.session_state.data) > 0:
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df.tail(10), use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download CSV Log", csv, "gps_log.csv", "text/csv")

if not st.session_state.tracking:
    st.info("Tracking stopped. Tap ▶️ **Start Tracking** to begin.")






