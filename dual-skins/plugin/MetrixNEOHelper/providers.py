"""Explicit weather endpoint and read-only local artwork catalog."""
import datetime
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

WEATHER_CODES = {
    0: "Clair", 1: "Peu nuageux", 2: "Nuages", 3: "Couvert", 45: "Brouillard",
    48: "Brouillard", 51: "Bruine", 53: "Bruine", 55: "Bruine",
    61: "Pluie", 63: "Pluie", 65: "Pluie", 71: "Neige", 73: "Neige",
    75: "Neige", 80: "Averses", 81: "Averses", 82: "Averses",
    95: "Orage", 96: "Orage", 99: "Orage",
}


def fetch_weather(settings):
    if not (settings["weather"] and settings["network_consent"]):
        return None
    latitude, longitude = settings["latitude"], settings["longitude"]
    if latitude is None or longitude is None:
        return None
    query = urlencode({"latitude": latitude, "longitude": longitude,
                       "daily": "weather_code,temperature_2m_max,temperature_2m_min",
                       "current": "temperature_2m,weather_code,is_day",
                       "forecast_days": 4, "timezone": "Africa/Casablanca"})
    request = Request("https://api.open-meteo.com/v1/forecast?" + query,
                      headers={"User-Agent": "MetrixNEO/0.1 (optional non-commercial weather)"})
    # This function must only be called by the background worker, never a renderer.
    with urlopen(request, timeout=5) as response:
        if response.geturl().split("/", 3)[2] != "api.open-meteo.com":
            raise ValueError("Unexpected weather redirect")
        raw = response.read(128 * 1024 + 1)
    if len(raw) > 128 * 1024:
        raise ValueError("Weather response too large")
    payload = json.loads(raw)
    daily = payload["daily"]
    result = []
    for index, date in enumerate(daily["time"][:4]):
        datetime.date.fromisoformat(date)
        low, high = daily["temperature_2m_min"][index], daily["temperature_2m_max"][index]
        if low is None or high is None:
            continue
        result.append({"date": date, "code": daily["weather_code"][index], "low": float(low), "high": float(high)})
    current = payload.get("current") or {}
    measured = None
    if type(current.get("temperature_2m")) in (int, float) and type(current.get("weather_code")) is int:
        measured = {"temperature": float(current["temperature_2m"]), "code": current["weather_code"], "is_day": current.get("is_day"), "label": settings.get("weather_label", ""), "time": current.get("time")}
    return {"days": result, "current": measured, "attribution": "Open-Meteo.com · CC BY 4.0"}


def local_catalog(root, role="poster"):
    """Exact title+event timestamp match. No scraping or guessed artwork."""
    root = Path(root).resolve()
    path = root / "metadata.json"
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        return {}
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("Catalog must be a list")
    result = {}
    for row in rows[:2000]:
        if not isinstance(row, dict) or not row.get("license") or not row.get("source"):
            continue
        if role not in ("poster", "home", "away") or row.get("role", "poster") != role:
            continue
        if not isinstance(row.get("title"), str) or type(row.get("start")) is not int:
            continue
        poster = (root / str(row.get("image", ""))).resolve()
        if not poster.is_relative_to(root) or not poster.is_file() or poster.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        # Bound async decoding input and accept only image signatures.
        if poster.stat().st_size > 4 * 1024 * 1024:
            continue
        with poster.open("rb") as stream:
            signature = stream.read(8)
        if not (signature.startswith(b"\xff\xd8\xff") or signature == b"\x89PNG\r\n\x1a\n"):
            continue
        result[(row["title"], row["start"])] = str(poster)
    return result
