from PySide2.QtCore import Slot, QObject
from PySide2.QtGui import QClipboard


class ClipboardHelper(QObject):
    """
    Simple wrapper around a QClipboard with methods exposed as Slots for QML use.
    """

    def __init__(self, parent=None):
        super(ClipboardHelper, self).__init__(parent)
        self._clipboard = QClipboard(parent=self)

    @Slot(str)
    def setText(self, value):
        self._clipboard.setText(value)

    @Slot()
    def clear(self):
        self._clipboard.clear()
