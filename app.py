from flask import Flask, render_template, request, jsonify
import requests
import time
import os

app = Flask(__name__)

# Minimal weather code -> (description, emoji)
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

# Simple in-memory TTL cache
CACHE = {}

def cache_get(key):
	item = CACHE.get(key)
	if not item:
		return None
	expires, value = item
	if time.time() > expires:
		del CACHE[key]
		return None
	return value


def cache_set(key, value, ttl=300):
	CACHE[key] = (time.time() + ttl, value)


def geocode_city(city, ttl=3600):
	key = f"geo:{city.lower()}"
	cached = cache_get(key)
	if cached:
		return cached

	geo_url = "https://geocoding-api.open-meteo.com/v1/search"
	params = {"name": city, "count": 1, "language": "en", "format": "json"}
	resp = requests.get(geo_url, params=params, timeout=10)
	try:
		resp.raise_for_status()
	except requests.HTTPError:
		if resp.status_code == 429:
			raise requests.HTTPError("Rate limited by geocoding API", response=resp)
		raise

	data = resp.json()
	results = data.get("results")
	if not results:
		raise ValueError("City not found")

	first = results[0]
	out = {
		"latitude": first.get("latitude"),
		"longitude": first.get("longitude"),
		"name": first.get("name"),
		"country": first.get("country"),
	}
	cache_set(key, out, ttl=ttl)
	return out


def get_current_weather_by_coords(lat, lon, ttl=300):
	key = f"current:{lat},{lon}"
	cached = cache_get(key)
	if cached:
		return cached

	weather_url = "https://api.open-meteo.com/v1/forecast"
	params = {
		"latitude": lat,
		"longitude": lon,
		"current_weather": True,
		"timezone": "auto",
	}
	resp = requests.get(weather_url, params=params, timeout=10)
	try:
		resp.raise_for_status()
	except requests.HTTPError:
		if resp.status_code == 429:
			raise requests.HTTPError("Rate limited by weather API", response=resp)
		raise

	data = resp.json()
	current = data.get("current_weather", {})
	code = current.get("weathercode", 0)
	desc, icon = WEATHER_CODES.get(code, ("Unknown", "❔"))
	out = {
		"temperature": round(current.get("temperature", 0)),
		"wind_speed": round(current.get("windspeed", 0)),
		"description": desc,
		"icon": icon,
	}
	cache_set(key, out, ttl=ttl)
	return out


def get_5_day_forecast(lat, lon, days=5, ttl=900):
	key = f"forecast:{lat},{lon}:{days}"
	cached = cache_get(key)
	if cached:
		return cached

	weather_url = "https://api.open-meteo.com/v1/forecast"
	params = {
		"latitude": lat,
		"longitude": lon,
		"daily": "temperature_2m_max,temperature_2m_min,weathercode",
		"timezone": "auto",
		"forecast_days": days,
	}
	resp = requests.get(weather_url, params=params, timeout=10)
	try:
		resp.raise_for_status()
	except requests.HTTPError:
		if resp.status_code == 429:
			raise requests.HTTPError("Rate limited by weather API", response=resp)
		raise

	data = resp.json()
	daily = data.get("daily", {})
	dates = daily.get("time", [])
	tmax = daily.get("temperature_2m_max", [])
	tmin = daily.get("temperature_2m_min", [])
	codes = daily.get("weathercode", [])

	days_out = []
	for i, date in enumerate(dates):
		code = codes[i] if i < len(codes) else 0
		desc, icon = WEATHER_CODES.get(code, ("Unknown", "❔"))
		days_out.append({
			"date": date,
			"tmax": round(tmax[i]) if i < len(tmax) else None,
			"tmin": round(tmin[i]) if i < len(tmin) else None,
			"description": desc,
			"icon": icon,
		})

	cache_set(key, days_out, ttl=ttl)
	return days_out


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
				geo = geocode_city(city)
				current = get_current_weather_by_coords(geo["latitude"], geo["longitude"])
				result = {
					"city": geo["name"],
					"country": geo["country"],
					"temperature": current["temperature"],
					"humidity": None,
					"wind_speed": current["wind_speed"],
					"description": current["description"],
					"icon": current["icon"],
				}
			except requests.HTTPError:
				error = "Weather service is currently unavailable or rate limited. Please try again later."
			except ValueError:
				error = "City not found. Please check the spelling and try again."

	return render_template("index.html", result=result, error=error)


@app.route("/suggest")
def suggest():
	q = request.args.get("q", "").strip()
	if not q:
		return jsonify([])

	# Proxy to geocoding API with small result set
	geo_url = "https://geocoding-api.open-meteo.com/v1/search"
	params = {"name": q, "count": 5, "language": "en", "format": "json"}
	resp = requests.get(geo_url, params=params, timeout=6)
	try:
		resp.raise_for_status()
	except requests.HTTPError:
		return jsonify([])

	data = resp.json()
	results = data.get("results", [])
	suggestions = []
	for r in results:
		suggestions.append({
			"name": r.get("name"),
			"country": r.get("country"),
			"latitude": r.get("latitude"),
			"longitude": r.get("longitude"),
		})
	return jsonify(suggestions)


@app.route("/forecast")
def forecast():
	city = request.args.get("city", "").strip()
	if not city:
		return render_template("forecast.html", city=None, days=None, error="No city provided")

	try:
		geo = geocode_city(city)
		days = get_5_day_forecast(geo["latitude"], geo["longitude"], days=5)
	except requests.HTTPError:
		return render_template("forecast.html", city=city, days=None, error="Weather service unavailable or rate limited.")
	except ValueError:
		return render_template("forecast.html", city=city, days=None, error="City not found.")

	return render_template("forecast.html", city=geo.get("name"), days=days, error=None)


if __name__ == "__main__":
	app.run(debug=True, host="0.0.0.0", port=5000)
