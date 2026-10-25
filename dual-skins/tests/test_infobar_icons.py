"""State transitions, truthful audio/shift fields and actual production assets."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"runtime"))
from Components.MetrixNEO.infobar_icons import ICONS,icon_name
from Components.MetrixNEO.infobar_facts import timeshift_status


class IconStates(unittest.TestCase):
    def test_unknown_and_empty_data_never_choose_a_badge(self):
        for kind in ICONS:
            self.assertIsNone(icon_name(kind,""))
            self.assertIsNone(icon_name(kind,"../../other-file"))
        self.assertIsNone(icon_name("AI","4K"))
        self.assertIsNone(icon_name("hdr","4K"))
        self.assertEqual(icon_name("audio","ATMOS"),"audio-atmos")

    def test_all_referenced_icons_exist_and_have_alpha(self):
        from PIL import Image
        names={value for group in ICONS.values() for value in group.values()}|{"record","timeshift"}
        for profile in ("MetrixNEO","MetrixNEOAdvanced"):
            for name in names:
                with Image.open(ROOT/"skins"/profile/"assets"/("infobar-icon-"+name+".png")) as asset:
                    self.assertEqual(asset.mode,"RGBA")
                    self.assertGreater(asset.width,0)
                    self.assertLess(asset.getchannel('A').getextrema()[0],255)

    def test_native_renderer_replaces_and_hides_old_state(self):
        renderer_mod=types.ModuleType('Components.Renderer.Renderer')
        class Renderer:
            CHANGED_CLEAR,CHANGED_ALL=0,1
        renderer_mod.Renderer=Renderer
        enigma=types.ModuleType('enigma');enigma.ePixmap=object
        directories=types.ModuleType('Tools.Directories');directories.SCOPE_SKINS=0;directories.resolveFilename=lambda scope,name:name
        loader=types.ModuleType('Tools.LoadPixmap');loader.LoadPixmap=Mock(side_effect=lambda name,cached:None if 'hdr-hlg' in name else 'pixmap:'+name)
        with patch.dict(sys.modules,{'Components.Renderer.Renderer':renderer_mod,'enigma':enigma,'Tools.Directories':directories,'Tools.LoadPixmap':loader}):
            spec=importlib.util.spec_from_file_location('neo_icon_test',ROOT/'runtime/Components/Renderer/MetrixNEOInfobarIcon.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            icon=module.MetrixNEOInfobarIcon();icon.instance=Mock();icon.kind='hdr';icon.source=types.SimpleNamespace(text='HDR')
            icon.changed((1,));icon.changed((1,))
            self.assertEqual(loader.LoadPixmap.call_count,1)
            icon.source.text='HLG';icon.changed((1,))
            icon.instance.hide.assert_called();self.assertIsNone(icon.last_name)
            icon.source.text='';icon.changed((1,))
            icon.source.text='HDR';icon.changed((0,))
            self.assertIsNone(icon.last_name)


class RealTimeshiftDelay(unittest.TestCase):
    def service(self,active=True,end=90000*120*60,current=90000*4*60,error=0):
        return types.SimpleNamespace(timeshift=lambda:types.SimpleNamespace(isTimeshiftActive=lambda:active),seek=lambda:types.SimpleNamespace(getLength=lambda:(error,end),getPlayPosition=lambda:(0,current)))

    def test_delay_is_computed_from_native_pts(self):
        self.assertEqual(timeshift_status(self.service()),'+116 min')
        self.assertEqual(timeshift_status(self.service(end=90000,current=90000)),'+0 min')

    def test_no_inactive_or_unknown_delay_is_invented(self):
        self.assertEqual(timeshift_status(None),'')
        self.assertEqual(timeshift_status(self.service(active=False)),'')
        self.assertEqual(timeshift_status(self.service(error=1)),'TIMESHIFT')
        self.assertEqual(timeshift_status(self.service(end=-1)),'TIMESHIFT')
        self.assertEqual(timeshift_status(self.service(end=1,current=2)),'TIMESHIFT')
