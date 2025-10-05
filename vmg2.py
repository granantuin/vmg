import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="📍 My GPS Location", layout="centered")

st.title("📍 My GPS Location")
st.markdown("Tap the button below and allow location access in your browser:")

# HTML + JS to capture coordinates
html_code = """
<script>
function getLocation() {
  const output = document.getElementById("location");
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude.toFixed(6);
        const lon = position.coords.longitude.toFixed(6);
        output.innerHTML = `<b>Latitude:</b> ${lat}<br><b>Longitude:</b> ${lon}`;
      },
      (error) => {
        output.innerHTML = "❌ Error: " + error.message;
      }
    );
  } else {
    output.innerHTML = "Geolocation not supported by this browser.";
  }
}
</script>

<button onclick="getLocation()">📍 Get My Coordinates</button>
<p id="location" style="margin-top:20px; font-size:16px; color:#333;"></p>
"""

# Render the HTML/JS
components.html(html_code, height=200)
