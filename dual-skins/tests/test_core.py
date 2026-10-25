import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "runtime"), str(ROOT / "plugin")]

from Components.MetrixNEO.model import clean_text, diagnostics, extract_metadata, fit_rect, is_stream, next_events, signal_percent
from Components.MetrixNEO.settings import DEFAULTS, Settings, validate
from MetrixNEOHelper.cache import Cache
from MetrixNEOHelper.providers import fetch_weather, local_catalog


class DisplayRules(unittest.TestCase):
    def test_raw_signal_bounds(self):
        self.assertEqual(signal_percent(0), 0)
        self.assertEqual(signal_percent(65535), 100)
        self.assertEqual(signal_percent(32768), 50)

    def test_invalid_signal_is_unknown(self):
        for value in (None, -1, 65536, float("nan"), "89", True):
            self.assertIsNone(signal_percent(value))

    def test_no_agc_inferred_from_snr(self):
        self.assertIsNone(signal_percent(None))

    def test_iptv_reference_types(self):
        for ref in ("4097:0:1:", "5001:0:1:", "1:0:1:0:0:0:0:0:0:0:https%3a//example.invalid/test"):
            self.assertTrue(is_stream(ref))
        self.assertFalse(is_stream("1:0:1:123:456:789:0:0:0:0:"))

    def test_picon_ratio_wide(self):
        x, y, w, h = fit_rect(400, 100, 180, 100)
        self.assertEqual((x, y, w, h), (0, 27, 180, 45))

    def test_picon_ratio_tall(self):
        x, y, w, h = fit_rect(100, 400, 180, 100)
        self.assertEqual((x, y, w, h), (77, 0, 25, 100))

    def test_empty_picon_bounds(self):
        self.assertEqual(fit_rect(0, 100, 200, 100), (0, 0, 0, 0))

    def test_unicode_preserved(self):
        text = "وثائقي – Épisode ٢ · Programme"
        self.assertEqual(clean_text(text), text)

    def test_control_sequences_removed(self):
        self.assertEqual(clean_text("EPG\x00titre\nعربي"), "EPGtitre\nعربي")

    def test_explicit_episode_multilingual(self):
        for text in ("Serie S02E04", "Saison 2 épisode 4", "الموسم ٢ الحلقة ٤"):
            result = extract_metadata(text)
            self.assertEqual((result["season"], result["episode"], result["confidence"]), (2, 4, 1.0))

    def test_no_guessing_teams_genres_or_episodes(self):
        for text in ("Finale A vs B", "Épisode spécial", "2-4", "Match ce soir"):
            result = extract_metadata(text)
            self.assertEqual(result["confidence"], 0.0)
            self.assertIsNone(result["genre"])

    def test_next_two_valid_and_ordered(self):
        rows = [dict(id=3, start=300, duration=100, title="Trois"), dict(id=1, start=100, duration=100, title="Un"), dict(id=2, start=200, duration=100, title="Deux"), dict(id=0, start=250, duration=0, title="Invalide")]
        self.assertEqual([x["title"] for x in next_events(rows, 200)], ["Deux", "Trois"])

    def test_missing_next_stays_empty(self):
        self.assertEqual(next_events([], 0), [])
        self.assertEqual(next_events([dict(start=None, duration=30, title="Absent")], 0), [])

    def test_next_deduplication(self):
        row = dict(id=1, start=200, duration=50, title="Titre")
        self.assertEqual(next_events([row, row], 100), [row])

    def test_diagnostics_unknown_is_not_an_error(self):
        self.assertEqual(diagnostics(), [])

    def test_diagnostics_iptv_no_signal_warning(self):
        self.assertEqual(diagnostics(stream=True, signal=0), [])

    def test_diagnostics_real_states(self):
        self.assertEqual(diagnostics(audio_tracks=0, epg=False, recording=True, timeshift=True), ["Aucune piste audio exposée", "EPG indisponible", "REC", "Timeshift actif"])


