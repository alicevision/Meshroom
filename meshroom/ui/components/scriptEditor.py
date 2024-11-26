""" Script Editor for Meshroom.
"""
# STD
from io import StringIO
from contextlib import redirect_stdout
import traceback

# Qt
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Property, QObject, Slot, Signal, QSettings


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


class CharFormat(QtGui.QTextCharFormat):
    """ The Char format for the syntax.
    """

    def __init__(self, color, bold=False, italic=False):
        """ Constructor.
        """
        super().__init__()

        self._color = QtGui.QColor()
        self._color.setNamedColor(color)

        # Update the Foreground color
        self.setForeground(self._color)

        # The font characteristics
        if bold:
            self.setFontWeight(QtGui.QFont.Bold)
        if italic:
            self.setFontItalic(True)


class PySyntaxHighlighter(QtGui.QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """

    # Syntax styles that can be shared by all languages
    STYLES = {
        "keyword"   : CharFormat("#9e59b3"),               # Purple
        "operator"  : CharFormat("#2cb8a0"),               # Teal
        "brace"     : CharFormat("#2f807e"),               # Dark Aqua
        "defclass"  : CharFormat("#c9ba49", bold=True),    # Yellow
        "deffunc"   : CharFormat("#4996c9", bold=True),    # Blue
        "string"    : CharFormat("#7dbd39"),               # Greeny
        "comment"   : CharFormat("#8d8d8d", italic=True),  # Dark Grayish
        "self"      : CharFormat("#e6ba43", italic=True),  # Yellow
        "numbers"   : CharFormat("#d47713"),               # Orangish
    }

    # Python keywords
    keywords = (
        "and", "assert", "break", "class", "continue", "def",
        "del", "elif", "else", "except", "exec", "finally",
        "for", "from", "global", "if", "import", "in",
        "is", "lambda", "not", "or", "pass", "print",
        "raise", "return", "try", "while", "yield",
        "None", "True", "False",
    )

    # Python operators
    operators = (
        "=",
        # Comparison
        "==", "!=", "<", "<=", ">", ">=",
        # Arithmetic
        r"\+", "-", r"\*", "/", "//", r"\%", r"\*\*",
        # In-place
        r"\+=", "-=", r"\*=", "/=", r"\%=",
        # Bitwise
        r"\^", r"\|", r"\&", r"\~", r">>", r"<<",
    )

    # Python braces
    braces = (r"\{", r"\}", r"\(", r"\)", r"\[", r"\]")

    def __init__(self, parent=None):
        """ Constructor.

        Keyword Args:
            parent (QObject): The QObject parent from the QML side.
        """
        super().__init__(parent)

        # The Document to highlight
        self._document = None

        # Build a QRegularExpression for each of the pattern
        self._rules = self.__rules()

    # Private
    def __rules(self):
        """ Formatting rules.
        """
        # Set of rules accordind to which the highlight should occur
        rules = []

        # Keyword rules
        rules += [(QtCore.QRegularExpression(r"\b" + w + r"\s"), 0, PySyntaxHighlighter.STYLES["keyword"]) for w in PySyntaxHighlighter.keywords]
        # Operator rules
        rules += [(QtCore.QRegularExpression(o), 0, PySyntaxHighlighter.STYLES["operator"]) for o in PySyntaxHighlighter.operators]
        # Braces
        rules += [(QtCore.QRegularExpression(b), 0, PySyntaxHighlighter.STYLES["brace"]) for b in PySyntaxHighlighter.braces]

        # All other rules
        rules += [
            # self
            (QtCore.QRegularExpression(r'\bself\b'), 0, PySyntaxHighlighter.STYLES["self"]),

            # 'def' followed by an identifier
            (QtCore.QRegularExpression(r'\bdef\b\s*(\w+)'), 1, PySyntaxHighlighter.STYLES["deffunc"]),
            # 'class' followed by an identifier
            (QtCore.QRegularExpression(r'\bclass\b\s*(\w+)'), 1, PySyntaxHighlighter.STYLES["defclass"]),

            # Numeric literals
            (QtCore.QRegularExpression(r'\b[+-]?[0-9]+[lL]?\b'), 0, PySyntaxHighlighter.STYLES["numbers"]),
            (QtCore.QRegularExpression(r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b'), 0, PySyntaxHighlighter.STYLES["numbers"]),
            (QtCore.QRegularExpression(r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b'), 0, PySyntaxHighlighter.STYLES["numbers"]),

            # Double-quoted string, possibly containing escape sequences
            (QtCore.QRegularExpression(r'"[^"\\]*(\\.[^"\\]*)*"'), 0, PySyntaxHighlighter.STYLES["string"]),
            # Single-quoted string, possibly containing escape sequences
            (QtCore.QRegularExpression(r"'[^'\\]*(\\.[^'\\]*)*'"), 0, PySyntaxHighlighter.STYLES["string"]),

            # From '#' until a newline
            (QtCore.QRegularExpression(r'#[^\n]*'), 0, PySyntaxHighlighter.STYLES['comment']),
        ]

        return rules

    def highlightBlock(self, text):
        """ Applies syntax highlighting to the given block of text.

        Args:
            text (str): The text to highlight.
        """
        # Do other syntax formatting
        for expression, nth, _format in self._rules:
            # fetch the index of the expression in text
            match = expression.match(text, 0)
            index = match.capturedStart()

            while index >= 0:
                # We actually want the index of the nth match
                index = match.capturedStart(nth)
                length = len(match.captured(nth))
                self.setFormat(index, length, _format)
                # index = expression.indexIn(text, index + length)
                match = expression.match(text, index + length)
                index = match.capturedStart()

    def textDoc(self):
        """ Returns the document being highlighted.
        """
        return self._document

    def setTextDocument(self, document):
        """ Sets the document on the Highlighter.

        Args:
            document (QtQuick.QQuickTextDocument): The document from the QML engine.
        """
        # If the same document is provided again
        if document == self._document:
            return

        # Update the class document
        self._document = document

        # Set the document on the highlighter
        self.setDocument(self._document.textDocument())

        # Emit that the document is now changed
        self.textDocumentChanged.emit()

    # Signals
    textDocumentChanged = Signal()

    # Property
    textDocument = Property(QObject, textDoc, setTextDocument, notify=textDocumentChanged)
