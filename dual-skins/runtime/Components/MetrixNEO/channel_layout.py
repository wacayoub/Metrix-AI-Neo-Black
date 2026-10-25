"""Shared detail geometry for native widgets and the offline XML simulator."""


def channel_geometry(advanced):
    if advanced:
        return {"list": (250, 178, 914, 760), "detail": (1178, 176, 536, 770), "row": 38, "image": (1194, 194, 504, 227), "service": (1200, 423), "title": (1200, 506), "progress": (1200, 554), "description": (1200, 578, 492, 192), "next": (1200, 784), "technical": (1200, 872)}
    return {"list": (24, 110, 1218, 900), "detail": (1260, 108, 642, 900), "row": 45, "image": (1278, 123, 604, 258), "service": (1287, 390), "title": (1287, 501), "progress": (1287, 548), "description": (1287, 578, 580, 216), "next": (1287, 818), "technical": (1287, 911)}


def detail_slots(profile, has_image):
    advanced = profile.endswith("Advanced")
    g = channel_geometry(advanced)
    sx, sy = g["service"]
    iw = g["image"][2]
    pw, ph = (180, 74) if advanced else (226, 94)
    shift = 0 if has_image else 227 if advanced else 255
    tx, ty = g["title"]
    px, py = g["progress"]
    slots = {
        (sx, sy): (sx, sy - shift, pw, ph),
        (sx + pw + 15, sy + 25): (sx + pw + 15, sy + 25 - shift, iw - pw - 25, 48),
        (tx, ty): (tx, ty - shift, iw - 16, 46),
        (px, py): (px, py - shift, iw - 16, 11),
    }
    x, y, w, h = g["description"]
    slots[(x, y)] = (x, y - shift, w, h + shift)
    return slots


class ChannelDetailLayout:
    def __init__(self, screen, profile):
        self.screen, self.profile = screen, profile
        self.entries = []
        self.state = None

    def capture(self):
        self.entries = []
        slots = detail_slots(self.profile, True)
        for renderer in self.screen.renderer:
            instance = getattr(renderer, "instance", None)
            if instance is None:
                continue
            # Aspect-preserving picons may already be centered within their frame.
            anchor = getattr(renderer, "frame_position", None)
            anchor = anchor if anchor is not None else instance.position()
            origin = anchor.x(), anchor.y()
            if origin in slots:
                self.entries.append((renderer, origin))

    def apply(self, has_image):
        if self.state == has_image:
            return
        from enigma import ePoint, eSize
        slots = detail_slots(self.profile, has_image)
        for renderer, origin in self.entries:
            x, y, w, h = slots[origin]
            if hasattr(renderer, "setFrame"):
                renderer.setFrame(ePoint(x, y), eSize(w, h))
            else:
                renderer.instance.move(ePoint(x, y))
                renderer.instance.resize(eSize(w, h))
        self.state = has_image

    def close(self):
        self.entries = []
        self.screen = None
