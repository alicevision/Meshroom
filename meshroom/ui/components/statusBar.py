from PySide6.QtCore import QObject, Signal


class MessageController(QObject):
    """
    Handles messages sent from the Python side to the StatusBar component
    """
    
    message = Signal(str, str, int)
    
    def __init__(self, parent):
        super().__init__(parent)
    
    def sendMessage(self, msg, status, duration):
        """ Sends a message that will be displayed on the status bar """
        self.message.emit(msg, status, duration)
