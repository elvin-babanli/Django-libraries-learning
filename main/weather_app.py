from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse

import requests
from collections import defaultdict
from datetime import datetime, timezone as tz


def _get_json(url, params, timeout=25):
    try:
        r = requests.get(url, params=params, timeout=timeout)
        try:
            return r.status_code, r.json(), None
        except Exception:
            return r.status_code, {"message": r.text}, None
    except requests.exceptions.Timeout:
        return 0, None, "timeout"
    except requests.exceptions.RequestException as e:
        return 0, None, f"network_error: {str(e)}"


def _fmt_local_hhmm(unix_ts: int, tz_offset_seconds: int):
    """
    OpenWeather sunrise/sunset -> UTC timestamp + timezone offset seconds.
    Local time = utc_ts + offset
    """
    if not unix_ts:
        return None
    return datetime.fromtimestamp(unix_ts + tz_offset_seconds, tz=tz.utc).strftime("%H:%M")


def _day_length_str(sunrise_ts: int, sunset_ts: int):
    if not sunrise_ts or not sunset_ts or sunset_ts <= sunrise_ts:
        return "—"
    secs = sunset_ts - sunrise_ts
    h = secs // 3600
    m = (secs % 3600) // 60
    return f"{int(h)}h {int(m)}m"


def _fetch_weather(city: str):
    """
    Kamran format (frontend JS bunu gözləyir):
      {
        "current": {
          "city","country","description",
          "temp","feels_like","temp_min","temp_max",
          "humidity","wind_speed","clouds",
          "lat","lon",
          "timezone","sunrise","sunset"
        },
        "daily": [
          {"date":"YYYY-MM-DD","min":...,"max":...,"description":...,"humidity":...,"wind_speed":...},
          ...
        ],
        "sun": {"sunrise":"HH:MM","sunset":"HH:MM","day_length":"Xh Ym"}
      }
    """
    api_key = getattr(settings, "OPENWEATHER_API_KEY", "")
    if not api_key:
        return None, "OPENWEATHER_API_KEY is not set in settings.py"

    # 1) geocode city -> lat/lon
    geo_url = "https://api.openweathermap.org/geo/1.0/direct"
    code, geo, err = _get_json(geo_url, {"q": city, "limit": 1, "appid": api_key})
    if err:
        return None, (
            "OpenWeather geocoding failed: "
            f"{err}. (Network/VPN/Firewall may block api.openweathermap.org)"
        )
    if code != 200 or not isinstance(geo, list) or not geo:
        return None, "City not found."

    lat = float(geo[0].get("lat", 0.0))
    lon = float(geo[0].get("lon", 0.0))
    country = geo[0].get("country", "")
    city_name = geo[0].get("name", city)

    # 2) current weather
    w_url = "https://api.openweathermap.org/data/2.5/weather"
    code, w, err = _get_json(w_url, {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"})
    if err:
        return None, f"OpenWeather current weather failed: {err}."
    if code != 200 or not isinstance(w, dict):
        msg = (w or {}).get("message", "weather fetch failed") if isinstance(w, dict) else "weather fetch failed"
        return None, msg

    weather0 = (w.get("weather") or [{}])[0]
    main = w.get("main", {}) or {}
    wind = w.get("wind", {}) or {}
    clouds = w.get("clouds", {}) or {}
    coord = w.get("coord", {}) or {}
    sys = w.get("sys", {}) or {}

    tz_offset = int(w.get("timezone", 0))  # seconds
    sunrise_ts = int(sys.get("sunrise", 0) or 0)
    sunset_ts = int(sys.get("sunset", 0) or 0)

    current = {
        "city": w.get("name", city_name),
        "country": country or sys.get("country", ""),

        "description": weather0.get("description", "—"),

        "temp": float(main.get("temp", 0.0)),
        "feels_like": float(main.get("feels_like", 0.0)),
        "temp_min": float(main.get("temp_min", 0.0)),
        "temp_max": float(main.get("temp_max", 0.0)),

        "humidity": int(main.get("humidity", 0)),
        "wind_speed": float(wind.get("speed", 0.0)),
        "clouds": int(clouds.get("all", 0)),

        "lat": float(coord.get("lat", lat)),
        "lon": float(coord.get("lon", lon)),

        "timezone": tz_offset,
        "sunrise": sunrise_ts,
        "sunset": sunset_ts,
    }

    sun = {
        "sunrise": _fmt_local_hhmm(sunrise_ts, tz_offset) or "—",
        "sunset": _fmt_local_hhmm(sunset_ts, tz_offset) or "—",
        "day_length": _day_length_str(sunrise_ts, sunset_ts),
    }

    # 3) 5-day forecast (3-hour) -> aggregate into daily summaries
    f_url = "https://api.openweathermap.org/data/2.5/forecast"
    code, f, err = _get_json(f_url, {"lat": lat, "lon": lon, "appid": api_key, "units": "metric"})
    if err:
        return None, f"OpenWeather forecast failed: {err}."
    if code != 200 or not isinstance(f, dict) or "list" not in f:
        msg = (f or {}).get("message", "forecast fetch failed") if isinstance(f, dict) else "forecast fetch failed"
        return None, msg

    by_date = defaultdict(list)
    for item in f.get("list", []):
        dt_txt = item.get("dt_txt")
        if not dt_txt or len(dt_txt) < 10:
            continue
        by_date[dt_txt[:10]].append(item)

    dates = sorted(by_date.keys())[:5]
    daily = []

    for d in dates:
        items = by_date[d]
        temps = [
            x.get("main", {}).get("temp")
            for x in items
            if isinstance(x.get("main", {}).get("temp"), (int, float))
        ]
        if not temps:
            continue

        tmin = float(min(temps))
        tmax = float(max(temps))

        # representative around 12:00 else middle
        rep = next((x for x in items if (x.get("dt_txt", "").endswith("12:00:00"))), None)
        if rep is None:
            rep = items[len(items) // 2]

        w0 = (rep.get("weather") or [{}])[0]
        rep_main = rep.get("main", {}) or {}
        rep_wind = rep.get("wind", {}) or {}

        daily.append({
            "date": d,
            "min": tmin,
            "max": tmax,
            "description": w0.get("description", "—"),
            "humidity": int(rep_main.get("humidity", 0)),
            "wind_speed": float(rep_wind.get("speed", 0.0)),
        })

    return {"current": current, "daily": daily, "sun": sun}, None


def weather_project_view(request):
    """
    Page render: base + weather_app.html
    Only passes 'city' so the input can prefill and auto-search.
    """
    city = (request.GET.get("city") or "").strip()
    return render(request, "weather_app.html", {"city": city})


def weather_api(request):
    """
    JS buranı çağırır: returns Kamran format with lat/lon
    """
    city = (request.GET.get("city") or "").strip()
    if not city:
        return JsonResponse({"error": "city is required"}, status=400)

    data, err = _fetch_weather(city)
    if err:
        return JsonResponse({"error": err}, status=503)

    return JsonResponse(data, status=200)
