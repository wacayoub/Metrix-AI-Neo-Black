"""Original code-drawn skin chrome/icons and original generated photo assets."""
import math
import shutil
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def rgb(color):
    return tuple(int(color[-6:][i:i+2], 16) for i in (0, 2, 4))


def rgba(color):
    # Enigma2 colors store inverse alpha (FF transparent, 00 opaque).
    return rgb(color) + ((255 - int(color[:2], 16)) if len(color) == 8 else 255,)


def gradient(size, top, bottom, radius=0, border=None, mid=None, direction="vertical"):
    width, height = size
    a, b = rgba(top), rgba(bottom)
    image = Image.new("RGBA", size)
    draw = ImageDraw.Draw(image)
    length = width if direction == "horizontal" else height
    for offset in range(length):
        ratio = offset / max(1, length - 1)
        start, end = a, b
        if mid:
            start, end = (a, rgba(mid)) if ratio <= .5 else (rgba(mid), b)
            ratio = ratio * 2 if ratio <= .5 else (ratio - .5) * 2
        c = tuple(round(start[i] + (end[i] - start[i]) * ratio) for i in range(4))
        draw.line((offset, 0, offset, height) if direction == "horizontal" else (0, offset, width, offset), fill=c)
    if radius:
        mask = Image.new("L", size)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1), radius, fill=255)
        image.putalpha(mask)
    if border:
        draw.rounded_rectangle((1, 1, width - 2, height - 2), radius, outline="#" + border, width=2)
    return image


