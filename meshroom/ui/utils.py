import os
import time

from PySide6.QtCore import QFileSystemWatcher, QUrl, Slot, QTimer, Property, QObject
from PySide6.QtQml import QQmlApplicationEngine
try:
    from PySide6 import shiboken6
except Exception:
    import shiboken6


class QmlInstantEngine(QQmlApplicationEngine):
    """
    QmlInstantEngine is an utility class helping developing QML applications.
    It reloads itself whenever one of the watched source files is modified.
    As it consumes resources, make sure to disable file watching in production mode.
    """

    def __init__(self, sourceFile="", watching=True, verbose=False, parent=None):
        """
        watching -- Defines whether the watcher is active (default: True)
        verbose -- if True, output log infos (default: False)
        """
        super(QmlInstantEngine, self).__init__(parent)

        self._fileWatcher = QFileSystemWatcher()  # Internal Qt File Watcher
        self._sourceFile = ""
        self._watchedFiles = []  # Internal watched files list
        self._verbose = verbose  # Verbose bool
        self._watching = False  #
        self._extensions = ["qml", "js"]  # File extensions that defines files to watch when adding a folder

        self._rootItem = None

        def onObjectCreated(root, url):
            if not root:
                return
            # Restore root item geometry
            if self._rootItem:
                root.setGeometry(self._rootItem.geometry())
                self._rootItem.deleteLater()
            self._rootItem = root

        self.objectCreated.connect(onObjectCreated)

        # Update the watching status
        self.setWatching(watching)

        if sourceFile:
            self.load(sourceFile)

    def load(self, sourceFile):
        self._sourceFile = sourceFile
        super(QmlInstantEngine, self).load(sourceFile)

    def setWatching(self, watchValue):
        """
        Enable (True) or disable (False) the file watching.
        Tip: file watching should be enable only when developing.
        """
        if self._watching is watchValue:
            return

        self._watching = watchValue
        # Enable the watcher
        if self._watching:
            # 1. Add internal list of files to the internal Qt File Watcher
            self.addFiles(self._watchedFiles)
            # 2. Connect 'filechanged' signal
            self._fileWatcher.fileChanged.connect(self.onFileChanged)

        # Disabling the watcher
        else:
            # 1. Remove all files in the internal Qt File Watcher
            self._fileWatcher.removePaths(self._watchedFiles)
            # 2. Disconnect 'filechanged' signal
            self._fileWatcher.fileChanged.disconnect(self.onFileChanged)

    @property
    def watchedExtensions(self):
        """ Returns the list of extensions used when using addFilesFromDirectory. """
        return self._extensions

    @watchedExtensions.setter
    def watchedExtensions(self, extensions):
        """ Set the list of extensions to search for when using addFilesFromDirectory. """
        self._extensions = extensions

    def setVerbose(self, verboseValue):
        """ Activate (True) or deactivate (False) the verbose. """
        self._verbose = verboseValue

    def addFile(self, filename):
        """
        Add the given 'filename' to the watched files list.
        'filename' can be an absolute or relative path (str and QUrl accepted)
        """
        # Deal with QUrl type
        # NOTE: happens when using the source() method on a QQuickView
        if isinstance(filename, QUrl):
            filename = filename.path()

        # Make sure the file exists
        if not os.path.isfile(filename):
            raise ValueError("addFile: file %s doesn't exist." % filename)

        # Return if the file is already in our internal list
        if filename in self._watchedFiles:
            return

        # Add this file to the internal files list
        self._watchedFiles.append(filename)
        # And, if watching is active, add it to the internal watcher as well
        if self._watching:
            if self._verbose:
                print("instantcoding: addPath", filename)
            self._fileWatcher.addPath(filename)

    def addFiles(self, filenames):
        """
        Add the given 'filenames' to the watched files list.
        filenames -- a list of absolute or relative paths (str and QUrl accepted)
        """
        # Convert to list
        if not isinstance(filenames, list):
            filenames = [filenames]

        for filename in filenames:
            self.addFile(filename)

    def addFilesFromDirectory(self, dirname, recursive=False):
        """
        Add files from the given directory name 'dirname'.
        dirname -- an absolute or a relative path
        recursive -- if True, will search inside each subdirectories recursively.
        """
        if not os.path.isdir(dirname):
            raise RuntimeError("addFilesFromDirectory : %s is not a valid directory." % dirname)

        if recursive:
            for dirpath, dirnames, filenames in os.walk(dirname):
                for filename in filenames:
                    # Removing the starting dot from extension
                    if os.path.splitext(filename)[1][1:] in self._extensions:
                        self.addFile(os.path.join(dirpath, filename))
        else:
            filenames = os.listdir(dirname)
            filenames = [os.path.join(dirname, filename) for filename in filenames if
                         os.path.splitext(filename)[1][1:] in self._extensions]
            self.addFiles(filenames)

    def removeFile(self, filename):
        """
        Remove the given 'filename' from the watched file list.
        Tip: make sure to use relative or absolute path according to how you add this file.
        """
        if filename in self._watchedFiles:
            self._watchedFiles.remove(filename)
        if self._watching:
            self._fileWatcher.removePath(filename)

    def getRegisteredFiles(self):
        """ Returns the list of watched files """
        return self._watchedFiles

    @Slot(str)
    def onFileChanged(self, filepath):
        """ Handle changes in a watched file. """
        if filepath not in self._watchedFiles:
            # could happen if a file has just been reloaded
            # and has not been re-added yet to the watched files
            return

        if self._verbose:
            print("Source file changed : ", filepath)
        # Clear the QQuickEngine cache
        self.clearComponentCache()
        # Remove the modified file from the watched list
        self.removeFile(filepath)
        cptTry = 0

        # Make sure file is available before doing anything
        # NOTE: useful to handle editors (Qt Creator) that deletes the source file and
        #       creates a new one when saving
        while not os.path.exists(filepath) and cptTry < 10:
            time.sleep(0.1)
            cptTry += 1

        self.reload()

        # Finally, re-add the modified file to the watch system
        # after a short cooldown to avoid multiple consecutive reloads
        QTimer.singleShot(200, lambda: self.addFile(filepath))

    def reload(self):
        print("Reloading {}".format(self._sourceFile))
        self.load(self._sourceFile)


