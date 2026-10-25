"""Aspect-preserving picon renderer, using Enigma2's existing picon resolver."""
from enigma import ePixmap, ePoint, eSize
from Components.Renderer.Renderer import Renderer
from Components.Renderer.Picon import getPiconName
from Components.MetrixNEO.model import fit_rect
from Tools.LoadPixmap import LoadPixmap


class MetrixNEOPicon(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.frame_position = None
        self.frame_size = None
        self.last_path = None

    def applySkin(self, desktop, parent):
        result = Renderer.applySkin(self, desktop, parent)
        self.frame_position = self.instance.position()
        self.frame_size = self.instance.size()
        self.changed((self.CHANGED_ALL,))
        return result

    def changed(self, what):
        if self.instance is None or self.frame_size is None:
            return
        if what[0] == self.CHANGED_CLEAR:
            self.instance.hide()
            self.last_path = None
            return
        try:
            path = getPiconName(self.source.text)
            if path and path == self.last_path:
                return
            self.last_path = path
            pixmap = LoadPixmap(path, cached=True) if path else None
            if pixmap is None:
                self.instance.hide()
                return
            size = pixmap.size()
            x, y, width, height = fit_rect(size.width(), size.height(), self.frame_size.width(), self.frame_size.height())
            self.instance.move(ePoint(self.frame_position.x() + x, self.frame_position.y() + y))
            self.instance.resize(eSize(width, height))
            self.instance.setScale(1)
            self.instance.setPixmap(pixmap)
            self.instance.show()
        except (AttributeError, OSError, RuntimeError):
            self.last_path = None
            self.instance.hide()

    def setFrame(self, position, size):
        """Re-anchor the picon without altering the user's source file or ratio."""
        self.frame_position, self.frame_size = position, size
        self.last_path = None
        self.changed((self.CHANGED_ALL,))