class SettingsTransactions(unittest.TestCase):
    def setUp(self):
        directory = ROOT / "build" / "test-tmp"
        directory.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=directory)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_constructor_and_cancel_write_nothing(self):
        settings = Settings(self.root / "missing", "MetrixNEO")
        settings.pending["weather"] = True
        settings.cancel()
        self.assertFalse(settings.pending["weather"])
        self.assertFalse((self.root / "missing").exists())

    def test_confirm_writes_only_profile(self):
        settings = Settings(self.root, "MetrixNEO")
        settings.pending["weather"] = True
        settings.save()
        self.assertEqual([p.name for p in self.root.iterdir()], ["MetrixNEO.json"])
        self.assertTrue(Settings(self.root, "MetrixNEO").saved["weather"])

    def test_independent_skins(self):
        settings = Settings(self.root, "MetrixNEO")
        settings.pending["compact"] = True
        settings.save()
        self.assertFalse(Settings(self.root, "MetrixNEOAdvanced").saved["compact"])

    def test_profile_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            Settings(self.root, "../settings")

    def test_backup_and_third_party_untouched(self):
        sentinel = self.root / "third-party-settings"
        sentinel.write_text("unchanged")
        settings = Settings(self.root, "MetrixNEO")
        settings.save()
        previous = settings.path.read_bytes()
        settings.pending["posters"] = True
        settings.save()
        self.assertEqual(settings.path.with_suffix(".json.bak").read_bytes(), previous)
        self.assertEqual(sentinel.read_text(), "unchanged")

    def test_invalid_save_preserves_previous(self):
        settings = Settings(self.root, "MetrixNEO")
        settings.save()
        previous = settings.path.read_bytes()
        settings.pending["latitude"] = 1000
        with self.assertRaises(ValueError):
            settings.save()
        self.assertEqual(settings.path.read_bytes(), previous)

    def test_unrecognised_setting_rejected(self):
        with self.assertRaises(ValueError):
            validate({"active_skin": "other"})

    def test_network_opt_in_default(self):
        self.assertFalse(DEFAULTS["network_consent"])
        self.assertFalse(DEFAULTS["weather"])


