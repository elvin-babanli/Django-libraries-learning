import requests
from django.conf import settings
from django.shortcuts import render


def fetch_weather(city: str):
    api_key = getattr(settings, "OPENWEATHER_API_KEY", None)
    if not api_key:
        return None, "Error: API key not configured in settings.py"

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": "metric"}

    try:
        resp = requests.get(url, params=params, timeout=10)
    except requests.RequestException as e:
        return None, f"Error: request failed ({e})"

    if resp.status_code == 200:
        data = resp.json()
        city_name = data["name"]
        temp = data["main"]["temp"]
        weather_desc = data["weather"][0]["description"]
        return f"Weather in {city_name}: {temp}°C, {weather_desc}", None
    else:
        return None, f"Error: {resp.status_code} – {resp.text}"


def weather_project_view(request):
    city = request.GET.get("city", "").strip()
    result, error = None, None

    if city:
        result, error = fetch_weather(city)

    return render(request, "weather_app.html", {
        "city": city,
        "result": result,
        "error": error,
    })
