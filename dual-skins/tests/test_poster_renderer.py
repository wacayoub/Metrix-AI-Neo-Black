"""Selected-event artwork behaviour with controllable asynchronous decoding."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))


class DynamicProgrammeArtwork(unittest.TestCase):
    def setUp(self):
        self.decoders = []
        created = self.decoders
        class Decoder:
            def __init__(self):
                self.callbacks = []
                self.PictureData = types.SimpleNamespace(get=lambda: self.callbacks)
                self.path = None
                created.append(self)
            def setPara(self, parameters):
                self.parameters = parameters
            def startDecode(self, path):
                self.path = path
                return 0
            def getData(self):
                return 'decoded:' + self.path
            def complete(self):
                for callback in list(self.callbacks):
                    callback()
        renderer_module = types.ModuleType('Components.Renderer.Renderer')
        class Renderer:
            CHANGED_CLEAR, CHANGED_ALL = 0, 1
        renderer_module.Renderer = Renderer
        enigma = types.ModuleType('enigma')
        enigma.ePicLoad, enigma.ePixmap = Decoder, object
        helper = types.ModuleType('Plugins.Extensions.MetrixNEOHelper.service')
        self.lookup = Mock(side_effect=lambda event, profile: self.catalog.get(event))
        helper.poster_path = self.lookup
        self.catalog = {'event-a':'/catalog/a.jpg', 'event-b':'/catalog/b.jpg'}
        self.modules = patch.dict(sys.modules, {'enigma':enigma, 'Components.Renderer.Renderer':renderer_module,
            'Plugins.Extensions.MetrixNEOHelper.service':helper})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        spec = importlib.util.spec_from_file_location('dynamic_poster_under_test',ROOT/'runtime/Components/Renderer/MetrixNEOPoster.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.renderer = module.MetrixNEOPoster()
        self.renderer.settings = {'posters':True}
        self.renderer.source = types.SimpleNamespace(event=None)
        self.renderer.instance = Mock()
        self.renderer.instance.size.return_value = types.SimpleNamespace(width=lambda:604,height=lambda:258)

    def select(self, event):
        self.renderer.source.event = event
        self.renderer.changed((self.renderer.CHANGED_ALL,))

    def test_club_slot_uses_curated_role_and_hides_when_pair_missing(self):
        helper=sys.modules['Plugins.Extensions.MetrixNEOHelper.service']
        helper.club_path=Mock(return_value='/catalog/home.png')
        self.renderer.role='home'
        self.select('event-a')
        helper.club_path.assert_called_once_with('event-a','MetrixNEO','home')
        self.lookup.assert_not_called()
        self.decoders[-1].complete()
        self.renderer.instance.setPixmap.assert_called_with('decoded:/catalog/home.png')
        helper.club_path.return_value=None
        self.select('event-b')
        self.renderer.instance.hide.assert_called()
        self.assertIsNone(self.renderer.desired_path)

    def test_automatic_clubs_work_with_programme_images_disabled(self):
        helper=sys.modules['Plugins.Extensions.MetrixNEOHelper.service']
        helper.watch_clubs=Mock()
        helper.settings_for=lambda profile,fallback:fallback
        helper.club_path=Mock(return_value=None)
        helper.request_clubs=Mock()
        self.renderer.settings={'posters':False,'club_logos':True}
        self.renderer.role='home'
        self.select('event-a')
        helper.request_clubs.assert_called_once_with('event-a','MetrixNEO',self.renderer.settings)
        self.assertFalse(self.decoders)
        helper.club_path.return_value='/cache/home.png'
        self.renderer.changed((self.renderer.CHANGED_ALL,))
        self.decoders[-1].complete()
        self.renderer.instance.setPixmap.assert_called_with('decoded:/cache/home.png')

    def test_saved_settings_can_enable_club_slot_without_restarting_gui(self):
        helper=sys.modules['Plugins.Extensions.MetrixNEOHelper.service']
        helper.watch_clubs=Mock()
        helper.settings_for=Mock(return_value={'posters':False,'club_logos':True})
        helper.club_path=Mock(return_value='/cache/home.png')
        helper.request_clubs=Mock()
        self.renderer.settings={'posters':False,'club_logos':False}
        self.renderer.role='home'
        self.select('event-a')
        self.assertEqual(self.decoders[-1].path,'/cache/home.png')

    def test_each_selected_programme_loads_its_own_picture(self):
        self.select('event-a')
        self.decoders[-1].complete()
        self.renderer.instance.setPixmap.assert_called_with('decoded:/catalog/a.jpg')
        self.select('event-b')
        self.assertEqual(self.decoders[-1].path,'/catalog/b.jpg')
        self.decoders[-1].complete()
        self.renderer.instance.setPixmap.assert_called_with('decoded:/catalog/b.jpg')

    def test_fast_navigation_ignores_obsolete_picture(self):
        self.select('event-a')
        first = self.decoders[-1]
        self.select('event-b')
        first.complete()
        self.renderer.instance.setPixmap.assert_not_called()
        self.assertEqual(self.decoders[-1].path,'/catalog/b.jpg')
        self.decoders[-1].complete()
        self.renderer.instance.setPixmap.assert_called_once_with('decoded:/catalog/b.jpg')

    def test_missing_artwork_hides_previous_picture(self):
        self.select('event-a')
        self.decoders[-1].complete()
        self.renderer.instance.reset_mock()
        self.select('event-without-artwork')
        self.renderer.instance.hide.assert_called_once()
        self.renderer.instance.show.assert_not_called()
        self.renderer.instance.setPixmap.assert_not_called()
        self.assertIsNone(self.renderer.desired_path)

    def test_missing_artwork_rejects_late_decoding(self):
        self.select('event-a')
        first = self.decoders[-1]
        self.select('event-without-artwork')
        first.complete()
        self.renderer.instance.show.assert_not_called()
        self.renderer.instance.setPixmap.assert_not_called()
        self.assertEqual(len(self.decoders),1)

    def test_disabled_artwork_never_queries_or_decodes(self):
        self.renderer.settings['posters'] = False
        self.select('event-a')
        self.lookup.assert_not_called()
        self.assertEqual(self.decoders,[])
        self.renderer.instance.show.assert_not_called()

    def test_closed_screen_detaches_pending_callback(self):
        self.select('event-a')
        decoder = self.decoders[-1]
        self.renderer.preWidgetRemove(self.renderer.instance)
        self.assertEqual(decoder.callbacks,[])
        decoder.complete()
        self.renderer.instance.setPixmap.assert_not_called()

    def test_initial_layout_loads_the_already_selected_event(self):
        self.renderer.source.event = 'event-a'
        self.renderer._initial_layout()
        self.lookup.assert_called_once_with('event-a', 'MetrixNEO')
        self.assertEqual(self.decoders[-1].path, '/catalog/a.jpg')

    def test_obsolete_decode_never_restores_picture_layout(self):
        self.renderer.detail_layout = Mock()
        self.select('event-a')
        first = self.decoders[-1]
        self.select('event-without-artwork')
        self.renderer.detail_layout.apply.reset_mock()
        first.complete()
        self.renderer.detail_layout.apply.assert_not_called()

    def test_successful_image_restores_layout_and_disabled_image_reflows(self):
        self.renderer.detail_layout = Mock()
        self.select('event-a')
        self.decoders[-1].complete()
        self.renderer.detail_layout.apply.assert_called_with(True)
        self.renderer.settings['posters'] = False
        self.select('event-a')
        self.renderer.detail_layout.apply.assert_called_with(False)


if __name__ == '__main__':
    unittest.main()
