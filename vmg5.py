<script>
let tracking = false;
let data = [];
let lastPos = null;
let waypoint = {lat:42.5608, lon:-8.9406};

function haversine(lat1, lon1, lat2, lon2){
  const R = 6371000;
  const φ1 = lat1*Math.PI/180, φ2 = lat2*Math.PI/180;
  const dφ = (lat2-lat1)*Math.PI/180, dλ = (lon2-lon1)*Math.PI/180;
  const a = Math.sin(dφ/2)**2 + Math.cos(φ1)*Math.cos(φ2)*Math.sin(dλ/2)**2;
  return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
}
function bearing(lat1, lon1, lat2, lon2){
  const φ1=lat1*Math.PI/180, φ2=lat2*Math.PI/180, Δλ=(lon2-lon1)*Math.PI/180;
  const x=Math.sin(Δλ)*Math.cos(φ2);
  const y=Math.cos(φ1)*Math.sin(φ2)-Math.sin(φ1)*Math.cos(φ2)*Math.cos(Δλ);
  return (Math.atan2(x,y)*180/Math.PI+360)%360;
}

function updateTable(){
  let html = "<b>Last 10 records</b><br><table border='1' cellspacing='0' cellpadding='3'><tr><th>Time</th><th>Lat</th><th>Lon</th><th>Speed(kn)</th><th>Bearing</th><th>VMG</th><th>ETA(min)</th></tr>";
  const last = data.slice(-10);
  last.forEach(r=>{
    html += `<tr><td>${r.time}</td><td>${r.lat.toFixed(5)}</td><td>${r.lon.toFixed(5)}</td>
             <td>${r.spd ? r.spd.toFixed(2) : "—"}</td><td>${r.brg.toFixed(1)}</td>
             <td>${r.vmg ? r.vmg.toFixed(2) : "—"}</td><td>${r.eta ? r.eta.toFixed(1) : "—"}</td></tr>`;
  });
  html += "</table>";
  document.getElementById("table").innerHTML = html;
}

function start(){
  if(!navigator.geolocation){
    document.getElementById("status").innerText="❌ Geolocation not supported.";
    return;
  }
  document.getElementById("status").innerText="✅ Tracking started...";
  tracking = true;
  navigator.geolocation.watchPosition((pos)=>{
    const lat = pos.coords.latitude;
    const lon = pos.coords.longitude;
    const now = new Date();

    let spd=0, brg=0, vmg=0, eta=null;
    if(lastPos){
      const dt = (now - lastPos.time)/1000;
      const dist = haversine(lastPos.lat,lastPos.lon,lat,lon);
      if(dt>0 && dist>1){        // ignore <1 m movement noise
        const speed_ms = dist/dt;
        spd = speed_ms * 1.94384; // knots
        brg = bearing(lat,lon,waypoint.lat,waypoint.lon);
        const distWP = haversine(lat,lon,waypoint.lat,waypoint.lon);
        vmg = spd * Math.cos((brg*Math.PI)/180);
        eta = speed_ms>0 ? (distWP/(speed_ms*60)) : null; // minutes
      }
    }
    lastPos = {lat, lon, time: now};
    data.push({time: now.toLocaleTimeString(), lat, lon, spd, brg, vmg, eta});
    updateTable();
  },(err)=>{
    document.getElementById("status").innerText="❌ "+err.message;
  },{enableHighAccuracy:true});
}

function stop(){
  tracking=false;
  document.getElementById("status").innerText="⏹ Tracking stopped.";
  const csv = "data:text/csv;charset=utf-8," +
              ["time,lat,lon,speed_knots,bearing,vmg,eta_min"].concat(
                data.map(d=>[d.time,d.lat,d.lon,
                             (d.spd||0).toFixed(2),
                             d.brg.toFixed(1),
                             (d.vmg||0).toFixed(2),
                             (d.eta||0).toFixed(1)].join(","))
              ).join("\\n");
  const link = document.createElement("a");
  link.href = encodeURI(csv);
  link.download = "gps_track.csv";
  link.innerText="💾 Download CSV";
  document.getElementById("table").appendChild(document.createElement("br"));
  document.getElementById("table").appendChild(link);
}
</script>



















