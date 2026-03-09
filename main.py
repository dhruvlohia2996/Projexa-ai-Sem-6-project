import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
import os

def generate_graph():
    data = [120, 130, 125, 140, 150, 160, 170, 165, 180, 190]

    model = ARIMA(data, order=(1, 1, 1))
    model_fit = model.fit()

    forecast = model_fit.forecast(steps=5)

    os.makedirs("static", exist_ok=True)

    plt.figure()
    plt.plot(data, label="Historical Traffic")
    plt.plot(
        range(len(data), len(data) + len(forecast)),
        forecast,
        label="Predicted Traffic"
    )
    plt.legend()
    plt.savefig("static/traffic_prediction.png")
    plt.close()

if __name__ == "__main__":
    generate_graph()