class CacheAndProviders(unittest.TestCase):
    def setUp(self):
        directory = ROOT / "build" / "test-tmp"
        directory.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=directory)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_cache_constructor_write_free(self):
        Cache(self.root / "missing")
        self.assertFalse((self.root / "missing").exists())

    def test_ttl_and_stale(self):
        now = [100]
        cache = Cache(self.root, clock=lambda: now[0])
        cache.put("weather", {"ok": True}, 10)
        self.assertEqual(cache.get("weather"), {"ok": True})
        now[0] = 111
        self.assertIsNone(cache.get("weather"))
        self.assertEqual(cache.get("weather", stale=True), {"ok": True})

    def test_evict_only_owned_files(self):
        sentinel = self.root / "other.json"
        sentinel.write_text("preserve")
        cache = Cache(self.root, max_bytes=180)
        for index in range(5):
            cache.put(str(index), "x" * 65, 100)
        self.assertEqual(sentinel.read_text(), "preserve")
        self.assertLessEqual(sum(p.stat().st_size for p in self.root.glob("neo-*.json")), 180)

    def test_large_cache_item_rejected(self):
        with self.assertRaises(ValueError):
            Cache(self.root, max_bytes=20).put("big", "x" * 200, 100)

    def test_corrupt_cache_falls_back(self):
        cache = Cache(self.root)
        cache._path("key").write_text("broken")
        self.assertIsNone(cache.get("key"))

    def test_network_requires_coordinates_and_consent(self):
        with patch("MetrixNEOHelper.providers.urlopen") as network:
            self.assertIsNone(fetch_weather(DEFAULTS))
            self.assertIsNone(fetch_weather(dict(DEFAULTS, weather=True, latitude=33.5, longitude=-7.6)))
            self.assertIsNone(fetch_weather(dict(DEFAULTS, weather=True, network_consent=True)))
            network.assert_not_called()

    def test_weather_bounded_timeout_and_timezone(self):
        response = types.SimpleNamespace(geturl=lambda: "https://api.open-meteo.com/v1/forecast", read=lambda max_bytes: json.dumps({"daily": {"time": ["2026-10-25", "2026-10-26", "2026-10-27"], "weather_code": [0, 3, 61], "temperature_2m_min": [16, 17, 18], "temperature_2m_max": [24, 23, 25]}}).encode())
        manager = unittest.mock.MagicMock()
        manager.__enter__.return_value = response
        with patch("MetrixNEOHelper.providers.urlopen", return_value=manager) as network:
            result = fetch_weather(dict(DEFAULTS, weather=True, network_consent=True, latitude=33.5, longitude=-7.6))
            self.assertEqual(len(result["days"]), 3)
            self.assertEqual(network.call_args.kwargs["timeout"], 5)
            self.assertIn("Africa%2FCasablanca", network.call_args.args[0].full_url)

    def test_local_artwork_exact_identity_and_licence(self):
        (self.root / "poster.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        rows = [dict(title="Film", start=100, image="poster.png", license="CC0", source="own"), dict(title="Unknown", start=100, image="poster.png")]
        (self.root / "metadata.json").write_text(json.dumps(rows))
        result = local_catalog(self.root)
        self.assertIn(("Film", 100), result)
        self.assertNotIn(("Unknown", 100), result)
        self.assertNotIn(("Film", 101), result)

    def test_local_catalog_rejects_escape(self):
        catalog = self.root / "catalog"
        catalog.mkdir()
        (self.root / "outside.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        (catalog / "metadata.json").write_text(json.dumps([dict(title="Film", start=100, image="../outside.png", license="CC0", source="own")]))
        self.assertEqual(local_catalog(catalog), {})


class NativeMenuIntegration(unittest.TestCase):
    def fake_screen(self):
        callback = unittest.mock.Mock()
        root = __import__("xml.etree.ElementTree", fromlist=["ElementTree"]).fromstring("<menuxml><menu key='mainmenu'><menu key='setup'/><menu key='information'/><menu key='timermenu'/><menu key='shutdown'/><item key='plugin_selection'/></menu><menu key='network'/><menu key='software_manager'/></menuxml>")
        class Screen(dict):
            menuID = "mainmenu"
            parentMenu = root.find("menu")
            def __init__(self):
                super().__init__(description=types.SimpleNamespace(setText=lambda text: None))
                self.menuList = [(key, callback, key, 10, "native", "icon") for key in ("setup", "information", "timermenu", "shutdown", "plugin_selection")]
            def setMenuList(self, rows):
                self.visible_rows = rows
            def addMenu(self, node):
                return (node.get("key"), callback, node.get("key"), 10, "native", "icon")
            def addItem(self, node):
                return self.addMenu(node)
            def getMenuEntryImage(self, key, lastKey):
                return "icon"
        return Screen(), root, callback

    def bind(self, profile, screen, root):
        from Components.MetrixNEO.bootstrap import bind_menu
        menu = types.ModuleType("Screens.Menu")
        menu.menuDom = lambda: root
        actions = types.ModuleType("Components.ActionMap")
        actions.ActionMap = lambda contexts, mapping, priority: (contexts, mapping, priority)
        with patch.dict(sys.modules, {"Screens.Menu": menu, "Components.ActionMap": actions}), patch("Components.MetrixNEO.bootstrap.find_spec", return_value=None):
            bind_menu(screen, profile)

    def test_neo_exact_five_callbacks_not_executed(self):
        screen, root, callback = self.fake_screen()
        self.bind("MetrixNEO", screen, root)
        self.assertEqual(len(screen.visible_rows), 5)
        self.assertEqual([row[2] for row in screen.visible_rows], ["plugin_selection", "setup", "timermenu", "shutdown", "information"])
        callback.assert_not_called()

    def test_advanced_exact_twelve_and_absent_files_explicit(self):
        screen, root, callback = self.fake_screen()
        self.bind("MetrixNEOAdvanced", screen, root)
        self.assertEqual(len(screen.visible_rows), 12)
        self.assertIn("indisponible", screen.visible_rows[4][0])
        self.assertEqual(screen.visible_rows[9][2], "neo_settings")
        callback.assert_not_called()

    def test_full_native_menu_access_remains(self):
        screen, root, callback = self.fake_screen()
        self.bind("MetrixNEO", screen, root)
        self.assertIn("menu", screen["neoMenuActions"][1])
        self.assertEqual(screen["neoMenuActions"][2], -10)

    def test_hidden_main_entry_not_reintroduced(self):
        screen, root, callback = self.fake_screen()
        screen.menuList = [row for row in screen.menuList if row[2] != "plugin_selection"]
        self.bind("MetrixNEO", screen, root)
        self.assertIn("indisponible", screen.visible_rows[0][0])

    def test_does_not_replace_other_menus(self):
        screen, root, callback = self.fake_screen()
        screen.menuID = "setup"
        old = screen.menuList
        self.bind("MetrixNEO", screen, root)
        self.assertIs(screen.menuList, old)


if __name__ == "__main__":
    unittest.main()
