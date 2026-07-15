import os
import time

from PySide6.QtCore import QFileSystemWatcher, QUrl, Slot, QTimer, Property, QObject
from PySide6.QtQml import QQmlApplicationEngine
try:
    from PySide6 import shiboken6
except Exception:
    import shiboken6


class QmlInstantEngine(QObject):
    """
    QmlInstantEngine is a utility class helping to develop QML applications.
    It reloads itself whenever one of the watched source files is modified.
    As it consumes resources, make sure to disable file watching in production mode.
    """

    def __init__(self, sourceFile, setupEngine, watching=True, verbose=False, parent=None):
        """
        sourceFile  -- Main QML file.
        setupEngine -- Callback to call on reload after creating the engine (for hot-reload).
        watching    -- Defines whether the watcher is active (default: True)
        verbose     -- if True, output log information (default: False)
        """
        super().__init__(parent)

        self._fileWatcher = QFileSystemWatcher()  # Internal Qt File Watcher
        self._sourceFile = str(sourceFile) or ""
        self._watchedFiles = []  # Internal watched files list
        self._verbose = verbose    # Verbose bool
        self._watching = False
        self._extensions = ["qml", "js"]

        # Callback to call for the engine setup (set the context properties, etc)
        self._setupEngine = setupEngine
        self._engine = QQmlApplicationEngine()
        self._rootItem = None

        # Add a single shot timer to launch the reload after all events are processed
        self._debounceTimer = QTimer(singleShot=True, interval=100)
        self._debounceTimer.timeout.connect(self.reload)

        # Update the watching status
        self.setWatching(watching)

    def __getattr__(self, name):
        engine = self.__dict__.get("_engine")
        if engine is not None and hasattr(engine, name):
            return getattr(engine, name)
        raise AttributeError(f"{type(self).__name__!r} object has no attribute {name!r}")

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
            raise ValueError(f"addFile: file {filename} does not exist.")

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
            raise RuntimeError(f"addFilesFromDirectory : {dirname} is not a valid directory.")

        if recursive:
            for dirpath, dirnames, filenames in os.walk(dirname):
                for filename in filenames:
                    # Removing the starting dot from extension
                    if os.path.splitext(filename)[1][1:] in self._extensions:
                        self.addFile(os.path.join(dirpath, filename))
        else:
            filenames = os.listdir(dirname)
            filenames = [os.path.join(dirname, f) for f in filenames if
                         os.path.splitext(f)[1][1:] in self._extensions]
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
        # Re-add file before debounce
        if os.path.isfile(filepath):
            self._fileWatcher.addPath(filepath)
        self._debounceTimer.start()

    def rootContext(self):
        """ Context of the currently-live engine (None before the first reload). """
        return self._engine.rootContext() if self._engine else None

    @property
    def engine(self):
        return self._engine

    @property
    def rootItem(self):
        return self._rootItem

    def reload(self):
        print(f"Reloading {self._sourceFile}")

        # Preserve window geometry across the swap.
        oldPos, oldSize = None, None
        if self._rootItem is not None and shiboken6.isValid(self._rootItem):
            try:
                oldPos = self._rootItem.position()
                oldSize = self._rootItem.size()
            except AttributeError:
                pass

        # Destroy old root item and engine before building the new one.
        if self._rootItem is not None and shiboken6.isValid(self._rootItem):
            shiboken6.delete(self._rootItem)
        self._rootItem = None

        if self._engine is not None and shiboken6.isValid(self._engine):
            shiboken6.delete(self._engine)
        self._engine = None

        # Build the new engine and load.
        engine = QQmlApplicationEngine()
        self._setupEngine(engine)

        def onObjectCreated(root, url):
            if root is None:
                print(f"Failed to load {url.toString()} - check QML warnings above.")
                return
            self._rootItem = root
            if oldPos is not None:
                root.setPosition(oldPos)
            if oldSize is not None:
                root.resize(oldSize)

        engine.objectCreated.connect(onObjectCreated)
        engine.load(QUrl.fromLocalFile(self._sourceFile))
        engine.objectCreated.disconnect(onObjectCreated)

        self._engine = engine

    def clearComponentCache(self):
        if self._engine:
            self._engine.clearComponentCache()

    def collectGarbage(self):
        if self._engine:
            self._engine.collectGarbage()

    def deleteLater(self):
        if self._engine:
            self._engine.deleteLater()
        super().deleteLater()


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
