import streamlit as st
import pydeck as pdk

st.set_page_config(page_title="📍 My GPS Location", layout="centered")

st.title("📍 My GPS Location")
st.markdown("This app gets your phone's location using the browser’s GPS (navigator.geolocation).")

# Inject JavaScript to get the position
st.markdown("""
<script>
function sendPositionToStreamlit(lat, lon) {
    const data = {latitude: lat, longitude: lon};
    window.parent.postMessage({isStreamlitMessage: true, type: "streamlit:setComponentValue", value: data}, "*");
}
navigator.geolocation.getCurrentPosition(
  (pos) => sendPositionToStreamlit(pos.coords.latitude, pos.coords.longitude),
  (err) => alert("Error getting location: " + err.message)
);
</script>
""", unsafe_allow_html=True)

# Placeholder for JS communication
location = st.session_state.get("location", None)
if location is None:
    st.warning("Waiting for location... Please allow location access.")
else:
    lat = location["latitude"]
    lon = location["longitude"]
    st.success(f"✅ Latitude: {lat:.6f}, Longitude: {lon:.6f}")

    # Show map
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/streets-v11",
        initial_view_state=pdk.ViewState(latitude=lat, longitude=lon, zoom=14, pitch=0),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=[{"lat": lat, "lon": lon}],
                get_position=["lon", "lat"],
                get_color=[255, 0, 0],
                get_radius=25,
            ),
        ],
    ))
