import logging
import os
import re
import argparse
import json

from PySide6 import __version__ as PySideVersion
from PySide6 import QtCore
from PySide6.QtCore import Qt, QUrl, QJsonValue, qInstallMessageHandler, QtMsgType, QSettings
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

import meshroom
from meshroom.core.taskManager import TaskManager
from meshroom.common import Property, Variant, Signal, Slot

from meshroom.ui import components
from meshroom.ui.plugins import NodesPluginManager
from meshroom.ui.components.clipboard import ClipboardHelper
from meshroom.ui.components.filepath import FilepathHelper
from meshroom.ui.components.scene3D import Scene3DHelper, Transformations3DHelper
from meshroom.ui.components.scriptEditor import ScriptEditorManager
from meshroom.ui.components.thumbnail import ThumbnailCache
from meshroom.ui.palette import PaletteManager
from meshroom.ui.reconstruction import Reconstruction
from meshroom.ui.utils import QmlInstantEngine
from meshroom.ui import commands


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

        if not cls.outputQmlWarnings:
            # If MESHROOM_OUTPUT_QML_WARNINGS is not set and an error in qml files happen we're
            # left without any output except "QQmlApplicationEngine failed to load component".
            # This is extremely hard to debug to someone who does not know about
            # MESHROOM_OUTPUT_QML_WARNINGS beforehand because by default Qml will output errors to
            # stdout.
            if "QQmlApplicationEngine failed to load component" in message:
                logging.warning("Set MESHROOM_OUTPUT_QML_WARNINGS=1 to get a detailed error message.")

            # discard blacklisted Qt messages related to QML when 'output qml warnings' is not enabled
            elif any(w in message for w in cls.qmlWarningsBlacklist):
                return
        MessageHandler.logFunctions[messageType](message)

def createMeshroomParser(args):

    # Create the main parser with a description
    parser = argparse.ArgumentParser(
        prog='meshroom',
        description='Launch Meshroom UI - The toolbox that connects research, industry and community at large.',
        add_help=True,
        formatter_class=argparse.RawTextHelpFormatter,
        epilog='''
Examples:
  1. Open an existing project in Meshroom:
     meshroom myProject.mg

  2. Open a new project in Meshroom with a specific pipeline, import images from a folder and save the project:
     meshroom -p photogrammetry -i /path/to/images/ --save /path/to/store/the/project.mg

  3. Process a pipeline in command line:
     meshroom_batch -p cameraTracking -i /input/path -o /output/path -s /path/to/store/the/project.mg
     See 'meshroom_batch -h' for more details.

Additional Resources:
  Website:      https://alicevision.org
  Manual:       https://meshroom-manual.readthedocs.io
  Forum:        https://groups.google.com/g/alicevision
  Tutorials:    https://www.youtube.com/c/AliceVisionOrg
  Contribute:   https://github.com/alicevision/Meshroom
'''
    )

    # Positional Arguments
    parser.add_argument(
        'project',
        metavar='PROJECT',
        type=str,
        nargs='?',
        help='Meshroom project file (e.g. myProject.mg) or folder with images to reconstruct.'
    )

    # General Options
    general_group = parser.add_argument_group('General Options')
    general_group.add_argument(
        '-v', '--verbose',
        help='Set the verbosity level for logging:\n'
             '  - fatal: Show only critical errors.\n'
             '  - error: Show errors only.\n'
             '  - warning: Show warnings and errors.\n'
             '  - info: Show standard informational messages.\n'
             '  - debug: Show detailed debug information.\n'
             '  - trace: Show all messages, including trace-level details.',
        default=os.environ.get('MESHROOM_VERBOSE', 'warning'),
        choices=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
    )
    general_group.add_argument(
        '--submitLabel',
        metavar='SUBMITLABEL',
        type=str,
        help='Label of a node when submitted on renderfarm.',
        default=os.environ.get('MESHROOM_SUBMIT_LABEL', '[Meshroom] {projectName}'),
    )

    # Project and Input Options
    project_group = parser.add_argument_group('Project and Input Options')
    project_group.add_argument(
        '-i', '--import',
        metavar='IMAGES/FOLDERS',
        type=str,
        nargs='*',
        help='Import images or a folder with images to process.'
    )
    project_group.add_argument(
        '-I', '--importRecursive',
        metavar='FOLDERS',
        type=str,
        nargs='*',
        help='Import images to process from specified folder and sub-folders.'
    )
    project_group.add_argument(
        '-s', '--save',
        metavar='PROJECT.mg',
        type=str,
        required=False,
        help='Save the created scene to the specified Meshroom project file.'
    )
    project_group.add_argument(
        '-1', '--latest',
        action='store_true',
        help='Load the most recent scene (-2 and -3 to load the previous ones).'
    )
    project_group.add_argument(
        '-2', '--latest2',
        action='store_true',
        help=argparse.SUPPRESS  # This hides the option from the help message
    )
    project_group.add_argument(
        '-3', '--latest3',
        action='store_true',
        help=argparse.SUPPRESS  # This hides the option from the help message
    )

    # Pipeline Options
    pipeline_group = parser.add_argument_group('Pipeline Options')
    pipeline_group.add_argument(
        '-p', '--pipeline',
        metavar='FILE.mg / PIPELINE',
        type=str,
        default=os.environ.get('MESHROOM_DEFAULT_PIPELINE', ''),
        help='Select the default Meshroom pipeline:\n'
        + '\n'.join(['    - ' + p for p in meshroom.core.pipelineTemplates]),
    )

    return parser.parse_args(args[1:])


