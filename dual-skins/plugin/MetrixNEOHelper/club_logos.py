"""Worker-only TheSportsDB adapter. Exact identities, bounded cache, no UI I/O."""
import json
import re
import struct
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from Components.MetrixNEO.teams import team_key

SOURCE = "https://www.thesportsdb.com"
HOSTS = {"www.thesportsdb.com", "thesportsdb.com", "r2.thesportsdb.com"}


def allowed_url(url):
    try:
        parts = urlsplit(url)
        return parts.scheme == "https" and parts.hostname in HOSTS and parts.port in (None,443) and not parts.username and not parts.password and not parts.fragment
    except (TypeError, ValueError):
        return False


class ProviderRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        if not allowed_url(newurl):
            raise ValueError("Unexpected logo provider redirect")
        return super().redirect_request(request,response,code,message,headers,newurl)


def read_url(url, limit):
    if not allowed_url(url):
        raise ValueError("Unknown logo provider host")
    request = Request(url, headers={"User-Agent":"MetrixNEO/0.1 (optional team badges; TheSportsDB)"})
    with build_opener(ProviderRedirect()).open(request, timeout=5) as response:
        if not allowed_url(response.geturl()):
            raise ValueError("Unexpected logo response")
        content = response.read(limit+1)
    if len(content)>limit:
        raise ValueError("Logo provider response too large")
    return content


def select_team(payload, name):
    """Never accept the first fuzzy result or collapse reserves into seniors."""
    rows = payload.get("teams") if isinstance(payload,dict) else None
    if not isinstance(rows,list) or len(rows)>100:
        return None
    wanted, matches = team_key(name), {}
    for row in rows:
        if not isinstance(row,dict) or row.get("strSport") != "Soccer":
            continue
        names = [row.get("strTeam","")]
        alternate = row.get("strTeamAlternate") or ""
        if isinstance(alternate,str):
            names += re.split(r"[;,|]",alternate)
        if not any(isinstance(n,str) and team_key(n)==wanted for n in names):
            continue
        identity, badge = str(row.get("idTeam","")), row.get("strBadge")
        if identity.isascii() and identity.isdigit() and isinstance(badge,str) and allowed_url(badge):
            matches[identity] = {"id":identity,"name":row["strTeam"],"badge":badge,"source":SOURCE}
    return next(iter(matches.values())) if len(matches)==1 else None


def png_badge(content):
    if len(content)<33 or content[:16] != b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR":
        return False
    width,height = struct.unpack(">II",content[16:24])
    return 0<width<=1024 and 0<height<=1024


def team_badge(name, settings, cache):
    key = "team:"+team_key(name)
    saved = cache.get(key)
    image = cache.image_path(key)
    if isinstance(saved,dict):
        if saved.get("missing"):
            return None
        if image is not None:
            return dict(saved,path=str(image))
    old = cache.get(key,stale=True)
    if not settings["club_network_consent"]:
        return dict(old,path=str(image)) if isinstance(old,dict) and not old.get("missing") and image is not None else None
    try:
        query = urlencode({"t":team_key(name)})
        url = SOURCE+"/api/v1/json/"+settings["sports_api_key"]+"/searchteams.php?"+query
        candidate = select_team(json.loads(read_url(url,256*1024)),name)
        if candidate is None:
            cache.put(key,{"missing":True},1800)
            return None
        # Provider's small preview preserves the badge, without recolouring it.
        badge_url = candidate["badge"]
        if badge_url.lower().endswith(".png"):
            badge_url += "/small"
        content = read_url(badge_url,512*1024)
        if not png_badge(content):
            raise ValueError("Invalid badge image")
        path = cache.put_image(key,content)
        if path is None:
            return None
        cache.put(key,candidate,settings["poster_ttl"])
        return dict(candidate,path=str(path)) if path.is_file() else None
    except (OSError, ValueError, TypeError, KeyError, IndexError):
        return dict(old,path=str(image)) if isinstance(old,dict) and not old.get("missing") and image is not None else None


def resolve_pair(names, settings, cache):
    pair = [team_badge(name,settings,cache) for name in names]
    if all(pair) and pair[0]["id"] != pair[1]["id"]:
        # A tiny cache may evict the first image while loading the second.
        if all(cache.image_path("team:"+team_key(name)) is not None for name in names):
            return {role:badge["path"] for role,badge in zip(("home","away"),pair)}
    return None
