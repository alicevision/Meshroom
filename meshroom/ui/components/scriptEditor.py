from PySide6.QtCore import QObject, Slot, QSettings

from io import StringIO
from contextlib import redirect_stdout
import traceback

class ScriptEditorManager(QObject):
    """ Manages the script editor history and logs.
    """

    _GROUP = "ScriptEditor"
    _KEY = "script"

    def __init__(self, parent=None):
        super(ScriptEditorManager, self).__init__(parent=parent)
        self._history = []
        self._index = -1

        self._globals = {}
        self._locals = {}

    # Protected
    def _defaultScript(self):
        """ Returns the default script for the script editor.
        """
        lines = (
            "from meshroom.ui import uiInstance\n",
            "graph = uiInstance.activeProject.graph",
            "for node in graph.nodes:",
            "    print(node.name)"
        )

        return "\n".join(lines)

    def _lastScript(self):
        """ Returns the last script from the user settings.
        """
        settings = QSettings()
        settings.beginGroup(self._GROUP)
        return settings.value(self._KEY)

    # Public
    @Slot(str, result=str)
    def process(self, script):
        """ Execute the provided input script, capture the output from the standard output, and return it. """
        # Saves the state if an exception has occured
        exception = False

        stdout = StringIO()
        with redirect_stdout(stdout):
            try:
                exec(script, self._globals, self._locals)
            except Exception:
                # Update that we have an exception that is thrown
                exception = True
                # Print the backtrace
                traceback.print_exc(file=stdout)

        result = stdout.getvalue().strip()

        # Strip out additional part
        if exception:
            # We know that we're executing the above statement and that caused the exception
            # What we want to show to the user is just the part that happened while executing the script
            # So just split with the last part and show it to the user
            result = result.split("self._locals)", 1)[-1]

        # Add the script to the history and move up the index to the top of history stack
        self._history.append(script)
        self._index = len(self._history)

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

    @Slot(result=str)
    def loadLastScript(self):
        """ Returns the last executed script from the prefs.
        """
        return self._lastScript() or self._defaultScript()

    @Slot(str)
    def saveScript(self, script):
        """ Returns the last executed script from the prefs.

        Args:
            script (str): The script to save.
        """
        settings = QSettings()
        settings.beginGroup(self._GROUP)
        settings.setValue(self._KEY, script)
        settings.sync()
