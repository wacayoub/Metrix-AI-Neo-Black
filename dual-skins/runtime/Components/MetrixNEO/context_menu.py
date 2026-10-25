"""Screen-local ChoiceList decoration; native payloads and shortcuts stay intact."""
from functools import partial


def geometry(profile):
    return {"x": 350 if profile.endswith("Advanced") else 540,
            "width": 720 if profile.endswith("Advanced") else 900,
            "row": 44, "font": 24, "icon": (14, 10, 24, 24),
            "text_x": 54, "shortcut_width": 38, "visible_rows": 15,
            "window": (220, 115, 1480, 850),
            "list_y": 112, "frame": (0, 0, 1480, 850), "footer_y": 798}


ACTION_META = {
    "keySetup": ("setup", "Ouvrir les paramètres de la liste de chaînes."),
    "showServiceInformations": ("info", "Consulter les informations du service sélectionné."),
    "addServiceToBouquetSelected": ("files", "Choisir le bouquet de destination de cette chaîne."),
    "renameEntry": ("theme", "Modifier le nom de l’entrée sélectionnée."),
    "toggleMoveMode": ("channels", "Activer ou désactiver le déplacement des entrées."),
    "toggleMoveModeSelect": ("channels", "Activer ou désactiver le déplacement des entrées."),
    "bouquetMarkStart": ("files", "Ouvrir l’édition du bouquet sélectionné."),
    "runPlugin": ("plugins", ""),
    "removeEntry": ("tools", "Ouvrir l’action native de suppression de cette entrée."),
    "reloadServices": ("channels", "Recharger les services depuis les fichiers du récepteur."),
    "findCurrentlyPlayed": ("channels", "Retrouver la chaîne en cours de lecture."),
    "showSubservices": ("channels", "Afficher les sous-services disponibles."),
}


def presentation(payload):
    if not isinstance(payload, (tuple, list)) or not payload:
        return "", "tools", ""
    callback = payload[1] if len(payload) > 1 else None
    if callback == "CALLFUNC" and len(payload) > 2:
        callback = payload[2]
    # functools.partial / boundFunction: inspect metadata, never call an action.
    while isinstance(callback, partial) or callback.__class__.__name__ == "boundFunction":
        callback = callback.func if isinstance(callback, partial) else callback.fnc
    icon, description = ACTION_META.get(getattr(callback, "__name__", ""), ("tools", ""))
    return str(payload[0]), icon, description


def decorate_rows(rows, profile, text_entry, pixmap_entry, load_icon, text_flags, pixmap_flags):
    g = geometry(profile)
    result = []
    for row in rows:
        payload = row[0]
        if payload is None:  # Native unselectable separator.
            result.append([None, text_entry(pos=(14, 0), size=(g["width"] - 42, g["row"]), font=0, flags=text_flags, text="—" * 80)])
            continue
        title, icon, _ = presentation(payload)
        rendered = [payload, text_entry(pos=(g["text_x"], 0), size=(g["width"] - g["text_x"] - 62, g["row"]), font=0, flags=text_flags, text=title)]
        png = load_icon(icon)
        if png is not None:
            x, y, w, h = g["icon"]
            rendered.append(pixmap_entry(pos=(x, y), size=(w, h), png=png, flags=pixmap_flags))
        # Preserve native numeric/colored shortcut glyphs separately at the right.
        if len(row) > 2:
            shortcut = list(row[2])
            shortcut[1:5] = [g["width"] - 50, (g["row"] - 32) // 2, 32, 32]
            rendered.append(tuple(shortcut))
        result.append(rendered)
    return result


def bind_context(screen, profile):
    if getattr(screen, "_neo_context_bound", False):
        return
    from enigma import BT_SCALE, BT_KEEP_ASPECT_RATIO, RT_HALIGN_LEFT, RT_VALIGN_CENTER, RT_ELLIPSIS, gFont
    from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaBlend
    from Tools.Directories import SCOPE_SKINS, resolveFilename
    from Tools.LoadPixmap import LoadPixmap
    listing = screen.get("menu") or screen.get("list")
    if listing is None:
        return
    screen._neo_context_bound = True
    g = geometry(profile)
    index = listing.getSelectionIndex()
    icons = {}
    def load_icon(name):
        if name not in icons:
            icons[name] = LoadPixmap(resolveFilename(SCOPE_SKINS, profile + "/assets/menu-" + name + ".png"), cached=True)
        return icons[name]
    rows = decorate_rows(listing.list, profile, MultiContentEntryText, MultiContentEntryPixmapAlphaBlend, load_icon, RT_HALIGN_LEFT | RT_VALIGN_CENTER | RT_ELLIPSIS, BT_SCALE | BT_KEEP_ASPECT_RATIO)
    listing.l.setFont(0, gFont("Regular", g["font"]))
    listing.l.setItemHeight(g["row"])
    listing.itemHeight = g["row"]
    listing.setList(rows)
    listing.moveToIndex(index)
