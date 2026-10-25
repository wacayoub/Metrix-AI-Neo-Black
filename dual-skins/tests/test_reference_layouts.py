import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "runtime"), str(ROOT / "tools")]
from Components.MetrixNEO.menu_model import ADVANCED_ORDER, NEO_ORDER
from build_ipk import payload


class ReferenceLayouts(unittest.TestCase):
    def root(self, profile):
        return ET.parse(ROOT / "skins" / profile / "skin.xml").getroot()

    def test_advanced_dashboard_four_columns_three_rows(self):
        dom = self.root("MetrixNEOAdvanced")
        listing = dom.find("screen[@name='menu_mainmenu']/widget[@source='menu']")
        self.assertEqual(listing.get("listOrientation"), "grid")
        w, h = map(int, listing.get("size").split(","))
        template = listing.find("template")
        self.assertEqual((w // int(template.get("itemWidth")), h // int(template.get("itemHeight"))), (4, 3))
        self.assertEqual(ADVANCED_ORDER[-4:], ("information", "neo_settings", "neo_tools", "shutdown"))

    def test_classic_five_tiles_with_real_icon_fields(self):
        listing = self.root("MetrixNEO").find("screen[@name='menu_mainmenu']/widget[@source='menu']")
        self.assertEqual(listing.get("listOrientation"), "horizontal")
        width = int(listing.get("size").split(",")[0])
        self.assertEqual(width // int(listing.find("template").get("itemWidth")), 5)
        self.assertEqual(len(NEO_ORDER), 5)
        self.assertEqual(listing.find("template/mode/pixmap").get("index"), "Image")

    def test_twenty_rows_as_latest_reference_images(self):
        for profile in ("MetrixNEO", "MetrixNEOAdvanced"):
            listing = self.root(profile).find("screen[@name='ChannelSelection']/widget[@name='list']")
            height = int(listing.get("size").split(",")[1])
            template = ET.parse(ROOT / "skins" / profile / "skinTemplates.xml").getroot()
            row = int(template.find("template[@name='NEO']/mode").get("itemHeight"))
            self.assertEqual(height // row, 20)

    def test_programme_picture_above_service_and_synopsis(self):
        for profile in ("MetrixNEO", "MetrixNEOAdvanced"):
            screen = self.root(profile).find("screen[@name='ChannelSelection']")
            picture = screen.find("widget[@render='MetrixNEOPoster']")
            y = int(picture.get("position").split(",")[1])
            h = int(picture.get("size").split(",")[1])
            title = next(w for w in screen.findall("widget") if w.find("convert[@type='EventName']") is not None and w.find("convert").text == "Name")
            self.assertLess(y + h, int(title.get("position").split(",")[1]))

    def test_local_menu_cells_fit_their_own_dimensions(self):
        for profile in ("MetrixNEO", "MetrixNEOAdvanced"):
            template = self.root(profile).find("screen[@name='menu_mainmenu']/widget[@source='menu']/template")
            width, height = int(template.get("itemWidth")), int(template.get("itemHeight"))
            for mode in template:
                for node in mode:
                    x, y = map(int, node.get("position").split(","))
                    w, h = map(int, node.get("size").split(","))
                    self.assertLessEqual(x + w, width)
                    self.assertLessEqual(y + h, height)

    def test_demo_film_is_not_bundled_in_any_receiver_package(self):
        for profile in ("MetrixNEO", "MetrixNEOAdvanced", "runtime", "helper"):
            names = payload(profile)
            self.assertFalse(any("programme-demo" in name or "scenic-reference" in name or ".codex-attachments" in name or "/previews/" in name for name in names))

    def test_no_reference_screenshot_embedded_as_live_ui(self):
        for profile in ("MetrixNEO", "MetrixNEOAdvanced"):
            text = ET.tostring(self.root(profile), encoding="unicode")
            self.assertNotIn("10005149", text)
            self.assertNotIn(".codex-attachments", text)


class MenuDecoration(unittest.TestCase):
    def test_preferences_access_without_helper_preserves_original_native_menu(self):
        from Components.MetrixNEO.bootstrap import _native_menu
        root = ET.fromstring('<menu key="mainmenu"><item key="third_party" text="Extension" /></menu>')
        session = types.SimpleNamespace(open=Mock())
        screen = types.SimpleNamespace(parentMenu=root, session=session, _neo_profile='MetrixNEOAdvanced')
        menu_module = types.ModuleType('Screens.Menu')
        menu_module.Menu = object()
        with patch.dict(sys.modules, {'Screens.Menu':menu_module}):
            _native_menu(screen)
        prepared = session.open.call_args.args[1]
        self.assertEqual(root.get('key'), 'mainmenu')
        self.assertEqual(len(root), 1)
        self.assertEqual(prepared[0].get('key'), 'third_party')
        self.assertIn('MetrixNEOAdvanced', prepared[-1].find('code').text)
        self.assertNotIn('Plugins.', prepared[-1].find('code').text)

    def test_decorating_preserves_native_callback_and_keys(self):
        from Components.MetrixNEO.bootstrap import decorate_menu_source
        callback = Mock()
        row = ("Plugins", "old image", "1", "Plugins", "Native description", "plugin_selection", 10, callback)
        class Source:
            list = [row]
            index = 5
            def setList(self, rows):
                self.list = rows
        source = Source()
        directories = types.ModuleType("Tools.Directories")
        directories.SCOPE_SKINS = 1
        directories.resolveFilename = lambda scope, path: path
        pixmaps = types.ModuleType("Tools.LoadPixmap")
        pixmaps.LoadPixmap = lambda path, cached: "loaded:" + path
        with patch.dict(sys.modules, {"Tools.Directories": directories, "Tools.LoadPixmap": pixmaps}):
            decorate_menu_source({"menu": source}, "MetrixNEOAdvanced")
        self.assertIs(source.list[0][7], callback)
        self.assertEqual(source.list[0][5], "plugin_selection")
        self.assertEqual(source.index, 0)
        self.assertIn("menu-plugins.png", source.list[0][1])
        callback.assert_not_called()


class SelectedChannelFacts(unittest.TestCase):
    def test_technical_columns_show_measured_values_and_hide_unknowns(self):
        label_module = types.ModuleType("Components.Renderer.Label")
        label_module.Label = type("Label", (), {"CHANGED_CLEAR": 0, "CHANGED_ALL": 1})
        enigma = types.ModuleType("enigma")
        enigma.iServiceInformation = types.SimpleNamespace(sTransponderData=1, sVideoWidth=2, sVideoHeight=3, sVideoType=4, sProgressive=5, sAspect=6)
        enigma.eServiceCenter = types.SimpleNamespace(getInstance=lambda: types.SimpleNamespace(info=lambda ref: types.SimpleNamespace(getInfoObject=lambda ref, field: {"tuner_type": "DVB-S"})))
        reference = types.SimpleNamespace(toString=lambda: "same-service")
        measured = {2: 1920, 3: 1080, 4: 1, 5: 0, 6: 1}
        info = types.SimpleNamespace(getInfo=lambda field: measured.get(field, -1))
        tracks = types.SimpleNamespace(getNumberOfTracks=lambda: 1, getCurrentTrack=lambda: 0, getTrackInfo=lambda index: types.SimpleNamespace(getDescription=lambda: "AC3", getLanguage=lambda: "ita"))
        navigation = types.ModuleType("NavigationInstance")
        navigation.instance = types.SimpleNamespace(getCurrentlyPlayingServiceReference=lambda: reference, getCurrentService=lambda: types.SimpleNamespace(info=lambda: info, audioTracks=lambda: tracks))
        with patch.dict(sys.modules, {"Components.Renderer.Label": label_module, "enigma": enigma, "NavigationInstance": navigation}):
            spec = importlib.util.spec_from_file_location("facts_columns_test", ROOT / "runtime/Components/Renderer/MetrixNEOServiceFacts.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            renderer = module.MetrixNEOServiceFacts()
            renderer.source = types.SimpleNamespace(service=reference)
            for field, text in (("video", "1080i\nH.264"), ("aspect_source", "16:9\nDVB-S"), ("audio", "AC3 ita")):
                renderer.field = field
                renderer.changed((1,))
                self.assertEqual(renderer.text, text)
            measured.clear()
            renderer.field = "video"
            renderer.changed((1,))
            self.assertEqual(renderer.text, "")
            renderer.field = "aspect_source"
            renderer.changed((1,))
            self.assertEqual(renderer.text, "DVB-S")

    def test_unplayed_channel_never_reuses_playing_decoder(self):
        label_module = types.ModuleType("Components.Renderer.Label")
        class Label:
            CHANGED_CLEAR, CHANGED_ALL = 0, 1
        label_module.Label = Label
        enigma = types.ModuleType("enigma")
        enigma.iServiceInformation = types.SimpleNamespace(sTransponderData=1)
        enigma.eServiceCenter = types.SimpleNamespace(getInstance=lambda: types.SimpleNamespace(info=lambda ref: types.SimpleNamespace(getInfoObject=lambda ref, field: {"tuner_type": "DVB-S"})))
        playing = types.SimpleNamespace(toString=lambda: "playing-channel")
        decoder = Mock()
        navigation = types.ModuleType("NavigationInstance")
        navigation.instance = types.SimpleNamespace(getCurrentlyPlayingServiceReference=lambda: playing, getCurrentService=decoder)
        with patch.dict(sys.modules, {"Components.Renderer.Label": label_module, "enigma": enigma, "NavigationInstance": navigation}):
            spec = importlib.util.spec_from_file_location("facts_under_test", ROOT / "runtime/Components/Renderer/MetrixNEOServiceFacts.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            renderer = module.MetrixNEOServiceFacts()
            renderer.source = types.SimpleNamespace(service=types.SimpleNamespace(toString=lambda: "selected-channel"))
            renderer.changed((1,))
            self.assertEqual(renderer.text, "DVB-S")
            decoder.assert_not_called()


if __name__ == "__main__":
    unittest.main()
