"""Pure, conservative display rules, independently testable without Enigma2."""
import re
import unicodedata


def signal_percent(raw):
    # 65536 is used by FrontendStatus as an invalid-value sentinel.
    if isinstance(raw, bool) or not isinstance(raw, (float, int)):
        return None
    if not 0 <= raw <= 65535:
        return None
    return round(raw * 100 / 65535)


def is_stream(reference):
    reference = str(reference or "")
    return reference.split(":", 1)[0] in ("4097", "5001", "5002", "8193") or bool(
        re.search(r"https?(?:%3a|:)//", reference, re.I)
    )


def fit_rect(source_width, source_height, width, height):
    if min(source_width, source_height, width, height) <= 0:
        return (0, 0, 0, 0)
    scale = min(width / source_width, height / source_height)
    w, h = max(1, int(source_width * scale)), max(1, int(source_height * scale))
    return ((width - w) // 2, (height - h) // 2, w, h)


def clean_text(text, limit=4096):
    # Preserve Arabic, diacritics, natural direction and the programme language.
    text = unicodedata.normalize("NFC", str(text or ""))
    return "".join(c for c in text if c in "\n\t" or unicodedata.category(c) != "Cc")[:limit]


def extract_metadata(title, description="", genre=None):
    """Only explicit episode labels and native genres are accepted as evidence."""
    text = clean_text(title) + "\n" + clean_text(description)
    patterns = (
        r"\bS(\d{1,2})\s*E(\d{1,3})\b",
        r"\b(?:saison|season)\s*(\d{1,2})\s*[,;:–-]?\s*(?:épisode|episode|ep\.?)[\s:]*(\d{1,3})\b",
        r"الموسم\s*(\d{1,2})\s*[,،:–-]?\s*الحلقة\s*(\d{1,3})",
    )
    result = {"confidence": 0.0, "genre": genre, "season": None, "episode": None}
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            result.update(season=int(match[1]), episode=int(match[2]), confidence=1.0)
            break
    # A versus sign alone is not proof of a match or of team identities.
    return result


def next_events(events, current_end, count=2):
    unique = {}
    for event in events:
        start = event.get("start")
        duration = event.get("duration")
        if (isinstance(start, (int, float)) and isinstance(duration, (int, float))
                and start >= current_end and duration > 0 and event.get("title")):
            unique[(start, event.get("id"))] = event
    return sorted(unique.values(), key=lambda x: x["start"])[:count]


def diagnostics(*, stream=False, signal=None, audio_tracks=None, epg=None,
                recording=False, timeshift=False):
    result = []
    if not stream and signal is not None and signal < 25:
        result.append("Signal faible")
    if audio_tracks == 0:
        result.append("Aucune piste audio exposée")
    if epg is False:
        result.append("EPG indisponible")
    if recording:
        result.append("REC")
    if timeshift:
        result.append("Timeshift actif")
    return result
