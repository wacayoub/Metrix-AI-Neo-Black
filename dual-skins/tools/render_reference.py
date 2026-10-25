"""Reference-layout previews using the actual XML geometry and actual skin assets.

Fixtures are confined to previews, never imported by a runtime component.
This is not the Enigma2 render engine and is not a receiver screenshot.
"""
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw, ImageOps

from generate_skins import ROOT, TOKENS
from reference_assets import gradient
from reference_design import channel_geometry

sys.path.insert(0, str(ROOT / "runtime"))
from Components.MetrixNEO.menu_model import ADVANCED_ORDER, MENU_META, NEO_ORDER
from Components.MetrixNEO.context_menu import geometry as context_geometry, presentation
from Components.MetrixNEO.channel_layout import detail_slots

CHANNELS = ["Rai 1", "Rai 2", "Rai 3", "RETE4", "CANALE5", "ITALIA 1", "LA7", "TV8", "NOVE", "Rai 4K", "SAN MARINO RTV", "RSI LA 1", "RSI LA 2", "20", "IRIS", "LA5", "REAL TIME", "FOCUS", "DMAX", "GIALLO"]
PROGRAMMES = ["Ciao Maschio", "TG2 Dossier", "Volveréis - Una storia d’amore quasi classica", "Firewall - Accesso negato", "Caduta libera", "Studio Aperto - La giornata", "L’aria che tira: Il diario", "F1 Paddock Live Post Qualifiche", "Accordi & disaccordi", "Bellezze d’Italia", "Calcio", "TG Notte", "Moto3: GP Australia - Gara", "The Equalizer - Il vendicatore", "L’ultimo samurai", "Grande Fratello", "Casa a prima vista", "Strane stranezze dal mondo", "Gold Rush - La febbre dell’oro", "Delitti ai Caraibi"]
SYNOPSIS = "Firewall: Accesso negato - Firewall - Accesso negato | Film, Thriller\nJack Stanfield è uno specialista di sistemi di sicurezza informatici bancari sotto ricatto, perché costretto a rubare nella banca in cui lavora.\nCon Harrison Ford. Regia di R. Loncraine; USA 2006."

# Native callback identities supply icons/help, without executing the callbacks.
def showServiceInformations():
    pass
CONTEXT_ACTIONS = (
    ("Informations du service", showServiceInformations),
    ("Ajouter aux favoris", "files"), ("Renommer l’entrée", "theme"),
    ("Activer le déplacement", "channels"), ("Outils de bouquets", "files"),
    ("Paramètres", "setup"), ("Définir comme chaîne de démarrage", "power"),
    ("Marquer comme service 3D dédié", "television"),
    ("Masquer la ligne VBI pour ce service", "television"),
    ("Centrer les sous-titres DVB", "channels"), ("Supprimer l’entrée", "tools"),
    ("Retrouver la chaîne en cours", "channels"), ("Ajouter un marqueur", "theme"),
    ("Éditer le bouquet", "files"), ("Recharger les services", "channels"),
)


