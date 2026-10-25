"""Exercise real preferences callbacks with local settings and native UI doubles."""
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
from Components.MetrixNEO.settings import DEFAULTS, Settings
from Components.MetrixNEO.preferences import KEY_LABELS, categories_for


class Editor:
    def __init__(self, default=None, **kwargs):
        self.value = default


class Text(Editor):
    pass


class Label:
    instance = None

    def __init__(self, text=""):
        self.text = text

    def setText(self, text):
        self.text = text


class Actions:
    def __init__(self, contexts=(), actions=None, priority=0):
        self.contexts, self.actions, self.enabled = contexts, actions or {}, True

    def setEnabled(self, value):
        self.enabled = value


class Listing:
    def __init__(self, rows):
        self.list, self.index, self.onSelectionChanged = rows, 0, []

    def setList(self, rows):
        self.list, self.index = rows, 0

    def getCurrent(self):
        return self.list[self.index] if self.list else None

    def setCurrentIndex(self, index):
        self.index = index

    def enableAutoNavigation(self, value):
        self.auto_navigation = value


class Screen(dict):
    def __init__(self, session):
        super().__init__()
        self.session, self.onLayoutFinish, self.closed = session, [], False

    def setTitle(self, title):
        self.title = title

    def close(self):
        self.closed = True


class ConfigListScreen:
    def __init__(self, entries, **kwargs):
        self["config"] = Listing(entries)
        self["menuConfigActions"] = Actions()


