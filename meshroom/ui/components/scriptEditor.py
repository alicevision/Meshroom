from PySide2.QtCore import QObject, Slot

from io import StringIO
from contextlib import redirect_stdout

class ScriptEditorManager(QObject):

    def __init__(self, parent=None):
        super(ScriptEditorManager, self).__init__(parent=parent)
        self._history = []
        self._index = -1

        self._globals = {}
        self._locals = {}


    @Slot(str, result=str)
    def process(self, script):
        """ Execute the provided input script, capture the output from the standard output, and return it. """
        stdout = StringIO()
        with redirect_stdout(stdout):
            try:
                exec(script, self._globals, self._locals)
            except Exception as exception:
                # Format and print the exception to stdout, which will be captured
                print("{}: {}".format(type(exception).__name__, exception))

        result = stdout.getvalue().strip()

        # Add the script to the history and move up the index
        self._history.append(script)
        self._index = self._index + 1

        return result

    @Slot()
    def clearHistory(self):
        """ Clear the list of executed scripts and reset the index. """
        self._history = []
        self._index = -1

    @Slot(result=str)
    def getNextScript(self):
        """ Get the next entry in the history of executed scripts and update the index adequately.
            If there is no next entry, return an empty string. """
        if self._index + 1 < len(self._history) and len(self._history) > 0:
            self._index = self._index + 1
            return self._history[self._index]
        return ""

    @Slot(result=str)
    def getPreviousScript(self):
        """ Get the previous entry in the history of executed scripts and update the index adequately.
            If there is no previous entry, return an empty string. """
        if self._index - 1 >= 0 and self._index - 1 < len(self._history):
            self._index = self._index - 1
            return self._history[self._index]
        elif self._index == 0 and len(self._history):
            return self._history[self._index]
        return ""