def icon(name, size=128, visual_scale=1.0):
    # Four-times geometry for antialiased original monochrome icon assets.
    image = Image.new("RGBA", (512, 512))
    d = ImageDraw.Draw(image)
    ink = "#E9F0F8"
    def line(points, width=20):
        d.line(points, fill=ink, width=width, joint="curve")
    if name == "plugins":
        d.rounded_rectangle((90, 160, 425, 430), 22, fill=ink)
        d.ellipse((195, 75, 300, 205), fill=ink)
        d.ellipse((365, 235, 470, 345), fill=ink)
        # Transparent puzzle sockets are drawn directly, not cut from another asset.
        d.ellipse((45, 235, 150, 345), fill=(0, 0, 0, 0))
        d.ellipse((205, 370, 310, 475), fill=(0, 0, 0, 0))
    elif name in ("setup", "software"):
        # Eight flat teeth around a round hub, as in the approved settings icon.
        d.ellipse((104, 104, 408, 408), fill=ink)
        for i in range(8):
            angle = i * math.pi / 4
            points = [(256 + r*math.cos(angle) - t*math.sin(angle), 256 + r*math.sin(angle) + t*math.cos(angle)) for r,t in ((134,-30),(198,-30),(198,30),(134,30))]
            d.polygon(points, fill=ink)
        d.ellipse((187, 187, 325, 325), fill=(0, 0, 0, 0))
    elif name == "timers":
        d.ellipse((85, 85, 427, 427), outline=ink, width=29)
        line((256, 132, 256, 256, 337, 303), 24)
    elif name == "power":
        d.arc((80, 85, 432, 437), 310, 590, fill=ink, width=35)
        line((256, 55, 256, 265), 35)
    elif name == "info":
        d.ellipse((76, 76, 436, 436), fill=ink)
        d.ellipse((237, 137, 275, 175), fill=(0, 0, 0, 0))
        d.rounded_rectangle((236, 209, 277, 366), 10, fill=(0, 0, 0, 0))
    elif name in ("channels", "television"):
        d.rounded_rectangle((60, 94, 452, 345), 15, outline=ink, width=22)
        if name == "television":
            line((175, 25, 256, 92, 330, 25), 18)
            d.rounded_rectangle((91, 126, 362, 304), 13, outline=ink, width=16)
            for cy in (166, 229):
                d.ellipse((392, cy, 419, cy + 27), fill=ink)
            line((138, 345, 112, 392), 18)
            line((374, 345, 400, 392), 18)
        else:
            line((256, 345, 256, 412), 20)
            line((167, 414, 345, 414), 20)
    elif name == "files":
        d.rounded_rectangle((56, 158, 456, 407), 18, fill=ink)
        d.rounded_rectangle((66, 106, 235, 211), 16, fill=ink)
    elif name == "film":
        d.rounded_rectangle((72, 98, 440, 409), 18, outline=ink, width=22)
        d.polygon(((223, 174), (223, 334), (345, 254)), fill=ink)
        for y in (145, 218, 291, 364):
            d.rectangle((90, y, 119, y + 23), fill=ink)
            d.rectangle((394, y, 423, y + 23), fill=ink)
    elif name == "recordings":
        # Folded video file and small play inset, distinct from the context film strip.
        d.polygon(((118, 68), (326, 68), (407, 149), (407, 399), (118, 399)), fill=ink)
        d.polygon(((320, 76), (320, 156), (399, 156)), fill=(0, 0, 0, 0))
        d.rounded_rectangle((65, 222, 342, 419), 16, fill="#E9F0F8", outline=(0, 0, 0, 0), width=15)
        d.rounded_rectangle((90, 246, 316, 394), 10, fill=(0, 0, 0, 0))
        d.polygon(((171, 273), (171, 369), (250, 320)), fill=ink)
        line((113, 452, 412, 452), 20)
    elif name == "network":
        d.ellipse((75, 75, 437, 437), outline=ink, width=20)
        d.ellipse((165, 75, 347, 437), outline=ink, width=16)
        line((75, 256, 437, 256), 18)
        line((110, 155, 403, 155), 16)
        line((110, 357, 403, 357), 16)
    elif name == "theme":
        d.polygon(((90, 358), (327, 120), (410, 203), (172, 440), (72, 458)), fill=ink)
        d.line((310, 137, 393, 220), fill=(0, 0, 0, 0), width=16)
        d.polygon(((76, 447), (97, 375), (151, 429)), fill=(0, 0, 0, 0))
    else:
        # Open wrench crossing a screwdriver, rather than two closed rings.
        d.polygon(((100, 61), (158, 79), (188, 126), (181, 161), (350, 326), (391, 321), (434, 362), (429, 406), (398, 436), (354, 431), (317, 391), (322, 350), (155, 183), (116, 186), (77, 155), (61, 103), (106, 135), (135, 106)), fill=ink)
        d.ellipse((356, 358, 399, 402), fill=(0, 0, 0, 0))
        line((139, 364, 362, 140), 21)
        d.polygon(((347, 135), (386, 75), (423, 75), (424, 112), (365, 152)), fill=ink)
        d.polygon(((77, 379), (126, 330), (178, 382), (129, 431), (101, 431), (77, 406)), fill=ink)
    # Equal visual footprints: the clock and power glyph no longer look undersized.
    bounds = image.getbbox()
    cropped = image.crop(bounds)
    side = max(cropped.size)
    canvas = Image.new("RGBA", (side + 24, side + 24))
    canvas.alpha_composite(cropped, ((canvas.width - cropped.width) // 2, (canvas.height - cropped.height) // 2))
    extent = max(1, round(size * visual_scale))
    scaled = canvas.resize((extent, extent), Image.Resampling.LANCZOS)
    result = Image.new("RGBA", (size, size))
    result.alpha_composite(scaled, ((size-extent)//2, (size-extent)//2))
    return result


def weather_icon(name):
    canvas = Image.new("RGBA", (256, 256))
    d = ImageDraw.Draw(canvas)
    white, yellow = "#F0F5FA", "#FFE13A"
    def sun(cx=105, cy=101, radius=37):
        d.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), fill=yellow)
        for i in range(8):
            a = i * math.pi / 4
            d.line((cx + (radius+13)*math.cos(a), cy + (radius+13)*math.sin(a), cx + (radius+32)*math.cos(a), cy + (radius+32)*math.sin(a)), fill=yellow, width=9)
    if name == "moon":
        d.ellipse((44, 21, 213, 227), fill=white)
        d.ellipse((104, 3, 243, 170), fill=(0, 0, 0, 0))
    elif name == "sun":
        sun(128, 128, 48)
    elif name in ("wind", "fog"):
        for cy in (76, 128, 180):
            d.line((33, cy, 209, cy), fill=white, width=10)
            if name == "wind":
                d.arc((179, cy - 27, 234, cy + 27), 265, 90, fill=white, width=10)
    else:
        sun(92, 86, 32)
        d.ellipse((62, 100, 160, 191), fill=white)
        d.ellipse((110, 68, 209, 180), fill=white)
        d.ellipse((166, 124, 238, 193), fill=white)
        d.rectangle((98, 147, 206, 191), fill=white)
        if name in ("rain", "snow", "storm"):
            for cx in (99, 151, 203):
                if name == "snow":
                    d.line((cx, 204, cx, 235), fill=white, width=7)
                    d.line((cx-13, 213, cx+13, 226), fill=white, width=6)
                    d.line((cx-13, 226, cx+13, 213), fill=white, width=6)
                else:
                    d.line((cx, 204, cx-9, 232), fill="#16B8EE", width=10)
            if name == "storm":
                d.polygon(((137, 159), (115, 207), (144, 204), (132, 246), (180, 186), (150, 188), (166, 157)), fill=yellow)
    return canvas.resize((64, 64), Image.Resampling.LANCZOS)


def build_assets():
    from reference_design import channel_geometry
    from generate_skins import TOKENS
    from Components.MetrixNEO.context_menu import geometry
    for profile in ("MetrixNEO", "MetrixNEOAdvanced"):
        folder = ROOT / "skins" / profile / "assets"
        folder.mkdir(parents=True, exist_ok=True)
        from audio_design import build_assets as build_audio_assets
        build_audio_assets(folder)
        from timer_design import build_assets as build_timer_assets
        build_timer_assets(folder)
        gradient((1920, 1080), "03172A", "010B15", mid="041322").save(folder / "background.png")
        advanced = profile.endswith("Advanced")
        gradient((1872, 633 if advanced else 516), "03182A", "02111F", radius=14, border="124365", mid="031523").save(folder / "menu-frame.png")
        cg = geometry(profile)
        gradient(cg["frame"][2:], "03182A", "02111F", radius=14, border="124365", mid="031523").save(folder / "context-frame.png")
        prefix = "" if advanced else "classic_"
        gradient((cg["width"], cg["row"]), TOKENS[prefix + "selected_top"], TOKENS[prefix + "selected_bottom"], radius=6, border="158CDF", mid=TOKENS[prefix + "selected_mid"]).save(folder / "context-selection.png")
        gradient((830, 78), "041321", "020C16", radius=10, border="103850").save(folder / "header-strip.png")
        gradient((116, 54), "061D2F", "020D18", radius=6, border="123D59").save(folder / "keycap.png")
        g = channel_geometry(profile.endswith("Advanced"))
        _, _, w, h = g["list"]
        gradient((w + 4, h + 4), "031624", "03121F", radius=9, border="123E5A").save(folder / "channels-frame.png")
        dw, dh = g["detail"][2:]
        gradient((dw, dh), "041A2B", "031321", radius=9, border="123E5A").save(folder / "details-frame.png")
        rp = "" if advanced else "classic_"
        inset = 2 if advanced else 4
        selected = Image.new("RGBA", (w, g["row"]), "#" + TOKENS["panel"])
        inner = gradient((w-2*inset, g["row"]), TOKENS[rp + "row_selected_top"], TOKENS[rp + "row_selected_bottom"], radius=7, border=TOKENS["row_selection_rim"], mid=TOKENS[rp + "row_selected_mid"])
        selected.alpha_composite(inner, (inset, 0))
        sd = ImageDraw.Draw(selected)
        sd.line((inset+8, 0, w-inset-9, 0), fill="#" + TOKENS["row_selection_highlight"], width=1)
        selected.save(folder / "selection-row.png")
        gradient((620, 10), "29D2FB", "078DD5").save(folder / "progress.png")
        gradient((1920, 248), "031321", "010C13", mid="03121D").save(folder / "infobar-strip.png")
        gradient((744, 124), "04121D", "020E17", radius=14 if not advanced else 2, border="385166").save(folder / "infobar-weather.png")
        gradient((354, 118), "04121D", "020E17", radius=14 if not advanced else 2, border="385166").save(folder / "infobar-clock.png")
        gradient((137, 12), "00C9EE", "F03839", mid="44DE32", direction="horizontal").save(folder / "infobar-signal.png")
        moon = Image.new("RGBA", (256,256))
        md = ImageDraw.Draw(moon)
        md.ellipse((36,24,208,235),fill="#F9E9BA")
        md.ellipse((102,0,244,175),fill=(0,0,0,0))
        for cx,cy,r in ((202,39,10),(232,78,7),(184,14,5)):
            md.polygon(((cx,cy-r),(cx+3,cy-3),(cx+r,cy),(cx+3,cy+3),(cx,cy+r),(cx-3,cy+3),(cx-r,cy),(cx-3,cy-3)),fill="#F0F5FA")
        if advanced:
            moon=Image.new("RGBA",(256,256))
            md=ImageDraw.Draw(moon)
            md.ellipse((26,26,230,230),fill="#B4BDC5")
            md.ellipse((57,18,235,223),fill="#273039")
        else:
            shaded=gradient((256,256),"FFF8E4","EBCB75",mid="F9E9BA")
            shaded.putalpha(moon.getchannel("A"))
            moon=shaded
        moon.resize((96,96),Image.Resampling.LANCZOS).save(folder / "infobar-weather-moon.png")
        lock = Image.new("RGBA", (48,43))
        ld=ImageDraw.Draw(lock)
        ld.rectangle((0,0,47,42),outline="#A7B6C8",width=1)
        ld.arc((16,7,31,25),180,360,fill="#E9F0F8",width=3)
        ld.rounded_rectangle((13,18,34,34),2,fill="#E9F0F8")
        ld.ellipse((22,23,26,27),fill=(0,0,0,0))
        ld.rectangle((23,26,25,30),fill=(0,0,0,0))
        lock.save(folder / "infobar-lock.png")
        from infobar_assets import build_icons
        build_icons(folder,advanced)
        if advanced:
            from infobar_assets import build_guide
            build_guide(ROOT/"assets/source/infobar-icons-guide.png")
        footprints = {"plugins":.98, "setup":.82, "timers":.80, "power":.80, "info":.80,
                      "channels":.85, "files":.83, "recordings":.85, "software":.82,
                      "network":.80, "theme":.85, "tools":.90} if advanced else {
                      "plugins":1.0, "setup":.72, "timers":.74, "power":.90, "info":.78}
        for name in ("plugins", "setup", "timers", "power", "info", "channels", "television", "files", "recordings", "film", "software", "network", "theme", "tools"):
            icon(name, visual_scale=footprints.get(name, 1.0)).save(folder / ("menu-" + name + ".png"))
        icon("film", 230).save(folder / "context.png")
        for name in ("sun", "cloud", "moon", "rain", "storm", "snow", "fog", "wind"):
            weather_icon(name).save(folder / ("weather-" + name + ".png"))
        # EPGList loads these native paths in its graphical mode. Supplying the
        # same palette here also covers existing user preferences for that mode.
        epg = folder.parent / "epg"
        epg.mkdir(exist_ok=True)
        for name in ("OtherEvent", "CurrentEvent", "OtherService", "CurrentService", "RecordEvent", "ZapEvent", "TimeLineDate", "TimeLineTime"):
            gradient((400, 64), "09263B" if name.startswith(("Current", "TimeLine")) else "031A2B", "031523").save(epg / (name + ".png"))
        for name in ("SelectedCurrentEvent", "SelectedEvent", "SelectedRecordEvent", "SelectedZapEvent"):
            gradient((400, 64), TOKENS[prefix + "selected_top"], TOKENS[prefix + "selected_bottom"], mid=TOKENS[prefix + "selected_mid"]).save(epg / (name + ".png"))
        gradient((400, 64), "702B35", "471C27").save(epg / "RecordingEvent.png")
        for name in ("Top", "Bottom", "Left", "Right"):
            size = (400, 1) if name in ("Top", "Bottom") else (1, 64)
            Image.new("RGBA", size, "#123E5A").save(epg / ("Border" + name + ".png"))
            Image.new("RGBA", size, "#158CDF").save(epg / ("SelectedBorder" + name + ".png"))
        for name in ("information", "SelectedInformation"):
            icon("info", 32).save(epg / (name + ".png"))
        if profile.endswith("Advanced"):
            shutil.copyfile(ROOT / "assets/source/lounge-reference-generated.png", folder / "lounge-reference.png")
            # Remove only our obsolete generated runtime copy. Keep its original
            # source for traceability; the user explicitly rejected a city backdrop.
            obsolete = folder / "scenic-reference.png"
            if obsolete.is_file():
                obsolete.unlink()