class PreferencesActions(unittest.TestCase):
    def setUp(self):
        directory = ROOT / "build/test-tmp"
        directory.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=directory)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        definitions = {
            "Components.ActionMap": {"ActionMap": Actions},
            "Components.ConfigList": {"ConfigListScreen": ConfigListScreen},
            "Components.config": {"ConfigInteger": Editor, "ConfigText": Text, "ConfigPassword": Text, "ConfigYesNo": Editor, "NoSave": lambda editor: editor, "getConfigListEntry": lambda *args: args},
            "Components.Label": {"Label": Label},
            "Components.MenuList": {"MenuList": Listing},
            "Components.Sources.StaticText": {"StaticText": Label},
            "Screens.Screen": {"Screen": Screen},
            "Screens.MessageBox": {"MessageBox": types.SimpleNamespace(TYPE_ERROR=1, TYPE_INFO=2)},
            "Screens.ChoiceBox": {"ChoiceBox": object},
        }
        modules = {}
        for name, members in definitions.items():
            modules[name] = types.ModuleType(name)
            modules[name].__dict__.update(members)
        context = patch.dict(sys.modules, modules)
        context.start()
        self.addCleanup(context.stop)
        spec = importlib.util.spec_from_file_location("neo_preferences_under_test", ROOT / "runtime/Components/MetrixNEO/ui.py")
        self.ui = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.ui)
        self.ui.Settings = lambda ignored, profile: Settings(self.root, profile)
        self.session = types.SimpleNamespace(open=Mock(), openWithCallback=Mock())

    def screen(self, profile="MetrixNEOAdvanced"):
        return self.ui.NeoSettings(self.session, profile)

    def test_keys_match_actions_and_opening_writes_nothing(self):
        screen = self.screen()
        for key, label in KEY_LABELS.items():
            self.assertEqual(screen[key].text, label)
        bindings = screen["neoActions"].actions
        for key, method in (("red", "cancel"), ("cancel", "cancel"), ("green", "save"), ("yellow", "defaults"), ("blue", "refresh"), ("menu", "choose_category")):
            self.assertEqual(bindings[key], getattr(screen, method))
        self.assertFalse(screen["menuConfigActions"].enabled)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_categories_filter_real_options_and_preserve_edits(self):
        screen = self.screen()
        screen.category_selected(("Météo", "weather"))
        screen.fields["latitude"].value = "33.57"
        screen.category_selected(("Images EPG", "images"))
        screen.fields["posters"].value = True
        screen.category_selected(("Météo", "weather"))
        self.assertEqual(screen.fields["latitude"].value, "33.57")
        self.assertTrue(screen.fields["posters"].value)
        self.assertEqual(len(screen["config"].list), 5)
        screen.choose_category()
        kwargs = self.session.openWithCallback.call_args.kwargs
        self.assertEqual(kwargs["selection"], 1)
        self.assertEqual(kwargs["choiceList"][1], ("Météo", "weather"))
        screen.category_selected(None)
        self.assertEqual(screen.category, "weather")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_classic_excludes_advanced_only_controls(self):
        screen = self.screen("MetrixNEO")
        self.assertEqual(len(categories_for("MetrixNEO")), 4)
        self.assertFalse({"compact", "smart_epg", "diagnostics"} & screen.fields.keys())
        screen.category_selected(("Diagnostics", "diagnostics"))
        self.assertEqual(screen.category, "presentation")

    def test_yellow_resets_all_categories_in_memory_then_cancel_keeps_saved(self):
        saved = Settings(self.root, "MetrixNEOAdvanced")
        saved.pending.update(weather=True, latitude=33.57, cache_mb=64)
        saved.save()
        before = saved.path.read_bytes()
        screen = self.screen()
        screen.fields["posters"].value = True
        screen.category_selected(("Cache", "cache"))
        screen["neoActions"].actions["yellow"]()
        self.assertEqual(screen.fields["cache_mb"].value, 32)
        self.assertEqual(screen.fields["latitude"].value, "")
        self.assertFalse(screen.fields["weather"].value)
        self.assertEqual(screen["config"].list[0][1].value, 32)
        screen["neoActions"].actions["red"]()
        self.assertTrue(screen.closed)
        self.assertEqual(saved.path.read_bytes(), before)
        self.assertEqual([p.name for p in self.root.iterdir()], ["MetrixNEOAdvanced.json"])

    def test_green_saves_edits_across_categories_only_to_current_profile(self):
        other = Settings(self.root, "MetrixNEO")
        other.save()
        untouched = other.path.read_bytes()
        screen = self.screen()
        screen.category_selected(("Météo", "weather"))
        screen.fields["weather"].value = True
        screen.fields["latitude"].value = "33.57"
        screen.fields["longitude"].value = "-7.59"
        screen.fields["weather_label"].value = "Casablanca"
        screen.category_selected(("Cache", "cache"))
        screen.fields["cache_mb"].value = 64
        screen["neoActions"].actions["green"]()
        self.assertTrue(screen.closed)
        result = json.loads((self.root / "MetrixNEOAdvanced.json").read_text())
        self.assertEqual((result["latitude"], result["longitude"], result["cache_mb"]), (33.57, -7.59, 64))
        self.assertFalse(result["network_consent"])
        self.assertEqual(other.path.read_bytes(), untouched)

    def test_automatic_logos_have_independent_saved_controls(self):
        screen=self.screen("MetrixNEO")
        screen.category_selected(("Images EPG","images"))
        self.assertEqual(len(screen["config"].list),4)
        screen.fields["club_logos"].value=True
        screen.fields["club_network_consent"].value=True
        screen.fields["sports_api_key"].value="123"
        screen.save()
        result=json.loads((self.root/"MetrixNEO.json").read_text())
        self.assertTrue(result["club_logos"])
        self.assertTrue(result["club_network_consent"])
        self.assertFalse(result["posters"])
        self.assertFalse(result["network_consent"])

    def test_invalid_coordinates_do_not_close_or_change_saved_file(self):
        saved = Settings(self.root, "MetrixNEOAdvanced")
        saved.save()
        before = saved.path.read_bytes()
        screen = self.screen()
        for value in ("outside", "91", "nan"):
            screen.fields["latitude"].value = value
            screen.save()
            self.assertFalse(screen.closed)
            self.assertEqual(saved.path.read_bytes(), before)
        self.assertEqual(self.session.open.call_count, 3)
        self.assertFalse(saved.path.with_suffix(".json.bak").exists())

    def test_blue_refreshes_current_saved_profile_without_saving_edits(self):
        helper = types.ModuleType("Plugins.Extensions.MetrixNEOHelper.service")
        helper.refresh = Mock()
        screen = self.screen()
        screen.fields["weather"].value = True
        with patch.dict(sys.modules, {helper.__name__: helper}):
            screen["neoActions"].actions["blue"]()
        helper.refresh.assert_called_once_with("MetrixNEOAdvanced")
        self.assertTrue(screen.fields["weather"].value)
        self.assertFalse(screen.closed)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_blue_without_helper_is_explained_and_keeps_pending_values(self):
        screen = self.screen()
        screen.fields["cache_mb"].value = 48
        with patch.dict(sys.modules, {"Plugins.Extensions.MetrixNEOHelper.service": None}):
            screen.refresh()
        self.assertIn("absent", self.session.open.call_args.args[1])
        self.assertEqual(screen.fields["cache_mb"].value, 48)
        self.assertEqual(list(self.root.iterdir()), [])
