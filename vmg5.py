import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="📡 Real-Time GPS Tracker", layout="centered")

st.title("📡 Real-Time GPS Tracker")
st.markdown("""
Use this app to track your live GPS position every second.  
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

# --- Tracking Logic ---
if st.session_state.tracking:
    st.success("✅ Tracking active — position updates every second.")
    
    html_code = """
    <div id="output" style="font-size:16px; color:#222; margin-top:10px; background:#f5f5f5; padding:10px; border-radius:10px;">
      Waiting for GPS data...
    </div>
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
          { enableHighAccuracy: true, maximumAge: 0, timeout: 5000 }
        );
      } else {
        output.innerHTML = "Geolocation not supported by this device.";
      }
    }

    function stopWatch() {
      if (watchID !== null) {
        navigator.geolocation.clearWatch(watchID);
        watchID = null;
        document.getElementById("output").innerHTML = "<b>Tracking stopped.</b>";
      }
    }

    startWatch();

    window.onbeforeunload = stopWatch;
    </script>
    """
    components.html(html_code, height=220)
else:
    st.warning("Tracking stopped. Tap ▶️ **Start Tracking** to begin.")
    # Ensure JS watch stops
    components.html("<script>if (watchID){navigator.geolocation.clearWatch(watchID);}</script>", height=0)
