import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 GPS Logger", layout="centered")

st.title("📡 Real-Time GPS Logger")
st.markdown("""
This app records your live GPS position every second.  
Tap **Start Tracking** to begin and **Stop Tracking** to end.  
When you stop, you can **download your position log** as a CSV file.
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

# --- Tracking active ---
if st.session_state.tracking:
    st.success("✅ Tracking active — your position updates live below.")

    html_code = """
    <div id="gps-output" style="
        font-family: monospace;
        background-color: #f0f0f0;
        padding: 15px;
        border-radius: 10px;
        margin-top: 10px;
        font-size: 16px;
        color: #222;">
      Waiting for GPS data...
    </div>

    <script>
    let watchId = null;

    async function postPosition(lat, lon, acc, time) {
      const payload = JSON.stringify({lat: lat, lon: lon, acc: acc, time: time});
      await fetch("/_stcore/stream", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: payload
      });
    }

    function startTracking() {
      const out = document.getElementById("gps-output");

      if (!navigator.geolocation) {
        out.innerHTML = "❌ Geolocation is not supported by your device.";
        return;
      }

      watchId = navigator.geolocation.watchPosition(
        (pos) => {
          const lat = pos.coords.latitude.toFixed(6);
          const lon = pos.coords.longitude.toFixed(6);
          const acc = pos.coords.accuracy.toFixed(1);
          const time = new Date().toISOString();
          out.innerHTML = `
            <b>Time:</b> ${new Date(time).toLocaleTimeString()}<br>
            <b>Latitude:</b> ${lat}<br>
            <b>Longitude:</b> ${lon}<br>
            <b>Accuracy:</b> ±${acc} m
          `;
          window.parent.postMessage({lat: lat, lon: lon, acc: acc, time: time}, "*");
        },
        (err) => {
          out.innerHTML = "❌ Error: " + err.message;
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

    startTracking();
    window.onbeforeunload = stopTracking;
    </script>
    """

    components.html(html_code, height=220)

    # JS sends coordinates via postMessage → Streamlit receives below
    msg = st.get_query_params
else:
    st.warning("Tracking stopped. Tap ▶️ **Start Tracking** to begin.")
    components.html("<script>stopTracking();</script>", height=0)

# --- JS → Streamlit communication (browser messages) ---
js_code = """
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
components.html(js_code, height=0)

# --- Capture data from URL parameters ---
params = st.get_query_params
if "lat" in params:
    lat = float(params["lat"][0])
    lon = float(params["lon"][0])
    acc = float(params["acc"][0])
    time = params["time"][0]
    st.session_state.data.append({"time": time, "latitude": lat, "longitude": lon, "accuracy_m": acc})

# --- Show table ---
if len(st.session_state.data) > 0:
    df = pd.DataFrame(st.session_state.data)
    st.dataframe(df.tail(10), use_container_width=True)
    
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("💾 Download CSV Log", csv, "gps_log.csv", "text/csv")



