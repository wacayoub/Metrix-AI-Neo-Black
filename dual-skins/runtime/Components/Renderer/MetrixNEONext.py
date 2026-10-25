from Components.Renderer.Label import Label
from Components.MetrixNEO.events import upcoming_text


class MetrixNEONext(Label):
    """Next events relative to the selected EPG event, not the playing channel."""
    def __init__(self):
        Label.__init__(self)
        self.parent_screen = None
        self.index = 0

    def applySkin(self, desktop, parent):
        attributes = []
        for key, value in self.skinAttributes or []:
            if key == "neoIndex":
                self.index = int(value)
            else:
                attributes.append((key, value))
        self.skinAttributes = attributes
        self.parent_screen = parent
        result = Label.applySkin(self, desktop, parent)
        self.changed((self.CHANGED_ALL,))
        return result

    def changed(self, what):
        self.text = ""
        if self.parent_screen is None or what[0] == self.CHANGED_CLEAR:
            return
        service_source = self.parent_screen.get("Service")
        reference = getattr(service_source, "service", None)
        self.text = upcoming_text(getattr(self.source, "event", None), reference, self.index)

    def preWidgetRemove(self, instance):
        self.parent_screen = None
