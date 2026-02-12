import json
from PySide6.QtCore import QObject
from datetime import datetime
from meshroom.common import Signal, Slot, Property


class Message:
    def __init__(self, msg, status=None):
        self.msg = msg
        self.status = status or "info"
        self.date = datetime.now()

    def dateStr(self, fullDate=False):
        dateFormat = "%H:%M:%S"
        if fullDate:
            dateFormat = "%Y-%m-%d %H:%M:%S.%f"
        return self.date.strftime(dateFormat)


class MessageController(QObject):
    """
    Handles messages sent from the Python side to the StatusBar component.
    """

    message = Signal(str, str, int)
    messagesChanged = Signal()  # Signal to notify when messages list changes

    def __init__(self, parent):
        super().__init__(parent)
        self._messages = []

    def sendMessage(self, msg, status, duration):
        """ Sends a message that will be displayed on the status bar. """
        self.message.emit(msg, status, duration)

    @Slot(str, str)
    def storeMessage(self, msg, status):
        """ Adds a new message in the stack. """
        self._messages.append(Message(msg, status or "info"))
        self.messagesChanged.emit()  # Notify QML that messages have changed

    def _getMessagesDict(self, fullDate=False):
        """ Get a dict with all stored messages. """
        messages = []
        for msg in self._messages:
            messages.append({
                "status": msg.status,
                "date": msg.dateStr(fullDate),
                "text": msg.msg,
            })
        return messages

    def getMessages(self):
        """
        Get the messages with simple date information.
        Reverse the list to make sure we see the most recent item on top
        """
        return self._getMessagesDict()[::-1]

    @Slot(result=str)
    def getMessagesAsString(self):
        """
        Return messages for clipboard copy.
        .. note::
           Could also do `json.dumps(self._getMessagesDict(fullDate=True), indent=4)`
        """
        messages = []
        for msg in self._messages:
            messages.append(f"{msg.dateStr(True)} [{msg.status.upper():<7}] {msg.msg}")
        return "\n".join(messages)

    @Slot()
    def clearMessages(self):
        """ Clear all stored messages. """
        self._messages.clear()
        self.messagesChanged.emit()

    # Property to expose messages to QML
    messages = Property("QVariantList", getMessages, notify=messagesChanged)
