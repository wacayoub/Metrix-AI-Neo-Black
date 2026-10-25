"""Explicit optional plugin; no autostart writes and no Enigma2 patching."""
from Plugins.Plugin import PluginDescriptor

_timer = None


def main(session, **kwargs):
    from Components.MetrixNEO.ui import NeoSettings
    from Components.config import config
    profile = "MetrixNEOAdvanced" if "MetrixNEOAdvanced" in config.skin.primary_skin.value else "MetrixNEO"
    session.open(NeoSettings, profile)


def sessionstart(reason, session=None, **kwargs):
    global _timer
    if reason != 0:
        if _timer is not None:
            _timer.stop()
            _timer = None
        return
    from enigma import eTimer
    from Components.MetrixNEO.settings import PROFILES, read_settings
    from .service import refresh

    def tick():
        for profile in PROFILES:
            settings = read_settings(profile)
            if settings["weather"] or settings["posters"] or settings["club_logos"]:
                refresh(profile)

    _timer = eTimer()
    _timer.callback.append(tick)
    _timer.start(900000, False)
    tick()


def Plugins(**kwargs):
    return [PluginDescriptor(name="Metrix NEO · Préférences", description="Modules facultatifs, aperçu et réglages par skin", where=PluginDescriptor.WHERE_PLUGINMENU, fnc=main),
            PluginDescriptor(where=PluginDescriptor.WHERE_SESSIONSTART, fnc=sessionstart)]
