import streamlit as st
import streamlit.components.v1 as components
import math

st.set_page_config(page_title="GPS + Buoy Bearings", layout="centered")
st.title("📍 My Location + Bearings to Buoys")

st.markdown("Tap the button to get your location, then see bearings to predefined buoys/landmarks.")

# Predefined buoys / landmarks in Ría de Arousa (lat, lon)
# Example: Salvora lighthouse from source: 42°28′00″ N, 9°00′48″ W → (42.46667, -9.01333) approx
buoys = {
    "Salvora Lighthouse": (42.46667, -9.01333),
    # Add more you know:
    # "Cortegada Buoy": (lat_c, lon_c),
    # "Ribeira Buoy": (lat_r, lon_r)
}

# JavaScript + HTML to get location on client
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
        // send to Streamlit
        window.parent.postMessage({ isStreamlitMessage: true, type: "SET_COORDS", value: {lat: position.coords.latitude, lon: position.coords.longitude} }, "*");
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

components.html(html_code, height=200)

# Listen for message from JS
if "lat" in st.session_state and "lon" in st.session_state:
    user_lat = st.session_state["lat"]
    user_lon = st.session_state["lon"]
else:
    # Use a callback to capture the message
    def _set_coords(msg):
        if msg["type"] == "SET_COORDS":
            st.session_state["lat"] = msg["value"]["lat"]
            st.session_state["lon"] = msg["value"]["lon"]
    st.query_params()  # trick to enable message passing
    st.session_state.callback = _set_coords

if "lat" in st.session_state and "lon" in st.session_state:
    lat = st.session_state["lat"]
    lon = st.session_state["lon"]
    st.success(f"✅ You: {lat:.6f}, {lon:.6f}")

    # Bearing calculation: formula to compute bearing from (lat1, lon1) to (lat2, lon2)
    def bearing(lat1, lon1, lat2, lon2):
        # convert degrees to radians
        φ1 = math.radians(lat1)
        φ2 = math.radians(lat2)
        Δλ = math.radians(lon2 - lon1)
        x = math.sin(Δλ) * math.cos(φ2)
        y = math.cos(φ1)*math.sin(φ2) - math.sin(φ1)*math.cos(φ2)*math.cos(Δλ)
        θ = math.atan2(x, y)
        bearing_deg = (math.degrees(θ) + 360) % 360
        return bearing_deg

    st.subheader("Bearings to buoys/landmarks")
    for name, (b_lat, b_lon) in buoys.items():
        bdeg = bearing(lat, lon, b_lat, b_lon)
        st.write(f"→ **{name}**: {bdeg:.1f}°")

    # Optional: show map with user point and buoy points
    import pydeck as pdk
    points = [{"lat": lat, "lon": lon, "name":"You"}]
    for name, (b_lat, b_lon) in buoys.items():
        points.append({"lat": b_lat, "lon": b_lon, "name": name})
    # Use deck to plot scatter + lines
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/streets-v11",
        initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=11, pitch=0),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=points,
                get_position=["lon", "lat"],
                get_color=[200, 30, 0],
                get_radius=50,
            ),
            pdk.Layer(
                "LineLayer",
                data=[{"start": [lon, lat], "end": [b_lon, b_lat]} for (b_lat, b_lon) in buoys.values()],
                get_source_position="start",
                get_target_position="end",
                get_color=[0, 100, 200],
                get_width=2,
            )
        ],
    ))


