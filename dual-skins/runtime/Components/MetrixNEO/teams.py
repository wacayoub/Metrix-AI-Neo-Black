"""Conservative football pair extraction; no fuzzy or substring identities."""
import re
import unicodedata

ALIASES = {"barcelone": "barcelona", "fc barcelone": "barcelona",
           "psg": "paris saint germain", "paris sg": "paris saint germain"}


def team_key(value):
    value = unicodedata.normalize("NFKD", str(value)).casefold()
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = " ".join(re.sub(r"[^\w]+", " ", value, flags=re.UNICODE).split())
    value = ALIASES.get(value, value)
    words = value.split()
    while words and words[0] in ("fc", "cf"):
        words.pop(0)
    while words and words[-1] in ("fc", "cf"):
        words.pop()
    return " ".join(words)


def match_pair(title, short="", description=""):
    """Return two explicit names in EPG order, including reserve/women suffixes.

    The initial provider is football only. Other sports, multiple pairs and
    missing separators are deliberately not assigned a football badge.
    """
    context = " ".join((title, short, description))[:4096]
    if re.search(r"\b(basket(?:ball)?|rugby|hockey|tennis|handball|volley(?:ball)?)\b", context, re.I):
        return None
    for content in (title[:240], short[:400], description[:1200]):
        candidates = []
        for line in content.splitlines()[:8]:
            line = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", line).strip()
            line = re.sub(r"^\d{1,2}:\d{2}\s+", "", line)
            if ": " in line:
                line = line.rsplit(": ", 1)[1]
            line = re.sub(r"\s*[\[(](?:football|soccer|live|direct|en direct|rediffusion)[\])]\s*", " ", line, flags=re.I).strip()
            parts = re.split(r"\s+(?:vs?\.?|contre|[-–—])\s+|\s*/\s*", line, flags=re.I)
            if len(parts) != 2:
                continue
            names = tuple(part.strip() for part in parts)
            keys = tuple(team_key(name) for name in names)
            if any(not (3 <= len(key) <= 80) or not any(c.isalpha() for c in key) for key in keys) or keys[0] == keys[1]:
                continue
            candidates.append((names, keys))
        identities = {keys for names, keys in candidates}
        if identities:
            # A clear title takes precedence over prose about previous games.
            return candidates[0][0] if len(identities) == 1 else None
    return None


def event_snapshot(event):
    if event is None:
        return None
    try:
        title, start = event.getEventName(), event.getBeginTime()
        if not isinstance(title, str) or not (0 < len(title) <= 240) or type(start) is not int or start <= 0:
            return None
        def text(method):
            value = getattr(event, method, lambda: "")()
            return value[:1600] if isinstance(value, str) else ""
        return (title, start), match_pair(title, text("getShortDescription"), text("getExtendedDescription"))
    except (AttributeError, RuntimeError, TypeError, ValueError):
        return None
