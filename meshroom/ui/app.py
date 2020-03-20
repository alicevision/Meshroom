import logging
import os
import argparse

from PySide2.QtCore import Qt, QUrl, Slot, QJsonValue, Property, Signal, qInstallMessageHandler, QtMsgType, QSettings
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication

import meshroom
from meshroom.core import nodesDesc
from meshroom.ui import components
from meshroom.ui.components.clipboard import ClipboardHelper
from meshroom.ui.components.filepath import FilepathHelper
from meshroom.ui.components.scene3D import Scene3DHelper
from meshroom.ui.palette import PaletteManager
from meshroom.ui.reconstruction import Reconstruction
from meshroom.ui.utils import QmlInstantEngine


class MessageHandler(object):
    """
    MessageHandler that translates Qt logs to Python logging system.
    Also contains and filters a list of blacklisted QML warnings that end up in the
    standard error even when setOutputWarningsToStandardError is set to false on the engine.
    """

    outputQmlWarnings = bool(os.environ.get("MESHROOM_OUTPUT_QML_WARNINGS", False))

    logFunctions = {
        QtMsgType.QtDebugMsg: logging.debug,
        QtMsgType.QtWarningMsg: logging.warning,
        QtMsgType.QtInfoMsg: logging.info,
        QtMsgType.QtFatalMsg: logging.fatal,
        QtMsgType.QtCriticalMsg: logging.critical,
        QtMsgType.QtSystemMsg: logging.critical
    }

    # Warnings known to be inoffensive and related to QML but not silenced
    # even when 'MESHROOM_OUTPUT_QML_WARNINGS' is set to False
    qmlWarningsBlacklist = (
        'Failed to download scene at QUrl("")',
        'QVariant(Invalid) Please check your QParameters',
        'Texture will be invalid for this frame',
    )

    @classmethod
    def handler(cls, messageType, context, message):
        """ Message handler remapping Qt logs to Python logging system. """
        # discard blacklisted Qt messages related to QML when 'output qml warnings' is set to false
        if not cls.outputQmlWarnings and any(w in message for w in cls.qmlWarningsBlacklist):
            return
        MessageHandler.logFunctions[messageType](message)


