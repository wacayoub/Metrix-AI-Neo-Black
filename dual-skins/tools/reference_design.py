"""Native XML layouts traced from the four user references received 2026-10-25.

No screenshot is used as a screen background. All text and lists remain native.
"""
import sys
from generate_skins import ROOT, sub, widget, label, rect, screen, applet

if str(ROOT / "runtime") not in sys.path:
    sys.path.insert(0, str(ROOT / "runtime"))


def picture(parent, profile, asset, pos, size, **attrs):
    attrs.setdefault("scale", "stretch")
    return sub(parent, "ePixmap", position=pos, size=size, pixmap=profile + "/assets/" + asset, alphatest="blend", **attrs)


def reference_header(parent, profile, title=True, menu=False, inset=False, context=False):
    advanced = profile.endswith("Advanced")
    x, y = (60, 80) if context else (250, 82) if inset else (60, 250 if advanced else 316) if menu else (48, 24)
    if menu or context:
        label(parent, "Vu", "%d,%d" % (x, y), "78,55", "MenuTitle;50")
        label(parent, "+", "%d,%d" % (x + 72, y - 2), "26,34", "MenuTitle;28")
        rect(parent, "%d,%d" % (x + 112, y + 10), "1,32", "line")
        label(parent, "Menu Contextuel" if context else "Main Menu", "%d,%d" % (x + 132, y + 9), "420,48", 31 if context else 34 if advanced else 36)
    elif title:
        picture(parent, profile, "menu-television.png", "%d,%d" % (x, y), "48,52")
        widget(parent, "%d,%d" % (x + 78, y - 1), "660,58", source="Title", font=42 if advanced else 45)
    # Right-aligned compact weather/date strip. Live data remain optional.
    wx, wy, strip_width = (1016, 80, 722) if inset else (660, y - 22, 1212) if menu or context else (990, 9, 903)
    unit = strip_width / 1212
    def xpos(value):
        return wx + round(value * unit)
    # Three stacked forecast columns; current temperature is larger than the city.
    picture(parent, profile, "header-strip.png", "%d,%d" % (wx, wy), "%d,88" % strip_width)
    city_width = round(161 * unit)
    for mode, offset, height, point in (("WeatherLocation", 7, 27, 26 if menu else 23), ("WeatherTemperature", 32, 49, 42 if menu else 37)):
        point = 17 if inset and mode == "WeatherLocation" else 19 if not menu and not context and mode == "WeatherLocation" else round(point * .78) if inset else point
        widget(parent, "%d,%d" % (wx + 15, wy + offset), "%d,%d" % (city_width, height), source="global.CurrentTime", font=point, converters=[("MetrixNEOInfo", mode + "," + profile)])
    widget(parent, "%d,%d" % (xpos(188), wy + 24), "44,44" if inset else "57,57", source="global.CurrentTime", render="MetrixNEOWeather", neoProfile=profile, neoDay="-1")
    forecast_start, forecast_step, cw = (172, 86, 80) if inset else (295, 184, 170) if menu or context else (220, 108, 100)
    for index in range(3):
        px = wx + forecast_start + index * forecast_step
        rect(parent, "%d,%d" % (px - 6, wy + 10), "1,65", "line")
        widget(parent, "%d,%d" % (px, wy + 4), "%d,25" % cw, source="global.CurrentTime", font=22 if menu else 20 if not inset else 17, halign="center", converters=[("MetrixNEOInfo", "WeatherDay%d,%s" % (index + 1, profile))])
        icon_size = 35 if not inset else 30
        widget(parent, "%d,%d" % (px + (cw - icon_size) // 2, wy + 26), "%d,%d" % (icon_size, icon_size), source="global.CurrentTime", render="MetrixNEOWeather", neoProfile=profile, neoDay=index)
        widget(parent, "%d,%d" % (px, wy + 61), "%d,24" % cw, source="global.CurrentTime", font=19 if menu else 18 if not inset else 15, halign="center", converters=[("MetrixNEOInfo", "WeatherRange%d,%s" % (index + 1, profile))])
    clock_width = 112 if inset else 146
    clock_x = wx + strip_width - clock_width - 9
    date_width = 150 if inset else 184 if menu or context else 175
    date_x = clock_x - date_width - 18
    rect(parent, "%d,%d" % (date_x - 6, wy + 10), "1,65", "line")
    widget(parent, "%d,%d" % (date_x, wy + 16), "%d,58" % date_width, source="global.CurrentTime", font=16 if inset else 22 if menu else 20 if context else 18, halign="right", converters=[("ClockToText", "Format:%A\n%d %B %Y")])
    rect(parent, "%d,%d" % (clock_x - 8, wy + 10), "1,65", "line")
    widget(parent, "%d,%d" % (clock_x, wy + 15), "%d,62" % clock_width, source="global.CurrentTime", font=37 if inset else 43 if context else 48, halign="right", converters=[("ClockToText", "Format:%H:%M")])


def reference_footer(parent, y=1012, x=48, spacing=400, menu=False):
    for index, key in enumerate(("red", "green", "yellow", "blue")):
        px = x + index * spacing
        rect(parent, "%d,%d" % (px, y + 2), "8,44", key)
        widget(parent, "%d,%d" % (px + 22, y), "%d,%d" % (spacing - 30, 64 if menu else 48), source="key_" + key, font=23, conditional="key_" + key)
    if not menu:
        for index, (button, text) in enumerate((("INFO", "Info / EPG"), ("MENU", "Menu"), ("EXIT", "Quitter"))):
            px = 1515 + index * 128
            picture(parent, "MetrixNEOAdvanced" if x > 100 else "MetrixNEO", "keycap.png", "%d,%d" % (px, y - 3), "116,54")
            label(parent, button + "\n" + text, "%d,%d" % (px + 5, y), "106,53", 17, halign="center")


def context_header(parent, profile):
    """The same menu header fitted inside the centered context window."""
    first = len(parent)
    reference_header(parent, profile, context=True)
    ratio = .77
    for node in list(parent)[first:]:
        x, y = map(int, node.get("position").split(","))
        w, h = map(int, node.get("size").split(","))
        node.set("position", "%d,%d" % (round((x - 24) * ratio), 20 + round((y - 58) * ratio)))
        node.set("size", "%d,%d" % (max(1, round(w * ratio)), max(1, round(h * ratio))))
        if node.get("font"):
            face, point = node.get("font").split(";")
            node.set("font", "%s;%d" % (face, round(int(point) * ratio)))


def menu_template(parent, width, height, horizontal_icon=False):
    template = sub(parent, "template", name="Default", fonts="Regular;28,Regular;19,MenuTitle;23" if horizontal_icon else "MenuTitle;32,Regular;24,Regular;24", itemWidth=width, itemHeight=height)
    for style in ("default", "text", "number", "image", "both"):
        mode = sub(template, "mode", name=style, itemWidth=width, itemHeight=height)
        sub(mode, "rectangle", position="5,5", size="%d,%d" % (width - 10, height - 10), backgroundColor="panel", backgroundColorSelected="selection", borderColor="line", borderColorSelected="selection_rim", borderWidth="2", cornerRadius="8")
        prefix = "" if horizontal_icon else "classic_"
        selected_prefix = "menu_" if horizontal_icon else "classic_menu_"
        sub(mode, "rectangle", position="8,8", size="%d,%d" % (width - 16, height - 16), foregroundGradient=prefix + "tile_top," + prefix + "tile_mid," + prefix + "tile_bottom,vertical", foregroundGradientSelected=selected_prefix + "selected_top," + selected_prefix + "selected_mid," + selected_prefix + "selected_bottom,vertical", cornerRadius="5")
        sub(mode, "rectangle", position="8,12", size="20,%d" % (height - 25), foregroundGradient="tile_edge,tile_edge_clear,horizontal,1", foregroundGradientSelected="selection_glow_alpha,selection_glow_clear,horizontal,1")
        sub(mode, "rectangle", position="%d,12" % (width - 20), size="12,%d" % (height - 25), foregroundGradient="selection_glow_clear,selection_glow_clear,horizontal,1", foregroundGradientSelected="selection_glow_clear,selection_glow_weak,horizontal,1")
        sub(mode, "rectangle", position="13,8", size="%d,1" % (width - 26), backgroundColor="tile_highlight", backgroundColorSelected="selection_highlight")
        if horizontal_icon:
            sub(mode, "pixmap", index="Image", position="24,42", size="64,64", alpha="blend", scale="centerScaled")
            sub(mode, "text", index="Text", position="102,24", size="%d,56" % (width - 117), font="2", verticalAlignment="center", wrap="wrap", foregroundColor="foreground", foregroundColorSelected="foreground")
            sub(mode, "text", index="Description", position="102,87", size="%d,44" % (width - 117), font="1", wrap="wrap", foregroundColor="muted")
        else:
            sub(mode, "pixmap", index="Image", position="%d,44" % (width // 2 - 52), size="104,104", alpha="blend", scale="centerScaled")
            sub(mode, "text", index="Text", position="16,161", size="%d,55" % (width - 32), font="0", horizontalAlignment="center", verticalAlignment="center", wrap="wrap", foregroundColor="foreground", foregroundColorSelected="foreground")
            sub(mode, "text", index="Description", position="20,219", size="%d,78" % (width - 40), font="1", horizontalAlignment="center", wrap="wrap", foregroundColor="muted")


def reference_menu(root, profile):
    advanced = profile.endswith("Advanced")
    main = screen(root, "menu_mainmenu", title="Main Menu", ignoreWidgets="menuimage")
    sub(main, "widget", name="menuimage", position="0,0", size="1,1")
    picture(main, profile, "background.png", "0,0", "1920,1080")
    picture(main, profile, "menu-frame.png", "24,222" if advanced else "24,286", "1872,633" if advanced else "1872,516")
    # The provided dashboard is a wide crop; preserve its proportions inside FHD.
    reference_header(main, profile, menu=True)
    # Header sits just above the framed menu content as in the references.
    if advanced:
        picture(main, profile, "lounge-reference.png", "50,328", "448,440", scale="fill", cornerRadius="8")
        rect(main, "50,675", "448,93", "photo_caption")
        widget(main, "76,691", "244,62", source="global.CurrentTime", font=23, converters=[("ClockToText", "Format:%A\n%d %B %Y")])
        widget(main, "323,698", "159,58", source="global.CurrentTime", font=43, halign="right", converters=[("ClockToText", "Format:%H:%M")])
        pos, size, width, height, orientation = "520,328", "1360,420", 340, 140, "grid"
    else:
        pos, size, width, height, orientation = "54,400", "1810,306", 362, 306, "horizontal"
    listing = widget(main, pos, size, source="menu", render="Listbox", listOrientation=orientation, backgroundColor="transparent", backgroundColorSelected="transparent", foregroundColor="foreground", scrollbarMode="showNever")
    menu_template(listing, width, height, advanced)
    # Description lives inside each tile; retain the native source without a second block.
    reference_footer(main, y=783 if advanced else 728, x=64, spacing=448, menu=True)
    applet(main, "bootstrap", "bind_menu", profile)
    alias = screen(root, "Menumainmenu", ignoreWidgets="menuimage")
    sub(alias, "panel", name="menu_mainmenu")


def channel_geometry(advanced):
    from Components.MetrixNEO.channel_layout import channel_geometry as native_geometry
    return native_geometry(advanced)


def channel_columns(advanced):
    # Independently traced FHD anchors. Scaling the entire classic row squeezed
    # the Advanced channel-name column and shifted both programme/progress fields.
    if advanced:
        return {"picon": (84, 70), "service": (176, 126), "divider": 310,
                "programme": (340, 436), "progress": (794, 78), "fonts": (20, 21, 21)}
    return {"picon": (94, 80), "service": (210, 152), "divider": 372,
            "programme": (402, 642), "progress": (1068, 98), "fonts": (23, 24, 23)}


def reference_channels(root, profile):
    advanced = profile.endswith("Advanced")
    g = channel_geometry(advanced)
    main = screen(root, "ChannelSelection", title="TV")
    # The city in the mockup represented example channel content, not wallpaper.
    # User choice: solid midnight blue, with no video or fixed photograph behind.
    rect(main, "0,0", "1920,1080", "background")
    reference_header(main, profile, inset=advanced)
    x, y, width, height = g["list"]
    picture(main, profile, "channels-frame.png", "%d,%d" % (x - 2, y - 2), "%d,%d" % (width + 4, height + 4))
    points = channel_columns(advanced)["fonts"]
    widget(main, "%d,%d" % (x, y), "%d,%d" % (width, height), name="list", render="Listbox", scrollbarMode="showNever", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground", serviceItemHeight=g["row"], serviceNameFont="Regular;%d" % points[0], serviceInfoFont="Regular;%d" % points[1], serviceNumberFont="Regular;%d" % points[2], selectionPixmap=profile + "/assets/selection-row.png")
    dx, dy, dw, dh = g["detail"]
    picture(main, profile, "details-frame.png", "%d,%d" % (dx, dy), "%d,%d" % (dw, dh))
    ix, iy, iw, ih = g["image"]
    source = "ServiceEvent"
    # Without artwork the native service/title/synopsis move up together.
    widget(main, "%d,%d" % (ix, iy), "%d,%d" % (iw, ih), source=source, render="MetrixNEOPoster", neoProfile=profile, neoChannelLayout="1", zPosition="2")
    sx, sy = g["service"]
    picon_width = 180 if advanced else 226
    widget(main, "%d,%d" % (sx, sy), "%d,%d" % (picon_width, 74 if advanced else 94), source=source, render="MetrixNEOPicon", converters=[("ServiceName", "Reference")])
    widget(main, "%d,%d" % (sx + picon_width + 15, sy + 25), "%d,48" % (iw - picon_width - 25), source=source, converters=[("ServiceName", "Name")], font=31 if advanced else 34)
    tx, ty = g["title"]
    widget(main, "%d,%d" % (tx, ty), "%d,46" % (iw - 16), source=source, converters=[("EventName", "Name")], font=31 if advanced else 35)
    px, py = g["progress"]
    widget(main, "%d,%d" % (px, py), "%d,11" % (iw - 16), source=source, render="Progress", converters=[("EventTime", "Progress")], pixmap=profile + "/assets/progress.png", backgroundColor="track", borderWidth="0")
    tx, ty, tw, th = g["description"]
    widget(main, "%d,%d" % (tx, ty), "%d,%d" % (tw, th), source=source, converters=[("EventName", "FullDescription")], font=21 if advanced else 23, foregroundColor="muted")
    nx, ny = g["next"]
    for index in range(2):
        label(main, "Suivant %d :" % (index + 1), "%d,%d" % (nx, ny + 39 * index), "124,35", 20, "epg")
        widget(main, "%d,%d" % (nx + 133, ny + 39 * index), "%d,35" % (iw - 145), source=source, converters=[("MetrixNEOInfo", "Next%d,%s" % (index + 1, profile))], font=20)
    # No codec, audio or tuner is guessed from a channel name or its current neighbour.
    techx, techy = g["technical"]
    rect(main, "%d,%d" % (techx, techy - 10), "%d,1" % (iw - 16), "line")
    column = (iw - 20) // 3
    for index, field in enumerate(("video", "aspect_source", "audio")):
        if index:
            rect(main, "%d,%d" % (techx + index * column, techy + 7), "1,55", "line_bright")
        widget(main, "%d,%d" % (techx + index * column + 5, techy + 5), "%d,62" % (column - 10), source=source, render="MetrixNEOServiceFacts", neoProfile=profile, neoField=field, font=19, halign="center", foregroundColor="foreground")
    reference_footer(main, y=978 if advanced else 1014, x=250 if advanced else 48, spacing=308 if advanced else 360)
    applet(main, "bootstrap", "bind_channel", profile)
    for name in ("ChannelSelectionDefault", "ChannelSelectionPIG", "ChannelSelectionFull", "ChannelSelection_PIG"):
        alias = screen(root, name, base="ChannelSelection", label="NEO · liste de référence sans PiG")
        sub(alias, "panel", name="ChannelSelection")


def reference_templates(folder, advanced):
    import xml.etree.ElementTree as ET
    from generate_skins import write_xml
    g = channel_geometry(advanced)
    width, height = g["list"][2:]
    root = ET.Element("templates")
    for name, row in (("NEO", g["row"]), ("NEO Compact", 34 if advanced else 40)):
        columns = channel_columns(advanced)
        template = sub(root, "template", component="serviceList", name=name, screens="ChannelSelectionDefault,ChannelSelectionPIG,ChannelSelectionFull", fonts=",".join("Regular;%d" % point for point in columns["fonts"]))
        for mode_name in ("services", "bouquets", "other"):
            mode = sub(template, "mode", name=mode_name, itemHeight=row, foregroundColor="foreground", foregroundColorSelected="foreground", backgroundColor="panel", backgroundColorSelected="selection")
            row_prefix = "" if advanced else "classic_"
            inset = 2 if advanced else 4
            sub(mode, "rectangle", position="0,0", size="%d,%d" % (width, row), backgroundColor="panel", backgroundColorSelected="panel")
            sub(mode, "rectangle", position="%d,0" % inset, size="%d,%d" % (width-2*inset, row), backgroundColor="panel", backgroundColorSelected="row_selection_rim", cornerRadius="7")
            sub(mode, "rectangle", position="%d,1" % (inset+1), size="%d,%d" % (width-2*inset-2, row-2), foregroundGradient="panel,panel,vertical", foregroundGradientSelected=row_prefix + "row_selected_top," + row_prefix + "row_selected_mid," + row_prefix + "row_selected_bottom,vertical", cornerRadius="6")
            sub(mode, "rectangle", position="%d,0" % (inset+8), size="%d,1" % (width-2*inset-16), backgroundColor="panel", backgroundColorSelected="row_selection_highlight")
            sub(mode, "rectangle", position="0,%d" % (row - 1), size="%d,1" % width, backgroundColor="row_line")
            if mode_name == "other":
                sub(mode, "text", index="EntryName", position="18,0", size="%d,%d" % (width - 36, row), font="0", verticalAlignment="center", wrap="ellipsis")
                continue
            def box(x, w):
                return "%d,0" % x, "%d,%d" % (w, row)
            pos, size = box(14, 45)
            sub(mode, "text", index="Number", position=pos, size=size, font="2", verticalAlignment="center", horizontalAlignment="center")
            sub(mode, "pixmap", index="Picon", position="%d,3" % columns["picon"][0], size="%d,%d" % (columns["picon"][1], row - 6), alpha="blend", scale="centerScaled")
            pos, size = box(*columns["service"])
            sub(mode, "text", index="ServiceName", position=pos, size=size, font="0", verticalAlignment="center", wrap="ellipsis", recordColor="red")
            sub(mode, "rectangle", position="%d,9" % columns["divider"], size="1,%d" % (row - 18), backgroundColor="line_bright")
            pos, size = box(*columns["programme"])
            sub(mode, "text", index="Title1", position=pos, size=size, font="1", verticalAlignment="center", wrap="ellipsis", foregroundColor="epg", foregroundColorSelected="foreground")
            bar_height = 12
            sub(mode, "progress", index="Progress", position="%d,%d" % (columns["progress"][0], (row-bar_height)//2), size="%d,%d" % (columns["progress"][1], bar_height), borderWidth="0", foregroundColor="accent", foregroundColorSelected="foreground", backgroundColor="track", cornerRadius="2")
    write_xml(root, folder / "skinTemplates.xml")


def apply_reference_design(root, profile):
    names = {"menu_mainmenu", "Menumainmenu", "ChannelSelection", "ChannelSelectionDefault", "ChannelSelectionPIG", "ChannelSelectionFull", "ChannelSelection_PIG", "ChannelContextMenu", "EventViewContextMenu", "EventViewContextMenuChoiceBox"}
    for node in list(root):
        if node.tag == "screen" and node.get("name") in names:
            root.remove(node)
    reference_menu(root, profile)
    reference_channels(root, profile)
    advanced = profile.endswith("Advanced")
    # Shared with the actual ChoiceList decorator, rather than global ChoiceList
    # metrics which also affect unrelated native dialogs.
    from Components.MetrixNEO.context_menu import geometry
    g = geometry(profile)
    for name in ("ChannelContextMenu", "EventViewContextMenu", "EventViewContextMenuChoiceBox"):
        wx, wy, ww, wh = g["window"]
        # Session.execEnd hides the previous dialog before this native window
        # opens. Outside its bounds the main decoder's live picture stays visible.
        # No full-screen blue underlay, fixed photo, PiG or service change here.
        main = screen(root, name, size="%d,%d" % (ww, wh), position="%d,%d" % (wx, wy), bg="transparent", title="Menu Contextuel")
        fx, fy, fw, fh = g["frame"]
        picture(main, profile, "context-frame.png", "%d,%d" % (fx, fy), "%d,%d" % (fw, fh))
        context_header(main, profile)
        if advanced:
            widget(main, "32,126", "280,123", source="global.CurrentTime", render="MetrixNEOPoster", neoProfile=profile, neoContext="1")
            widget(main, "32,260", "280,90", source="global.CurrentTime", render="MetrixNEOContext", neoPart="title", font=22)
            widget(main, "1110,126", "330,560", source="global.CurrentTime", render="MetrixNEOContext", neoPart="action", font=24)
        else:
            picture(main, profile, "menu-film.png", "142,190", "200,200")
            widget(main, "44,432", "440,256", source="global.CurrentTime", render="MetrixNEOContext", neoPart="action", font=26)
        is_choicebox = name == "EventViewContextMenuChoiceBox"
        widget(main, "%d,%d" % (g["x"], g["list_y"]), "%d,%d" % (g["width"], g["visible_rows"] * g["row"]), name="list" if is_choicebox else "menu", render="Listbox", font=g["font"], scrollbarMode="showOnDemand", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground", itemHeight=g["row"], selectionPixmap=profile + "/assets/context-selection.png")
        if is_choicebox:
            # ChoiceBox's text/summary sources remain native; no action map changes.
            label(main, "EXIT · Annuler       OK · Sélectionner", "30,%d" % g["footer_y"], "1100,38", 23, "muted")
        else:
            for index, key in enumerate(("red", "green", "yellow", "blue")):
                x = 30 + index * 360
                rect(main, "%d,%d" % (x, g["footer_y"]), "8,36", key)
                widget(main, "%d,%d" % (x + 22, g["footer_y"]), "310,38", source="key_" + key, font=23, conditional="key_" + key)
        applet(main, "context_menu", "bind_context", profile)
