"""Native page changes update presentation only; callbacks leave on close."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]


class Page:
    def __init__(self,value):self.value=value;self.callbacks=[]
    def addNotifier(self,callback,initial_call=True):
        self.callbacks.append(callback)
        if initial_call:callback(self)
    def removeNotifier(self,callback):self.callbacks.remove(callback)
    def select(self,value):
        self.value=value
        for callback in self.callbacks[:]:callback(self)


class SubtitleIcon(unittest.TestCase):
    def setUp(self):
        renderer=types.ModuleType('Components.Renderer.Renderer')
        class Renderer:
            CHANGED_ALL,CHANGED_CLEAR=1,0
            def __init__(self):self.instance=None;self.skinAttributes=[]
            def applySkin(self,desktop,parent):return True
            def destroy(self):self.__dict__.clear()
        renderer.Renderer=Renderer
        enigma=types.ModuleType('enigma');enigma.ePixmap=object
        directories=types.ModuleType('Tools.Directories');directories.SCOPE_SKINS=0;directories.resolveFilename=lambda scope,path:path
        loader=types.ModuleType('Tools.LoadPixmap');self.load=loader.LoadPixmap=Mock(side_effect=lambda path,cached:'png:'+path)
        self.modules=patch.dict(sys.modules,{'Components.Renderer.Renderer':renderer,'enigma':enigma,'Tools.Directories':directories,'Tools.LoadPixmap':loader})
        self.modules.start();self.addCleanup(self.modules.stop)
        spec=importlib.util.spec_from_file_location('track_icon_under_test',ROOT/'runtime/Components/Renderer/MetrixNEOTrackIcon.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        self.Icon=module.MetrixNEOTrackIcon

    def bind(self,page,profile='MetrixNEO'):
        icon=self.Icon();icon.instance=Mock();icon.source=types.SimpleNamespace(text='عنوان مترجم')
        icon.skinAttributes=[('neoProfile',profile),('alphatest','blend')]
        icon.applySkin(None,types.SimpleNamespace(settings=types.SimpleNamespace(menupage=page)))
        return icon

    def test_local_mode_controls_icon_in_both_profiles_without_title_matching(self):
        for profile in ('MetrixNEO','MetrixNEOAdvanced'):
            page=Page('audio');icon=self.bind(page,profile)
            self.assertEqual(icon.last_name,'audio-speaker')
            page.select('subtitles')
            self.assertEqual(icon.last_name,'subtitle-icon')
            icon.instance.setPixmap.assert_called_with('png:'+profile+'/assets/subtitle-icon.png')
            self.assertEqual(page.value,'subtitles')
            icon.destroy();self.assertEqual(page.callbacks,[])

    def test_missing_image_and_unknown_page_hide_the_previous_artwork(self):
        page=Page('audio');icon=self.bind(page)
        self.load.side_effect=lambda path,cached:None
        page.select('subtitles');self.assertIsNone(icon.last_name);icon.instance.hide.assert_called()
        page.select('unknown');self.assertIsNone(icon.last_name)
        page.select('audio');self.assertEqual(icon.last_name,'audio-speaker')

    def test_clear_then_refresh_and_repeated_page_changes_use_bounded_cache(self):
        page=Page('subtitles');icon=self.bind(page)
        for mode in ('audio','subtitles','audio','subtitles'):page.select(mode)
        self.assertEqual(self.load.call_count,2)
        self.assertEqual(len(icon.pixmaps),2)
        icon.changed((0,));self.assertIsNone(icon.last_name)
        icon.changed((1,));self.assertEqual(icon.last_name,'subtitle-icon')
        self.assertEqual(self.load.call_count,2)

    def test_reskin_and_close_detach_the_notifier_and_do_not_change_page(self):
        old=Page('audio');icon=self.bind(old);new=Page('subtitles')
        icon.skinAttributes=[('neoProfile','MetrixNEOAdvanced')]
        icon.applySkin(None,types.SimpleNamespace(settings=types.SimpleNamespace(menupage=new)))
        self.assertEqual(old.callbacks,[]);self.assertEqual(len(new.callbacks),1)
        self.assertEqual(old.value,'audio');self.assertEqual(new.value,'subtitles')
        icon.destroy();self.assertEqual(new.callbacks,[])
        old.select('subtitles');new.select('audio')

    def test_parent_without_mode_is_hidden_and_profile_path_is_allowlisted(self):
        icon=self.Icon();icon.instance=Mock();icon.skinAttributes=[('neoProfile','../outside')]
        icon.applySkin(None,types.SimpleNamespace())
        self.assertEqual(icon.profile,'MetrixNEO');self.assertIsNone(icon.last_name)
        icon.instance.hide.assert_called();self.load.assert_not_called()


if __name__=='__main__':unittest.main()