class MeshroomApp(QApplication):
    """ Meshroom UI Application. """
    def __init__(self, args):
        QtArgs = [args[0], '-style', 'fusion'] + args[1:]  # force Fusion style by default

        parser = argparse.ArgumentParser(prog=args[0], description='Launch Meshroom UI.', add_help=True)

        parser.add_argument('project', metavar='PROJECT', type=str, nargs='?',
                            help='Meshroom project file (e.g. myProject.mg) or folder with images to reconstruct.')
        parser.add_argument('-i', '--import', metavar='IMAGES/FOLDERS', type=str, nargs='*',
                            help='Import images or folder with images to reconstruct.')
        parser.add_argument('-I', '--importRecursive', metavar='FOLDERS', type=str, nargs='*',
                            help='Import images to reconstruct from specified folder and sub-folders.')
        parser.add_argument('-s', '--save', metavar='PROJECT.mg', type=str, default='',
                            help='Save the created scene.')
        parser.add_argument('-p', '--pipeline', metavar='MESHROOM_FILE/photogrammetry/hdri', type=str, default=os.environ.get("MESHROOM_DEFAULT_PIPELINE", "photogrammetry"),
                            help='Override the default Meshroom pipeline with this external graph.')
        parser.add_argument("--verbose", help="Verbosity level", default='warning',
                            choices=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],)

        args = parser.parse_args(args[1:])

        logStringToPython = {
            'fatal': logging.FATAL,
            'error': logging.ERROR,
            'warning': logging.WARNING,
            'info': logging.INFO,
            'debug': logging.DEBUG,
            'trace': logging.DEBUG,
        }
        logging.getLogger().setLevel(logStringToPython[args.verbose])

        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

        super(MeshroomApp, self).__init__(QtArgs)

        self.setOrganizationName('AliceVision')
        self.setApplicationName('Meshroom')
        self.setApplicationVersion(meshroom.__version_name__)

        font = self.font()
        font.setPointSize(9)
        self.setFont(font)

        pwd = os.path.dirname(__file__)
        self.setWindowIcon(QIcon(os.path.join(pwd, "img/meshroom.svg")))

        # QML engine setup
        qmlDir = os.path.join(pwd, "qml")
        url = os.path.join(qmlDir, "main.qml")
        self.engine = QmlInstantEngine()
        self.engine.addFilesFromDirectory(qmlDir, recursive=True)
        self.engine.setWatching(os.environ.get("MESHROOM_INSTANT_CODING", False))
        # whether to output qml warnings to stderr (disable by default)
        self.engine.setOutputWarningsToStandardError(MessageHandler.outputQmlWarnings)
        qInstallMessageHandler(MessageHandler.handler)

        self.engine.addImportPath(qmlDir)
        components.registerTypes()

        # expose available node types that can be instantiated
        self.engine.rootContext().setContextProperty("_nodeTypes", sorted(nodesDesc.keys()))

        # instantiate Reconstruction object
        r = Reconstruction(defaultPipeline=args.pipeline, parent=self)
        self.engine.rootContext().setContextProperty("_reconstruction", r)

        # those helpers should be available from QML Utils module as singletons, but:
        #  - qmlRegisterUncreatableType is not yet available in PySide2
        #  - declaring them as singleton in qmldir file causes random crash at exit
        # => expose them as context properties instead
        self.engine.rootContext().setContextProperty("Filepath", FilepathHelper(parent=self))
        self.engine.rootContext().setContextProperty("Scene3DHelper", Scene3DHelper(parent=self))
        self.engine.rootContext().setContextProperty("Clipboard", ClipboardHelper(parent=self))

        # additional context properties
        self.engine.rootContext().setContextProperty("_PaletteManager", PaletteManager(self.engine, parent=self))
        self.engine.rootContext().setContextProperty("MeshroomApp", self)

        # request any potential computation to stop on exit
        self.aboutToQuit.connect(r.stopChildThreads)

        if args.project and not os.path.isfile(args.project):
            raise RuntimeError(
                "Meshroom Command Line Error: 'PROJECT' argument should be a Meshroom project file (.mg).\n"
                "Invalid value: '{}'".format(args.project))

        if args.project:
            r.load(args.project)
            self.addRecentProjectFile(args.project)
        else:
            r.new()

        # import is a python keyword, so we have to access the attribute by a string
        if getattr(args, "import", None):
            r.importImagesFromFolder(getattr(args, "import"), recursive=False)

        if args.importRecursive:
            r.importImagesFromFolder(args.importRecursive, recursive=True)

        if args.save:
            if os.path.isfile(args.save):
                raise RuntimeError(
                    "Meshroom Command Line Error: Cannot save the new Meshroom project as the file (.mg) already exists.\n"
                    "Invalid value: '{}'".format(args.save))
            projectFolder = os.path.dirname(args.save)
            if not os.path.isdir(projectFolder):
                if not os.path.isdir(os.path.dirname(projectFolder)):
                    raise RuntimeError(
                        "Meshroom Command Line Error: Cannot save the new Meshroom project file (.mg) as the parent of the folder does not exists.\n"
                        "Invalid value: '{}'".format(args.save))
                os.mkdir(projectFolder)
            r.saveAs(args.save)
            self.addRecentProjectFile(args.save)

        self.engine.load(os.path.normpath(url))

    def _recentProjectFiles(self):
        projects = []
        settings = QSettings()
        settings.beginGroup("RecentFiles")
        size = settings.beginReadArray("Projects")
        for i in range(size):
            settings.setArrayIndex(i)
            p = settings.value("filepath")
            if p:
                projects.append(p)
        settings.endArray()
        return projects

    @Slot(str)
    def addRecentProjectFile(self, projectFile):
        projectFile = QUrl(projectFile).path()
        projects = self._recentProjectFiles()

        # remove duplicates while preserving order
        from collections import OrderedDict
        uniqueProjects = OrderedDict.fromkeys(projects)
        projects = list(uniqueProjects)
        # remove previous usage of the value
        if projectFile in uniqueProjects:
            projects.remove(projectFile)
        # add the new value in the first place
        projects.insert(0, projectFile)

        # keep only the 10 first elements
        projects = projects[0:20]

        settings = QSettings()
        settings.beginGroup("RecentFiles")
        size = settings.beginWriteArray("Projects")
        for i, p in enumerate(projects):
            settings.setArrayIndex(i)
            settings.setValue("filepath", p)
        settings.endArray()
        settings.sync()

        self.recentProjectFilesChanged.emit()

    @Slot(str, result=str)
    def markdownToHtml(self, md):
        """
        Convert markdown to HTML.

        Args:
            md (str): the markdown text to convert

        Returns:
            str: the resulting HTML string
        """
        try:
            from markdown import markdown
        except ImportError:
            logging.warning("Can't import markdown module, returning source markdown text.")
            return md
        return markdown(md)

    @Property(QJsonValue, constant=True)
    def systemInfo(self):
        import platform
        import sys
        return {
            'platform': '{} {}'.format(platform.system(), platform.release()),
            'python': 'Python {}'.format(sys.version.split(" ")[0])
        }

    @Property("QVariantList", constant=True)
    def licensesModel(self):
        """
        Get info about open-source licenses for the application.
        Model provides:
            title: the name of the project
            localUrl: the local path to COPYING.md
            onlineUrl: the remote path to COPYING.md
        """
        rootDir = os.environ.get("MESHROOM_INSTALL_DIR", os.getcwd())
        return [
            {
                "title": "Meshroom",
                "localUrl": os.path.join(rootDir, "COPYING.md"),
                "onlineUrl": "https://raw.githubusercontent.com/alicevision/meshroom/develop/COPYING.md"
            },
            {
                "title": "AliceVision",
                "localUrl": os.path.join(rootDir, "aliceVision", "share", "aliceVision", "COPYING.md"),
                "onlineUrl": "https://raw.githubusercontent.com/alicevision/AliceVision/develop/COPYING.md"
            }
        ]

    recentProjectFilesChanged = Signal()
    recentProjectFiles = Property("QVariantList", _recentProjectFiles, notify=recentProjectFilesChanged)

