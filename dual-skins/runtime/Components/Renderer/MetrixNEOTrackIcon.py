"""Screen-local audio/subtitle artwork; observes page selection, never actions."""
from enigma import ePixmap
from Components.Renderer.Renderer import Renderer
from Tools.Directories import SCOPE_SKINS, resolveFilename
from Tools.LoadPixmap import LoadPixmap


class MetrixNEOTrackIcon(Renderer):
    GUI_WIDGET=ePixmap

    def __init__(self):
        Renderer.__init__(self)
        self.profile='MetrixNEO'
        self.mode=None
        self.last_name=None
        self.pixmaps={}

    def _detach(self):
        if self.mode is not None:
            self.mode.removeNotifier(self._mode_changed)
            self.mode=None

    def applySkin(self,desktop,parent):
        self._detach()
        attributes=[]
        for key,value in self.skinAttributes or []:
            if key=='neoProfile':
                self.profile=value if value in ('MetrixNEO','MetrixNEOAdvanced') else 'MetrixNEO'
            else:attributes.append((key,value))
        self.skinAttributes=attributes
        self.pixmaps.clear()
        self.last_name=None
        result=Renderer.applySkin(self,desktop,parent)
        self.mode=getattr(getattr(parent,'settings',None),'menupage',None)
        if self.mode is not None:self.mode.addNotifier(self._mode_changed,initial_call=True)
        else:self.changed((self.CHANGED_ALL,))
        return result

    def _mode_changed(self,config=None):
        self.changed((self.CHANGED_ALL,))

    def changed(self,what):
        if self.instance is None:return
        name=None if what[0]==self.CHANGED_CLEAR else {'audio':'audio-speaker','subtitles':'subtitle-icon'}.get(getattr(self.mode,'value',None))
        if name is None:
            self.last_name=None
            self.instance.hide()
            return
        if name!=self.last_name:
            if name not in self.pixmaps:
                path=resolveFilename(SCOPE_SKINS,self.profile+'/assets/'+name+'.png')
                self.pixmaps[name]=LoadPixmap(path,cached=True)
            pixmap=self.pixmaps[name]
            if pixmap is None:
                self.last_name=None
                self.instance.hide()
                return
            self.instance.setPixmap(pixmap)
            self.last_name=name
        self.instance.show()

    def destroy(self):
        self._detach()
        Renderer.destroy(self)
