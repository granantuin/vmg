import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 Live GPS Tracker", layout="centered")

st.title("📡 Live GPS Tracker")
st.markdown("""
This app reads your phone’s GPS every second.
Tap **Start Tracking** to begin and **Stop Tracking** to end.
""")

# --- Session State ---
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

# --- HTML + JavaScript for continuous GPS updates ---
if st.session_state.tracking:
    st.success("✅ Tracking active — move around to see updates!")
    html_code = """
    <div id="output" style="font-size:16px; color:#222; margin-top:10px;"></div>
    <script>
    let watchID = null;

    function startWatch() {
      const output = document.getElementById("output");
      if (navigator.geolocation) {
        watchID = navigator.geolocation.watchPosition(
          (pos) => {
            const lat = pos.coords.latitude.toFixed(6);
            const lon = pos.coords.longitude.toFixed(6);
            const acc = pos.coords.accuracy.toFixed(1);
            const time = new Date().toLocaleTimeString();
            output.innerHTML = `<b>Time:</b> ${time}<br>
                                <b>Latitude:</b> ${lat}<br>
                                <b>Longitude:</b> ${lon}<br>
                                <b>Accuracy:</b> ±${acc} m`;
          },
          (err) => {
            output.innerHTML = "❌ Error: " + err.message;
          },
          { enableHighAccuracy: true, maximumAge: 1000, timeout: 5000 }
        );
      } else {
        output.innerHTML = "Geolocation not supported.";
      }
    }

    function stopWatch() {
      if (watchID !== null) {
        navigator.geolocation.clearWatch(watchID);
        watchID = null;
        document.getElementById("output").innerHTML = "<b>Tracking stopped.</b>";
      }
    }

    // Auto-start watching on load
    startWatch();

    // Stop watching if user closes tab
    window.onbeforeunload = stopWatch;
    </script>
    """
    components.html(html_code, height=200)
else:
    st.warning("Tracking is stopped. Tap ▶️ **Start Tracking** to begin.")
