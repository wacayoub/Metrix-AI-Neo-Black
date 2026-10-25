"""Measured infobar fields. No codec, encryption or HDR guessed from a title."""
from Components.MetrixNEO.model import clean_text


def read_facts(service, keys):
    result = {}
    if service is None:
        return result
    def value(name):
        try:
            info = service.info()
            key = getattr(keys, name, None)
            return info.getInfo(key) if info and key is not None else -1
        except (AttributeError, RuntimeError, TypeError):
            return -1
    try:
        w, h, fps = value("sVideoWidth"), value("sVideoHeight"), value("sFrameRate")
        if h > 0:
            result["BadgeResolution"] = "4K" if h >= 2160 else "FHD" if h >= 1080 else "HD" if h >= 720 else "SD"
        result["BadgeHDR"] = {1: "HDR", 2: "HDR10", 3: "HLG"}.get(value("sGamma"), "")
        result["BadgeCodec"] = {0: "MPEG2", 1: "H.264", 7: "HEVC"}.get(value("sVideoType"), "")
        result["BadgeCA"] = "CA" if value("sIsCrypted") == 1 else ""
        result["TechnicalResolution"] = f"{w} × {h}" if min(w,h)>0 else ""
        result["TechnicalFrameRate"] = f"{fps/1000:.2f}".rstrip("0").rstrip(".")+" fps" if fps>0 else ""
        aspect = value("sAspect")
        result["TechnicalAspect"] = "16:9" if aspect in (1,3,4,7,8,11,12,15,16) else "4:3" if aspect in (0,2,5,6,9,10,13,14) else ""
    except (TypeError, ValueError):
        pass
    audio, language = "", ""
    try:
        tracks = service.audioTracks()
        if tracks and tracks.getNumberOfTracks():
            track = tracks.getTrackInfo(tracks.getCurrentTrack())
            audio, language = clean_text(track.getDescription(), 50), clean_text(track.getLanguage(), 20)
    except (AttributeError, RuntimeError, TypeError, IndexError):
        pass
    upper = audio.upper()
    result["BadgeAudio"] = "ATMOS" if "ATMOS" in upper else "DD+" if any(v in upper for v in ("AC3+", "E-AC-3", "EAC3", "DD+")) else "AC3" if "AC3" in upper or "AC-3" in upper else "DTS" if "DTS" in upper else "AAC" if "AAC" in upper else ""
    # The full selected-track description is retained for the detailed screen;
    # the compact row uses a bounded, recognised audio format.
    result["TechnicalAudio"] = "Atmos" if result["BadgeAudio"] == "ATMOS" else result["BadgeAudio"]
    result["TechnicalLanguage"] = language.upper() if len(language)<=7 else ""
    result["VideoDetails"] = "  |  ".join(filter(None, (result.get("TechnicalResolution"), result.get("TechnicalFrameRate"), result.get("TechnicalAspect"), audio, language)))
    try:
        frontend = service.frontendInfo()
        data = (frontend.getAll(True) if frontend else {}) or {}
        tuner = data.get("tuner_type", "")
        result["SourceShort"] = "SAT" if tuner.startswith("DVB-S") else "TNT" if tuner.startswith("DVB-T") else "CABLE" if tuner.startswith("DVB-C") else ""
        if tuner.startswith("DVB-S"):
            orbit, frequency, rate = data.get("orbital_position"), data.get("frequency"), data.get("symbol_rate")
            orbit_text = (f"{(3600-orbit)/10:g}°W" if orbit>1800 else f"{orbit/10:g}°E") if type(orbit) is int and 0<=orbit<3600 else ""
            tuning = f"{frequency/1000:g} { {0:'H',1:'V',2:'L',3:'R'}.get(data.get('polarization'), '')}".strip() if type(frequency) is int and frequency>0 else ""
            if tuning and type(rate) is int and rate>0:
                tuning += f" {rate/1000:g}"
            result["TechnicalOrbital"] = orbit_text
            result["TechnicalTuning"] = tuning
            result["TunerDetails"] = "  |  ".join(filter(None,(tuner,orbit_text,tuning)))
    except (AttributeError, RuntimeError, TypeError, IndexError, ValueError):
        pass
    return result


def timeshift_status(service):
    """Delay from native PTS length-position only; no guessed time or seek action."""
    active=False
    try:
        shift=service.timeshift() if service else None
        active=bool(shift and shift.isTimeshiftActive())
        if not active:
            return ""
        seek=service.seek()
        length,position=seek.getLength(),seek.getPlayPosition()
        if len(length)==2 and len(position)==2 and length[0]==0 and position[0]==0:
            end,current=length[1],position[1]
            if type(end) is int and type(current) is int and end>0 and 0<=current<=end:
                return "+%d min" % ((end-current)//(90000*60))
    except (AttributeError, RuntimeError, TypeError, IndexError):
        pass
    return "TIMESHIFT" if active else ""
