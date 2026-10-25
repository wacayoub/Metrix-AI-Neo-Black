"""Selected-service technical facts. Never reuse another channel's decoder data."""
from Components.Renderer.Label import Label
from Components.MetrixNEO.model import clean_text, is_stream


class MetrixNEOServiceFacts(Label):
    def __init__(self):
        Label.__init__(self)
        self.field = "summary"

    def applySkin(self, desktop, parent):
        for key, value in self.skinAttributes or []:
            if key == "neoField":
                self.field = value
        self.skinAttributes = [(k, v) for k, v in (self.skinAttributes or []) if k not in ("neoProfile", "neoField")]
        result = Label.applySkin(self, desktop, parent)
        self.changed((self.CHANGED_ALL,))
        return result

    def changed(self, what):
        self.text = ""
        if what[0] == self.CHANGED_CLEAR:
            return
        reference = getattr(self.source, "service", None)
        if reference is None or not hasattr(reference, "toString"):
            return
        try:
            import NavigationInstance
            from enigma import eServiceCenter, iServiceInformation
            ref = reference.toString()
            source_type = "IPTV" if is_stream(ref) else ""
            if not source_type:
                static_info = eServiceCenter.getInstance().info(reference)
                transponder = static_info.getInfoObject(reference, iServiceInformation.sTransponderData) if static_info else None
                source_type = (transponder or {}).get("tuner_type", "") if isinstance(transponder, dict) else ""
            navigation = NavigationInstance.instance
            playing = navigation.getCurrentlyPlayingServiceReference() if navigation else None
            if playing is None or playing.toString() != ref:
                self.text = clean_text(source_type, 70) if self.field in ("summary", "aspect_source") else ""
                return
            service = navigation.getCurrentService()
            info = service.info() if service else None
            if info is None:
                return
            width = info.getInfo(iServiceInformation.sVideoWidth)
            height = info.getInfo(iServiceInformation.sVideoHeight)
            codec = {0: "MPEG-2", 1: "H.264", 7: "HEVC"}.get(info.getInfo(iServiceInformation.sVideoType), "")
            resolution = "%d×%d" % (width, height) if min(width, height) > 0 else ""
            progressive_key = getattr(iServiceInformation, "sProgressive", None)
            progressive = info.getInfo(progressive_key) if progressive_key is not None else -1
            if height > 0 and progressive in (0, 1):
                resolution = "%d%s" % (height, "p" if progressive else "i")
            aspect_key = getattr(iServiceInformation, "sAspect", None)
            aspect = {0: "4:3", 1: "16:9"}.get(info.getInfo(aspect_key), "") if aspect_key is not None else ""
            tracks = service.audioTracks()
            audio = ""
            if tracks and tracks.getNumberOfTracks():
                track = tracks.getTrackInfo(tracks.getCurrentTrack())
                audio = " ".join(filter(None, (track.getDescription(), track.getLanguage())))
            if self.field == "video":
                self.text = "\n".join(filter(None, (resolution, codec)))
            elif self.field == "aspect_source":
                self.text = "\n".join(filter(None, (aspect, source_type)))
            elif self.field == "audio":
                self.text = clean_text(audio, 100)
            else:
                self.text = clean_text("  |  ".join(filter(None, (resolution, codec, source_type, audio))), 180)
        except (AttributeError, RuntimeError, TypeError, IndexError):
            self.text = ""
