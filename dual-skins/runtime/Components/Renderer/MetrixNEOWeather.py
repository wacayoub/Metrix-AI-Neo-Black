from enigma import ePixmap
from Components.Renderer.Renderer import Renderer
from Components.MetrixNEO.settings import read_settings
from Tools.Directories import SCOPE_SKINS, resolveFilename


class MetrixNEOWeather(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.profile = "MetrixNEO"
        self.day = 0
        self.enabled = False
        self.last_icon = None
        self.infobar = False

    def applySkin(self, desktop, parent):
        attributes = []
        for key, value in self.skinAttributes or []:
            if key == "neoProfile":
                self.profile = value
            elif key == "neoDay":
                self.day = int(value)
            elif key == "neoInfobar":
                self.infobar = value == "1"
            else:
                attributes.append((key, value))
        self.skinAttributes = attributes
        self.enabled = read_settings(self.profile)["weather"]
        return Renderer.applySkin(self, desktop, parent)

    def changed(self, what):
        if self.instance is None:
            return
        self.instance.hide()
        if not self.enabled or what[0] == self.CHANGED_CLEAR:
            return
        try:
            from Plugins.Extensions.MetrixNEOHelper.service import weather_day
            day = weather_day(self.profile, self.day)
        except (ImportError, ValueError, OSError):
            return
        if day is None:
            return
        code = day["code"]
        icon = "sun" if code == 0 else "cloud" if code in (1, 2, 3) else "fog" if code in (45, 48) else "snow" if code in (71, 73, 75, 77, 85, 86) else "storm" if code in (95, 96, 99) else "rain" if 50 <= code <= 82 else None
        if code == 0 and day.get("is_day") == 0:
            icon = "moon"
        if icon:
            if icon != self.last_icon:
                prefix = "infobar-weather-" if self.infobar and icon == "moon" else "weather-"
                self.instance.setPixmapFromFile(resolveFilename(SCOPE_SKINS, self.profile + "/assets/" + prefix + icon + ".png"))
                self.last_icon = icon
            self.instance.show()
