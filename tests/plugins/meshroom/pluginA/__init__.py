import webbrowser


def _openDocumentation():
    webbrowser.open("https://example.com/docs")


def _reportIssue():
    webbrowser.open("https://example.com/issues")


def register(plugin):
    plugin.addMenuAction("Plugin Documentation", _openDocumentation, "Open plugin documentation")
    plugin.addMenuAction("Report Issue", _reportIssue)
