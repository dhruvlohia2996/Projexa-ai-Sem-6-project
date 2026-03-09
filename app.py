import matplotlib
matplotlib.use("Agg")

from flask import Flask, request
import matplotlib.pyplot as plt
import numpy as np
import io, base64, random

app = Flask(__name__)

# ---------------- ROUTES ----------------
LOCATIONS = {
    "Delhi - ITO": [(28.6280,77.2410),(28.6310,77.2385)],
    "Sohna Bus Stand → Gurugram Bus Stand": [
        (28.2473,77.0654),
        (28.3200,77.0750),
        (28.3800,77.0800),
        (28.4300,77.0820),
        (28.4595,77.0266)
    ]
}

# ---------------- AQI ----------------
def generate_aqi():
    aqi = random.randint(70, 210)
    status = "Moderate" if aqi <= 100 else "Unhealthy" if aqi <= 150 else "Very Unhealthy"
    return aqi, status

# ---------------- TRAFFIC ----------------
def generate_traffic():
    base = random.randint(80,130)
    trend = random.randint(6,14)
    noise = np.random.randint(-5,6,5)
    return [base + i*trend + noise[i] for i in range(5)]

def predict(data):
    x = np.arange(len(data))
    coeff = np.polyfit(x,data,1)
    trend = np.poly1d(coeff)
    future = trend(np.arange(len(data),len(data)+3))
    future += np.random.randint(-8,8,3)
    return future.astype(int)

def moving_avg(data):
    return np.convolve(data,np.ones(3)/3,mode="valid")

# ---------------- GRAPH ----------------
def make_graph(hist,pred,ma):
    plt.figure(figsize=(4,2.6))
    plt.plot(hist,marker="o",label="Historical")
    plt.plot(range(len(hist),len(hist)+len(pred)),pred,
             marker="s",linestyle="--",label="Predicted")
    plt.plot(range(2,2+len(ma)),ma,linestyle=":",label="Moving Avg")

    plt.legend(fontsize=7)
    plt.grid(True,alpha=0.3)

    img = io.BytesIO()
    plt.savefig(img,format="png",bbox_inches="tight")
    plt.close()
    img.seek(0)
    return base64.b64encode(img.getvalue()).decode()

# ---------------- UI ----------------
PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>Traffic Prediction Engine</title>
<meta name="viewport" content="width=device-width, initial-scale=1">

<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

<style>
body {font-family:Segoe UI;background:#0f172a;color:white;margin:0}
.nav {background:#1e293b;padding:12px 20px;display:flex;justify-content:space-between}
.container {width:90%%;max-width:900px;margin:auto;text-align:center}
.card {background:#1e293b;padding:18px;border-radius:10px;margin-top:20px}
input {padding:7px;width:260px}
.graph-img {width:420px;max-width:100%%;margin-top:10px}
#map {height:300px;width:100%%;margin-top:15px;border-radius:8px;}
</style>
</head>

<body>

<div class="nav"><b>🚦 Traffic Prediction Engine</b></div>

<div class="container">

<div class="card">
<form method="post">
<input list="locations" name="location" placeholder="Select Route" required>
<datalist id="locations">
%s
</datalist>
<br><br>
<button type="submit">Predict Traffic</button>
</form>
</div>

%s

</div>

</body>
</html>
"""

# ---------------- ROUTE ----------------
@app.route("/",methods=["GET","POST"])
def home():
    options = "".join([f"<option value='{l}'>{l}</option>" for l in LOCATIONS])
    result = ""

    if request.method == "POST":
        loc = request.form.get("location")

        if loc in LOCATIONS:
            route = LOCATIONS[loc]

            hist = generate_traffic()
            pred = predict(hist)
            ma = moving_avg(hist)
            graph = make_graph(hist,pred,ma)
            aqi,status = generate_aqi()

            route_js = ",".join([f"[{lat},{lon}]" for lat,lon in route])

            result = f"""
            <div class="card">
            <h3>{loc}</h3>
            <p><b>AQI:</b> {aqi} ({status})</p>

            <img class="graph-img" src="data:image/png;base64,{graph}">

            <div id="map"></div>

            <script>
            // 🔥 wait until browser paints DOM
            requestAnimationFrame(function() {{

                var map = L.map('map');
                var coords = [{route_js}];

                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);

                var poly = L.polyline(coords, {{color:'red',weight:6}}).addTo(map);

                map.fitBounds(poly.getBounds());

                L.marker(coords[0]).addTo(map).bindPopup("Start").openPopup();
                L.marker(coords[coords.length-1]).addTo(map).bindPopup("End");

                // 🔥 force resize fix
                setTimeout(function() {{
                    map.invalidateSize();
                }}, 300);

            }});
            </script>

            </div>
            """

    return PAGE % (options,result)

if __name__ == "__main__":
    app.run(debug=True)