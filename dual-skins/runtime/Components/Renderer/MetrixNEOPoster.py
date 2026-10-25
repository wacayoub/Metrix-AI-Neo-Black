"""Artwork of the selected EPG event, never a fixed skin photograph.

Optional cache-only lookup; decoding is asynchronous through ePicLoad. Every
selection hides the previous picture and obsolete decoding results are ignored.
"""
from enigma import ePicLoad, ePixmap
from Components.Renderer.Renderer import Renderer
from Components.MetrixNEO.settings import read_settings


class MetrixNEOPoster(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.profile = "MetrixNEO"
        self.decoder = None
        self.last_path = None
        self.desired_path = None
        self.settings = {}
        self.parent_screen = None
        self.channel_layout = False
        self.detail_layout = None
        self.context = False
        self.context_event = None
        self.context_loaded = False
        self.role = "poster"

    def applySkin(self, desktop, parent):
        attributes = []
        for key, value in self.skinAttributes or []:
            if key == "neoProfile":
                self.profile = value
            elif key == "neoRole":
                self.role = value if value in ("home", "away") else "poster"
            elif key in ("neoReflow", "neoChannelLayout"):
                self.channel_layout = value == "1"
            elif key == "neoContext":
                self.context = value == "1"
            else:
                attributes.append((key, value))
        self.skinAttributes = attributes
        self.parent_screen = parent
        self.settings = read_settings(self.profile)
        result = Renderer.applySkin(self, desktop, parent)
        parent.onLayoutFinish.append(self._initial_layout)
        return result

    def _initial_layout(self):
        if self.channel_layout and self.parent_screen is not None:
            from Components.MetrixNEO.channel_layout import ChannelDetailLayout
            self.detail_layout = ChannelDetailLayout(self.parent_screen, self.profile)
            self.detail_layout.capture()
        # Sources can connect before applySkin creates the ePixmap. Load the
        # initially selected event now instead of waiting for a channel change.
        self.changed((self.CHANGED_ALL,))

    def _resize_description(self, has_image):
        if self.detail_layout is not None:
            self.detail_layout.apply(has_image)

    def changed(self, what):
        if self.instance is None:
            return
        self.instance.hide()
        self._resize_description(False)
        self.desired_path = None
        if what[0] == self.CHANGED_CLEAR:
            return
        if self.role != "poster":
            try:
                from Plugins.Extensions.MetrixNEOHelper.service import settings_for, watch_clubs
                watch_clubs(self.profile,self)
                self.settings = settings_for(self.profile,self.settings)
            except ImportError:
                pass
        enabled = self.settings.get("posters") if self.role == "poster" else self.settings.get("posters") or self.settings.get("club_logos")
        if not enabled:
            return
        event = getattr(self.source, "event", None)
        if self.context and self.parent_screen is not None:
            from Components.MetrixNEO.context import context_selection
            if not self.context_loaded:
                try:
                    _, self.context_event = context_selection(self.parent_screen)
                except (AttributeError, RuntimeError):
                    self.context_event = None
                self.context_loaded = True
            event = self.context_event
        try:
            from Plugins.Extensions.MetrixNEOHelper.service import poster_path
            if self.role == "poster":
                self.desired_path = poster_path(event, self.profile)
            else:
                from Plugins.Extensions.MetrixNEOHelper.service import club_path
                self.desired_path = club_path(event, self.profile, self.role)
                if self.settings.get("club_logos"):
                    from Plugins.Extensions.MetrixNEOHelper.service import request_clubs
                    request_clubs(event,self.profile,self.settings)
        except (ImportError, AttributeError, OSError, ValueError):
            return
        if self.desired_path:
            self._start_decode()

    def _start_decode(self):
        if self.decoder is not None or not self.desired_path or self.instance is None:
            return
        self.last_path = self.desired_path
        self.decoder = ePicLoad()
        self.decoder.PictureData.get().append(self._ready)
        size = self.instance.size()
        self.decoder.setPara((size.width(), size.height(), 1, 1, False, 1, "#00162231"))
        if self.decoder.startDecode(self.last_path):
            self.decoder = None

    def _ready(self, *unused):
        decoder, self.decoder = self.decoder, None
        if decoder is None or self.instance is None:
            return
        picture = decoder.getData()
        if self.last_path == self.desired_path:
            if picture is not None:
                self.instance.setPixmap(picture.__deref__() if hasattr(picture, "__deref__") else picture)
                self.instance.show()
                self._resize_description(True)
        else:
            self._start_decode()

    def preWidgetRemove(self, instance):
        try:
            from Plugins.Extensions.MetrixNEOHelper.service import unwatch_clubs
            unwatch_clubs(self.profile,self)
        except ImportError:
            pass
        self.desired_path = None
        if self.decoder is not None:
            callbacks = self.decoder.PictureData.get()
            if self._ready in callbacks:
                callbacks.remove(self._ready)
        self.decoder = None
        if self.parent_screen is not None and self._initial_layout in self.parent_screen.onLayoutFinish:
            self.parent_screen.onLayoutFinish.remove(self._initial_layout)
        if self.detail_layout is not None:
            self.detail_layout.close()
            self.detail_layout = None
        self.parent_screen = None
