"""Static checks against the pinned API inventory, paths, layout and assets."""
import ast
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE_CONVERTERS = {"ClockToText", "ServiceName", "EventName", "EventTime", "RemainingToText", "ConditionalShowHide", "TemplatedMultiContent"}
NATIVE_RENDERERS = {"Label", "Progress", "Pixmap", "Listbox"}
REQUIRED = {"menu_mainmenu", "Menu", "ChannelSelection", "InfoBar", "SecondInfoBar", "GraphicalEPG", "EPGSelection", "EventView", "ChannelContextMenu", "EventViewContextMenuChoiceBox", "Setup", "AudioSelection", "Subtitles", "MessageBox", "ChoiceBox", "Volume", "Mute", "PluginBrowser", "MovieSelection", "RecordTimerOverview", "VirtualKeyboard", "MetrixNEOSettings"}


def validate():
    errors, checks = [], 0
    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(message)
    for profile in ("MetrixNEO", "MetrixNEOAdvanced"):
        folder = ROOT / "skins" / profile
        dom = ET.parse(folder / "skin.xml").getroot()
        screens = {s.get("name"): s for s in dom.findall("screen")}
        for face in dom.findall("fonts/font"):
            filename=face.get("filename","")
            if filename.startswith("/usr/share/enigma2/"):
                embedded=(ROOT/"skins"/filename.removeprefix("/usr/share/enigma2/")).resolve()
                check(embedded.is_relative_to((ROOT/"skins").resolve()) and embedded.is_file(),profile+": bundled font missing or unsafe")
        check(REQUIRED <= screens.keys(), profile + ": missing screen")
        check(len(screens) == len(dom.findall("screen")), profile + ": duplicate screens")
        resolution = dom.find("output/resolution")
        check(resolution.get("xres") == "1920" and resolution.get("yres") == "1080", profile + ": FHD")
        for screen in dom.findall("screen"):
            width, height = map(int, screen.get("size").split(","))
            check(width <= 1920 and height <= 1080, profile + ": screen oversized")
            for node in screen.iter():
                if node.tag == "applet":
                    ast.parse(node.text)
                    check("onLayoutFinish" == node.get("type"), "Unsupported applet hook")
                if node.tag == "panel":
                    check(node.get("name") in screens, "Undefined panel: " + str(node.get("name")))
                if node.get("position") and node.get("size") and node.tag not in ("screen", "mode"):
                    x, y = map(int, node.get("position").split(","))
                    w, h = map(int, node.get("size").split(","))
                    check(min(x, y, w, h) >= 0 and x + w <= width and y + h <= height,
                          "%s/%s: widget outside %s: %s" % (profile, screen.get("name"), screen.get("size"), ET.tostring(node, encoding="unicode")[:200]))
                for attr in ("pixmap", "pixmaps"):
                    for asset in node.get(attr, "").split(","):
                        if asset:
                            check(not asset.startswith(("/", "C:", "..")) and (ROOT / "skins" / asset).is_file(), "Missing/unsafe asset: " + asset)
                if node.tag == "convert":
                    name = node.get("type")
                    check(name in NATIVE_CONVERTERS or (ROOT / "runtime/Components/Converter" / (name + ".py")).is_file(), "Unknown converter: " + name)
                if node.get("render"):
                    name = node.get("render")
                    check(name in NATIVE_RENDERERS or (ROOT / "runtime/Components/Renderer" / (name + ".py")).is_file(), "Unknown renderer: " + name)
            if screen.get("name", "").startswith("ChannelSelection"):
                check(not any(n.get("render") in ("Pig", "Video") or n.get("name") == "video" for n in screen.iter()), "PiG in channel list")
            if screen.get("name") in ("ChannelContextMenu", "EventViewContextMenu", "EventViewContextMenuChoiceBox"):
                check(width < 1920 and height < 1080 and screen.get("backgroundColor") == "transparent", "Context must leave the live video visible outside its window")
                check(not any(n.get("size") == "1920,1080" or "scenic-reference" in n.get("pixmap", "") for n in screen.iter()), "Full-screen overlay or fixed channel photo in context")
        for bar in screens["InfoBar"].findall("widget[@render='Progress']"):
            if bar.get("source") == "session.FrontendStatus":
                check(bar.get("orientation") == "orRightToLeft", "Signal orientation")
        for name in ("GraphicalEPG", "EPGSelection", "EPGSelectionMulti", "QuickEPG"):
            listing = screens[name].find("widget[@name='list']")
            check(listing.get("ServiceFontGraphical") == "Regular;24" and listing.get("EntryFontGraphical") == "Regular;24", profile + ": unsupported/default EPG fonts")
            for attr in ("EntryBackgroundColorSelected", "EntryBackgroundColorNowSelected", "EntryBackgroundColorPastSelected", "RecordBackgroundColorSelected", "ZapBackgroundColorSelected"):
                check(listing.get(attr) == "selection", profile + ": unthemed EPG state: " + attr)
        native_epg = {"CurrentEvent", "SelectedCurrentEvent", "OtherEvent", "SelectedEvent", "OtherService", "CurrentService", "RecordEvent", "SelectedRecordEvent", "RecordingEvent", "ZapEvent", "SelectedZapEvent", "information", "SelectedInformation", "TimeLineDate", "TimeLineTime"}
        native_epg.update(prefix + side for prefix in ("Border", "SelectedBorder") for side in ("Top", "Bottom", "Left", "Right"))
        for name in native_epg:
            check((folder / "epg" / (name + ".png")).is_file(), profile + ": missing native graphical EPG asset: " + name)
        bottom = any(n.get("position") == "0,832" and n.get("size") == "1920,248" for n in screens["InfoBar"])
        check(bottom, "InfoBar must meet bottom edge")
        templates = ET.parse(folder / "skinTemplates.xml").getroot()
        list_width = int(screens["ChannelSelection"].find("widget[@name='list']").get("size").split(",")[0])
        for template in templates:
            for mode in template:
                check(mode.get("itemHeight") in ("34", "38", "40", "44", "45"), "ServiceList row density")
                row_height = int(mode.get("itemHeight"))
                for node in mode:
                    if node.get("position") and node.get("size"):
                        x, y = map(int, node.get("position").split(","))
                        w, h = map(int, node.get("size").split(","))
                        check(min(x,y) >= 0 and min(w,h) > 0 and x+w <= list_width and y+h <= row_height,
                              "%s/%s/%s: ServiceList cell exceeds row bounds" % (profile,template.get("name"),mode.get("name")))
                indexes = {n.get("index", "") for n in mode.iter()}
                check(not any("Time" in i or "Resolution" in i for i in indexes), "Time or quality badge in channel row")
        check((folder / "prev.png").is_file(), "Selector preview missing")
    for base in ("runtime", "plugin", "tools", "tests"):
        for path in (ROOT / base).rglob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            checks += 1
    report = {"checks": checks, "errors": errors, "result": "PASS" if not errors else "FAIL", "hardware": "NOT_PERFORMED", "visual_reference_comparison": "SIX_USER_IMAGES_TRACED_HARDWARE_NOT_COMPARED"}
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build/static-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return not errors


if __name__ == "__main__":
    sys.exit(0 if validate() else 1)
