"""Only worker refreshes touch disk/network; navigation reads memory snapshots."""
from datetime import date
from pathlib import Path
from time import time
from weakref import WeakSet

from Components.MetrixNEO.settings import PROFILES, read_settings
from .cache import Cache
from .providers import WEATHER_CODES, fetch_weather, local_catalog

_state = {}
_busy = set()
_club_listeners = {}
_auto_clubs = {}
_club_seen = {}
_club_pending = {}
_club_active = False
_club_due = 0
_club_timer = None


def settings_for(profile, fallback):
    return _state.get(profile, {}).get("settings", fallback)


def watch_clubs(profile, listener):
    if profile in PROFILES:
        _club_listeners.setdefault(profile, WeakSet()).add(listener)


def unwatch_clubs(profile, listener):
    _club_listeners.get(profile, set()).discard(listener)


def _notify_clubs(profile):
    for listener in list(_club_listeners.get(profile, ())):
        try:
            listener.changed((listener.CHANGED_ALL,))
        except (AttributeError, RuntimeError):
            pass


def weather_text(profile):
    snapshot = _state.get(profile, {})
    weather = snapshot.get("weather")
    if not weather:
        return ""
    today = date.today().isoformat()
    days = [day for day in weather.get("days", []) if day["date"] >= today]
    if not days:
        return ""
    stale = snapshot.get("weather_expires", 0) <= time()
    label = " · cache hors ligne" if stale else ""
    return "  |  ".join("%s %s %.0f/%.0f°" % (day["date"][5:], WEATHER_CODES.get(day["code"], "Météo"), day["low"], day["high"]) for day in days[:3]) + label


def weather_day(profile, index):
    snapshot = _state.get(profile, {})
    weather = snapshot.get("weather") or {}
    if index == -1:
        current = weather.get("current")
        return dict(current, stale=snapshot.get("weather_expires", 0) <= time()) if current else None
    if index < 0:
        return None
    days = [day for day in weather.get("days", []) if day["date"] >= date.today().isoformat()]
    if index >= len(days):
        return None
    return dict(days[index], stale=snapshot.get("weather_expires", 0) <= time())


def poster_path(event, profile):
    if event is None:
        return None
    return _state.get(profile, {}).get("catalog", {}).get((event.getEventName(), event.getBeginTime()))


def club_path(event, profile, role):
    if event is None or role not in ("home", "away"):
        return None
    key = (event.getEventName(), event.getBeginTime())
    clubs = _state.get(profile, {}).get("clubs", {})
    # A curated pair must exist for this exact event; a lone or unrelated logo
    # never establishes a match. Neither badge nor club identities are guessed.
    if all(key in clubs.get(side, {}) for side in ("home", "away")):
        return clubs[role][key]
    if not settings_for(profile,{"club_logos":True}).get("club_logos"):
        return None
    from Components.MetrixNEO.teams import event_snapshot, team_key
    snapshot = event_snapshot(event)
    pair = _auto_clubs.get(profile, {}).get(key, {})
    if snapshot and snapshot[1] and pair.get("teams") == tuple(map(team_key,snapshot[1])):
        return pair.get(role)
    return None


def _match_key(key, names):
    from Components.MetrixNEO.teams import team_key
    return key+tuple(map(team_key,names))


def request_clubs(event, profile, settings):
    """Main-thread memory-only queue; no service object enters the worker."""
    if profile not in PROFILES or not settings.get("club_logos"):
        return
    from Components.MetrixNEO.teams import event_snapshot
    snapshot = event_snapshot(event)
    if not snapshot or not snapshot[1]:
        return
    key,names = snapshot
    if _club_seen.get(profile, {}).get(_match_key(key,names), 0)>time():
        return
    _club_pending[profile] = key,names,dict(settings)
    _start_club_job()


def _resolve_clubs(profile, names, settings):
    from .club_logos import resolve_pair
    cache = Cache(Path("/tmp/metrix-neo-cache")/profile/"teams", settings["cache_mb"]*1024*1024//2)
    return resolve_pair(names,settings,cache)


def _start_club_job():
    global _club_active, _club_due, _club_timer
    if _club_active or not _club_pending:
        return
    profile = next(iter(_club_pending))
    key,names,unused_settings = _club_pending[profile]
    if _club_seen.get(profile,{}).get(_match_key(key,names),0)>time():
        _club_pending.pop(profile)
        _start_club_job()
        return
    from twisted.internet import reactor
    delay = _club_due-time()
    if delay>0:
        if _club_timer is None:
            def later():
                global _club_timer
                _club_timer = None
                _start_club_job()
            _club_timer = reactor.callLater(delay,later)
        return
    key,names,settings = _club_pending.pop(profile)
    settings = settings_for(profile,settings)
    if not settings.get("club_logos"):
        _start_club_job()
        return
    from twisted.internet.threads import deferToThread
    _club_active, _club_due = True, time()+20

    def done(pair):
        global _club_active
        _club_active = False
        seen = _club_seen.setdefault(profile,{})
        seen[_match_key(key,names)] = time()+(3600 if pair else 1800)
        while len(seen)>32:
            seen.pop(next(iter(seen)))
        if pair:
            entries = _auto_clubs.setdefault(profile,{})
            from Components.MetrixNEO.teams import team_key
            entries[key] = dict(pair,teams=tuple(map(team_key,names)))
            while len(entries)>32:
                entries.pop(next(iter(entries)))
        # Home, away and VS refresh together on the main thread. A listener
        # already zapped elsewhere always reads its current event afresh.
        _notify_clubs(profile)
        _start_club_job()
        return None

    deferToThread(_resolve_clubs,profile,names,settings).addCallbacks(done,lambda failure:done(None))


def _load(profile):
    settings = read_settings(profile)
    cache = Cache(Path("/tmp/metrix-neo-cache") / profile, settings["cache_mb"] * 1024 * 1024//2)
    weather = cache.get("weather", stale=True) if settings["weather"] else None
    expires = weather.get("expires", 0) if weather else 0
    try:
        if settings["weather"] and expires <= time():
            fresh = fetch_weather(settings)
            if fresh:
                fresh["expires"] = time() + settings["weather_ttl"]
                cache.put("weather", fresh, settings["weather_ttl"])
                weather, expires = fresh, fresh["expires"]
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        pass
    catalog, clubs = {}, {}
    if settings["posters"]:
        try:
            catalog = local_catalog("/media/hdd/metrix-neo/artwork")
            clubs = {role: local_catalog("/media/hdd/metrix-neo/artwork", role) for role in ("home", "away")}
        except (OSError, ValueError, TypeError):
            pass
    return {"weather": weather, "weather_expires": expires, "catalog": catalog, "clubs": clubs, "settings": settings}


def refresh(profile):
    if profile not in PROFILES or profile in _busy:
        return
    from twisted.internet.threads import deferToThread
    _busy.add(profile)

    def success(snapshot):
        _state[profile] = snapshot
        _busy.discard(profile)
        _notify_clubs(profile)

    def failed(failure):
        # No tracebacks containing provider URLs, credentials or channel references.
        _busy.discard(profile)
        return None

    deferToThread(_load, profile).addCallbacks(success, failed)
