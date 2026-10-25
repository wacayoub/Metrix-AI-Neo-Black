"""Native cached pixmaps driven by measured converter text, never badge literals."""
from enigma import ePixmap
from Components.Renderer.Renderer import Renderer
from Components.MetrixNEO.infobar_icons import icon_name
from Tools.Directories import SCOPE_SKINS, resolveFilename
from Tools.LoadPixmap import LoadPixmap


class MetrixNEOInfobarIcon(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.profile = "MetrixNEO"
        self.kind = ""
        self.last_name = None

    def applySkin(self, desktop, parent):
        attributes=[]
        for key,value in self.skinAttributes or []:
            if key == "neoProfile":
                self.profile = value if value in ("MetrixNEO","MetrixNEOAdvanced") else "MetrixNEO"
            elif key == "neoKind":
                self.kind=value
            else:
                attributes.append((key,value))
        self.skinAttributes=attributes
        result=Renderer.applySkin(self,desktop,parent)
        self.changed((self.CHANGED_ALL,))
        return result

    def changed(self, what):
        if self.instance is None:
            return
        name=None if what[0] == self.CHANGED_CLEAR else icon_name(self.kind,getattr(self.source,"text",""))
        if not name:
            self.last_name=None
            self.instance.hide()
            return
        if name != self.last_name:
            path=resolveFilename(SCOPE_SKINS,self.profile+"/assets/infobar-icon-"+name+".png")
            pixmap=LoadPixmap(path,cached=True)
            if pixmap is None:
                self.last_name=None
                self.instance.hide()
                return
            self.instance.setPixmap(pixmap)
            self.last_name=name
        self.instance.show()