class MeshroomApp(QApplication):
    """ Meshroom UI Application. """
    def __init__(self, args):
        meshroom.core.initPipelines()

        QtArgs = [args[0], '-style', 'Fusion'] + args[1:]  # force Fusion style by default

        args = createMeshroomParser(args)

        logStringToPython = {
            'fatal': logging.FATAL,
            'error': logging.ERROR,
            'warning': logging.WARNING,
            'info': logging.INFO,
            'debug': logging.DEBUG,
            'trace': logging.DEBUG,
        }
        logging.getLogger().setLevel(logStringToPython[args.verbose])

        super(MeshroomApp, self).__init__(QtArgs)

        self.setOrganizationName('AliceVision')
        self.setApplicationName('Meshroom')
        self.setApplicationVersion(meshroom.__version_label__)

        font = self.font()
        font.setPointSize(9)
        self.setFont(font)

        pwd = os.path.dirname(__file__)
        self.setWindowIcon(QIcon(os.path.join(pwd, "img/meshroom.svg")))

        # Initialize thumbnail cache:
        # - read related environment variables
        # - clean cache directory and make sure it exists on disk
        ThumbnailCache.initialize()

        meshroom.core.initNodes()
        meshroom.core.initSubmitters()

        # QML engine setup
        qmlDir = os.path.join(pwd, "qml")
        url = os.path.join(qmlDir, "main.qml")
        self.engine = QmlInstantEngine()
        self.engine.addFilesFromDirectory(qmlDir, recursive=True)
        self.engine.setWatching(os.environ.get("MESHROOM_INSTANT_CODING", False))
        # whether to output qml warnings to stderr (disable by default)
        self.engine.setOutputWarningsToStandardError(MessageHandler.outputQmlWarnings)
        if QtCore.__version_info__ < (5, 14, 2):
            # After 5.14.1, it gets stuck during logging
            qInstallMessageHandler(MessageHandler.handler)

        self.engine.addImportPath(qmlDir)
        components.registerTypes()

        # instantiate Reconstruction object
        self._undoStack = commands.UndoStack(self)
        self._taskManager = TaskManager(self)
        self._activeProject = Reconstruction(undoStack=self._undoStack, taskManager=self._taskManager, defaultPipeline=args.pipeline, parent=self)
        self._activeProject.setSubmitLabel(args.submitLabel)

        # The Plugin manager for UI to communicate with
        self._pluginManager = NodesPluginManager(parent=self)
        self.engine.rootContext().setContextProperty("_reconstruction", self._activeProject)
        self.engine.rootContext().setContextProperty("_pluginator", self._pluginManager)

        # those helpers should be available from QML Utils module as singletons, but:
        #  - qmlRegisterUncreatableType is not yet available in PySide2
        #  - declaring them as singleton in qmldir file causes random crash at exit
        # => expose them as context properties instead
        self.engine.rootContext().setContextProperty("Filepath", FilepathHelper(parent=self))
        self.engine.rootContext().setContextProperty("Scene3DHelper", Scene3DHelper(parent=self))
        self.engine.rootContext().setContextProperty("Transformations3DHelper", Transformations3DHelper(parent=self))
        self.engine.rootContext().setContextProperty("Clipboard", ClipboardHelper(parent=self))
        self.engine.rootContext().setContextProperty("ThumbnailCache", ThumbnailCache(parent=self))

        # additional context properties
        self.engine.rootContext().setContextProperty("_PaletteManager", PaletteManager(self.engine, parent=self))
        self.engine.rootContext().setContextProperty("ScriptEditorManager", ScriptEditorManager(parent=self))
        self.engine.rootContext().setContextProperty("MeshroomApp", self)

        # request any potential computation to stop on exit
        self.aboutToQuit.connect(self._activeProject.stopChildThreads)

        if args.project and not os.path.isfile(args.project):
            raise RuntimeError(
                "Meshroom Command Line Error: 'PROJECT' argument should be a Meshroom project file (.mg).\n"
                "Invalid value: '{}'".format(args.project))

        if args.project:
            args.project = os.path.abspath(args.project)
            self._activeProject.load(args.project)
            self.addRecentProjectFile(args.project)
        elif args.latest or args.latest2 or args.latest3:
            projects = self._recentProjectFiles()
            if projects:
                index = [args.latest, args.latest2, args.latest3].index(True)
                project = os.path.abspath(projects[index]["path"])
                self._activeProject.load(project)
                self.addRecentProjectFile(project)
        elif getattr(args, "import", None) or args.importRecursive or args.save or args.pipeline:
            self._activeProject.new()

        # import is a python keyword, so we have to access the attribute by a string
        if getattr(args, "import", None):
            self._activeProject.importImagesFromFolder(getattr(args, "import"), recursive=False)

        if args.importRecursive:
            self._activeProject.importImagesFromFolder(args.importRecursive, recursive=True)

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
            self._activeProject.saveAs(args.save)
            self.addRecentProjectFile(args.save)

        self.engine.load(os.path.normpath(url))

    def _pipelineTemplateFiles(self):
        templates = []
        for key in sorted(meshroom.core.pipelineTemplates.keys()):
            # Use uppercase letters in the names as separators to format the templates' name nicely
            # e.g: the template "panoramaHdr" will be shown as "Panorama Hdr" in the menu
            name = " ".join(re.findall('[A-Z][^A-Z]*', key[0].upper() + key[1:]))
            variant = {"name": name, "key": key, "path": meshroom.core.pipelineTemplates[key]}
            templates.append(variant)
        return templates

    def _pipelineTemplateNames(self):
        return [p["name"] for p in self.pipelineTemplateFiles]

    @Slot()
    def reloadTemplateList(self):
        meshroom.core.initPipelines()
        self.pipelineTemplateFilesChanged.emit()

    def _recentProjectFiles(self):
        projects = []
        settings = QSettings()
        settings.beginGroup("RecentFiles")
        size = settings.beginReadArray("Projects")
        for i in range(size):
            settings.setArrayIndex(i)
            p = settings.value("filepath")
            thumbnail = ""
            if p:
                # get the first image path from the project
                try:
                    with open(p) as file:
                        file = json.load(file)
                        # find the first camerainit node
                        file = file["graph"]
                        for node in file:
                            if file[node]["nodeType"] == "CameraInit" and file[node]["inputs"].get("viewpoints"):
                                if len(file[node]["inputs"]["viewpoints"]) > 0:
                                    thumbnail = file[node]["inputs"]["viewpoints"][0]["path"]
                                    break
                except FileNotFoundError:
                    pass
                p = {"path": p, "thumbnail": thumbnail}
                projects.append(p)
        settings.endArray()
        settings.endGroup()
        return projects

    @Slot(str)
    @Slot(QUrl)
    def addRecentProjectFile(self, projectFile):
        if not isinstance(projectFile, (QUrl, str)):
            raise TypeError("Unexpected data type: {}".format(projectFile.__class__))
        if isinstance(projectFile, QUrl):
            projectFileNorm = projectFile.toLocalFile()
            if not projectFileNorm:
                projectFileNorm = projectFile.toString()
        else:
            projectFileNorm = QUrl(projectFile).toLocalFile()
            if not projectFileNorm:
                projectFileNorm = QUrl.fromLocalFile(projectFile).toLocalFile()

        projects = self._recentProjectFiles()
        projects = [p["path"] for p in projects]

        # remove duplicates while preserving order
        from collections import OrderedDict
        uniqueProjects = OrderedDict.fromkeys(projects)
        projects = list(uniqueProjects)
        # remove previous usage of the value
        if projectFileNorm in uniqueProjects:
            projects.remove(projectFileNorm)
        # add the new value in the first place
        projects.insert(0, projectFileNorm)

        # keep only the 40 first elements
        projects = projects[0:40]

        settings = QSettings()
        settings.beginGroup("RecentFiles")
        settings.beginWriteArray("Projects")
        for i, p in enumerate(projects):
            settings.setArrayIndex(i)
            settings.setValue("filepath", p)
        settings.endArray()
        settings.endGroup()
        settings.sync()

        self.recentProjectFilesChanged.emit()

    @Slot(str)
    @Slot(QUrl)
    def removeRecentProjectFile(self, projectFile):
        if not isinstance(projectFile, (QUrl, str)):
            raise TypeError("Unexpected data type: {}".format(projectFile.__class__))
        if isinstance(projectFile, QUrl):
            projectFileNorm = projectFile.toLocalFile()
            if not projectFileNorm:
                projectFileNorm = projectFile.toString()
        else:
            projectFileNorm = QUrl(projectFile).toLocalFile()
            if not projectFileNorm:
                projectFileNorm = QUrl.fromLocalFile(projectFile).toLocalFile()

        projects = self._recentProjectFiles()
        projects = [p["path"] for p in projects]

        # remove duplicates while preserving order
        from collections import OrderedDict
        uniqueProjects = OrderedDict.fromkeys(projects)
        projects = list(uniqueProjects)
        # remove previous usage of the value
        if projectFileNorm not in uniqueProjects:
            return

        projects.remove(projectFileNorm)

        settings = QSettings()
        settings.beginGroup("RecentFiles")
        settings.beginWriteArray("Projects")
        for i, p in enumerate(projects):
            settings.setArrayIndex(i)
            settings.setValue("filepath", p)
        settings.endArray()
        settings.sync()

        self.recentProjectFilesChanged.emit()

    def _recentImportedImagesFolders(self):
        folders = []
        settings = QSettings()
        settings.beginGroup("RecentFiles")
        size = settings.beginReadArray("ImagesFolders")
        for i in range(size):
            settings.setArrayIndex(i)
            f = settings.value("path")
            if f:
                folders.append(f)
        settings.endArray()
        return folders

    @Slot(QUrl)
    def addRecentImportedImagesFolder(self, imagesFolder):
        if isinstance(imagesFolder, QUrl):
            folderPath = imagesFolder.toLocalFile()
            if not folderPath:
                folderPath = imagesFolder.toString()
        else:
            raise TypeError("Unexpected data type: {}".format(imagesFolder.__class__))

        folders = self._recentImportedImagesFolders()

        # remove duplicates while preserving order
        from collections import OrderedDict
        uniqueFolders = OrderedDict.fromkeys(folders)
        folders = list(uniqueFolders)
        # remove previous usage of the value
        if folderPath in uniqueFolders:
            folders.remove(folderPath)
        # add the new value in the first place
        folders.insert(0, folderPath)

        # keep only the first three elements to have a backup if one of the folders goes missing
        folders = folders[0:3]

        settings = QSettings()
        settings.beginGroup("RecentFiles")
        settings.beginWriteArray("ImagesFolders")
        for i, p in enumerate(folders):
            settings.setArrayIndex(i)
            settings.setValue("path", p)
        settings.endArray()
        settings.sync()

        self.recentImportedImagesFoldersChanged.emit()

    @Slot(QUrl)
    def removeRecentImportedImagesFolder(self, imagesFolder):
        if isinstance(imagesFolder, QUrl):
            folderPath = imagesFolder.toLocalFile()
            if not folderPath:
                folderPath = imagesFolder.toString()
        else:
            raise TypeError("Unexpected data type: {}".format(imagesFolder.__class__))

        folders = self._recentImportedImagesFolders()

        # remove duplicates while preserving order
        from collections import OrderedDict
        uniqueFolders = OrderedDict.fromkeys(folders)
        folders = list(uniqueFolders)
        # remove previous usage of the value
        if folderPath not in uniqueFolders:
            return

        folders.remove(folderPath)

        settings = QSettings()
        settings.beginGroup("RecentFiles")
        settings.beginWriteArray("ImagesFolders")
        for i, f in enumerate(folders):
            settings.setArrayIndex(i)
            settings.setValue("path", f)
        settings.endArray()
        settings.sync()

        self.recentImportedImagesFoldersChanged.emit()

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

    def _systemInfo(self):
        import platform
        import sys
        return {
            'platform': '{} {}'.format(platform.system(), platform.release()),
            'python': 'Python {}'.format(sys.version.split(" ")[0]),
            'pyside': 'PySide6 {}'.format(PySideVersion)
        }

    systemInfo = Property(QJsonValue, _systemInfo, constant=True)

    def _changelogModel(self):
        """
        Get the complete changelog for the application.
        Model provides:
            title: the name of the changelog
            localUrl: the local path to CHANGES.md
            onlineUrl: the remote path to CHANGES.md
        """
        rootDir = os.environ.get("MESHROOM_INSTALL_DIR", os.getcwd())
        return [
            {
                "title": "Changelog",
                "localUrl": os.path.join(rootDir, "CHANGES.md"),
                "onlineUrl": "https://raw.githubusercontent.com/alicevision/meshroom/develop/CHANGES.md"
            }
        ]

    def _licensesModel(self):
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

    def _default8bitViewerEnabled(self):
        return bool(os.environ.get("MESHROOM_USE_8BIT_VIEWER", False))
    
    def _defaultSequencePlayerEnabled(self):
        return bool(os.environ.get("MESHROOM_USE_SEQUENCE_PLAYER", True))

    activeProjectChanged = Signal()
    activeProject = Property(Variant, lambda self: self._activeProject, notify=activeProjectChanged)

    changelogModel = Property("QVariantList", _changelogModel, constant=True)
    licensesModel = Property("QVariantList", _licensesModel, constant=True)
    pipelineTemplateFilesChanged = Signal()
    recentProjectFilesChanged = Signal()
    recentImportedImagesFoldersChanged = Signal()
    pipelineTemplateFiles = Property("QVariantList", _pipelineTemplateFiles, notify=pipelineTemplateFilesChanged)
    pipelineTemplateNames = Property("QVariantList", _pipelineTemplateNames, notify=pipelineTemplateFilesChanged)
    recentProjectFiles = Property("QVariantList", _recentProjectFiles, notify=recentProjectFilesChanged)
    recentImportedImagesFolders = Property("QVariantList", _recentImportedImagesFolders, notify=recentImportedImagesFoldersChanged)
    default8bitViewerEnabled = Property(bool, _default8bitViewerEnabled, constant=True)
    defaultSequencePlayerEnabled = Property(bool, _defaultSequencePlayerEnabled, constant=True)
