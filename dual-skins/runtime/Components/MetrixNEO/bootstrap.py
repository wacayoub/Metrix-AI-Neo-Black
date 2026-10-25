"""Screen-local skin applets. No monkeypatches, no system configuration writes."""
from copy import deepcopy
from functools import partial
from importlib.util import find_spec
from xml.etree.ElementTree import SubElement
from Components.MetrixNEO.menu_model import ADVANCED_ORDER, MENU_META, NEO_ORDER


def bind_channel(screen, profile):
    from Components.MetrixNEO.settings import read_settings
    widget = screen["list"]
    settings = read_settings(profile)
    if hasattr(widget, "readTemplate"):
        name = "NEO Compact" if profile == "MetrixNEOAdvanced" and settings["compact"] else "NEO"
        widget.readTemplate(name)
        widget.setMode(widget.mode)
    # Legacy ServiceList retains the safe native mode, without changing user config.


def _unavailable(screen, text):
    from Screens.MessageBox import MessageBox
    screen.session.open(MessageBox, text, type=MessageBox.TYPE_INFO, timeout=6)


def _native_menu(screen):
    from Screens.Menu import Menu
    root = deepcopy(screen.parentMenu)
    root.set("key", "neo_native_mainmenu")
    profile = getattr(screen, "_neo_profile", "MetrixNEO")
    item = SubElement(root, "item", {"text": "Metrix NEO · Préférences", "key": "neo_profile_preferences", "weight": "95"})
    SubElement(item, "code").text = "from Components.MetrixNEO.ui import NeoSettings\nself.session.open(NeoSettings, %r)" % profile
    screen.session.open(Menu, root)


def _channel_editor(screen):
    from Screens.InfoBar import InfoBar
    infobar = InfoBar.instance
    if infobar and getattr(infobar, "servicelist", None):
        screen.session.execDialog(infobar.servicelist)
    else:
        _unavailable(screen, "Liste native indisponible dans ce contexte")


def _settings(screen, profile):
    from Components.MetrixNEO.ui import NeoSettings
    screen.session.open(NeoSettings, profile)


def _open_channels(screen, mode):
    from Screens.InfoBar import InfoBar
    infobar = InfoBar.instance
    csel = getattr(infobar, "servicelist", None)
    if csel is None:
        return _unavailable(screen, "Liste de chaînes native indisponible")
    if mode == "reception":
        csel.showSatellites()
    elif mode == "all":
        csel.showAllServices()
    elif mode == "tv":
        csel.setModeTv()
    screen.session.execDialog(csel)


def decorate_menu_source(screen, profile):
    source = screen.get("menu")
    if source is None:
        return
    from Tools.Directories import SCOPE_SKINS, resolveFilename
    from Tools.LoadPixmap import LoadPixmap
    decorated = []
    for row in source.list:
        meta = MENU_META.get(row[5], (row[3], row[4], "tools"))
        icon = LoadPixmap(resolveFilename(SCOPE_SKINS, profile + "/assets/menu-" + meta[2] + ".png"), cached=True)
        unavailable = "indisponible" in row[3]
        title = meta[0] + (" · indisponible" if unavailable else "")
        description = "Fonction absente" if unavailable else meta[1]
        decorated.append((row[0], icon, row[2], title, description) + tuple(row[5:8]))
    source.setList(decorated)
    source.index = 0


def bind_menu(screen, profile):
    if getattr(screen, "menuID", None) != "mainmenu" or getattr(screen, "_neo_bound", False):
        return
    from Screens.Menu import menuDom
    from Components.ActionMap import ActionMap
    screen._neo_bound = True
    screen._neo_profile = profile
    original = list(screen.menuList)
    by_key = {entry[2]: entry for entry in original}
    root = menuDom()

    def native(key, label):
        entry = by_key.get(key)
        if entry:
            return (label,) + tuple(entry[1:])
        main_keys = {"plugin_selection", "setup", "timermenu", "shutdown", "information", "movie_selection"}
        node = root.find(".//*[@key='%s']" % key) if root is not None and key not in main_keys else None
        if node is not None:
            entry = screen.addMenu(node) if node.tag == "menu" else screen.addItem(node)
            if entry:
                return (label,) + tuple(entry[1:])
        return (label + " · indisponible", partial(_unavailable, screen, label + " indisponible"), key, 50, "Fonction native absente ou masquée par les autorisations", None)

    rows = [native("plugin_selection", "Plugin Browser"), native("setup", "Paramètres")]
    if profile == "MetrixNEO":
        rows += [native("timermenu", "Programmations"), native("shutdown", "Veille / Redémarrer"), native("information", "Informations")]
    else:
        rows += [("Éditeur de chaînes", partial(_channel_editor, screen), "neo_channels", 30, "Outils de chaînes natifs : MENU dans la liste", None), native("timermenu", "Programmations")]
        # File Commander is optional; absence is explicit and never triggers installation.
        module = "Plugins.Extensions.FileCommander.plugin"
        try:
            available = find_spec(module) is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            available = False
        if available:
            def files():
                from Plugins.Extensions.FileCommander.plugin import main
                main(screen.session)
            rows.append(("Gestionnaire de fichiers", files, "neo_files", 40, "File Commander installé", None))
        else:
            rows.append(("Fichiers · indisponible", partial(_unavailable, screen, "File Commander absent. Aucune installation automatique."), "neo_files", 40, "Plugin facultatif absent", None))
        rows += [native("movie_selection", "Enregistrements"), native("software_manager", "Logiciels"), native("network", "Réseau"), native("shutdown", "Veille / Redémarrer"), native("information", "Informations")]
        rows += [("Thème & Skin", partial(_settings, screen, profile), "neo_settings", 90, "Prévisualisation et réglages NEO uniquement", None), ("Outils", partial(_native_menu, screen), "neo_tools", 95, "Toutes les fonctions du menu natif", None)]
    by_identity = {row[2]: row for row in rows}
    order = ADVANCED_ORDER if profile.endswith("Advanced") else NEO_ORDER
    rows = [by_identity[key] for key in order]
    rows = [tuple(row[:5]) + (screen.getMenuEntryImage(row[2], None),) + tuple(row[6:]) if row[5] is None else row for row in rows]
    screen.menuList = rows
    screen.setMenuList(rows)
    decorate_menu_source(screen, profile)
    # MENU always exposes the full original native menu, including plugin additions.
    screen["neoMenuActions"] = ActionMap(["MenuActions"], {"menu": partial(_native_menu, screen)}, -10)
    def update_keys():
        for key, value in (("key_red", "Quitter\nFermer le menu"), ("key_green", "Tous les services\nListe des chaînes"), ("key_yellow", "Listes de réception\nSatellites / TNT"), ("key_blue", "Télévision\nMode TV")):
            if key in screen:
                screen[key].setText(value)
    source = screen.get("menu")
    if source is not None:
        source.onSelectionChanged.append(update_keys)
    update_keys()
    screen["neoColorActions"] = ActionMap(["ColorActions"], {"green": partial(_open_channels, screen, "all"), "yellow": partial(_open_channels, screen, "reception"), "blue": partial(_open_channels, screen, "tv")}, -10)
    screen["description"].setText("MENU : toutes les fonctions natives")
