from flask import Flask, render_template, request
import requests

app = Flask(__name__)

WEATHER_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    56: ("Freezing drizzle", "🌧️"),
    57: ("Heavy freezing drizzle", "🌧️"),
    61: ("Slight rain", "🌦️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Freezing rain", "🌧️"),
    67: ("Heavy freezing rain", "🌧️"),
    71: ("Slight snow", "🌨️"),
    73: ("Moderate snow", "❄️"),
    75: ("Heavy snow", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    85: ("Slight snow showers", "🌨️"),
    86: ("Heavy snow showers", "🌨️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with hail", "⛈️"),
    99: ("Heavy thunderstorm with hail", "⛈️"),
}


def get_weather_data(city):
    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    geo_params = {
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json",
    }
    geo_response = requests.get(geo_url, params=geo_params, timeout=10)
    geo_response.raise_for_status()
    geo_data = geo_response.json()

    results = geo_data.get("results")
    if not results:
        raise ValueError("City not found")

    first_result = results[0]
    latitude = first_result["latitude"]
    longitude = first_result["longitude"]
    place_name = first_result.get("name")
    country = first_result.get("country")

    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "timezone": "auto",
    }
    weather_response = requests.get(weather_url, params=weather_params, timeout=10)
    weather_response.raise_for_status()
    weather_data = weather_response.json()

    current = weather_data.get("current", {})
    code = current.get("weather_code", 0)
    description, icon = WEATHER_CODES.get(code, ("Unknown", "❔"))

    return {
        "city": place_name,
        "country": country,
        "temperature": round(current.get("temperature_2m", 0)),
        "humidity": current.get("relative_humidity_2m", 0),
        "wind_speed": round(current.get("wind_speed_10m", 0)),
        "description": description,
        "icon": icon,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        city = request.form.get("city", "").strip()
        if not city:
            error = "Please enter a city name."
        else:
            try:
                result = get_weather_data(city)
            except requests.RequestException:
                error = "Weather service is currently unavailable. Please try again later."
            except ValueError:
                error = "City not found. Please check the spelling and try again."

    return render_template("index.html", result=result, error=error)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
