"""Instance-local volume decoration. No audio setting or global handler changes."""

ART_ROOT = "MetrixNEO/assets/volume-styles/"
TRACK_X, TRACK_Y, TRACK_WIDTH, TRACK_HEIGHT = 66, 16, 318, 32
LENS_TIP_WIDTH = 12


def load_volume_art(style, name):
    from Tools.Directories import SCOPE_SKINS, resolveFilename
    from Tools.LoadPixmap import LoadPixmap

    return LoadPixmap(resolveFilename(SCOPE_SKINS, ART_ROOT + style + "/" + name), cached=True)


class VolumeArtwork:
    def __init__(self, parent):
        from enigma import ePoint, eWidget
        from Tools.Directories import SCOPE_SKINS, resolveFilename
        from Tools.LoadPixmap import LoadPixmap

        self.background = self.pixmap(parent, 0, (0, 0, 460, 64))
        self.classic_panel = LoadPixmap(resolveFilename(
            SCOPE_SKINS, "MetrixNEO/assets/launcher/volume-panel.png"), cached=True)
        self.fill_clip = eWidget(parent)
        self.fill_clip.setTransparent(1)
        self.fill_clip.setZPosition(1)
        self.fill_clip.move(ePoint(TRACK_X, TRACK_Y))
        self.fill_clip.hide()
        self.fill = self.pixmap(self.fill_clip, 0, (0, 0, TRACK_WIDTH, TRACK_HEIGHT))
        self.tip = self.pixmap(parent, 2, (TRACK_X, TRACK_Y, LENS_TIP_WIDTH, TRACK_HEIGHT))
        self.digits = self.pixmap(parent, 3, (390, 11, 56, 42))
        self.style = None

    @staticmethod
    def place(widget, box):
        from enigma import ePoint, eSize

        x, y, width, height = box
        widget.move(ePoint(x, y))
        widget.resize(eSize(width, height))

    def pixmap(self, parent, layer, box):
        from enigma import BT_SCALE, ePixmap

        widget = ePixmap(parent)
        widget.setAlphatest(2)
        widget.setPixmapScale(BT_SCALE)
        widget.setZPosition(layer)
        self.place(widget, box)
        widget.hide()
        return widget

    def set_style(self, style):
        if style == self.style:
            return self.style
        if style != "classic":
            panel = load_volume_art(style, "panel.png")
            fill = load_volume_art(style, "fill.png")
            if panel is None or fill is None:
                style = "classic"
        if style == "classic":
            self.background.setPixmap(self.classic_panel)
            self.fill_clip.hide()
        else:
            self.background.setPixmap(panel)
            self.fill.setPixmap(fill)
            self.fill.show()
        if style == "lens":
            self.tip.setPixmap(load_volume_art(style, "tip.png"))
        self.tip.hide()
        self.digits.hide()
        self.background.show()
        self.style = style
        return style

    def set_value(self, value):
        from enigma import eSize

        length = round(TRACK_WIDTH * value / 100)
        if self.style == "lens" and length:
            tip_width = min(LENS_TIP_WIDTH, length)
            length -= tip_width
            self.place(self.tip, (TRACK_X + length, TRACK_Y, tip_width, TRACK_HEIGHT))
            self.tip.show()
        else:
            self.tip.hide()
        if length:
            self.fill_clip.resize(eSize(length, TRACK_HEIGHT))
            self.fill_clip.show()
        else:
            self.fill_clip.hide()
        if self.style == "liquid":
            pixmap = load_volume_art(self.style, "digits/%d.png" % value)
            if pixmap is not None:
                self.digits.setPixmap(pixmap)
                self.digits.show()
                return True
            self.digits.hide()
        return False


def bind_volume(screen, profile):
    if profile != 'MetrixNEO' or getattr(screen, '_neo_volume_bound', False):
        return

    from enigma import BT_SCALE, ePixmap, eLabel, ePoint, eSize, gFont, gRGB
    from Tools.LoadPixmap import LoadPixmap
    from Tools.Directories import SCOPE_SKINS, resolveFilename
    from .settings import read_settings

    bar = screen.get('Volume')
    slider = getattr(bar, 'instance', None)
    if slider is None or not hasattr(bar, 'setValue'):
        return

    position, size = slider.position(), slider.size()
    x, y, width, height = position.x(), position.y(), size.width(), size.height()
    diameter = max(10, round(height * 2.25))
    artwork = VolumeArtwork(screen.instance)
    pointer = ePixmap(screen.instance)
    pointer.setAlphatest(2)
    pointer.setPixmapScale(BT_SCALE)
    pointer.setZPosition(3)  # Progress is z=2; keep the whole white thumb above it.
    pointer.setPixmap(LoadPixmap(resolveFilename(SCOPE_SKINS, 'MetrixNEO/assets/launcher/volume-thumb.png'), cached=True))
    pointer.resize(eSize(diameter, diameter))

    label = getattr(screen.get('VolumeText'), 'instance', None)
    own_label = label is None
    if own_label:
        window = screen.instance.size()
        left = x + width + 12
        label_height = round(window.height() * 0.625)
        label = eLabel(screen.instance)
        label.setTransparent(1)
        label.setFont(gFont('MenuTitle', round(window.height() * 0.4375)))
        label.setForegroundColor(gRGB(0x00F5FAFD))
        label.setHAlign(eLabel.alignRight)
        label.setVAlign(eLabel.alignCenter)
        label.move(ePoint(left, (window.height() - label_height) // 2))
        label.resize(eSize(max(1, window.width() - left - 14), label_height))
        label.setZPosition(3)
        label.show()

    original = bar.setValue

    def update(value):
        original(value)
        value = max(0, min(100, int(value)))
        previous_style = artwork.style
        style = artwork.set_style(read_settings(profile)["volume_style"])
        if style != previous_style:
            (bar.show if style == "classic" else bar.hide)()
        if style == "classic":
            pointer.move(ePoint(x + round(width * value / 100) - diameter // 2, y + (height - diameter) // 2))
            pointer.show()
            themed_digits = False
        else:
            pointer.hide()
            themed_digits = artwork.set_value(value)
        label.setText("" if themed_digits else str(value))
        label.show()

    bar.setValue = update
    screen._neo_volume_bound = True
    try:
        update(bar.getValue())
    except (AttributeError, TypeError, ValueError):
        pointer.hide()

    def close():
        bar.setValue = original
        pointer.hide()
        if own_label:
            label.hide()
        screen._neo_volume_bound = False

    screen.onClose.append(close)
    screen._neo_volume_widgets = (pointer, label, artwork)
