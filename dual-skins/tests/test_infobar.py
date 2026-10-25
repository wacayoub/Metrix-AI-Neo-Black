"""Reference geometry, measured badges and exact-event club matching."""
import json
import sys
import tempfile
import types
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/"runtime"), str(ROOT/"plugin")]
from Components.MetrixNEO.infobar_facts import read_facts
from MetrixNEOHelper.providers import local_catalog
from MetrixNEOHelper import service as helper


class InfobarGeometry(unittest.TestCase):
    def test_technical_fields_have_fixed_non_overlapping_columns_and_one_baseline(self):
        for profile in ("MetrixNEO", "MetrixNEOAdvanced"):
            screen=ET.parse(ROOT/"skins"/profile/"skin.xml").find("screen[@name='InfoBar']")
            fields=[]
            for node in screen.findall("widget"):
                converter=node.find("convert[@type='MetrixNEOInfo']")
                if converter is not None and converter.text.startswith("Technical"):
                    fields.append(node)
            self.assertEqual(len(fields),7 if profile.endswith("Advanced") else 6)
            baselines=set()
            previous_end=0
            for node in fields:
                x,y=map(int,node.get("position").split(','))
                width,height=map(int,node.get("size").split(','))
                self.assertGreater(x,previous_end)
                previous_end=x+width
                baselines.add(y+height/2)
                self.assertEqual(node.get("valign"),"center")
                self.assertEqual(node.get("noWrap"),"1")
            self.assertEqual(len(baselines),1)
            self.assertLessEqual(previous_end,1510 if profile.endswith("Advanced") else 1416)
            self.assertFalse(any(n.text.startswith(("VideoDetails,","TunerDetails,")) for n in screen.findall("widget/convert[@type='MetrixNEOInfo']")))

    def test_advanced_signal_labels_values_and_bars_never_overlap(self):
        screen=ET.parse(ROOT/"skins/MetrixNEOAdvanced/skin.xml").find("screen[@name='InfoBar']")
        spans=[]
        for node in screen.findall("widget[@source='session.FrontendStatus']"):
            x=int(node.get('position').split(',')[0]);w=int(node.get('size').split(',')[0])
            spans.append((x,x+w))
        spans.sort()
        self.assertEqual(len(spans),6)
        for left,right in zip(spans,spans[1:]):self.assertLessEqual(left[1],right[0])

    def test_both_profiles_follow_248_pixel_reference_band_to_bottom(self):
        for profile in ("MetrixNEO", "MetrixNEOAdvanced"):
            screen = ET.parse(ROOT/"skins"/profile/"skin.xml").find("screen[@name='InfoBar']")
            self.assertIsNotNone(screen.find("eLabel[@position='0,832'][@size='1920,248']"))
            self.assertIsNotNone(screen.find("ePixmap[@pixmap='%s/assets/infobar-weather.png']"%profile))
            clock = screen.find("ePixmap[@pixmap='%s/assets/infobar-clock.png']"%profile)
            self.assertGreater(int(clock.get("position").split(',')[0]),1500)
            self.assertEqual(len(screen.findall("widget[@neoRole]")),2)
            self.assertEqual(screen.find("widget[@render='MetrixNEOPicon']").get("position"),"33,866" if profile.endswith("Advanced") else "158,861")
            self.assertFalse(any(node.get("render") in ("Pig","Video") for node in screen))
            for bar in screen.findall("widget[@source='session.FrontendStatus'][@render='Progress']"):
                self.assertEqual(bar.get("orientation"),"orRightToLeft")

    def test_no_frozen_live_ai_atmos_or_timeshift_offsets(self):
        for profile in ("MetrixNEO", "MetrixNEOAdvanced"):
            screen = ET.parse(ROOT/"skins"/profile/"skin.xml").find("screen[@name='InfoBar']")
            text = ET.tostring(screen,encoding="unicode")
            for literal in ("Real Madrid", "Barcelona", "beIN", "+116", "Atmos", "Smart Match", "LIVE", "−30s", "+30s"):
                self.assertNotIn(literal,text)


