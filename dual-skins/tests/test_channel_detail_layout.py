"""Artwork absence must not leave a large empty panel or move upcoming events."""
import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
from Components.MetrixNEO.channel_layout import ChannelDetailLayout, channel_geometry, detail_slots


class Pair:
    def __init__(self, x, y):
        self.values = x, y
    def x(self):
        return self.values[0]
    def y(self):
        return self.values[1]
    width = x
    height = y


class DetailReflow(unittest.TestCase):
    def test_missing_image_reclaims_space_and_restores_both_profiles(self):
        enigma = types.ModuleType("enigma")
        enigma.ePoint = enigma.eSize = Pair
        for profile in ("MetrixNEO", "MetrixNEOAdvanced"):
            g = channel_geometry(profile.endswith("Advanced"))
            renderers = []
            for origin, box in detail_slots(profile, True).items():
                instance = Mock()
                instance.position.return_value = Pair(*origin)
                instance.size.return_value = Pair(*box[2:])
                renderers.append(types.SimpleNamespace(instance=instance))
            fixed = Mock()
            fixed.position.return_value = Pair(*g["next"])
            renderers.append(types.SimpleNamespace(instance=fixed))
            layout = ChannelDetailLayout(types.SimpleNamespace(renderer=renderers), profile)
            layout.capture()
            with patch.dict(sys.modules, {"enigma": enigma}):
                layout.apply(False)
                x, y = renderers[-2].instance.move.call_args.args[0].values
                w, h = renderers[-2].instance.resize.call_args.args[0].values
                self.assertLess(y, g["description"][1])
                self.assertGreater(h, g["description"][3])
                self.assertEqual(y + h, g["description"][1] + g["description"][3])
                calls = renderers[0].instance.move.call_count
                layout.apply(False)
                self.assertEqual(renderers[0].instance.move.call_count, calls)
                layout.apply(True)
            for renderer, original in zip(renderers, detail_slots(profile, True).values()):
                self.assertEqual(renderer.instance.move.call_args.args[0].values, original[:2])
                self.assertEqual(renderer.instance.resize.call_args.args[0].values, original[2:])
            fixed.move.assert_not_called()
            fixed.resize.assert_not_called()
            layout.close()
            self.assertIsNone(layout.screen)
            self.assertEqual(layout.entries, [])

    def test_picon_reanchors_without_changing_its_aspect_ratio(self):
        base = types.ModuleType("Components.Renderer.Renderer")
        base.Renderer = type("Renderer", (), {"CHANGED_ALL": 1, "CHANGED_CLEAR": 0})
        enigma = types.ModuleType("enigma")
        enigma.ePoint = enigma.eSize = Pair
        enigma.ePixmap = object
        native = types.ModuleType("Components.Renderer.Picon")
        native.getPiconName = lambda text: '/existing/picon.png'
        pixmaps = types.ModuleType("Tools.LoadPixmap")
        pixmaps.LoadPixmap = Mock(return_value=types.SimpleNamespace(size=lambda: Pair(400, 100)))
        with patch.dict(sys.modules, {"enigma": enigma, "Components.Renderer.Renderer": base,
                       "Components.Renderer.Picon": native, "Tools.LoadPixmap": pixmaps}):
            spec = importlib.util.spec_from_file_location("picon_reanchor_test", ROOT / "runtime/Components/Renderer/MetrixNEOPicon.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            renderer = module.MetrixNEOPicon()
            renderer.instance = Mock()
            renderer.source = types.SimpleNamespace(text='same-service')
            renderer.setFrame(Pair(1200, 196), Pair(180, 74))
            self.assertEqual(renderer.instance.resize.call_args.args[0].values, (180, 45))
            renderer.setFrame(Pair(1200, 423), Pair(180, 74))
            self.assertEqual(renderer.instance.resize.call_args.args[0].values, (180, 45))
            self.assertEqual(renderer.instance.move.call_args.args[0].values, (1200, 437))
            pixmaps.LoadPixmap.assert_called_with('/existing/picon.png', cached=True)
            module.getPiconName = lambda text: None
            renderer.instance.hide.reset_mock()
            renderer.setFrame(Pair(1200, 196), Pair(180, 74))
            renderer.instance.hide.assert_called_once()
