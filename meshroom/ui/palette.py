from PySide6.QtCore import QObject, Qt, Slot, Property, Signal
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QApplication


class PaletteManager(QObject):
    """
    Manages QApplication's palette and provides a toggle between a dark and a light theme.
    """
    def __init__(self, qmlEngine, parent=None):
        super(PaletteManager, self).__init__(parent)
        self.qmlEngine = qmlEngine
        darkPalette = QPalette()
        window = QColor(50, 52, 55)
        text = QColor(200, 200, 200)
        disabledText = text.darker(170)
        base = window.darker(150)
        button = window.lighter(115)
        highlight = QColor(42, 130, 218)
        dark = window.darker(170)

        darkPalette.setColor(QPalette.Window, window)
        darkPalette.setColor(QPalette.WindowText, text)
        darkPalette.setColor(QPalette.Disabled, QPalette.WindowText, disabledText)
        darkPalette.setColor(QPalette.Base, base)
        darkPalette.setColor(QPalette.AlternateBase, QColor(46, 47, 48))
        darkPalette.setColor(QPalette.ToolTipBase, base)
        darkPalette.setColor(QPalette.ToolTipText, text)
        darkPalette.setColor(QPalette.Text, text)
        darkPalette.setColor(QPalette.Disabled, QPalette.Text, disabledText)
        darkPalette.setColor(QPalette.Button, button)
        darkPalette.setColor(QPalette.ButtonText, text)
        darkPalette.setColor(QPalette.Disabled, QPalette.ButtonText, disabledText)

        darkPalette.setColor(QPalette.Mid, button.lighter(120))
        darkPalette.setColor(QPalette.Highlight, highlight)
        darkPalette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
        darkPalette.setColor(QPalette.HighlightedText, Qt.white)
        darkPalette.setColor(QPalette.Disabled, QPalette.HighlightedText, QColor(127, 127, 127))
        darkPalette.setColor(QPalette.Shadow, Qt.black)
        darkPalette.setColor(QPalette.Link, highlight.lighter(130))

        self.darkPalette = darkPalette
        self.defaultPalette = QApplication.instance().palette()
        self.togglePalette()

    @Slot()
    def togglePalette(self):
        app = QApplication.instance()
        if app.palette() == self.darkPalette:
            app.setPalette(self.defaultPalette)
        else:
            app.setPalette(self.darkPalette)
        if self.qmlEngine.rootObjects():
            self.qmlEngine.reload()
        self.paletteChanged.emit()

    paletteChanged = Signal()
    palette = Property(QPalette, lambda self: QApplication.instance().palette(), notify=paletteChanged)
    alternateBase = Property(QColor, lambda self: self.palette.color(QPalette.AlternateBase), notify=paletteChanged)
    base = Property(QColor, lambda self: self.palette.color(QPalette.Base), notify=paletteChanged)
    button = Property(QColor, lambda self: self.palette.color(QPalette.Button), notify=paletteChanged)
    buttonText = Property(QColor, lambda self: self.palette.color(QPalette.ButtonText), notify=paletteChanged)
    disabledButtonText = Property(QColor, lambda self: self.palette.color(QPalette.Disabled, QPalette.ButtonText), notify=paletteChanged)
    highlight = Property(QColor, lambda self: self.palette.color(QPalette.Highlight), notify=paletteChanged)
    disabledHighlight = Property(QColor, lambda self: self.palette.color(QPalette.Disabled, QPalette.Highlight), notify=paletteChanged)
    highlightedText = Property(QColor, lambda self: self.palette.color(QPalette.HighlightedText), notify=paletteChanged)
    disabledHighlightedText = Property(QColor, lambda self: self.palette.color(QPalette.Disabled, QPalette.HighlightedText), notify=paletteChanged)
    link = Property(QColor, lambda self: self.palette.color(QPalette.Link), notify=paletteChanged)
    mid = Property(QColor, lambda self: self.palette.color(QPalette.Mid), notify=paletteChanged)
    shadow = Property(QColor, lambda self: self.palette.color(QPalette.Shadow), notify=paletteChanged)
    text = Property(QColor, lambda self: self.palette.color(QPalette.Text), notify=paletteChanged)
    disabledText = Property(QColor, lambda self: self.palette.color(QPalette.Disabled, QPalette.Text), notify=paletteChanged)
    toolTipBase = Property(QColor, lambda self: self.palette.color(QPalette.ToolTipBase), notify=paletteChanged)
    toolTipText = Property(QColor, lambda self: self.palette.color(QPalette.ToolTipText), notify=paletteChanged)
    window = Property(QColor, lambda self: self.palette.color(QPalette.Window), notify=paletteChanged)
    windowText = Property(QColor, lambda self: self.palette.color(QPalette.WindowText), notify=paletteChanged)
    disabledWindowText = Property(QColor, lambda self: self.palette.color(QPalette.Disabled, QPalette.WindowText), notify=paletteChanged)
