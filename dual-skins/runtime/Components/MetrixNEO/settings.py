"""Transactional settings, confined to the NEO namespace; no global config save."""
import copy
import json
import os
import tempfile
from pathlib import Path

PROFILES = ("MetrixNEO", "MetrixNEOAdvanced")
DEFAULTS = {
    "weather": False, "posters": False, "smart_epg": True, "diagnostics": True,
    "compact": False, "large_text": False, "latitude": None, "longitude": None,
    "cache_mb": 32, "weather_ttl": 3600, "poster_ttl": 604800,
    "network_consent": False,
    "weather_label": "",
    "club_logos": False, "club_network_consent": False, "sports_api_key": "123",
}


def validate(data):
    if set(data) - set(DEFAULTS):
        raise ValueError("Unknown NEO setting")
    result = copy.deepcopy(DEFAULTS)
    result.update(data)
    if not isinstance(result["weather_label"], str) or len(result["weather_label"]) > 48:
        raise ValueError("weather_label")
    if not isinstance(result["sports_api_key"],str) or not (1 <= len(result["sports_api_key"]) <= 64 and result["sports_api_key"].isascii() and result["sports_api_key"].isdigit()):
        raise ValueError("sports_api_key")
    for key in ("weather", "posters", "smart_epg", "diagnostics", "compact", "large_text", "network_consent", "club_logos", "club_network_consent"):
        if type(result[key]) is not bool:
            raise ValueError(key)
    for key, low, high in (("cache_mb", 1, 128), ("weather_ttl", 900, 86400), ("poster_ttl", 3600, 2592000)):
        if type(result[key]) is not int or not low <= result[key] <= high:
            raise ValueError(key)
    for key, low, high in (("latitude", -90, 90), ("longitude", -180, 180)):
        value = result[key]
        if value is not None and (type(value) not in (int, float) or not low <= value <= high):
            raise ValueError(key)
    return result


class Settings:
    def __init__(self, root, profile):
        if profile not in PROFILES:
            raise ValueError("Unknown skin identity")
        self.path = Path(root) / (profile + ".json")
        self.saved = copy.deepcopy(DEFAULTS)
        try:
            self.saved = validate(json.loads(self.path.read_text(encoding="utf-8")))
        except (OSError, ValueError, TypeError):
            pass
        self.pending = copy.deepcopy(self.saved)

    def cancel(self):
        self.pending = copy.deepcopy(self.saved)

    def reset_preview(self):
        self.pending = copy.deepcopy(DEFAULTS)

    def save(self):
        data = validate(self.pending)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.is_file():
            self.path.with_suffix(".json.bak").write_bytes(self.path.read_bytes())
        fd, name = tempfile.mkstemp(prefix=".neo-", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        self.saved = copy.deepcopy(data)


def read_settings(profile):
    return Settings("/etc/enigma2/metrix-neo", profile).saved
