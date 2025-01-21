import matplotlib
matplotlib.use("Agg")  # Non-GUI backend
from flask import Flask, request, jsonify, render_template, send_from_directory
import requests
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
import os

app = Flask(__name__)
app.config["STATIC_FOLDER"] = "static"
os.makedirs(app.config["STATIC_FOLDER"], exist_ok=True)

# WeatherStack API configuration
API_KEY = "YOUR API KEY"  # Replace with your WeatherStack API key
BASE_URL = "http://api.weatherstack.com/current"

def fetch_weather_data(location):
    params = {
        "access_key": API_KEY,
        "query": location
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if "error" in data:
        raise ValueError(f"Error fetching data: {data['error']['info']}")

    # Parse data
    temperature = data["current"]["temperature"]
    humidity = data["current"]["humidity"]
    rainfall = data["current"].get("precip", 0)  # Precipitation data
    return temperature, humidity, rainfall

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        location = request.json.get("location")
        if not location:
            return jsonify({"error": "Location is required"}), 400

        temp, humidity, rainfall = fetch_weather_data(location)

        # Create a DataFrame with dummy historical data for training
        historical_data = {
            "Temperature": [temp - i for i in range(10, 0, -1)],
            "Humidity": [humidity - i for i in range(10, 0, -1)],
            "Rainfall": [rainfall + i for i in range(10, 0, -1)],
        }
        df = pd.DataFrame(historical_data)

        # Features and target
        X = df[["Temperature", "Humidity"]]
        y = df["Rainfall"]

        # Split the dataset
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train the model
        model = LinearRegression()
        model.fit(X_train, y_train)

        # Make predictions
        y_pred = model.predict(X_test)

        # Evaluate the model
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        # Plot actual vs predicted rainfall
        plt.figure(figsize=(10, 6))
        plt.scatter(y_test, y_pred, color="blue", label="Predictions")
        plt.plot([min(y_test), max(y_test)], [min(y_test), max(y_test)], color="red", linestyle="--", label="Ideal Fit")
        plt.xlabel("Actual Rainfall")
        plt.ylabel("Predicted Rainfall")
        plt.title(f"Actual vs Predicted Rainfall for {location}")
        plt.legend()
        plot_path = os.path.join(app.config["STATIC_FOLDER"], "rainfall_prediction_plot.png")
        plt.savefig(plot_path)
        plt.close()

        return jsonify({
            "temperature": temp,
            "humidity": humidity,
            "rainfall": rainfall,
            "r2": r2
        })

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
