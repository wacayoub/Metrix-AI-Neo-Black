import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
from Components.MetrixNEO.events import upcoming_text
from Components.MetrixNEO.settings import DEFAULTS


class EventQueries(unittest.TestCase):
    def test_missing_event_or_reference_no_lookup(self):
        self.assertEqual(upcoming_text(None, None, 0), "")

    def test_two_future_events_relative_to_selection(self):
        event = types.SimpleNamespace(getBeginTime=lambda: 5000, getDuration=lambda: 1000)
        reference = types.SimpleNamespace(toString=lambda: "local-test-service")
        query = unittest.mock.Mock(return_value=[(1, 6000, 600, "الأخبار"), (2, 6600, 600, "Documentaire")])
        enigma = types.ModuleType("enigma")
        enigma.eEPGCache = types.SimpleNamespace(getInstance=lambda: types.SimpleNamespace(lookupEvent=query))
        with patch.dict(sys.modules, {"enigma": enigma}):
            self.assertTrue(upcoming_text(event, reference, 0).endswith("الأخبار"))
            self.assertTrue(upcoming_text(event, reference, 1).endswith("Documentaire"))
        self.assertEqual(query.call_args.args[0][1][2], 6000)

    def test_missing_next_is_never_current_event(self):
        event = types.SimpleNamespace(getBeginTime=lambda: 5000, getDuration=lambda: 1000)
        reference = types.SimpleNamespace(toString=lambda: "local-test-service")
        enigma = types.ModuleType("enigma")
        enigma.eEPGCache = types.SimpleNamespace(getInstance=lambda: types.SimpleNamespace(lookupEvent=lambda query: []))
        with patch.dict(sys.modules, {"enigma": enigma}):
            self.assertEqual(upcoming_text(event, reference, 0), "")
            self.assertEqual(upcoming_text(event, reference, 1), "")