def render(profile, name, text_box, font, artwork=True):
    root = ET.parse(ROOT / "skins" / profile / "skin.xml").getroot()
    screens = {s.get("name"): s for s in root.findall("screen")}
    is_context = "Context" in name
    if is_context:
        # Stand-in for the decoder's live output, only in this offline preview.
        # The native centered window leaves this region outside its OSD bounds.
        # No fixed photograph or video widget is added to the receiver skin.
        with Image.open(ROOT / "assets/source/scenic-reference-generated.png") as fixture:
            image = ImageOps.fit(fixture.convert("RGB"), (1920, 1080), method=Image.Resampling.LANCZOS)
    else:
        image = Image.new("RGB", (1920, 1080), "#031323")
    draw = ImageDraw.Draw(image)
    if is_context:
        draw.text((960, 44), "HORS MENU : VIDÉO DE LA CHAÎNE EN COURS · IMAGE D’EXEMPLE POUR LA SIMULATION", font=font(19), fill="#E9F0F8", anchor="mm", stroke_width=1, stroke_fill="#031323")
    selected = 3
    # XML positions inside a non-fullscreen dialog are local to that window.
    origin_x, origin_y = map(int, screens[name].get("position", "0,0").split(","))
    text_slots = detail_slots(profile, False) if name == "ChannelSelection" and not artwork else {}

    def ink(value):
        value = TOKENS.get(value, value.lstrip("#"))
        return "#" + value[-6:]

    def paste(path, box, contain=False, fill=False):
        if not path.is_file():
            return
        asset = Image.open(path).convert("RGBA")
        x, y, w, h = box
        if fill:
            from PIL import ImageOps
            asset = ImageOps.fit(asset, (w, h), method=Image.Resampling.LANCZOS)
            width, height = w, h
        elif contain:
            ratio = min(w / asset.width, h / asset.height)
            width, height = int(asset.width * ratio), int(asset.height * ratio)
            x, y = x + (w - width) // 2, y + (h - height) // 2
        else:
            width, height = w, h
        asset = asset.resize((width, height), Image.Resampling.LANCZOS)
        image.paste(asset, (x, y), asset)

    def picon(index, box):
        x, y, w, h = box
        colors = ["1267D3", "D82332", "19A553", "EF6514", "181818", "181818", "E3C317", "06172A", "06172A", "1267D3", "1A8FC3", "ED9412", "ED9412", "FFFFFF", "D1B524", "D82665", "06A98D", "E32E37", "DAD7D2", "EDCD13"]
        # Original typographic stand-ins; actual logos come from the receiver's picon set.
        ratio = 2.3 if index in (10, 14, 16, 17, 18, 19) else 1.7
        pw = min(w, int(h * ratio))
        ph = min(h, int(pw / ratio))
        px, py = x + (w - pw) // 2, y + (h - ph) // 2
        if index == 3:
            diameter = ph
            px = x + (w - diameter) // 2
            draw.ellipse((px, py, px + diameter, py + diameter), fill="#FF6A00")
            draw.text((px + diameter // 2, py + diameter // 2), "4", font=font(int(ph * .82)), fill="#061626", anchor="mm")
            return
        if index in (0, 1, 2, 9, 10, 11, 12, 16, 17, 18, 19):
            draw.rounded_rectangle((px, py, px + pw, py + ph), 1, fill="#" + colors[index])
        label = ["Rai 1", "Rai 2", "Rai 3", "4", "5", "1", "LA7", "TV8", "NOVE", "Rai 4K", "RTV", "RSI 1", "RSI 2", "20", "IRIS", "LA5", "Real Time", "Focus", "DMAX", "Giallo"][index]
        label_ink = "#DAD6D0" if index == 13 else "#F2D73C" if index in (6, 14) else "#1BDDB6" if index == 8 else "#F04B92" if index == 15 else "#101B24" if index in (18, 19) else "#FFFFFF"
        face = font(max(12, min(round(ph * .52), pw // max(2, len(label) // 2))))
        draw.text((px + pw // 2, py + ph // 2), label, font=face, fill=label_ink, anchor="mm")

    def sample(node):
        source = node.get("source", "")
        converter = node.find("convert")
        token = converter.text or "" if converter is not None else ""
        converter_type = converter.get("type", "") if converter is not None else ""
        if token.startswith("WeatherCurrent"):
            return "Casablanca\n16°C"
        if token.startswith("WeatherLocation"):
            return "Casablanca"
        if token.startswith("WeatherTemperature"):
            return "16°C"
        if token.startswith("WeatherDay"):
            return ("Sam", "Dim", "Lun")[int(token.split(",")[0][-1]) - 1]
        if token.startswith("WeatherRange"):
            return ("24°/16°", "23°/16°", "20°/15°")[int(token.split(",")[0][-1]) - 1]
        if token.startswith("Weather"):
            return {"Weather1": "Sam\n24°/16°", "Weather2": "Dim\n23°/16°", "Weather3": "Lun\n20°/15°"}.get(token.split(",")[0], "")
        if node.get("render") == "MetrixNEOContext":
            if node.get("neoPart") == "action":
                title, _, help_text = presentation(CONTEXT_ACTIONS[0])
                return title + "\n\n" + help_text
            title, description = "Firewall - Accesso negato", "Informations sur le programme sélectionné.\nFilm, Thriller.\n\nLes opérations disponibles proviennent du menu contextuel natif."
            return title if node.get("neoPart") == "title" else description if node.get("neoPart") == "description" else title + "\n\n" + description
        if source == "global.CurrentTime":
            return "23:59" if "%H" in token else "Samedi\n24 Octobre 2026"
        if source == "Title":
            return "TV - Top Italia" if name == "ChannelSelection" else "Menu Contextuel" if "Context" in name else name
        if source.startswith("key_"):
            if "Context" in name:
                return {"key_red": "Annuler", "key_green": "Sélectionner", "key_yellow": "", "key_blue": ""}[source]
            if name == "menu_mainmenu":
                return {"key_red": "Quitter\nFermer le menu", "key_green": "Tous les services\nListe des chaînes", "key_yellow": "Listes de réception\nSatellites / TNT", "key_blue": "Télévision\nMode TV"}[source]
            return {"key_red": "Tous les services", "key_green": "Listes de réception", "key_yellow": "Fournisseurs", "key_blue": "Bouquets"}[source]
        if source == "description":
            return ""
        if token.startswith("Next1"):
            return "01:27   Tg4 26 - ultima ora notte"
        if token.startswith("Next2"):
            return "02:05   Film del mattino"
        if converter_type == "ServiceName":
            return "RETE4"
        if token == "Name":
            return PROGRAMMES[3]
        if "Description" in token:
            return SYNOPSIS
        if node.get("render") == "MetrixNEOServiceFacts":
            return {"video": "1080i\nH.264", "aspect_source": "16:9\nDVB-S", "audio": "AC3"}.get(node.get("neoField"), "1920×1080 | H.264 | DVB-S | AC3")
        if node.get("render") == "MetrixNEOContext":
            return "Firewall - Accesso negato\n\nInformations sur la chaîne sélectionnée. Les actions à droite proviennent du menu contextuel natif."
        return node.get("text", "")

    def template_rectangle(item, box, is_selected):
        x, y, width, height = box
        colors = item.get("foregroundGradientSelected", item.get("foregroundGradient")) if is_selected else item.get("foregroundGradient")
        if colors:
            parts = colors.split(",")
            axis = next(i for i, value in enumerate(parts) if value in ("horizontal", "vertical"))
            stops = parts[:axis]
            asset = gradient((width, height), TOKENS[stops[0]], TOKENS[stops[-1]], int(item.get("cornerRadius", "0")), mid=TOKENS[stops[1]] if len(stops) == 3 else None, direction=parts[axis])
        else:
            bg = item.get("backgroundColorSelected", item.get("backgroundColor", "panel")) if is_selected else item.get("backgroundColor", "panel")
            border = item.get("borderColorSelected", item.get("borderColor")) if is_selected else item.get("borderColor")
            asset = gradient((width, height), TOKENS[bg], TOKENS[bg], int(item.get("cornerRadius", "0")), TOKENS[border] if border else None)
        image.paste(asset, (x, y), asset)

    def menu_list(node, box):
        x, y, width, height = box
        template = node.find("template")
        mode = template.find("mode")
        tw, th = int(template.get("itemWidth")), int(template.get("itemHeight"))
        families = [value.split(";")[0] for value in template.get("fonts").split(",")]
        fonts = [int(value.split(";")[-1]) for value in template.get("fonts").split(",")]
        keys = ADVANCED_ORDER if profile.endswith("Advanced") else NEO_ORDER
        columns = width // tw
        for index, key in enumerate(keys):
            cx, cy = x + (index % columns) * tw, y + (index // columns) * th
            for item in mode:
                ix, iy = map(int, item.get("position").split(","))
                iw, ih = map(int, item.get("size").split(","))
                ibox = (cx + ix, cy + iy, iw, ih)
                if item.tag == "rectangle":
                    template_rectangle(item, ibox, index == 0)
                elif item.tag == "pixmap":
                    paste(ROOT / "skins" / profile / "assets" / ("menu-" + MENU_META[key][2] + ".png"), ibox, contain=True)
                else:
                    text = MENU_META[key][0] if item.get("index") == "Text" else MENU_META[key][1]
                    # Sample assumes the optional file manager is present. Runtime
                    # still labels its absence; this fixture changes no callback.
                    align = item.get("horizontalAlignment", "left")
                    point = fonts[int(item.get("font"))]
                    if item.get("verticalAlignment") == "center":
                        lines = 2 if len(text) * point * .48 > iw or "\n" in text else 1
                        text_height = round(point * 1.15) * lines
                        ibox = (ibox[0], ibox[1] + max(0, (ih - text_height) // 2), iw, ih)
                    text_box(draw, ibox, text, point, ink(item.get("foregroundColor", "foreground")), align, family=families[int(item.get("font"))])

    def channel_list(node, box):
        x, y, width, height = box
        templates = ET.parse(ROOT / "skins" / profile / "skinTemplates.xml").getroot()
        template = templates.find("template")
        mode = template.find("mode[@name='bouquets']")
        row = int(mode.get("itemHeight"))
        fonts = [int(value.split(";")[-1]) for value in template.get("fonts").split(",")]
        for index in range(min(20, height // row)):
            cy = y + index * row
            for item in mode:
                ix, iy = map(int, item.get("position").split(","))
                iw, ih = map(int, item.get("size").split(","))
                ibox = x + ix, cy + iy, iw, ih
                kind = item.get("index", "")
                if item.tag == "rectangle":
                    template_rectangle(item, ibox, index == selected)
                    continue
                if kind == "Picon":
                    picon(index, ibox)
                elif item.tag == "progress":
                    draw.rectangle((ibox[0], ibox[1], ibox[0] + iw-1, ibox[1] + ih-1), fill=ink(item.get("backgroundColor", "track")))
                    fill = item.get("foregroundColorSelected" if index == selected else "foregroundColor", "accent")
                    draw.rectangle((ibox[0], ibox[1], ibox[0] + iw * (index * 13 % 67 + 20) // 100, ibox[1] + ih-1), fill=ink(fill))
                elif item.tag == "text":
                    text = str(index + 1) if kind == "Number" else CHANNELS[index] if kind == "ServiceName" else PROGRAMMES[index]
                    point = fonts[int(item.get("font"))]
                    if item.get("verticalAlignment") == "center":
                        ibox = (ibox[0], ibox[1] + max(0,(ih-round(point*1.15))//2), iw, ih)
                    text_box(draw, ibox, text, point, ink("foreground" if index == selected or kind != "Title1" else "epg"), item.get("horizontalAlignment", "left"))

    def visit(node, seen=()):
        for item in node:
            if item.tag == "panel":
                panel = item.get("name")
                if panel in screens and panel not in seen:
                    visit(screens[panel], seen + (panel,))
                continue
            if item.tag not in ("widget", "ePixmap", "eLabel"):
                continue
            try:
                x, y = map(int, item.get("position").split(","))
                w, h = map(int, item.get("size").split(","))
            except (AttributeError, ValueError):
                continue
            if (x, y) in text_slots:
                x, y, w, h = text_slots[(x, y)]
            x, y = x + origin_x, y + origin_y
            box = x, y, w, h
            if item.tag == "ePixmap":
                paste(ROOT / "skins" / item.get("pixmap"), box, fill=item.get("scale") == "fill")
            elif item.get("source") == "menu":
                menu_list(item, box)
            elif item.get("name") == "list" and "Context" not in name:
                channel_list(item, box)
            elif item.get("name") in ("menu", "list") and "Context" in name:
                g = context_geometry(profile)
                row = g["row"]
                for index, action in enumerate(CONTEXT_ACTIONS[:h // row]):
                    if index == 0:
                        paste(ROOT / "skins" / profile / "assets/context-selection.png", (x, y, w, row))
                    ix, iy, iw, ih = g["icon"]
                    icon = presentation(action)[1] if index == 0 else action[1]
                    paste(ROOT / "skins" / profile / "assets" / ("menu-" + icon + ".png"), (x + ix, y + index * row + iy, iw, ih), contain=True)
                    text_box(draw, (x + g["text_x"], y + index * row + (row - round(g["font"] * 1.15)) // 2, w - g["text_x"] - 62, row), action[0], g["font"], ink("foreground"))
            elif item.get("render") == "MetrixNEOPoster":
                if artwork:
                    paste(ROOT / "previews/fixtures/programme-demo-generated.png", box, contain=True)
            elif item.get("render") == "MetrixNEOPicon":
                if item.get("zPosition") != "1":
                    picon(3, box)
            elif item.get("render") == "MetrixNEOWeather":
                day = item.get("neoDay", "0")
                icon = "moon" if day == "-1" else "sun" if day == "0" else "cloud" if day == "1" else "rain"
                paste(ROOT / "skins" / profile / "assets" / ("weather-" + icon + ".png"), box)
            elif item.get("render") == "Progress":
                draw.rectangle((x, y, x + w, y + h), fill=ink("track"))
                paste(ROOT / "skins" / profile / "assets/progress.png", (x, y, int(w * .28), h))
            else:
                background = item.get("backgroundColor")
                if background and item.get("transparent") != "1":
                    # Enigma2 inverse alpha for the photo's live date overlay.
                    c = TOKENS.get(background, background)
                    alpha = 255 - int(c[:2], 16) if len(c) == 8 else 255
                    overlay = Image.new("RGBA", (w, h), tuple(int(c[-6:][i:i+2], 16) for i in (0, 2, 4)) + (alpha,))
                    image.paste(overlay, (x, y), overlay)
                text = item.get("text", "") if item.tag == "eLabel" else sample(item)
                size = int(item.get("font", "Regular;24").split(";")[-1])
                text_box(draw, box, text, size, ink(item.get("foregroundColor", "foreground")), item.get("halign", "left"), family=item.get("font", "Regular;24").split(";")[0])
    visit(screens[name], (name,))
    # Small but explicit evidence label, outside the main reference composition.
    draw.rectangle((0, 1062, 1919, 1079), fill="#02101C")
    draw.text((960, 1070), "SIMULATION DU XML · MÉTÉO, PICTOGRAMMES DE CHAÎNES ET EPG D’EXEMPLE · IMAGE PROGRAMME GÉNÉRÉE · AUCUN TEST VU+", font=font(12), fill="#9AAABD", anchor="mm")
    return image
