"""Reproducible FHD skins. Builds only inside this repository."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TOKENS = {"background": "031323", "panel": "031523", "secondary": "09263B",
          "selection": "084B9C", "accent": "11B8EF", "foreground": "E9F0F8",
          "muted": "A7B6C8", "red": "F02C2C", "green": "23CD38", "yellow": "F2D936",
          "blue": "119BE6", "transparent": "FF031323", "line": "123E5A",
          "line_bright": "178AB4", "row_line": "092333", "epg": "48A6CC",
          "track": "1D2E3E", "tile_top": "0B3154", "tile_mid": "082641", "tile_bottom": "072039",
          "tile_highlight": "174468", "tile_edge": "A00064A0", "tile_edge_clear": "FF0064A0", "selected_top": "0046AE", "selected_mid": "00368F", "selected_bottom": "0052B2",
          "selection_rim": "158CDF", "selection_glow": "008EEB", "selection_glow_alpha": "60008EEB", "selection_glow_weak": "A0008EEB", "selection_glow_clear": "FF008EEB", "selection_highlight": "329AE9", "photo_caption": "38030E18",
          "classic_tile_top": "0C2B47", "classic_tile_mid": "09243D", "classic_tile_bottom": "091E31",
          "classic_selected_top": "003389", "classic_selected_mid": "002E7C", "classic_selected_bottom": "002E6D",
          "menu_selected_top": "003EA0", "menu_selected_mid": "00358F", "menu_selected_bottom": "0048A9",
          "classic_menu_selected_top": "003389", "classic_menu_selected_mid": "003080", "classic_menu_selected_bottom": "002B73",
          "row_selected_top": "0348B6", "row_selected_mid": "023289", "row_selected_bottom": "0052BC",
          "classic_row_selected_top": "003F9F", "classic_row_selected_mid": "00358D", "classic_row_selected_bottom": "0241AC",
          "row_selection_rim": "1A7BCB", "row_selection_highlight": "2084D9",
          "infobar_ink": "DDE5EC", "infobar_muted": "ADB9C5", "infobar_line": "536571",
          "infobar_cyan": "12BCE2", "infobar_gold": "EFC643"}
# Audio keeps the reference layout and inherits the Metrix NEO palette.
TOKENS.update({"audio_panel":"18"+TOKENS["background"],
               **{"audio_"+name:TOKENS[target] for name,target in (
                   ("ink","foreground"),("selection","selection"),("rule","accent"),
                   ("button_ink","foreground"),("red","red"),("green","green"),
                   ("yellow","yellow"),("blue","blue"))}})


def sub(parent, tag, **attrs):
    return ET.SubElement(parent, tag, {k: str(v) for k, v in attrs.items()})


def label(parent, text, pos, size, font=28, color="foreground", **attrs):
    return sub(parent, "eLabel", text=text, position=pos, size=size, font=font if isinstance(font, str) else "Regular;%d" % font,
               foregroundColor=color, backgroundColor="background", transparent="1", **attrs)


def widget(parent, pos, size, source=None, name=None, render="Label", converters=(), font=28, **attrs):
    args = {"position": pos, "size": size}
    if source:
        args.update(source=source, render=render)
    else:
        args["name"] = name
    if render in ("Label", "MetrixNEONext", "MetrixNEOServiceFacts", "MetrixNEOContext"):
        args.update(font=font if isinstance(font, str) else "Regular;%d" % font, foregroundColor="foreground", backgroundColor="background", transparent="1")
    elif render == "Listbox" and not source:
        args["font"] = font if isinstance(font, str) else "Regular;%d" % font
    args.update(attrs)
    result = sub(parent, "widget", **args)
    for type_, value in converters:
        sub(result, "convert", type=type_).text = value
    return result


def rect(parent, pos, size, color="panel"):
    return sub(parent, "eLabel", position=pos, size=size, backgroundColor=color)


def screen(root, name, size="1920,1080", position="0,0", bg="background", **attrs):
    return sub(root, "screen", name=name, position=position, size=size, backgroundColor=bg,
               flags="wfNoBorder", **attrs)


def applet(parent, module, function, profile):
    sub(parent, "applet", type="onLayoutFinish").text = "from Components.MetrixNEO.%s import %s\n%s(self, %r)" % (module, function, function, profile)


def header(parent, profile, title=True):
    from reference_design import reference_header
    reference_header(parent, profile, title=title)


def footer(parent, y=1008, conditional=False):
    for index, color in enumerate(("red", "green", "yellow", "blue")):
        x = 48 + index * 405
        widget(parent,"%d,%d"%(x,y+7),"5,30",source="key_"+color,font=1,
               backgroundColor=color,foregroundColor=color,transparent="0",conditional="key_"+color,
               converters=[("ConditionalShowHide", "")])
        widget(parent, "%d,%d" % (x + 18, y), "365,44", source="key_" + color, font=24,
               conditional="key_" + color,converters=[("ConditionalShowHide", "")])


def menu(root, profile, advanced):
    native = screen(root, "Menu", ignoreWidgets="menuimage")
    sub(native, "widget", name="menuimage", position="0,0", size="1,1")
    header(native, profile)
    list_widget = widget(native, "490,210", "1330,648", source="menu", render="Listbox",
                         scrollbarMode="showOnDemand", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground")
    menu_template(list_widget, 1330, 72, "vertical")
    widget(native, "490,880", "1320,92", source="description", font=26)
    footer(native)

    main = screen(root, "menu_mainmenu", title="Metrix NEO Advanced" if advanced else "Metrix NEO", ignoreWidgets="menuimage")
    sub(main, "widget", name="menuimage", position="0,0", size="1,1")
    header(main, profile)
    if advanced:
        sub(main, "ePixmap", position="48,190", size="550,706", pixmap=profile + "/assets/lounge.png", alphatest="blend")
        label(main, "METRIX NEO", "80,225", "480,60", 42)
        label(main, "ADVANCED", "82,288", "470,42", 26, "accent")
        widget(main, "80,760", "480,110", source="description", font=24)
        pos, size, width, height, orient = "640,190", "1230,708", 410, 177, "grid"
    else:
        pos, size, width, height, orient = "60,320", "1800,250", 360, 250, "horizontal"
        widget(main, "70,638", "1780,150", source="description", font=28)
    menu_widget = widget(main, pos, size, source="menu", render="Listbox", listOrientation=orient,
                         backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground", scrollbarMode="showNever")
    menu_template(menu_widget, width, height, orient)
    footer(main)
    label(main, "MENU · Toutes les fonctions natives", "1260,952", "610,36", 23, "muted", halign="right")
    applet(main, "bootstrap", "bind_menu", profile)
    alias = screen(root, "Menumainmenu", ignoreWidgets="menuimage")
    sub(alias, "panel", name="menu_mainmenu")


def menu_template(parent, width, height, orientation):
    template = sub(parent, "template", name="Default", fonts="Regular;28,Regular;22", itemWidth=width, itemHeight=height)
    # All native entry styles use the same data mapping and retain their callbacks.
    for style in ("default", "text", "number", "image", "both"):
        mode = sub(template, "mode", name=style, orientation=orientation, itemWidth=width, itemHeight=height)
        sub(mode, "text", index="Text", position="24,16", size="%d,%d" % (width - 48, min(94, height - 20)), font="0", verticalAlignment="center", wrap="wrap")
        if height > 130:
            sub(mode, "text", index="Number", position="24,%d" % (height - 52), size="70,32", font="1", foregroundColor="muted")


def channels(root, profile, advanced):
    main = screen(root, "ChannelSelection", title="Chaînes")
    header(main, profile)
    widget(main, "48,180", "1190,780" if advanced else "1190,800", name="list", render="Listbox",
           scrollbarMode="showOnDemand", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground",
           serviceItemHeight=60 if advanced else 40, serviceNameFont="Regular;26", serviceInfoFont="Regular;25", serviceNumberFont="Regular;23")
    rect(main, "1270,180", "1,800", "secondary")
    source = "ServiceEvent"
    widget(main, "1310,188", "550,68", source=source, render="MetrixNEOPicon", converters=[("ServiceName", "Reference")])
    widget(main, "1310,570", "550,260", source=source, render="MetrixNEOPoster", neoProfile=profile, neoReflow="1")
    widget(main, "1310,280", "550,82", source=source, converters=[("EventName", "Name")], font=31)
    widget(main, "1310,380", "550,175", source=source, converters=[("EventName", "FullDescription")], font=24, foregroundColor="muted")
    widget(main, "1310,850", "550,46", source=source, converters=[("MetrixNEOInfo", "Next1," + profile)], font=24)
    widget(main, "1310,901", "550,46", source=source, converters=[("MetrixNEOInfo", "Next2," + profile)], font=24)
    if advanced:
        widget(main, "1310,953", "550,35", source=source, converters=[("MetrixNEOInfo", "Smart," + profile)], font=23, foregroundColor="accent")
    footer(main)
    applet(main, "bootstrap", "bind_channel", profile)
    for name in ("ChannelSelectionDefault", "ChannelSelectionPIG", "ChannelSelectionFull", "ChannelSelection_PIG"):
        alias = screen(root, name, base="ChannelSelection", label="NEO · texte et image fixe")
        sub(alias, "panel", name="ChannelSelection")


def infobar(root, profile, advanced):
    from infobar_design import build
    build(root, profile)
    second = screen(root, "SecondInfoBar", bg="transparent")
    rect(second, "24,430", "1872,378" if advanced else "1872,270", "background")
    widget(second, "56,456", "1650,62", source="session.Event_Now", converters=[("EventName", "Name")], font=34)
    widget(second, "56,528", "1740,200" if advanced else "1740,160", source="session.Event_Now", converters=[("EventName", "FullDescription")], font=27)
    if advanced:
        widget(second, "56,750", "1740,45", source="session.CurrentService", converters=[("MetrixNEOInfo", "Diagnostics," + profile)], font=24, foregroundColor="muted")
    sub(second, "panel", name="InfoBar")


def epg(root, profile, advanced):
    main = screen(root, "GraphicalEPG", title="Guide des programmes")
    header(main, profile)
    left = 410 if advanced else 48
    if advanced:
        widget(main, "48,188", "320,180", source="Event", render="MetrixNEOPoster", neoProfile=profile)
        widget(main, "48,390", "320,115", source="Event", converters=[("EventName", "Name")], font=28)
        widget(main, "48,530", "320,280", source="Event", converters=[("EventName", "FullDescription")], font=24, foregroundColor="muted")
        widget(main, "48,845", "320,48", source="Event", converters=[("MetrixNEOInfo", "Smart," + profile)], font=24)
        widget(main, "48,900", "320,44", source="Event", render="MetrixNEONext", neoIndex="0", font="Regular;23", foregroundColor="muted")
        widget(main, "48,950", "320,44", source="Event", render="MetrixNEONext", neoIndex="1", font="Regular;23", foregroundColor="muted")
    else:
        widget(main, "48,180", "1750,50", source="Event", converters=[("EventName", "Name")], font=32)
        widget(main, "48,236", "1750,100", source="Event", converters=[("EventName", "FullDescription")], font=25, foregroundColor="muted")
    y = 195 if advanced else 375
    width = 1872 - left
    height = 660 if advanced else 550
    widget(main, "%d,%d" % (left, y), "%d,42" % width, name="timeline_text", font=24, TimelineFont="Regular;24", itemHeight="42", backgroundColor="secondary", borderColor="line", borderWidth="1")
    listing = widget(main, "%d,%d" % (left, y + 42), "%d,%d" % (width, height), name="list", render="Listbox", scrollbarMode="showNever", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground")
    epg_style(listing)
    widget(main, "%d,%d" % (left + 20, y + 62), "%d,150" % (width - 40), name="lab1", font=28, zPosition="3")
    widget(main, "%d,%d" % (left, y + 42), "3,%d" % height, name="timeline_now", render="Pixmap", pixmap=profile + "/assets/timeline.png", zPosition="2")
    for index in range(6):
        widget(main, "%d,%d" % (left, y + 42), "1,%d" % height, name="timeline%d" % index, render="Pixmap", pixmap=profile + "/assets/timeline.png", zPosition="1")
    footer(main)
    for name in ("GraphicalEPGPIG", "GraphicalInfoBarEPG"):
        alias = screen(root, name)
        sub(alias, "panel", name="GraphicalEPG")
    for name in ("EPGSelection", "EPGSelectionMulti", "QuickEPG"):
        view = screen(root, name)
        header(view, profile)
        listing = widget(view, "48,190", "1170,720", name="list", render="Listbox", scrollbarMode="showOnDemand", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground")
        epg_style(listing)
        widget(view, "1270,195", "590,100", source="Event", converters=[("EventName", "Name")], font=32)
        widget(view, "1270,320", "590,550", source="Event", converters=[("EventName", "FullDescription")], font=26)
        widget(view, "48,925", "1170,55", name="lab1", font=25)
        footer(view)


def epg_style(listing):
    """Exact EPGList.applySkin attribute names from the pinned OpenATV API."""
    listing.attrib.pop("font", None)
    palette = {
        "ServiceForegroundColor": "foreground", "ServiceForegroundColorNow": "foreground",
        "ServiceBackgroundColor": "panel", "ServiceBackgroundColorNow": "secondary",
        "EntryForegroundColor": "foreground", "EntryForegroundColorSelected": "foreground",
        "EntryBackgroundColor": "panel", "EntryBackgroundColorSelected": "selection",
        "EntryForegroundColorNow": "foreground", "EntryForegroundColorNowSelected": "foreground",
        "EntryBackgroundColorNow": "secondary", "EntryBackgroundColorNowSelected": "selection",
        "EntryForegroundColorPast": "muted", "EntryForegroundColorPastSelected": "foreground",
        "EntryBackgroundColorPast": "panel", "EntryBackgroundColorPastSelected": "selection",
        "TimeForegroundColor": "muted", "TimeBackgroundColor": "panel",
        "PrimeTimeForegroundColor": "foreground", "PrimeTimeBackgroundColor": "secondary",
        "RecordForegroundColor": "foreground", "RecordForegroundColorSelected": "foreground",
        "RecordBackgroundColor": "secondary", "RecordBackgroundColorSelected": "selection",
        "ZapForegroundColor": "foreground", "ZapForegroundColorSelected": "foreground",
        "ZapBackgroundColor": "secondary", "ZapBackgroundColorSelected": "selection",
        "ServiceBorderColor": "line", "EntryBorderColor": "line",
        "ServiceBorderWidth": "1", "EventBorderWidth": "1", "EventNamePadding": "8",
        "ServiceNamePadding": "8", "EntryFontAlignment": "left", "EntryFontWrap": "yes",
    }
    for attr in ("ServiceFontGraphical", "ServiceFontInfobar", "EntryFontGraphical", "EventFontInfobar", "EventFontSingle", "EventFontMulti", "EventFontVertical", "TimeFontVertical"):
        palette[attr] = "Regular;24"
    listing.attrib.update(palette)


def event_views(root, profile, advanced):
    for name in ("EventView", "EventViewSimple", "InfoBarEventView"):
        main = screen(root, name)
        header(main, profile)
        widget(main, "48,180", "1650,50", name="channel", font=28)
        widget(main, "48,245", "900,42", name="datetime", font=26)
        widget(main, "1000,245", "800,42", name="duration", font=26, halign="right")
        if advanced:
            widget(main, "48,325", "460,260", source="Event", render="MetrixNEOPoster", neoProfile=profile)
            widget(main, "48,620", "460,45", source="Event", converters=[("MetrixNEOInfo", "Smart," + profile)], font=26, foregroundColor="accent")
            widget(main, "48,710", "460,70", source="Event", render="MetrixNEONext", neoIndex="0", font="Regular;24", foregroundColor="muted")
            widget(main, "48,805", "460,70", source="Event", render="MetrixNEONext", neoIndex="1", font="Regular;24", foregroundColor="muted")
        widget(main, "560,325" if advanced else "48,325", "1300,575" if advanced else "1810,575", name="epg_description", font=28)
        footer(main)


def settings(root, profile, advanced):
    main = screen(root, "Setup")
    header(main, profile)
    widget(main, "48,195", "1230,690", name="config", render="Listbox", font="Regular;28", itemHeight="46", enableWrapAround="1", scrollbarMode="showOnDemand", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground")
    widget(main, "1320,200", "530,590", name="description", font=27, foregroundColor="muted")
    widget(main, "48,920", "1790,50", name="footnote", font=24)
    footer(main, conditional=True)
    own = screen(root, "MetrixNEOSettings", title="Metrix NEO · Préférences")
    header(own, profile)
    widget(own, "48,205", "320,480", name="categories", render="Listbox", font="Regular;28", itemHeight="64", scrollbarMode="showNever", backgroundColor="panel", backgroundColorSelected="secondary", foregroundColor="muted", foregroundColorSelected="foreground")
    widget(own, "405,205", "960,640", name="config", render="Listbox", font="Regular;26", itemHeight="64", scrollbarMode="showOnDemand", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground")
    widget(own, "1420,205", "440,310", name="description", font=24, foregroundColor="muted")
    widget(own, "1420,550", "440,330", name="preview", font=26)
    widget(own, "48,930", "1790,50", name="footnote", font=24, foregroundColor="muted")
    footer(own)


def dialogs(root, profile, advanced):
    for name in ("ChannelContextMenu", "EventViewContextMenu"):
        main = screen(root, name, title="Actions contextuelles")
        header(main, profile)
        sub(main, "ePixmap", position="110,300", size="230,230", pixmap=profile + "/assets/context.png", alphatest="blend")
        label(main, "Actions de la sélection", "64,585", "460,90", 28)
        if advanced:
            label(main, "Toutes les opérations natives restent accessibles.\nLes actions proposées dépendent du contexte et des permissions.", "64,700", "470,230", 26, "muted")
        widget(main, "600,195", "1250,760", name="menu", render="Listbox", scrollbarMode="showOnDemand", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground", font="Regular;28", itemHeight="52")
    choice = screen(root, "ChoiceBox", size="1340,790", position="center,center")
    widget(choice, "40,35", "1260,160", name="text", font=29)
    widget(choice, "40,210", "1260,520", name="list", render="Listbox", scrollbarMode="showOnDemand", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground", font="Regular;28", itemHeight="48")
    message = screen(root, "MessageBox", size="1120,560", position="center,center")
    widget(message, "34,35", "64,64", name="icon", render="Pixmap", conditional="icon", pixmaps=",".join(profile + "/assets/" + icon + ".png" for icon in ("question", "info", "warning", "error", "info")), alphatest="blend")
    widget(message, "130,40", "950,320", name="text", font=30)
    widget(message, "40,385", "1030,130", name="list", render="Listbox", conditional="list", font="Regular;28", itemHeight="48", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground")
    volume = screen(root, "Volume", size="600,80", position="660,70")
    label(volume, "VOL", "22,18", "90,44", 25)
    widget(volume, "125,26", "440,24", name="Volume", render="Progress", foregroundColor="accent", backgroundColor="secondary", borderWidth="0")
    mute = screen(root, "Mute", size="250,66", position="835,70")
    label(mute, "MUET / MUTE", "14,15", "224,42", 26)


def audio(root, profile):
    from audio_design import build
    build(root,profile)
    subview = screen(root, "Subtitles")
    header(subview, profile)
    widget(subview, "48,200", "1810,730", name="config", render="Listbox", font="Regular;28", itemHeight="48", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground")


def secondary_screens(root, profile):
    from timer_design import build as build_timers
    build_timers(root,profile)
    movie = screen(root, "MovieSelection")
    header(movie, profile)
    widget(movie, "48,195", "1810,710", name="list", render="Listbox", scrollbarMode="showOnDemand", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground")
    widget(movie, "48,930", "850,50", name="freeDiskSpace", font=24)
    widget(movie, "950,930", "850,50", name="waitingtext", font=24)
    footer(movie)
    browser = screen(root, "PluginBrowser")
    header(browser, profile)
    for name, orientation in (("pluginList", "vertical"), ("pluginGrid", "grid")):
        listing = widget(browser, "48,190", "1810,700", source=name, render="Listbox", conditional=name, listOrientation=orientation, backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground", scrollbarMode="showOnDemand")
        if orientation == "vertical":
            spec = '{"template": [MultiContentEntryPixmapAlphaBlend(pos=(12,10),size=(100,50),png=3,flags=BT_SCALE|BT_KEEP_ASPECT_RATIO), MultiContentEntryText(pos=(150,4),size=(1600,40),font=0,text=1), MultiContentEntryText(pos=(150,46),size=(1600,32),font=1,text=2)], "fonts": [gFont("Regular",30),gFont("Regular",24)], "itemHeight": 88}'
        else:
            spec = '{"template": [MultiContentEntryPixmapAlphaBlend(pos=(145,20),size=(100,50),png=3,flags=BT_SCALE|BT_KEEP_ASPECT_RATIO), MultiContentEntryText(pos=(16,90),size=(358,78),font=0,flags=RT_WRAP|RT_HALIGN_CENTER,text=1)], "fonts": [gFont("Regular",28)], "itemWidth": 450, "itemHeight": 175}'
        sub(listing, "convert", type="TemplatedMultiContent").text = spec
    widget(browser, "48,190", "1810,700", name="quickselect", font=70, halign="center", valign="center", zPosition="2")
    widget(browser, "48,920", "1810,60", name="description", font=25)
    footer(browser)
    input_ = screen(root, "InputBox", size="1300,290", position="center,center")
    widget(input_, "40,35", "1220,80", name="text", font=30)
    widget(input_, "40,155", "1220,80", name="input", font=32)
    keyboard = screen(root, "VirtualKeyboard")
    header(keyboard, profile)
    widget(keyboard, "48,175", "1810,70", name="prompt", font=28)
    widget(keyboard, "48,260", "1810,80", name="text", font=34)
    widget(keyboard, "48,375", "1810,500", name="list", render="Listbox", scrollbarMode="showNever", backgroundColor="panel", backgroundColorSelected="selection", foregroundColor="foreground")
    widget(keyboard, "48,925", "1810,45", name="locale", font=24)
    footer(keyboard)
    alias = screen(root, "VirtualKeyBoard")
    sub(alias, "panel", name="VirtualKeyboard")
    console = screen(root, "Console")
    header(console, profile)
    widget(console, "48,195", "1810,770", name="text", font=24)


def service_templates(folder, advanced):
    root = ET.Element("templates")
    for name, height in (("NEO", 60 if advanced else 40), ("NEO Compact", 40)):
        template = sub(root, "template", component="serviceList", name=name,
                       screens="ChannelSelectionDefault,ChannelSelectionPIG,ChannelSelectionFull", fonts="Regular;26,Regular;24,Regular;23")
        for mode_name in ("services", "bouquets", "other"):
            mode = sub(template, "mode", name=mode_name, itemHeight=height,
                       foregroundColor="foreground", foregroundColorSelected="foreground", backgroundColor="panel", backgroundColorSelected="selection")
            if mode_name == "other":
                sub(mode, "text", index="EntryName", position="20,0", size="1130,%d" % height, font="0", verticalAlignment="center", wrap="ellipsis")
                continue
            sub(mode, "text", index="Number", position="12,0", size="58,%d" % height, font="2", verticalAlignment="center", horizontalAlignment="right")
            sub(mode, "pixmap", index="Picon", position="86,3", size="88,%d" % (height - 6), alpha="blend", scale="centerScaled")
            sub(mode, "text", index="ServiceName", position="192,0", size="270,%d" % height, font="0", verticalAlignment="center", wrap="ellipsis", recordColor="red")
            sub(mode, "text", index="Title1", position="480,0", size="580,%d" % height, font="1", verticalAlignment="center", wrap="ellipsis", foregroundColor="muted")
            sub(mode, "progress", index="Progress", position="1080,%d" % (height // 2 - 4), size="75,8", borderWidth="0", foregroundColor="accent", backgroundColor="secondary")
    write_xml(root, folder / "skinTemplates.xml")


def write_xml(root, path):
    ET.indent(root, space="  ")
    path.write_bytes(b'<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="utf-8") + b"\n")


def generate():
    for advanced, profile in ((False, "MetrixNEO"), (True, "MetrixNEOAdvanced")):
        folder = ROOT / "skins" / profile
        folder.mkdir(parents=True, exist_ok=True)
        root = ET.Element("skin")
        root.append(ET.Comment(" MetrixHD technical structure by iMaxxx / openATV Team. OpenATV-only; original notice in LICENSES/MetrixHD.txt. NEO modifications: Metrix NEO contributors, 2026. "))
        output = sub(root, "output", id="0")
        sub(output, "resolution", xres="1920", yres="1080", bpp="32")
        colors = sub(root, "colors")
        for name, value in TOKENS.items():
            sub(colors, "color", name=name, value="#" + ("00" if len(value) == 6 else "") + value)
        fonts = sub(root, "fonts")
        sub(fonts, "font", filename="LiberationSans-Regular.ttf", name="Regular", scale="100")
        sub(fonts, "font", filename="LiberationSans-Bold.ttf", name="MenuTitle", scale="100")
        if not advanced:
            sub(fonts, "font", filename="/usr/share/enigma2/MetrixNEO/fonts/Raleway-Light.ttf", name="ChannelLight", scale="100")
        else:
            font_folder=folder/"fonts"
            font_folder.mkdir(exist_ok=True)
            (font_folder/"Raleway-Light.ttf").write_bytes((ROOT/"skins/MetrixNEO/fonts/Raleway-Light.ttf").read_bytes())
        sub(fonts,"font",filename="/usr/share/enigma2/"+profile+"/fonts/Raleway-Light.ttf",name="AudioLight",scale="100")
        sub(fonts, "font", filename="ae_AlMateen.ttf", name="Replacement", scale="100", replacement="1")
        sub(fonts, "alias", name="ChoiceList", font="Regular", size="28", height="52")
        sub(fonts, "alias", name="VirtualKeyBoard", font="Regular", size="28", height="60")
        sub(fonts, "alias", name="VirtualKeyboard", font="Regular", size="28", height="60")
        parameters = sub(root, "parameters")
        sub(parameters, "parameter", name="ChoicelistName", value="48,0,1180,52")
        sub(parameters, "parameter", name="ChoicelistNameSingle", value="12,0,1216,52")
        sub(parameters, "parameter", name="ChoicelistIcon", value="6,8,32,32")
        sub(parameters, "parameter", name="ChoicelistVerticalAlignment", value="*center")
        sub(parameters, "parameter", name="VirtualKeyboard", value="112,60")
        menu(root, profile, advanced)
        channels(root, profile, advanced)
        infobar(root, profile, advanced)
        epg(root, profile, advanced)
        event_views(root, profile, advanced)
        settings(root, profile, advanced)
        dialogs(root, profile, advanced)
        audio(root, profile)
        secondary_screens(root, profile)
        from reference_design import apply_reference_design, reference_templates
        apply_reference_design(root, profile)
        from remaining_design import apply as apply_remaining_design
        apply_remaining_design(root,profile)
        write_xml(root, folder / "skin.xml")
        reference_templates(folder, advanced)


if __name__ == "__main__":
    generate()
