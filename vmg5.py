import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 Real-Time GPS Tracker", layout="centered")

st.title("📡 Real-Time GPS Tracker")
st.markdown("""
Track your GPS position every second directly from your smartphone.  
Tap **Start Tracking** to begin and **Stop Tracking** to end.
""")

# --- Session state ---
if "tracking" not in st.session_state:
    st.session_state.tracking = False

# --- Buttons ---
col1, col2 = st.columns(2)
with col1:
    if st.button("▶️ Start Tracking"):
        st.session_state.tracking = True
with col2:
    if st.button("⏹ Stop Tracking"):
        st.session_state.tracking = False

# --- Active tracking ---
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
    let watching = true;
    let watchId = null;

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
          const time = new Date().toLocaleTimeString();
          out.innerHTML = `
            <b>Time:</b> ${time}<br>
            <b>Latitude:</b> ${lat}<br>
            <b>Longitude:</b> ${lon}<br>
            <b>Accuracy:</b> ±${acc} m
          `;
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

    if (watching) startTracking();
    window.onbeforeunload = stopTracking;
    </script>
    """
    components.html(html_code, height=220)

else:
    st.warning("Tracking is stopped. Tap ▶️ **Start Tracking** to begin.")
    components.html("<script>stopTracking();</script>", height=0)


