from Components.Renderer.Label import Label
from Components.MetrixNEO.context import context_selection
from Components.MetrixNEO.model import clean_text


class MetrixNEOContext(Label):
    def __init__(self):
        Label.__init__(self)
        self.parent_screen = None
        self.snapshot = None
        self.part = "full"
        self.listing = None

    def applySkin(self, desktop, parent):
        self.parent_screen = parent
        for key, value in self.skinAttributes or []:
            if key == "neoPart":
                self.part = value
        self.skinAttributes = [(key, value) for key, value in (self.skinAttributes or []) if key != "neoPart"]
        result = Label.applySkin(self, desktop, parent)
        if self.part == "action":
            self.listing = parent.get("menu") or parent.get("list")
            if self.listing is not None:
                self.listing.onSelectionChanged.append(self.selection_changed)
        self.changed((self.CHANGED_ALL,))
        return result

    def selection_changed(self):
        self.changed((self.CHANGED_ALL,))

    def changed(self, what):
        if self.parent_screen is None or what[0] == self.CHANGED_CLEAR:
            self.text = ""
            return
        if self.part == "action":
            from Components.MetrixNEO.context_menu import presentation
            current = self.listing.getCurrent() if self.listing is not None else None
            title, _, description = presentation(current[0] if current else None)
            self.text = title + ("\n\n" + description if description else "")
            return
        if self.snapshot is None:
            try:
                _, event = context_selection(self.parent_screen)
                self.snapshot = clean_text(event.getEventName() + "\n\n" + event.getShortDescription(), 800) if event else "Actions natives\n\nLes opérations disponibles dépendent de la sélection et des permissions."
            except (AttributeError, RuntimeError):
                self.snapshot = ""
        title, _, description = self.snapshot.partition("\n\n")
        self.text = title if self.part == "title" else description if self.part == "description" else self.snapshot

    def preWidgetRemove(self, instance):
        if self.listing is not None and self.selection_changed in self.listing.onSelectionChanged:
            self.listing.onSelectionChanged.remove(self.selection_changed)
        self.listing = None
        self.parent_screen = None
