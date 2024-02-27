from PySide6.QtCore import Slot, QObject
from PySide6.QtGui import QClipboard


class ClipboardHelper(QObject):
    """
    Simple wrapper around a QClipboard with methods exposed as Slots for QML use.
    """

    def __init__(self, parent=None):
        super(ClipboardHelper, self).__init__(parent)
        self._clipboard = QClipboard(parent=self)

    def __del__(self):
        # Workaround to avoid the "QXcbClipboard: Unable to receive an event from the clipboard manager
        # in a reasonable time" that will hold up the application when exiting if the clipboard has been
        # used at least once and its content exceeds a certain size (on X11/XCB).
        # The bug occurs in QClipboard and is present on all Qt5 versions.
        self.clear()

    @Slot(str)
    def setText(self, value):
        self._clipboard.setText(value)

    @Slot(result=str)
    def getText(self):
        return self._clipboard.text()

    @Slot()
    def clear(self):
        self._clipboard.clear()
