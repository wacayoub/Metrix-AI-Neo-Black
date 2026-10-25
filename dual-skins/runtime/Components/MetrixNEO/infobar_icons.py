"""Closed icon vocabulary. A missing/unknown measured state has no icon."""
ICONS = {
    "resolution": {key: "resolution-"+key.lower() for key in ("4K", "FHD", "HD", "SD")},
    "hdr": {key: "hdr-"+key.lower() for key in ("HDR", "HDR10", "HLG")},
    "audio": {key: "audio-"+key.lower().replace('+','plus').replace('.','') for key in ("AC3", "DD+", "DTS", "AAC", "ATMOS")},
    "codec": {key: "codec-"+key.lower().replace('.','') for key in ("HEVC", "H.264", "MPEG2")},
    "source": {key: "source-"+key.lower() for key in ("SAT", "TNT", "CABLE", "IPTV")},
    "lock": {"CA": "lock"},
}


def icon_name(kind, text):
    if kind in ("record", "timeshift"):
        return kind if text else None
    return ICONS.get(kind, {}).get(text)
