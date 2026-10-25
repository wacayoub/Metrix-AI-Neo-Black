"""Native source adapter. No network, writes, or estimated receiver metrics."""
from Components.Converter.Converter import Converter
from Components.Element import cached
from Components.MetrixNEO.model import clean_text, diagnostics, extract_metadata, is_stream, signal_percent
from Components.MetrixNEO.settings import read_settings


class MetrixNEOInfo(Converter):
    range = 100

    def __init__(self, arguments):
        Converter.__init__(self, arguments)
        self.mode, _, self.profile = arguments.partition(",")
        self.profile = self.profile or "MetrixNEO"
        self.settings = read_settings(self.profile)

    def _reference(self):
        try:
            import NavigationInstance
            ref = NavigationInstance.instance.getCurrentlyPlayingServiceReference()
            return ref.toString() if ref else ""
        except (AttributeError, ImportError):
            return ""

    def _signal(self):
        if is_stream(self._reference()):
            return None
        return signal_percent(getattr(self.source, self.mode[:3].lower(), None))

    @cached
    def getValue(self):
        value = self._signal()
        return value if value is not None else 0

    value = property(getValue)

    @cached
    def getBoolean(self):
        if self.mode.startswith(("SNR", "AGC")):
            return self._signal() is not None
        return bool(self.text)

    boolean = property(getBoolean)

    @cached
    def getText(self):
        if self.mode.startswith(("SNR", "AGC")):
            value = self._signal()
            if self.mode.endswith("Label"):
                return self.mode[:3] if value is not None else ""
            if self.mode.endswith("Percent"):
                return "%d%%" % value if value is not None else ""
            return "" if value is None else "%s %d %%" % (self.mode, value)
        if self.mode in ("Record", "RecordLabel"):
            return ("REC" if self.mode == "RecordLabel" else "● REC") if getattr(self.source, "boolean", False) else ""
        if self.mode.startswith("Weather"):
            try:
                from Plugins.Extensions.MetrixNEOHelper.service import weather_day, weather_text
                if not self.settings["weather"]:
                    return ""
                if self.mode == "Weather":
                    return weather_text(self.profile)
                if self.mode in ("WeatherTodayRange","WeatherTodayLabel"):
                    today=weather_day(self.profile,0)
                    if self.mode == "WeatherTodayLabel":
                        from datetime import date
                        return ("Aujourd’hui" if today["date"] == date.today().isoformat() else date.fromisoformat(today["date"]).strftime("%a")) if today else ""
                    return "%.0f°   %.0f°" % (today["high"],today["low"]) if today else ""
                if self.mode in ("WeatherCurrent", "WeatherLocation", "WeatherTemperature", "WeatherTemperatureCompact", "WeatherCondition"):
                    current = weather_day(self.profile, -1)
                    if current:
                        if self.mode == "WeatherLocation":
                            return current["label"]
                        if self.mode == "WeatherTemperature":
                            return "%.0f°C%s" % (current["temperature"], " · cache" if current["stale"] else "")
                        if self.mode == "WeatherTemperatureCompact":
                            return "%.0f°%s" % (current["temperature"], " · cache" if current["stale"] else "")
                        if self.mode == "WeatherCondition":
                            from Plugins.Extensions.MetrixNEOHelper.providers import WEATHER_CODES
                            return WEATHER_CODES.get(current.get("code"), "")
                        return "%s\n%.0f°C%s" % (current["label"], current["temperature"], " · cache" if current["stale"] else "")
                    return ""
                day = weather_day(self.profile, int(self.mode[-1]) - 1)
                if day:
                    from datetime import date
                    if self.mode.startswith("WeatherDay"):
                        return date.fromisoformat(day["date"]).strftime("%a")
                    if self.mode.startswith("WeatherRange"):
                        return "%.0f°/%.0f°%s" % (day["high"], day["low"], " · cache" if day["stale"] else "")
                    if self.mode.startswith("WeatherHigh"):
                        return "%.0f°" % day["high"]
                    if self.mode.startswith("WeatherLow"):
                        return "%.0f°" % day["low"]
                    return "%s\n%.0f°/%.0f°%s" % (date.fromisoformat(day["date"]).strftime("%a"), day["high"], day["low"], " · cache" if day["stale"] else "")
                return ""
            except (ImportError, ValueError, OSError):
                return ""
        event = getattr(self.source, "event", None)
        if self.mode == "NextSummary":
            if event is None:
                return ""
            try:
                from time import localtime, strftime
                start, duration = event.getBeginTime(), event.getDuration()
                if start <= 0 or duration <= 0:
                    return ""
                times = strftime("%H:%M", localtime(start)) + " – " + strftime("%H:%M", localtime(start+duration))
                return "Suivant : " + clean_text(event.getEventName(), 160) + "\n" + times
            except (AttributeError, TypeError, ValueError):
                return ""
        if self.mode == "Match":
            if event is None:
                return ""
            try:
                from Plugins.Extensions.MetrixNEOHelper.service import club_path, settings_for, watch_clubs
                watch_clubs(self.profile,self)
                settings = settings_for(self.profile,self.settings)
                if not (settings.get("posters") or settings.get("club_logos")):
                    return ""
                return "VS" if club_path(event, self.profile, "home") and club_path(event, self.profile, "away") else ""
            except (ImportError, AttributeError):
                return ""
        if self.mode in ("Next1", "Next2"):
            from Components.MetrixNEO.events import upcoming_text
            reference = getattr(self.source, "service", None)
            return upcoming_text(event, reference, 0 if self.mode == "Next1" else 1)
        if self.mode == "Smart":
            if not event or not self.settings["smart_epg"]:
                return ""
            metadata = extract_metadata(event.getEventName(), event.getExtendedDescription())
            if metadata["season"] is not None:
                return "S%02dE%02d" % (metadata["season"], metadata["episode"])
            return ""
        service = getattr(self.source, "service", None)
        if self.mode == "TimeshiftCompact":
            from Components.MetrixNEO.infobar_facts import timeshift_status
            return timeshift_status(service)
        if self.mode.startswith(("Badge", "Technical")) or self.mode in ("VideoDetails", "TunerDetails", "SourceShort"):
            if service is None:
                return ""
            if self.mode == "SourceShort" and is_stream(self._reference()):
                return "IPTV"
            try:
                from enigma import iServiceInformation
                from Components.MetrixNEO.infobar_facts import read_facts
                return read_facts(service, iServiceInformation).get(self.mode, "")
            except ImportError:
                return ""
        if self.mode == "Timeshift":
            try:
                shift = service.timeshift() if service else None
                return "TIMESHIFT" if shift and shift.isTimeshiftActive() else ""
            except (AttributeError, RuntimeError):
                return ""
        if self.mode == "Quality":
            if service is None:
                return ""
            try:
                from enigma import iServiceInformation
                info = service.info() if service else None
                if not info:
                    return ""
                width = info.getInfo(iServiceInformation.sVideoWidth)
                height = info.getInfo(iServiceInformation.sVideoHeight)
                fps = info.getInfo(iServiceInformation.sFrameRate)
                codec = {0: "MPEG-2", 1: "H.264", 7: "HEVC"}.get(info.getInfo(iServiceInformation.sVideoType), "")
                gamma = {1: "HDR", 2: "HDR10", 3: "HLG"}.get(info.getInfo(iServiceInformation.sGamma), "")
                size = "%d×%d" % (width, height) if width > 0 and height > 0 else ""
                quality = "4K" if height >= 2160 else "FHD" if height >= 1080 else "HD" if height >= 720 else "SD" if height > 0 else ""
                rate = "%g fps" % (fps / 1000) if fps > 0 else ""
                return " · ".join(filter(None, (quality, size, codec, rate, gamma)))
            except (AttributeError, RuntimeError, TypeError):
                return ""
        if self.mode == "Audio":
            try:
                tracks = service.audioTracks() if service else None
                if tracks and tracks.getNumberOfTracks():
                    track = tracks.getTrackInfo(tracks.getCurrentTrack())
                    return clean_text(" · ".join(filter(None, (track.getDescription(), track.getLanguage()))), 120)
            except (AttributeError, RuntimeError, IndexError):
                pass
            return ""
        if self.mode == "Source":
            if is_stream(self._reference()):
                return "IPTV"
            try:
                frontend = service.frontendInfo() if service else None
                data = frontend.getAll(True) if frontend else {}
                return clean_text((data or {}).get("tuner_type", ""), 40)
            except (AttributeError, RuntimeError):
                return ""
        if self.mode == "Diagnostics" and self.settings["diagnostics"]:
            try:
                tracks = service.audioTracks() if service else None
                info = service.info() if service else None
                current_event = info.getEvent(0) if info else None
                return " · ".join(diagnostics(
                    audio_tracks=tracks.getNumberOfTracks() if tracks else None,
                    epg=bool(current_event) if service else None,
                ))
            except (AttributeError, RuntimeError):
                return ""
        return ""

    text = property(getText)
