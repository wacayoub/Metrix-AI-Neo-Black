"""Context decoration must preserve every native action and its shortcut."""
import importlib.util
import sys
import types
import unittest
from functools import partial
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
from Components.MetrixNEO.context_menu import bind_context, decorate_rows, presentation


def showServiceInformations(*args):
    raise AssertionError("Presentation must never execute a native action")


class ContextActions(unittest.TestCase):
    def decorate(self, rows):
        return decorate_rows(rows, "MetrixNEOAdvanced", lambda **kw: kw,
                             lambda **kw: kw, lambda name: name, 7, 3)

    def test_all_payloads_order_and_native_shortcuts_preserved(self):
        callbacks = [Mock() for _ in range(19)]
        rows = [[("Action %d" % i, callback), (0, 48, 0, 1180, 52, 0, 0, "old"),
                 (1, 6, 8, 32, 32, "native-key-%d" % i)] for i, callback in enumerate(callbacks)]
        result = self.decorate(rows)
        self.assertEqual(len(result), 19)  # No truncation to the 15 visible rows.
        for old, new in zip(rows, result):
            self.assertIs(new[0], old[0])
            self.assertEqual(new[-1][5:], old[-1][5:])
            self.assertEqual(old[-1][1:5], (6, 8, 32, 32))
        for callback in callbacks:
            callback.assert_not_called()

    def test_separator_remains_unselectable_and_unknown_plugin_is_kept(self):
        callback = Mock()
        result = self.decorate([[None, (0,)], [("Extension externe", callback), (0,)]])
        self.assertIsNone(result[0][0])
        self.assertEqual(result[1][1]["text"], "Extension externe")
        self.assertIs(result[1][0][1], callback)
        callback.assert_not_called()

    def test_native_bound_function_and_choicebox_callfunc_metadata(self):
        boundFunction = type("boundFunction", (), {})
        native = boundFunction()
        native.fnc = partial(showServiceInformations, None)
        self.assertEqual(presentation(("Informations", native))[1], "info")
        self.assertEqual(presentation(("Informations", "CALLFUNC", native, None))[1], "info")
        self.assertEqual(presentation(("Plugin inconnu", Mock()))[2], "")

    def test_bind_retains_selection_actions_and_permissions(self):
        callback = Mock()
        payload = ("Plugin autorisé", callback)
        listing = types.SimpleNamespace(list=[[payload, (0,)]], l=Mock(),
                                        getSelectionIndex=lambda: 9, moveToIndex=Mock())
        listing.setList = lambda rows: setattr(listing, "list", rows)
        class Screen(dict):
            pass
        actions = object()
        screen = Screen(menu=listing, actions=actions)
        screen.protectContextMenu = True
        enigma = types.ModuleType("enigma")
        for name in ("BT_SCALE", "BT_KEEP_ASPECT_RATIO", "RT_HALIGN_LEFT", "RT_VALIGN_CENTER", "RT_ELLIPSIS"):
            setattr(enigma, name, 1)
        enigma.gFont = lambda *args: args
        content = types.ModuleType("Components.MultiContent")
        content.MultiContentEntryText = content.MultiContentEntryPixmapAlphaBlend = lambda **kw: kw
        directories = types.ModuleType("Tools.Directories")
        directories.SCOPE_SKINS = 1
        directories.resolveFilename = lambda scope, path: path
        pixmaps = types.ModuleType("Tools.LoadPixmap")
        pixmaps.LoadPixmap = lambda path, cached: path
        with patch.dict(sys.modules, {"enigma": enigma, "Components.MultiContent": content,
                         "Tools.Directories": directories, "Tools.LoadPixmap": pixmaps}):
            bind_context(screen, "MetrixNEOAdvanced")
            bind_context(screen, "MetrixNEOAdvanced")
        listing.moveToIndex.assert_called_once_with(9)
        self.assertIs(listing.list[0][0], payload)
        self.assertIs(screen["actions"], actions)
        self.assertTrue(screen.protectContextMenu)
        callback.assert_not_called()

    def test_action_help_follows_selection_and_unsubscribes_on_close(self):
        base = types.ModuleType("Components.Renderer.Label")
        class Label:
            CHANGED_ALL, CHANGED_CLEAR = 1, 0
            def applySkin(self, desktop, parent):
                return True
        base.Label = Label
        with patch.dict(sys.modules, {"Components.Renderer.Label": base}):
            spec = importlib.util.spec_from_file_location("context_renderer_test", ROOT / "runtime/Components/Renderer/MetrixNEOContext.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            current = [("Informations", partial(showServiceInformations, None))]
            listing = types.SimpleNamespace(getCurrent=lambda: [current[0]], onSelectionChanged=[])
            renderer = module.MetrixNEOContext()
            renderer.skinAttributes = [("neoPart", "action")]
            renderer.applySkin(None, {"menu": listing})
            self.assertIn("Consulter", renderer.text)
            callback = Mock()
            current[0] = ("Extension", callback)
            listing.onSelectionChanged[0]()
            self.assertEqual(renderer.text, "Extension")
            callback.assert_not_called()
            renderer.preWidgetRemove(None)
            self.assertEqual(listing.onSelectionChanged, [])
