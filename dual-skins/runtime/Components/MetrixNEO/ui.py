"""Native cancellable preferences; only the green key saves the NEO profile."""
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import ConfigInteger, ConfigPassword, ConfigText, ConfigYesNo, NoSave, getConfigListEntry
from Components.Label import Label
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Screens.Screen import Screen
from Components.MetrixNEO.settings import Settings, validate
from Components.MetrixNEO.preferences import KEY_LABELS, NAVIGATION, categories_for, options_for, preview_text


class NeoSettings(Screen, ConfigListScreen):
    def __init__(self, session, profile="MetrixNEO"):
        Screen.__init__(self, session)
        self.skinName = "MetrixNEOSettings"
        self.setTitle(("NEO Advanced" if profile.endswith("Advanced") else "NEO") + " · Préférences")
        self.profile = profile
        self.store = Settings("/etc/enigma2/metrix-neo", profile)
        for key, label in KEY_LABELS.items():
            self[key] = StaticText(label)
        self["preview"] = Label()
        self["description"] = Label()
        self["footnote"] = Label(NAVIGATION)
        self.categories = categories_for(profile)
        self["categories"] = MenuList([label for key, label in self.categories])
        self.category = self.categories[0][0]
        self.fields = {}
        for key, label, kind, category, description in options_for(profile):
            value = self.store.pending[key]
            if kind == "bool":
                editor = ConfigYesNo(default=value)
            elif kind == "integer":
                editor = ConfigInteger(default=value, limits=(1, 128))
            elif kind == "password":
                editor = ConfigPassword(default=value, fixed_size=False)
            else:
                editor = ConfigText(default="" if value is None else str(value), fixed_size=False)
            self.fields[key] = NoSave(editor)
        ConfigListScreen.__init__(self, self.entries(), session=session, on_change=self.preview)
        # MENU chooses a category; OK and arrows retain native editing.
        self["menuConfigActions"].setEnabled(False)
        self["neoActions"] = ActionMap(["OkCancelActions", "ColorActions", "ConfigListActions"], {
            "cancel": self.cancel, "red": self.cancel, "green": self.save,
            "yellow": self.defaults, "blue": self.refresh, "menu": self.choose_category,
        }, -2)
        self["config"].onSelectionChanged.append(self.preview)
        self.onLayoutFinish.append(self.layout_ready)
        self.preview()

    def entries(self):
        return [getConfigListEntry(label, self.fields[key], description)
                for key, label, kind, category, description in options_for(self.profile, self.category)]

    def layout_ready(self):
        self["categories"].enableAutoNavigation(False)
        self["categories"].setCurrentIndex([key for key, label in self.categories].index(self.category))
        self.preview()

    def choose_category(self):
        from Screens.ChoiceBox import ChoiceBox
        self.session.openWithCallback(self.category_selected, ChoiceBox,
            windowTitle="Catégories NEO", choiceList=[(label, key) for key, label in self.categories],
            selection=[key for key, label in self.categories].index(self.category))

    def category_selected(self, choice):
        if not choice or choice[1] not in dict(self.categories):
            return
        self.category = choice[1]
        self["config"].setList(self.entries())
        self["config"].setCurrentIndex(0)
        self.layout_ready()

    def preview(self):
        large = self.fields["large_text"].value
        self["preview"].setText(preview_text(large))
        current = self["config"].getCurrent()
        self["description"].setText(current[2] if current and len(current) > 2 else "")
        if self["preview"].instance is not None:
            from enigma import gFont
            self["preview"].instance.setFont(gFont("Regular", 32 if large else 26))

    def defaults(self):
        self.store.reset_preview()
        for key, editor in self.fields.items():
            value = self.store.pending[key]
            editor.value = ("" if value is None else str(value)) if isinstance(editor, ConfigText) else value
        # Rebuild the visible list so every reset value is repainted.
        self["config"].setList(self.entries())
        self.preview()

    def cancel(self):
        self.store.cancel()
        self.close()

    def save(self):
        from Screens.MessageBox import MessageBox
        try:
            candidate = dict(self.store.pending)
            for key, editor in self.fields.items():
                value = editor.value
                if key in ("latitude", "longitude"):
                    value = float(value) if value.strip() else None
                candidate[key] = value
            self.store.pending = validate(candidate)
            self.store.save()
        except (OSError, ValueError, TypeError):
            self.session.open(MessageBox, "Enregistrement NEO impossible. Vérifiez les coordonnées, la clé API numérique et le cache. Réglages enregistrés conservés.", type=MessageBox.TYPE_ERROR)
            return
        try:
            from Plugins.Extensions.MetrixNEOHelper.service import refresh
            refresh(self.profile)
        except ImportError:
            pass
        self.close()

    def refresh(self):
        from Screens.MessageBox import MessageBox
        try:
            from Plugins.Extensions.MetrixNEOHelper.service import refresh
            refresh(self.profile)
            text = "Actualisation demandée avec les réglages déjà enregistrés. Les modifications de cet écran ne sont pas enregistrées par la touche bleue. La météo et les logos ont chacun leur autorisation réseau. Les logos suivent le match de l’EPG."
        except ImportError:
            text = "Helper facultatif absent : aucune actualisation effectuée. Les réglages temporaires sont conservés."
        self.session.open(MessageBox, text, type=MessageBox.TYPE_INFO, timeout=8)
