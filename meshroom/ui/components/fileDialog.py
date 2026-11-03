from enum import IntEnum
import os

from PySide6.QtCore import QDir, QObject, QSettings, QUrl, Property, QEnum, Signal, Slot, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFileDialog

from meshroom.env import EnvVar


def parseGtkBookmarks(content):
    """
    Parse the content of a GTK bookmarks file.

    Each line is of the form "file:///path/to/folder [optional label]".

    Args:
        content (str): the content of the bookmarks file.

    Returns:
        list[str]: the local paths of the "file://" bookmarks, in order.
    """
    paths = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        url = QUrl(line.split(" ", 1)[0])
        if url.isLocalFile():
            paths.append(url.toLocalFile())
    return paths


def gtkBookmarks():
    """ Return the local paths bookmarked in the GTK file chooser (Linux), if any. """
    configHome = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    for bookmarksFile in (os.path.join(configHome, "gtk-3.0", "bookmarks"), os.path.expanduser("~/.gtk-bookmarks")):
        try:
            with open(bookmarksFile, encoding="utf-8") as f:
                return parseGtkBookmarks(f.read())
        except OSError:
            continue
    return []


def readSettingsArray(group, array, key):
    """ Return the values of `key` stored in the QSettings array `group/array`. """
    values = []
    settings = QSettings()
    settings.beginGroup(group)
    size = settings.beginReadArray(array)
    for i in range(size):
        settings.setArrayIndex(i)
        value = settings.value(key)
        if value:
            values.append(value)
    settings.endArray()
    settings.endGroup()
    return values


