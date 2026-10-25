"""Schematic XML previews, never receiver screenshots. Pillow is build-only."""
import html
import math
import textwrap
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from generate_skins import ROOT, TOKENS

sys.path.insert(0, str(ROOT / "runtime"))
from Components.MetrixNEO.preferences import KEY_LABELS, NAVIGATION, categories_for, options_for, preview_text
from Components.MetrixNEO.settings import DEFAULTS
from Components.MetrixNEO.infobar_icons import icon_name

COLORS = {key: "#" + value[-6:] for key, value in TOKENS.items()}
# Prefer the same native font declared by skin.xml, read from the audited clone.
# The font itself is never copied into the skins or source archive.
FONTS = (ROOT / ".upstream/enigma2/data/fonts/LiberationSans-Regular.ttf", Path("C:/Windows/Fonts/segoeui.ttf"), Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
SCREENS = ("menu_mainmenu", "ChannelSelection", "ChannelSelectionText", "InfoBar", "SecondInfoBar", "GraphicalEPG", "EventView", "ChannelContextMenu", "Setup", "MetrixNEOSettings")
SCREEN_TITLES = dict(zip(SCREENS, ("Menu principal", "Liste des chaînes · image EPG disponible", "Liste des chaînes · sans image EPG", "Infobar", "Seconde infobar", "Guide EPG", "Détails du programme", "Menu contextuel", "Paramètres système", "Préférences NEO")))
NEO_MENU = ["Plugin Browser", "Paramètres", "Programmations", "Veille / Redémarrer", "Informations"]
ADVANCED_MENU = ["Plugin Browser", "Paramètres", "Éditeur de chaînes", "Programmations", "Fichiers · indisponible", "Enregistrements", "Logiciels", "Réseau", "Veille / Redémarrer", "Informations", "Thème & Skin", "Outils"]


def font(size, family="Regular"):
    if family in ("ChannelLight","AudioLight"):
        return ImageFont.truetype(str(ROOT/"skins/MetrixNEO/fonts/Raleway-Light.ttf"),size)
    candidates = (ROOT / ".upstream/enigma2/data/fonts/LiberationSans-Bold.ttf", Path("C:/Windows/Fonts/segoeuib.ttf"), Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")) if family == "MenuTitle" else FONTS
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default(size=size)


def color(value, default="foreground"):
    return COLORS.get(value, "#" + value[-6:] if value.startswith("#") else COLORS[default])


def assets(folder):
    folder.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (550, 706), COLORS["panel"])
    draw = ImageDraw.Draw(image)
    # Original procedural decor, not the missing approved salon photograph.
    draw.rectangle((0, 460, 550, 706), fill=COLORS["secondary"])
    draw.rectangle((66, 175, 484, 420), fill=COLORS["background"], outline=COLORS["muted"], width=2)
    draw.line((245, 420, 235, 445, 315, 445, 305, 420), fill=COLORS["muted"], width=3)
    draw.rounded_rectangle((35, 510, 505, 620), 10, fill="#25394A", outline="#456071", width=2)
    draw.line((90, 520, 90, 610), fill="#456071", width=2)
    draw.line((460, 520, 460, 610), fill="#456071", width=2)
    draw.ellipse((40, 95, 55, 110), fill=COLORS["accent"])
    image.save(folder / "lounge.png")
    Image.new("RGB", (3, 660), COLORS["accent"]).save(folder / "timeline.png")
    for name, text in (("context", "≡"), ("question", "?"), ("info", "i"), ("warning", "!"), ("error", "!")):
        icon = Image.new("RGBA", (230 if name == "context" else 64,) * 2, (0, 0, 0, 0))
        d = ImageDraw.Draw(icon)
        size = icon.width
        d.rounded_rectangle((3, 3, size - 4, size - 4), 8, outline=COLORS["muted"], width=3)
        d.text((size // 2, size // 2), text, font=font(size * 2 // 3), fill=COLORS["foreground"], anchor="mm")
        icon.save(folder / (name + ".png"))
    for name in ("sun", "cloud", "moon", "rain", "storm", "snow", "fog", "wind"):
        icon = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        d = ImageDraw.Draw(icon)
        ink = "#F0D558" if name == "sun" else COLORS["foreground"]
        if name == "sun":
            d.ellipse((22, 22, 42, 42), outline=ink, width=3)
            for i in range(8):
                angle = i * math.pi / 4
                d.line((32 + 17 * math.cos(angle), 32 + 17 * math.sin(angle), 32 + 25 * math.cos(angle), 32 + 25 * math.sin(angle)), fill=ink, width=3)
        elif name == "moon":
            d.ellipse((12, 8, 52, 54), fill=ink)
            d.ellipse((26, 2, 61, 43), fill=(0, 0, 0, 0))
        elif name == "wind":
            for y in (20, 32, 44):
                d.line((9, y, 48, y), fill=ink, width=3)
                d.arc((43, y - 8, 58, y + 8), 250, 80, fill=ink, width=3)
        elif name == "fog":
            for y in (18, 30, 42, 54):
                d.line((10, y, 54, y), fill=ink, width=3)
        else:
            d.arc((12, 17, 33, 43), 140, 280, fill=ink, width=3)
            d.arc((23, 10, 48, 40), 175, 345, fill=ink, width=3)
            d.arc((37, 23, 57, 43), 240, 70, fill=ink, width=3)
            d.line((18, 41, 50, 41), fill=ink, width=3)
            if name == "rain":
                for x in (21, 34, 47):
                    d.line((x, 48, x - 3, 56), fill=COLORS["accent"], width=3)
            elif name == "storm":
                d.line((35, 43, 29, 52, 38, 52, 31, 61), fill=COLORS["accent"], width=3)
            elif name == "snow":
                for x in (22, 42):
                    d.line((x, 47, x, 59), fill=ink, width=2)
                    d.line((x - 5, 50, x + 5, 56), fill=ink, width=2)
                    d.line((x - 5, 56, x + 5, 50), fill=ink, width=2)
        icon.save(folder / ("weather-" + name + ".png"))


def text_box(draw, box, text, size, fill, align="left", family="Regular", valign="top", no_wrap=False):
    x, y, width, height = box
    face = font(size, family)
    lines = []
    for paragraph in (str(text).splitlines() if not no_wrap else [str(text).replace("\n", " ")]):
        line = ""
        for word in paragraph.split():
            candidate = (line + " " + word).strip()
            if not no_wrap and draw.textlength(candidate, font=face) > width and line:
                lines.append(line)
                line = word
            else:
                line = candidate
        lines.append(line)
    line_height = max(size + 2, round(size * 1.15))
    max_lines = max(1, height // line_height)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = lines[-1].rstrip(" .") + "…"
    ascent, descent = face.getmetrics()
    total_height = len(lines) * line_height
    top = y + max(0,(height-total_height)//2) if valign == "center" else y + max(0,height-total_height) if valign == "bottom" else y
    for index, line in enumerate(lines):
        while draw.textlength(line, font=face) > width and len(line) > 1:
            line = line[:-2] + "…"
        offset = width - draw.textlength(line, font=face) if align == "right" else (width - draw.textlength(line, font=face)) // 2 if align == "center" else 0
        if valign in ("center", "bottom"):
            baseline = top + index*line_height + (line_height-ascent-descent)//2 + ascent
            draw.text((x + offset, baseline), line, font=face, fill=fill, anchor="ls")
        else:
            draw.text((x + offset, top + index * line_height), line, font=face, fill=fill)


def sample_text(node, screen_name, profile="MetrixNEO", category="presentation"):
    source, name = node.get("source", ""), node.get("name", "")
    converter = node.find("convert")
    token = converter.text if converter is not None else ""
    infobar = screen_name in ("InfoBar", "SecondInfoBar")
    if infobar:
        mode = (token or "").split(",")[0]
        technical = {"TechnicalResolution":"3840 × 2160", "TechnicalFrameRate":"50 fps", "TechnicalAspect":"16:9", "TechnicalAudio":"DD+" if profile.endswith("Advanced") else "Atmos", "TechnicalLanguage":"FRA", "TechnicalOrbital":"7°W", "TechnicalTuning":"11054 H 30000"}
        if mode in technical:
            return technical[mode]
        fixtures = {"BadgeResolution":"4K", "BadgeHDR":"HDR", "BadgeAudio":"AC3", "BadgeCodec":"HEVC", "BadgeCA":"CA", "SourceShort":"SAT", "VideoDetails":"3840 × 2160 | 50 fps | 16:9 | AC3 | FRA", "TunerDetails":"DVB-S2 | 7.0°W | 11054 H 30000", "Record":"● REC", "Timeshift":"TIMESHIFT", "Match":"VS", "NextSummary":"Suivant : Le débrief\n22:30 – 23:00", "SNRLabel":"SNR", "AGCLabel":"AGC", "SNRPercent":"72%" if profile.endswith("Advanced") else "82%", "AGCPercent":"68%" if profile.endswith("Advanced") else "76%"}
        if mode in fixtures:
            if mode == "BadgeAudio":
                return "DD+" if profile.endswith("Advanced") else "ATMOS"
            if mode == "VideoDetails":
                return "3840 × 2160 | 50 fps | 16:9 | DD+ | FRA" if profile.endswith("Advanced") else "3840 × 2160 | 50 fps | 16:9 | Atmos | FRA"
            return fixtures[mode]
        if mode == "RecordLabel":
            return "REC"
        if mode == "TimeshiftCompact":
            return "+116 min"
        if mode == "Number":
            return "9" if profile.endswith("Advanced") else "002"
        if mode in ("StartTime", "EndTime", "Remaining"):
            return {"StartTime":"20:15", "EndTime":"22:30", "Remaining":"+71 min"}[mode]
        if mode == "ShortDescription":
            return "La Liga · Journée 20"
        if mode == "Name":
            return "beIN SPORTS 1" if "Service" in source else "Le débrief" if source == "session.Event_Next" else "Real Madrid – Barcelona"
        if mode == "Smart":
            return ""
    if token and token.startswith("Weather"):
        mode = token.split(",")[0]
        if mode == "WeatherLocation":
            return "Casablanca"
        if mode == "WeatherCondition":
            return "Ciel dégagé"
        if mode == "WeatherTemperature":
            return "16°C"
        if mode == "WeatherTemperatureCompact":
            return "16°"
        if mode == "WeatherTodayLabel":
            return "Aujourd’hui"
        if mode == "WeatherTodayRange":
            return "22°   15°"
        if mode.startswith("WeatherDay"):
            if infobar and profile=="MetrixNEO":
                return ("Dim","Lun","Mar")[int(mode[-1])-2]
            return ("Sam", "Dim", "Lun")[int(mode[-1]) - 1]
        if mode.startswith("WeatherRange"):
            if infobar and profile=="MetrixNEO":
                return ("18°/12°","17°/11°","18°/12°")[int(mode[-1])-2]
            return ("24°/16°", "23°/16°", "20°/15°")[int(mode[-1]) - 1]
        if mode.startswith("WeatherHigh"):
            return ("24°","24°","23°")[int(mode[-1])-1]
        if mode.startswith("WeatherLow"):
            return ("16°","17°","17°")[int(mode[-1])-1]
        return ""  # These are explicitly labelled offline fixtures, never runtime data.
    if source == "global.CurrentTime":
        if infobar:
            return "23:19" if "%H" in (token or "") else "Samedi\n24 Octobre" if "\n" in (token or "") else "Samedi 24 octobre 2026"
        return "20:45" if "%H" in (token or "") else "Samedi\n24 Octobre 2026"
    if source == "Title":
        return {"menu_mainmenu": "Menu principal", "ChannelSelection": "Chaînes · Favoris", "GraphicalEPG": "Guide des programmes", "Setup": "Paramètres audio", "MetrixNEOSettings": ("NEO Advanced" if profile.endswith("Advanced") else "NEO") + " · Préférences"}.get(screen_name, screen_name)
    if source.startswith("key_"):
        if screen_name == "MetrixNEOSettings":
            return KEY_LABELS.get(source, "")
        if screen_name == "Setup":
            # ConfigListScreen fullUI, Audio setup without allowDefault, French PO.
            return {"key_red": "Annuler", "key_green": "Sauvegarder"}.get(source, "")
        return {"key_red": "Retour", "key_green": "Sélectionner", "key_yellow": "Options", "key_blue": "Bouquets"}.get(source, "")
    if screen_name == "MetrixNEOSettings":
        if name == "preview":
            return preview_text()
        if name == "description":
            entries = options_for(profile, category)
            return entries[0][4] if entries else ""
        if name == "footnote":
            return NAVIGATION
    if screen_name == "Setup":
        if name == "description":
            return "Select the size of the volume step when the VOLUME buttons are pressed."
        if name == "footnote":
            return "Extrait Audio natif · valeurs de démonstration · les rubriques réelles dépendent du récepteur"
    if source == "description":
        return "MENU : toutes les fonctions natives. Les données de cet aperçu sont des exemples."
    if node.get("render") == "MetrixNEONext":
        return ("22:00  Programme suivant · exemple", "23:15  Deuxième programme · exemple")[int(node.get("neoIndex", "0"))]
    if token and token.startswith("Next"):
        return "22:00  Prochain programme (exemple)" if token.startswith("Next1") else "23:15  Deuxième programme (exemple)"
    if token and token.startswith(("SNR", "AGC", "Quality", "Audio", "Source", "Timeshift", "Diagnostics")):
        return ""  # Unknown states are hidden, rather than invented.
    if token and token.startswith("Smart"):
        return "S02E04 · exemple explicite"
    if source == "session.RecordState":
        return ""
    if token == "Name" and "Service" in source:
        return "Chaîne de démonstration"
    if token == "Name" or name == "channel":
        return "Horizons · Les routes du monde"
    if "Description" in (token or "") or name in ("description", "epg_description"):
        return "Un programme de démonstration permet de vérifier la hiérarchie des textes et la lisibilité. Les titres, descriptions et horaires seront fournis par l’EPG natif, sans modifier sa langue ni ses données."
    return {"datetime": "Dimanche · 20:45 – 22:00 · exemple", "duration": "75 min · exemple", "preview": "Émission · برنامج · Programme\nBleu nuit\nAnnuler conserve les réglages.", "categories": "Présentation\n\nMétéo\n\nImages\n\nSmart EPG\n\nDiagnostics\n\nRéseau / cache", "footnote": "Prévisualisation locale · aucune écriture système", "text": "Confirmer ou annuler avec les commandes natives"}.get(name, node.get("text", ""))


def render(profile, screen_name, category="presentation"):
    folder = ROOT / "skins" / profile
    dom = ET.parse(folder / "skin.xml").getroot()
    screens = {s.get("name"): s for s in dom.findall("screen")}
    image = Image.new("RGB", (1920, 1080), COLORS["background"])
    draw = ImageDraw.Draw(image)
    advanced = profile.endswith("Advanced")
    if screen_name in ("InfoBar", "SecondInfoBar"):
        draw.rectangle((0, 0, 1919, 1079), fill="#25323D")
        draw.text((960, 440), "Zone vidéo · non représentée", font=font(36), fill=COLORS["muted"], anchor="mm")

    def visit(screen_node, visited=()):
        for node in screen_node:
            if node.tag == "panel":
                name = node.get("name")
                if name in screens and name not in visited:
                    visit(screens[name], visited + (name,))
                continue
            if node.tag not in ("eLabel", "ePixmap", "widget"):
                continue
            condition = node.get("conditional", "")
            if screen_name == "Setup" and condition.startswith("key_") and condition not in ("key_red", "key_green"):
                continue
            try:
                x, y = map(int, node.get("position", "0,0").split(","))
                width, height = map(int, node.get("size", "0,0").split(","))
            except ValueError:
                continue
            box = x, y, width, height
            background = node.get("backgroundColor")
            if background and node.get("transparent") != "1":
                draw.rectangle((x, y, x + width - 1, y + height - 1), fill=color(background))
            if node.tag == "ePixmap" or (node.get("render")=="Pixmap" and node.get("pixmap")):
                path = ROOT / "skins" / node.get("pixmap", "")
                if path.is_file():
                    asset = Image.open(path).convert("RGBA").resize((width, height))
                    image.paste(asset, (x, y), asset)
            elif node.get("render") == "MetrixNEOPicon":
                draw.rounded_rectangle((x, y, x + width, y + height), 3, outline=COLORS["secondary"], width=2)
                draw.text((x + width // 2, y + height // 2), "beIN\nSPORTS 1" if screen_name in ("InfoBar", "SecondInfoBar") else "PICON", font=font(21), fill=COLORS["muted"], anchor="mm", align="center")
            elif node.get("render") == "MetrixNEOInfobarIcon":
                name=icon_name(node.get("neoKind"),sample_text(node,screen_name,profile,category))
                if name:
                    with Image.open(folder/"assets"/("infobar-icon-"+name+".png")) as source:
                        asset=source.convert("RGBA").resize((width,height),Image.Resampling.LANCZOS)
                    image.paste(asset,(x,y),asset)
            elif node.get("render") in ("MetrixNEOPoster", "MetrixNEOWeather"):
                if node.get("neoRole") in ("home", "away"):
                    # Typographic placeholders demonstrate licensed-club slots;
                    # the receiver only displays curated, exact-event artwork.
                    radius = min(width, height)//2-5
                    cx, cy = x+width//2, y+height//2
                    draw.ellipse((cx-radius,cy-radius,cx+radius,cy+radius), outline=COLORS["muted"], width=2)
                    draw.text((cx,cy), "RM" if node.get("neoRole")=="home" else "FCB", font=font(20), fill=COLORS["foreground"], anchor="mm")
                    continue
                if node.get("render") == "MetrixNEOPoster":
                    path = ROOT / "previews/fixtures/programme-demo-generated.png"
                else:
                    day=node.get("neoDay","0")
                    choices={"-1":"moon","0":"sun","1":"sun","2":"cloud","3":"rain"} if screen_name in ("InfoBar","SecondInfoBar") else {"-1":"moon","0":"sun","1":"cloud","2":"rain"}
                    name=choices[day]
                    path = folder / "assets" / (("infobar-weather-" if node.get("neoInfobar")=="1" and name=="moon" else "weather-") + name + ".png")
                with Image.open(path) as source:
                    asset = ImageOps.contain(source.convert("RGBA"), (width, height), method=Image.Resampling.LANCZOS)
                image.paste(asset, (x + (width-asset.width)//2, y + (height-asset.height)//2), asset)
            elif node.get("source") == "menu":
                labels = (ADVANCED_MENU if advanced else NEO_MENU) if screen_name == "menu_mainmenu" else NEO_MENU
                cols = 3 if advanced and screen_name == "menu_mainmenu" else len(labels) if screen_name == "menu_mainmenu" else 1
                rows = math.ceil(len(labels) / cols)
                for index, text in enumerate(labels):
                    tx = x + (index % cols) * width // cols
                    ty = y + (index // cols) * height // rows
                    tw, th = width // cols, height // rows
                    draw.rectangle((tx + 4, ty + 4, tx + tw - 4, ty + th - 4), fill=COLORS["selection"] if index == 1 else COLORS["panel"])
                    text_box(draw, (tx + 24, ty + 26, tw - 48, th - 66), text, 28, COLORS["foreground"])
                    draw.text((tx + 24, ty + th - 42), "%02d" % (index + 1), font=font(22), fill=COLORS["muted"])
            elif node.get("name") == "list" and screen_name == "ChannelSelection":
                count = 13 if advanced else 20
                row = height // count
                for index in range(count):
                    ty = y + index * row
                    if index == 3:
                        draw.rectangle((x, ty, x + width, ty + row - 1), fill=COLORS["selection"])
                    draw.text((x + 12, ty + 4), "%02d" % (index + 1), font=font(23), fill=COLORS["muted"])
                    draw.rectangle((x + 86, ty + 5, x + 155, ty + row - 5), outline=COLORS["muted"], width=1)
                    text_box(draw, (x + 192, ty + 2, 270, row), "Chaîne %02d" % (index + 1), 26, COLORS["foreground"])
                    text_box(draw, (x + 480, ty + 2, 575, row), "Horizons · programme de démonstration", 24, COLORS["muted"])
                    draw.rectangle((x + 1080, ty + row // 2 - 4, x + 1155, ty + row // 2 + 4), fill=COLORS["secondary"])
                    draw.rectangle((x + 1080, ty + row // 2 - 4, x + 1110, ty + row // 2 + 4), fill=COLORS["accent"])
            elif node.get("name") == "list" and screen_name == "GraphicalEPG":
                row = height // 8
                for index in range(8):
                    ty = y + row * index
                    text_box(draw, (x + 10, ty + 12, 220, row), "Chaîne %02d" % (index + 1), 25, COLORS["foreground"])
                    for col in range(3):
                        tx = x + 240 + col * (width - 240) // 3
                        tw = (width - 240) // 3
                        attribute = "EntryBackgroundColorNowSelected" if index == 2 and col == 0 else "EntryBackgroundColorNow" if col == 0 else "EntryBackgroundColor"
                        draw.rectangle((tx + 2, ty + 3, tx + tw - 2, ty + row - 3), fill=COLORS[node.get(attribute, "panel")])
                        point = int(node.get("EntryFontGraphical", "Regular;24").split(";")[-1])
                        text_box(draw, (tx + 15, ty + 8, tw - 30, row - 16), "%02d:00  Programme exemple" % (20 + col), point, COLORS["foreground"])
            elif node.get("name") == "categories" and screen_name == "MetrixNEOSettings":
                row = int(node.get("itemHeight", "64"))
                for index, (key, text) in enumerate(categories_for(profile)):
                    ty = y + index * row
                    if key == category:
                        draw.rectangle((x, ty, x + width - 1, ty + row - 1), fill=COLORS["secondary"])
                    text_box(draw, (x + 14, ty + 14, width - 28, row - 18), text, 28, COLORS["foreground"] if key == category else COLORS["muted"])
            elif node.get("name") == "config" and screen_name in ("Setup", "MetrixNEOSettings"):
                if screen_name == "MetrixNEOSettings":
                    rows = [(label, "••••" if kind=="password" else "Oui" if DEFAULTS[key] is True else "Non" if DEFAULTS[key] is False else "" if DEFAULTS[key] is None else str(DEFAULTS[key])) for key, label, kind, section, description in options_for(profile, category)]
                else:
                    # These are actual OpenATV Audio setup labels; the audited French
                    # PO leaves these three untranslated, so the native fallback is EN.
                    rows = [("Volume steps", "1"), ("Long press volume steps", "5"), ("Volume/Mute display timer", "3")]
                row = int(node.get("itemHeight", "46"))
                size = int(node.get("font", "Regular;26").split(";")[-1])
                for index, (text, value) in enumerate(rows):
                    ty = y + index * row
                    if index == 0:
                        from remaining_design import paint_selection
                        paint_selection(image,node,(x,ty,width,row))
                    text_box(draw, (x + 18, ty + 12, width - 180, row - 14), text, size, COLORS["foreground"])
                    text_box(draw, (x + width - 154, ty + 12, 136, row - 14), value, size, COLORS["foreground"], align="right")
            elif node.get("name") in ("config", "menu"):
                rows = ["Présentation et interface", "Météo à trois jours", "Images sous licence", "Smart EPG · local", "Diagnostics contextuels", "Cache et performances", "Prévisualiser / annuler"] if screen_name != "ChannelContextMenu" else ["Informations du service", "Ajouter aux favoris", "Renommer l’entrée", "Activer le déplacement", "Outils de bouquets", "Recherche et paramètres"]
                for index, text in enumerate(rows):
                    ty = y + 66 * index
                    if index == 1:
                        draw.rectangle((x, ty, x + width, ty + 62), fill=COLORS["selection"])
                    text_box(draw, (x + 22, ty + 12, width - 44, 48), text, 27, COLORS["foreground"])
            elif node.get("name") == "timeline_text":
                text_box(draw, (x + 10, y + 6, 220, height), "Chaînes", 24, COLORS["muted"])
                for index in range(3):
                    tx = x + 240 + index * (width - 240) // 3
                    text_box(draw, (tx + 12, y + 6, (width - 240)//3 - 24, height), "%02d:00" % (20 + index), 24, COLORS["muted"])
            elif node.get("render") == "Progress" and screen_name in ("InfoBar", "SecondInfoBar"):
                signal = node.get("source") == "session.FrontendStatus"
                base = (node.find("convert").text or "").split(",")[0]
                ratio = (.72 if profile.endswith("Advanced") else .82) if base == "SNR" else (.68 if profile.endswith("Advanced") else .76) if base == "AGC" else .71
                fill_width = max(1,round(width*ratio))
                left = x+width-fill_width if node.get("orientation")=="orRightToLeft" else x
                draw.rectangle((x,y,x+width-1,y+height-1),fill=COLORS["track"])
                if node.get("pixmap"):
                    with Image.open(ROOT/"skins"/node.get("pixmap")) as asset:
                        bar=asset.convert("RGB").resize((width,height))
                        offset=width-fill_width
                        image.paste(bar.crop((offset,0,width,height)),(left,y))
                else:
                    draw.rectangle((left,y,left+fill_width-1,y+height-1),fill=color(node.get("foregroundColor","accent")))
            elif node.get("render") not in ("MetrixNEOPoster", "MetrixNEOWeather", "Progress", "Pixmap"):
                size = int(node.get("font", "Regular;28").split(";")[-1])
                if node.get("borderWidth") and screen_name in ("InfoBar", "SecondInfoBar"):
                    draw.rectangle((x,y,x+width-1,y+height-1),outline=color(node.get("borderColor","line")),width=int(node.get("borderWidth")))
                text_box(draw, box, node.get("text", "") if node.tag == "eLabel" else sample_text(node, screen_name, profile, category), size, color(node.get("foregroundColor", "foreground")), node.get("halign", "left"), family=node.get("font", "Regular;28").split(";")[0], valign=node.get("valign", "top"), no_wrap=node.get("noWrap")=="1")

    visit(screens[screen_name], (screen_name,))
    draw.rectangle((0, 0, 1919, 19), fill=COLORS["secondary"])
    draw.text((960, 9), "SIMULATION XML · DONNÉES D’EXEMPLE · SIX RÉFÉRENCES UTILISATEUR REÇUES · PAS UNE CAPTURE VU+", font=font(13), fill=COLORS["muted"], anchor="mm")
    return image


def main():
    for profile in ("MetrixNEO", "MetrixNEOAdvanced"):
        assets(ROOT / "skins" / profile / "assets")
    from reference_assets import build_assets
    from render_reference import render as render_traced
    build_assets()
    output = ROOT / "previews"
    output.mkdir(exist_ok=True)
    cards = []
    anchors = {"menu_mainmenu": "menus", "ChannelSelection": "listes-chaines", "ChannelSelectionText": "listes-sans-image", "InfoBar": "infobars", "SecondInfoBar": "seconde-infobar", "GraphicalEPG": "epg", "EventView": "fiche-programme", "ChannelContextMenu": "menu-contextuel", "Setup": "parametres-systeme", "MetrixNEOSettings": "preferences-neo"}
    for name in SCREENS:
        anchor = " id='" + anchors[name] + "'"
        cards.append("<h2" + anchor + ">" + html.escape(SCREEN_TITLES[name]) + "</h2>" + ("<p>Fenêtre centrée : 1 480 × 850 px sur une sortie 1 920 × 1 080, avec la vidéo de la chaîne en lecture visible autour ; le bleu nuit reste dans la fenêtre. La scène de ville de cet aperçu illustre cette vidéo, sans être un fond fixe du skin. Quinze lignes de 44 px, texte de 24 px et défilement natif au-delà. Le menu réel conserve uniquement les actions disponibles. Icônes communes aux menus, dégradé propre à chaque skin et aide liée à l’action sélectionnée. Les raccourcis disponibles dépendent du contexte réel.</p>" if name == "ChannelContextMenu" else "") + "<div class='pair'>")
        for profile in ("MetrixNEO", "MetrixNEOAdvanced"):
            target = "ChannelSelection" if name == "ChannelSelectionText" else name
            image = render_traced(profile, target, text_box, font, artwork=name != "ChannelSelectionText") if target in ("menu_mainmenu", "ChannelSelection", "ChannelContextMenu") else render(profile, target)
            filename = profile + "-" + name + ".png"
            image.save(output / filename, optimize=True)
            picker = ""
            if name == "MetrixNEOSettings":
                choices = []
                for category, category_label in categories_for(profile):
                    category_filename = filename if category == "presentation" else profile + "-MetrixNEOSettings-" + category + ".png"
                    if category != "presentation":
                        render(profile, name, category).save(output / category_filename, optimize=True)
                    choices.append("<option value='" + category_filename + "'>" + html.escape(category_label) + "</option>")
                picker = "<label>Catégorie <select aria-label='Catégorie " + profile + "' onchange=\"const figure=this.closest('figure');figure.querySelector('a').href=this.value;figure.querySelector('img').src=this.value\">" + "".join(choices) + "</select></label>"
            cards.append("<figure><figcaption>" + ("Metrix NEO Advanced" if profile.endswith("Advanced") else "Metrix NEO") + "</figcaption>" + picker + "<a href='" + filename + "'><img src='" + filename + "' alt='Simulation " + profile + " " + html.escape(name) + "'></a></figure>")
            if name == "menu_mainmenu":
                image.resize((720, 405)).save(ROOT / "skins" / profile / "prev.png")
        cards.append("</div>")
    page = (ROOT / "tools/preview-gallery.template.html").read_text(encoding="utf-8").replace("__CARDS__", "".join(cards))
    (output / "index.html").write_text(page, encoding="utf-8")
    print("28 simulations XML créées : 20 écrans principaux et 8 vues de catégories ; 2 aperçus du sélecteur.")
    return



if __name__ == "__main__":
    main()