class MeasuredFacts(unittest.TestCase):
    def keys_and_service(self, values=None, audio="AC3", gamma=0):
        names=("sVideoWidth","sVideoHeight","sFrameRate","sGamma","sVideoType","sIsCrypted","sAspect")
        keys=types.SimpleNamespace(**dict(zip(names,range(len(names)))))
        data=dict(zip(range(len(names)),(3840,2160,50000,gamma,7,1,1)))
        if values is not None:data.update(values)
        track=types.SimpleNamespace(getDescription=lambda:audio,getLanguage=lambda:"fra")
        tracks=types.SimpleNamespace(getNumberOfTracks=lambda:1,getCurrentTrack=lambda:0,getTrackInfo=lambda index:track)
        frontend=types.SimpleNamespace(getAll=lambda real:{"tuner_type":"DVB-S2","orbital_position":3530,"frequency":11054000,"symbol_rate":30000000,"polarization":0})
        service=types.SimpleNamespace(info=lambda:types.SimpleNamespace(getInfo=lambda key:data[key]), audioTracks=lambda:tracks,frontendInfo=lambda:frontend)
        return keys,service

    def test_uhd_does_not_imply_hdr_or_atmos(self):
        keys,service=self.keys_and_service()
        result=read_facts(service,keys)
        self.assertEqual(result["BadgeResolution"],"4K")
        self.assertEqual(result["BadgeHDR"],"")
        self.assertEqual(result["BadgeAudio"],"AC3")
        self.assertNotIn("Atmos",str(result))
        self.assertEqual(result["SourceShort"],"SAT")
        self.assertIn("7°W",result["TunerDetails"])

    def test_hdr_and_ddplus_require_exposed_track_and_gamma(self):
        keys,service=self.keys_and_service(audio="E-AC-3",gamma=3)
        result=read_facts(service,keys)
        self.assertEqual((result["BadgeHDR"],result["BadgeAudio"]),("HLG","DD+"))

    def test_atmos_requires_explicit_selected_audio_description(self):
        keys,service=self.keys_and_service(audio="Dolby Atmos",gamma=0)
        self.assertEqual(read_facts(service,keys)["BadgeAudio"],"ATMOS")
        keys,service=self.keys_and_service(audio="E-AC-3",gamma=2)
        self.assertEqual(read_facts(service,keys)["BadgeAudio"],"DD+")

    def test_unknown_video_values_hide_badges(self):
        keys,service=self.keys_and_service(values={0:-1,1:-1,2:-1,3:-1,4:-1,5:-1,6:-1},audio="unknown")
        result=read_facts(service,keys)
        for key in ("BadgeResolution","BadgeHDR","BadgeCodec","BadgeCA","BadgeAudio"):
            self.assertFalse(result.get(key))
        self.assertNotIn("fps",result["VideoDetails"])

    def test_absent_service_is_empty(self):
        self.assertEqual(read_facts(None,object()),{})

    def test_compact_columns_return_independent_measured_fields(self):
        keys,service=self.keys_and_service(values={2:59940},audio="E-AC-3 5.1 surround selected track")
        result=read_facts(service,keys)
        expected=dict(TechnicalResolution="3840 × 2160",TechnicalFrameRate="59.94 fps",TechnicalAspect="16:9",TechnicalAudio="DD+",TechnicalLanguage="FRA",TechnicalOrbital="7°W",TechnicalTuning="11054 H 30000")
        for key,value in expected.items():self.assertEqual(result[key],value)
        self.assertIn("selected track",result["VideoDetails"])

    def test_missing_audio_does_not_hide_resolution_or_satellite(self):
        keys,service=self.keys_and_service()
        def unavailable():raise RuntimeError("No audio decoder")
        service.audioTracks=unavailable
        result=read_facts(service,keys)
        self.assertEqual(result["TechnicalResolution"],"3840 × 2160")
        self.assertEqual(result["SourceShort"],"SAT")
        self.assertEqual(result["TechnicalTuning"],"11054 H 30000")
        self.assertEqual(result["TechnicalAudio"],"")

    def test_unknown_fields_leave_their_columns_empty(self):
        keys,service=self.keys_and_service(values={0:-1,1:-1,2:-1,6:-1},audio="unknown codec description")
        service.frontendInfo=lambda:None
        result=read_facts(service,keys)
        for mode in ("Resolution","FrameRate","Aspect","Audio","Orbital","Tuning"):
            self.assertFalse(result.get("Technical"+mode))

    def test_native_widescreen_aspect_codes_use_the_same_column(self):
        keys,service=self.keys_and_service(values={6:3})
        self.assertEqual(read_facts(service,keys)["TechnicalAspect"],"16:9")

    def test_frequency_survives_missing_symbol_rate(self):
        keys,service=self.keys_and_service()
        service.frontendInfo=lambda:types.SimpleNamespace(getAll=lambda real:{"tuner_type":"DVB-S2","frequency":11054000,"polarization":1})
        self.assertEqual(read_facts(service,keys)["TechnicalTuning"],"11054 V")


class CuratedClubs(unittest.TestCase):
    def setUp(self):
        path=ROOT/"build/test-tmp";path.mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=path);self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        # Provider validates signatures; decoder validates actual pixel input later.
        (self.root/"club.png").write_bytes(b'\x89PNG\r\n\x1a\n')

    def test_roles_are_separate_and_require_license_and_source(self):
        row=dict(title="Match",start=100,license="User licensed",source="Local",image="club.png")
        (self.root/"metadata.json").write_text(json.dumps([dict(row,role="home"),dict(row,role="away"),dict(row,role="away",license="")]))
        self.assertEqual(local_catalog(self.root),{})
        self.assertEqual(len(local_catalog(self.root,"home")),1)
        self.assertEqual(len(local_catalog(self.root,"away")),1)
        self.assertEqual(local_catalog(self.root,"unknown"),{})

    def test_both_sides_of_exact_event_required(self):
        profile="MetrixNEOAdvanced"
        previous=helper._state.get(profile)
        try:
            event=types.SimpleNamespace(getEventName=lambda:"Match",getBeginTime=lambda:100)
            helper._state[profile]={"clubs":{"home":{("Match",100):"home.png"},"away":{("Other",100):"away.png"}}}
            self.assertIsNone(helper.club_path(event,profile,"home"))
            helper._state[profile]["clubs"]["away"][("Match",100)]="away.png"
            self.assertEqual(helper.club_path(event,profile,"home"),"home.png")
            self.assertEqual(helper.club_path(event,profile,"away"),"away.png")
            self.assertIsNone(helper.club_path(event,profile,"invalid"))
        finally:
            if previous is None:helper._state.pop(profile,None)
            else:helper._state[profile]=previous