class FileDialog(QObject):
    """
    File dialog exposed to QML, with an API close to Qt.labs.platform's FileDialog.

    It relies on the Qt Widgets QFileDialog. On Linux, it is non-native by default (native GTK dialogs
    used to crash) and its sidebar is filled with the standard locations, the GTK bookmarks, the recent
    project and images folders, and the bookmarks added by the user in the dialog, which are persisted
    in the QSettings. On Windows and macOS, the native dialog is used, with the system bookmarks.
    This can be changed with the MESHROOM_NATIVE_FILE_DIALOGS environment variable.
    """

    @QEnum
    class FileMode(IntEnum):
        OpenFile = 0
        OpenFiles = 1
        SaveFile = 2

    @QEnum
    class DialogResult(IntEnum):
        Rejected = 0
        Accepted = 1

    _settingsGroup = "FileDialog"
    _maxRecentFolders = 5

    def __init__(self, parent=None):
        super().__init__(parent)
        self._title = ""
        self._nameFilters = []
        self._defaultSuffix = ""
        self._fileMode = FileDialog.FileMode.OpenFile
        self._folder = QUrl()
        self._currentFiles = []
        self._dialog = None

    @staticmethod
    def _userBookmarks():
        return [QUrl(url) for url in readSettingsArray(FileDialog._settingsGroup, "Bookmarks", "url")]

    @staticmethod
    def _saveUserBookmarks(urls):
        settings = QSettings()
        settings.beginGroup(FileDialog._settingsGroup)
        settings.beginWriteArray("Bookmarks")
        for i, url in enumerate(urls):
            settings.setArrayIndex(i)
            settings.setValue("url", url.toString())
        settings.endArray()
        settings.endGroup()

    @staticmethod
    def _defaultSidebarUrls():
        """ Return the sidebar urls that are not user bookmarks: standard locations, GTK bookmarks, recent folders. """
        recentProjectFolders = [os.path.dirname(p) for p in readSettingsArray("RecentFiles", "Projects", "filepath")]
        recentImagesFolders = [QUrl(p).toLocalFile() if p.startswith("file:") else p
                               for p in readSettingsArray("RecentFiles", "ImagesFolders", "path")]
        paths = [QDir.homePath(), QDir.rootPath()] + gtkBookmarks() \
            + recentProjectFolders[:FileDialog._maxRecentFolders] + recentImagesFolders[:FileDialog._maxRecentFolders]
        urls = []
        for path in paths:
            url = QUrl.fromLocalFile(os.path.normpath(path))
            if os.path.isdir(path) and url not in urls:
                urls.append(url)
        return urls

    @Slot()
    def open(self):
        """ Open the dialog (non-blocking): `accepted` or `rejected` is emitted when it is closed. """
        if self._dialog:
            self._dialog.raise_()
            return
        dialog = QFileDialog(None, self._title, self._folder.toLocalFile())
        native = EnvVar.get(EnvVar.MESHROOM_NATIVE_FILE_DIALOGS)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, not native)
        if self._nameFilters:
            dialog.setNameFilters(self._nameFilters)
        if self._fileMode == FileDialog.FileMode.SaveFile:
            dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            dialog.setFileMode(QFileDialog.FileMode.AnyFile)
            dialog.setDefaultSuffix(self._defaultSuffix.lstrip("."))
        elif self._fileMode == FileDialog.FileMode.OpenFiles:
            dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        else:
            dialog.setFileMode(QFileDialog.FileMode.ExistingFile)

        # Native dialogs have their own sidebar with the system bookmarks
        if not native:
            defaultUrls = FileDialog._defaultSidebarUrls()
            userUrls = [url for url in FileDialog._userBookmarks() if url not in defaultUrls]
            dialog.setSidebarUrls(defaultUrls + userUrls)

        # Keep the dialog above the Meshroom window and block it while opened
        parentWindow = QGuiApplication.focusWindow() or next((w for w in QGuiApplication.topLevelWindows() if w.isVisible()), None)
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        dialog.winId()
        if parentWindow and dialog.windowHandle():
            dialog.windowHandle().setTransientParent(parentWindow)

        dialog.finished.connect(self._onFinished)
        self._dialog = dialog
        dialog.show()

    def _onFinished(self, result):
        dialog = self._dialog
        self._dialog = None
        if dialog.testOption(QFileDialog.Option.DontUseNativeDialog):
            # Persist the folders added to the sidebar by the user (drag and drop) or removed from it
            defaultUrls = FileDialog._defaultSidebarUrls()
            FileDialog._saveUserBookmarks([url for url in dialog.sidebarUrls() if url not in defaultUrls])
        dialog.deleteLater()

        if result == QFileDialog.DialogCode.Accepted:
            self._currentFiles = dialog.selectedUrls()
            self.currentFilesChanged.emit()
            self.accepted.emit()
        else:
            self.rejected.emit()

    def _setTitle(self, title):
        if title != self._title:
            self._title = title
            self.titleChanged.emit()

    def _setNameFilters(self, nameFilters):
        if nameFilters != self._nameFilters:
            self._nameFilters = list(nameFilters)
            self.nameFiltersChanged.emit()

    def _setDefaultSuffix(self, defaultSuffix):
        if defaultSuffix != self._defaultSuffix:
            self._defaultSuffix = defaultSuffix
            self.defaultSuffixChanged.emit()

    def _setFileMode(self, fileMode):
        if fileMode != self._fileMode:
            self._fileMode = FileDialog.FileMode(fileMode)
            self.fileModeChanged.emit()

    def _setFolder(self, folder):
        if folder != self._folder:
            self._folder = folder
            self.folderChanged.emit()

    def _currentFile(self):
        return self._currentFiles[0] if self._currentFiles else QUrl()

    def _setCurrentFile(self, currentFile):
        self._currentFiles = [currentFile]
        self.currentFilesChanged.emit()

    accepted = Signal()
    rejected = Signal()
    titleChanged = Signal()
    nameFiltersChanged = Signal()
    defaultSuffixChanged = Signal()
    fileModeChanged = Signal()
    folderChanged = Signal()
    currentFilesChanged = Signal()

    title = Property(str, lambda self: self._title, _setTitle, notify=titleChanged)
    nameFilters = Property("QStringList", lambda self: self._nameFilters, _setNameFilters, notify=nameFiltersChanged)
    defaultSuffix = Property(str, lambda self: self._defaultSuffix, _setDefaultSuffix, notify=defaultSuffixChanged)
    fileMode = Property(int, lambda self: int(self._fileMode), _setFileMode, notify=fileModeChanged)
    folder = Property(QUrl, lambda self: self._folder, _setFolder, notify=folderChanged)
    currentFile = Property(QUrl, _currentFile, _setCurrentFile, notify=currentFilesChanged)
    currentFiles = Property("QVariantList", lambda self: self._currentFiles, notify=currentFilesChanged)