def makeProperty(T, attributeName, notify=None, resetOnDestroy=False):
    """
    Shortcut function to create a Qt Property with generic getter and setter.

    Getter returns the underlying attribute value.
    Setter sets and emit notify signal only if the given value is different from the current one.

    Args:
        T (type): the type of the property
        attributeName (str): the name of underlying instance attribute to get/set
        notify (Signal): the notify signal; if None, property will be constant
        resetOnDestroy (bool): Only applicable for QObject-type properties.
                               Whether to reset property to None when current value gets destroyed.


    Examples:
        class Foo(QObject):
            _bar = 10
            barChanged = Signal()
            # read/write
            bar = makeProperty(int, "_bar", notify=barChanged)
            # read only (constant)
            bar = makeProperty(int, "_bar")

    Returns:
        Property: the created Property
    """
    def setter(instance, value):
        """ Generic setter. """
        currentValue = getattr(instance, attributeName)
        if currentValue == value:
            return

        resetCallbackName = '__reset__' + attributeName
        if resetOnDestroy and not hasattr(instance, resetCallbackName):
            # store reset callback on instance, only way to keep a reference to this function
            # that can be used for destroyed signal (dis)connection
            setattr(instance, resetCallbackName, lambda self=instance, *args: setter(self, None))
        resetCallback = getattr(instance, resetCallbackName, None)

        if resetCallback and currentValue and shiboken6.isValid(currentValue):
            currentValue.destroyed.disconnect(resetCallback)
        setattr(instance, attributeName, value)
        if resetCallback and value:
            value.destroyed.connect(resetCallback)
        getattr(instance, signalName(notify)).emit()

    def getter(instance):
        """ Generic getter. """
        return getattr(instance, attributeName)

    def signalName(signalInstance):
        """ Get signal name from instance. """
        # string representation contains trailing '()', remove it
        return str(signalInstance)[:-2]

    if resetOnDestroy and not issubclass(T, QObject):
        raise RuntimeError("destroyCallback can only be used with QObject-type properties.")
    if notify:
        return Property(T, getter, setter, notify=notify)
    else:
        return Property(T, getter, constant=True)