class NativeSourceAdapter(unittest.TestCase):
    def setUp(self):
        converter = types.ModuleType("Components.Converter.Converter")
        class Converter:
            def __init__(self, arguments):
                self.source = None
        converter.Converter = Converter
        element = types.ModuleType("Components.Element")
        element.cached = lambda function: function
        navigation = types.ModuleType("NavigationInstance")
        self.reference = "1:0:1:123:0:0:0:0:0:0:"
        navigation.instance = types.SimpleNamespace(getCurrentlyPlayingServiceReference=lambda: types.SimpleNamespace(toString=lambda: self.reference))
        self.module_patch = patch.dict(sys.modules, {"Components.Converter.Converter": converter, "Components.Element": element, "NavigationInstance": navigation})
        self.module_patch.start()
        self.addCleanup(self.module_patch.stop)
        spec = importlib.util.spec_from_file_location("neo_adapter_under_test", ROOT / "runtime/Components/Converter/MetrixNEOInfo.py")
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.settings_patch = patch.object(self.module, "read_settings", return_value=dict(DEFAULTS))
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)

    def adapter(self, token, source):
        result = self.module.MetrixNEOInfo(token)
        result.source = source
        return result

    def test_weather_header_parts_remain_optional_and_hide_missing_cache(self):
        helper = types.ModuleType("Plugins.Extensions.MetrixNEOHelper.service")
        helper.weather_text = lambda profile: ""
        helper.weather_day = lambda profile, day: {"label": "Casablanca", "temperature": 16, "stale": False} if day == -1 else {"date": "2026-10-24", "high": 24, "low": 16, "stale": False}
        with patch.dict(sys.modules, {"Plugins.Extensions.MetrixNEOHelper.service": helper}):
            for mode, expected in (("WeatherLocation", "Casablanca"), ("WeatherTemperature", "16°C"), ("WeatherRange1", "24°/16°")):
                adapter = self.adapter(mode, None)
                adapter.settings["weather"] = False
                self.assertEqual(adapter.text, "")
                adapter.settings["weather"] = True
                self.assertEqual(adapter.text, expected)
            helper.weather_day = lambda profile, day: None
            self.assertEqual(adapter.text, "")

    def test_missing_agc_hidden_despite_valid_snr(self):
        adapter = self.adapter("AGC", types.SimpleNamespace(snr=65535, agc=None))
        self.assertFalse(adapter.boolean)
        self.assertEqual(adapter.text, "")

    def test_invalid_snr_hidden(self):
        adapter = self.adapter("SNR", types.SimpleNamespace(snr=65536))
        self.assertFalse(adapter.boolean)
        self.assertEqual(adapter.text, "")

    def test_measured_zero_visible(self):
        adapter = self.adapter("SNR", types.SimpleNamespace(snr=0))
        self.assertTrue(adapter.boolean)
        self.assertEqual(adapter.text, "SNR 0 %")

    def test_iptv_hides_frontend_even_with_stale_value(self):
        self.reference = "4097:0:1:0:0:0:0:0:0:0:"
        adapter = self.adapter("SNR", types.SimpleNamespace(snr=65535))
        self.assertFalse(adapter.boolean)
        self.assertEqual(adapter.text, "")

    def test_helper_absent_weather_safe(self):
        adapter = self.adapter("Weather", types.SimpleNamespace())
        adapter.settings["weather"] = True
        self.assertEqual(adapter.text, "")

    def test_absent_service_metrics_hidden(self):
        for token in ("Quality", "Audio", "Timeshift", "Source", "Diagnostics"):
            self.assertEqual(self.adapter(token, types.SimpleNamespace(service=None)).text, "")

    def test_technical_columns_are_connected_to_native_service_values(self):
        enigma=types.ModuleType("enigma")
        enigma.iServiceInformation=types.SimpleNamespace(sVideoWidth=0,sVideoHeight=1,sFrameRate=2,sAspect=3)
        service=types.SimpleNamespace(info=lambda:types.SimpleNamespace(getInfo=lambda key:(3840,2160,59940,1)[key]))
        with patch.dict(sys.modules,{"enigma":enigma}):
            source=types.SimpleNamespace(service=service)
            for token,value in (("TechnicalResolution","3840 × 2160"),("TechnicalFrameRate","59.94 fps"),("TechnicalAspect","16:9"),("TechnicalAudio",""),("TechnicalTuning","")):
                self.assertEqual(self.adapter(token,source).text,value)

    def test_explicit_smart_episode_only(self):
        event = types.SimpleNamespace(getEventName=lambda: "Film S03E11", getExtendedDescription=lambda: "")
        self.assertEqual(self.adapter("Smart", types.SimpleNamespace(event=event)).text, "S03E11")

    def test_match_separator_follows_automatic_pair_independently_of_posters(self):
        helper=types.ModuleType("Plugins.Extensions.MetrixNEOHelper.service")
        helper.watch_clubs=Mock()
        helper.settings_for=lambda profile,fallback:dict(DEFAULTS,club_logos=True,posters=False)
        badges={}
        helper.club_path=lambda event,profile,role:badges.get(role)
        with patch.dict(sys.modules,{helper.__name__:helper}):
            adapter=self.adapter("Match",types.SimpleNamespace(event=object()))
            self.assertEqual(adapter.text,"")
            badges.update(home="home.png",away="away.png")
            self.assertEqual(adapter.text,"VS")
            helper.watch_clubs.assert_called_with("MetrixNEO",adapter)
            helper.settings_for=lambda profile,fallback:DEFAULTS
            self.assertEqual(adapter.text,"")

    def test_inactive_timeshift_hidden(self):
        service = types.SimpleNamespace(timeshift=lambda: types.SimpleNamespace(isTimeshiftActive=lambda: False))
        self.assertEqual(self.adapter("Timeshift", types.SimpleNamespace(service=service)).text, "")

    def test_record_label_uses_real_record_state_boolean(self):
        for active,expected in ((False,""),(True,"● REC")):
            self.assertEqual(self.adapter("Record",types.SimpleNamespace(boolean=active)).text,expected)

    def test_infobar_weather_fields_follow_enable_flag_and_cached_values(self):
        from datetime import date
        helper=types.ModuleType("Plugins.Extensions.MetrixNEOHelper.service")
        helper.weather_text=lambda profile:"cached weather"
        helper.weather_day=lambda profile,day: {"temperature":16,"label":"Casablanca","stale":False} if day==-1 else {"date":date.today().isoformat(),"high":18,"low":12,"stale":False}
        with patch.dict(sys.modules,{helper.__name__:helper}):
            for mode,expected in (("WeatherTemperatureCompact","16°"),("WeatherTodayLabel","Aujourd’hui"),("WeatherTodayRange","18°   12°"),("WeatherHigh4","18°"),("WeatherLow4","12°")):
                adapter=self.adapter(mode,None)
                adapter.settings["weather"]=False
                self.assertEqual(adapter.text,"")
                adapter.settings["weather"]=True
                self.assertEqual(adapter.text,expected)

    def test_signal_separate_labels_hide_for_iptv_and_unknown(self):
        for mode in ("SNRLabel","SNRPercent","AGCLabel","AGCPercent"):
            adapter=self.adapter(mode,types.SimpleNamespace(snr=65535,agc=32768))
            self.assertTrue(adapter.boolean)
            self.assertTrue(adapter.text)
            self.reference="4097:0:1:0:0:0:0:0:0:0:"
            self.assertEqual(adapter.text,"")
            self.assertFalse(adapter.boolean)
            self.reference="1:0:1:123:0:0:0:0:0:0:"

    def test_next_summary_requires_real_event_and_valid_duration(self):
        self.assertEqual(self.adapter("NextSummary",types.SimpleNamespace(event=None)).text,"")
        event=types.SimpleNamespace(getEventName=lambda:"Titre suivant",getBeginTime=lambda:10000,getDuration=lambda:1200)
        self.assertIn("Titre suivant",self.adapter("NextSummary",types.SimpleNamespace(event=event)).text)
        event.getDuration=lambda:0
        self.assertEqual(self.adapter("NextSummary",types.SimpleNamespace(event=event)).text,"")


if __name__ == "__main__":
    unittest.main()
