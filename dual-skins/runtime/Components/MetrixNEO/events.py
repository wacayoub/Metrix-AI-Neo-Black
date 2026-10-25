"""Read-only EPG queries. No provider or external plugin access."""
from time import localtime, strftime
from .model import clean_text, next_events


def upcoming_text(event, reference, index):
    if event is None or reference is None or not hasattr(reference, "toString"):
        return ""
    from enigma import eEPGCache
    end = event.getBeginTime() + event.getDuration()
    rows = eEPGCache.getInstance().lookupEvent(["IBDT", (reference.toString(), 0, end, 1440)]) or []
    events = next_events([{"id": row[0], "start": row[1], "duration": row[2], "title": row[3]} for row in rows], end)
    if index >= len(events):
        return ""
    item = events[index]
    return strftime("%H:%M", localtime(item["start"])) + "  " + clean_text(item["title"], 240)
