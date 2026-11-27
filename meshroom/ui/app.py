import logging
import os
import argparse
import sys
from enum import Enum
from threading import Thread

from PySide6 import __version__ as PySideVersion
from PySide6 import QtCore
from PySide6.QtCore import QUrl, QJsonValue, qInstallMessageHandler, QtMsgType, QSettings, QProcess
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlDebuggingEnabler
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication

import meshroom
from meshroom.core import pluginManager
from meshroom.core.desc import MrNodeType, NodeVersionTypeEnum
from meshroom.core.graphIO import getTemplateInfo
from meshroom.core.plugins.local.taskQueue import PluginTaskQueue
from meshroom.core.submitter import BaseSubmitter
from meshroom.core.taskManager import TaskManager
from meshroom.common import Property, Variant, Signal, Slot

from meshroom.env import EnvVar, EnvVarHelpAction

from meshroom.ui import components
from meshroom.ui.components.clipboard import ClipboardHelper
from meshroom.ui.components.filepath import FilepathHelper
from meshroom.ui.components.scene3D import Scene3DHelper, Transformations3DHelper
from meshroom.ui.components.scriptEditor import ScriptEditorManager
from meshroom.ui.components.thumbnail import ThumbnailCache
from meshroom.ui.components.messaging import MessageController
from meshroom.ui.dockLayoutManager import DockLayoutManager
from meshroom.ui.components.shapes import SurveyPointViewerHelper, ShapeFilesHelper, ShapeViewerHelper
from meshroom.ui.palette import PaletteManager
from meshroom.ui.scene import Scene
from meshroom.ui import projectInfo, templateInfo
from meshroom.ui.utils import QmlInstantEngine
from meshroom.ui import commands


class FileStatus(Enum):
    MISSING=0
    EXISTS=1
    ERROR=2  # If the file exists but have errors like missing nodes, file content corruption...


class MessageHandler:
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
            # If MESHROOM_OUTPUT_QML_WARNINGS is not set and an error in qml files happen we are
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
        '-0', '--new',
        action='store_true',
        help='Opens directly a new project.'
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
    project_group.add_argument(
        '-o', '--output',
        metavar='OUTPUT_FOLDER',
        type=str,
        required=False,
        nargs='*',
        help='Set the output folder for the output nodes.'
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

    advanced_group = parser.add_argument_group("Advanced Options")
    advanced_group.add_argument(
        "--env-help",
        action=EnvVarHelpAction,
        nargs=0,
        help=EnvVarHelpAction.DEFAULT_HELP,
    )

    return parser.parse_args(args[1:])


class MeshroomApp(QApplication):
    """ Meshroom UI Application. """
    def __init__(self, inputArgs):
        meshroom.core.initPipelines()

        args = createMeshroomParser(inputArgs)
        qtArgs = []

        if EnvVar.get(EnvVar.MESHROOM_QML_DEBUG):
            debuggerParams = EnvVar.get(EnvVar.MESHROOM_QML_DEBUG_PARAMS)
            self.debugger = QQmlDebuggingEnabler(printWarning=True)
            qtArgs = [f"-qmljsdebugger={debuggerParams}"]

        logging.getLogger().setLevel(meshroom.logStringToPython[args.verbose])

        super().__init__(inputArgs[:1] + qtArgs)

        # Store how Meshroom was launched, to be able to restart it
        self._launchVerbosity = args.verbose
        self._launchWorkingDir = os.getcwd()
        if meshroom.isFrozen:
            self._launchCommand = [sys.executable]
        else:
            self._launchCommand = [sys.executable, os.path.abspath(sys.argv[0])]

        self.setOrganizationName('AliceVision')
        self.setApplicationName('Meshroom')
        self.setApplicationVersion(meshroom.__version_label__)

        font = self.font()
        font.setPointSize(9)
        self.setFont(font)

        # Use Fusion style by default.
        QQuickStyle.setStyle("Fusion")

        pwd = os.path.dirname(__file__)
        self.setWindowIcon(QIcon(os.path.join(pwd, "img/meshroom.svg")))

        # Initialize thumbnail cache:
        # - read related environment variables
        # - clean cache directory and make sure it exists on disk
        ThumbnailCache.initialize()

        meshroom.core.initSubmitters()
        meshroom.core.initPlugins()
        meshroom.core.initNodes()

        self._templateCategoryColors = templateInfo.loadCategoryColors()
        self._pipelineTemplates = None  # list of the registered templates with their metadata, read on first access

        # Initialize the list of recent project files: they are read in a thread when the homepage is shown
        self._recentProjectFiles = self._getRecentProjectFilesFromSettings()
        self._recentTemplateFiles = self._getRecentTemplateFilesFromSettings()
        # Id of the last read request of each project file: the result of an older one is dropped
        self._projectInfoRequests = {}
        self._lastProjectInfoRequest = 0
        self._refreshRequest = 0  # id of the running refresh of all the recent projects, 0 if none
        self._projectInfosRead.connect(self._applyProjectInfos, QtCore.Qt.QueuedConnection)

        # Register components for QML before instantiating the engine
        components.registerTypes()

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
        # Add PySide6's bundled QML modules path (Qt3D, QtQuick.Scene3D, etc.)
        pyside6QmlPath = os.path.join(os.path.dirname(QtCore.__file__), "Qt", "qml")
        if os.path.isdir(pyside6QmlPath):
            self.engine.addImportPath(pyside6QmlPath)

        # expose the plugin manager
        self.engine.rootContext().setContextProperty("_pluginManager", pluginManager)

        # expose the queue processing the plugin installation, update and removal tasks
        self._pluginTaskQueue = PluginTaskQueue(parent=self)
        self.engine.rootContext().setContextProperty("_pluginTaskQueue", self._pluginTaskQueue)
        # stop the running plugin task properly on exit
        self.aboutToQuit.connect(self._pluginTaskQueue.shutdown)

        # expose available node types that can be instantiated
        self.engine.rootContext().setContextProperty("_nodeTypes", {n: {"category": pluginManager.getNodeDescProviders()[n].nodeDescClass.category} for n in sorted(pluginManager.getNodeDescProviders().keys())})

        # instantiate the 3D Scene object
        self._undoStack = commands.UndoStack(self)
        self._defaultSubmitterName = os.environ.get('MESHROOM_DEFAULT_SUBMITTER', '')
        self._taskManager = TaskManager(self)
        self._activeProject = Scene(undoStack=self._undoStack, taskManager=self._taskManager, defaultPipeline=args.pipeline, parent=self)
        self._activeProject.setSubmitLabel(args.submitLabel)
        self.engine.rootContext().setContextProperty("_currentScene", self._activeProject)

        # those helpers should be available from QML Utils module as singletons, but:
        #  - qmlRegisterUncreatableType is not yet available in PySide2
        #  - declaring them as singleton in qmldir file causes random crash at exit
        # => expose them as context properties instead
        self.engine.rootContext().setContextProperty("Filepath", FilepathHelper(parent=self))
        self.engine.rootContext().setContextProperty("Scene3DHelper", Scene3DHelper(parent=self))
        self.engine.rootContext().setContextProperty("Transformations3DHelper", Transformations3DHelper(parent=self))
        self.engine.rootContext().setContextProperty("Clipboard", ClipboardHelper(parent=self))
        self.engine.rootContext().setContextProperty("ThumbnailCache", ThumbnailCache(parent=self))
        self.engine.rootContext().setContextProperty("ShapeFilesHelper", ShapeFilesHelper(self.activeProject, parent=self))
        shapeViewerHelper = ShapeViewerHelper(self.activeProject, parent=self)
        surveyPointViewerHelper = SurveyPointViewerHelper(self.activeProject, shapeViewerHelper, parent=self)
        self.engine.rootContext().setContextProperty("SurveyPointViewerHelper", surveyPointViewerHelper)
        self.engine.rootContext().setContextProperty("ShapeViewerHelper", shapeViewerHelper)

        # additional context properties
        self._messageController = MessageController(parent=self)
        self.engine.rootContext().setContextProperty("_messageController", self._messageController)
        self._paletteManager = PaletteManager(parent=self)
        self.engine.rootContext().setContextProperty("_PaletteManager", self._paletteManager)
        self.engine.rootContext().setContextProperty("ScriptEditorManager", ScriptEditorManager(parent=self))
        self.engine.rootContext().setContextProperty("_dockLayout", DockLayoutManager(parent=self))
        self.engine.rootContext().setContextProperty("MeshroomApp", self)
        self.engine.rootContext().setContextProperty("NodeVersionType", NodeVersionTypeEnum(parent=self))

        # request any potential computation to stop on exit
        self.aboutToQuit.connect(self._activeProject.stopChildThreads)

        if args.project and not os.path.isfile(args.project):
            raise RuntimeError(
                "Meshroom Command Line Error: 'PROJECT' argument should be a Meshroom project file (.mg).\n"
                "Invalid value: '{}'".format(args.project))

        if args.project:
            args.project = os.path.abspath(args.project)
            self._activeProject.load(args.project)
            if self._activeProject.graph.filepath:
                self.addRecentProjectFile(args.project)
            else:
                self.addRecentTemplateFile(args.project)
        elif args.new:
            self._activeProject.new()
        elif args.latest or args.latest2 or args.latest3:
            projects = self._recentProjectFiles
            if projects:
                index = [args.latest, args.latest2, args.latest3].index(True)
                project = os.path.abspath(projects[index]["path"])
                self._activeProject.load(project)
                self.addRecentProjectFile(project)
        elif getattr(args, "import", None) or args.importRecursive or args.save or args.pipeline:
            if args.output:
                # Initialize the template and keep the output nodes
                self._activeProject.newWithOutputNodes()
                # Use the provided output paths to initialize the output nodes
                outputNodes = self._activeProject.graph.findOutputNodes()
                if len(outputNodes) > 0:
                    for index, node in enumerate(outputNodes):
                        outputFolder = args.output[index] if index < len(args.output) else args.output[0]
                        node.nodeDesc.setOutputFolder(node, outputFolder)
            else:
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

        # Apply the initial theme now.
        # Quick Controls Fusion-style palette machinery has already initialized.
        self._paletteManager.togglePalette()

    @Slot()
    def restart(self):
        """
        Restart Meshroom, reopening the current project if it has been saved to a file.
        The original command line arguments are not reused, as they may import images or save a project again.
        """
        program, *programArgs = self._launchCommand
        programArgs += ["--verbose", self._launchVerbosity]
        if self._activeProject.graph.filepath:
            programArgs.append(self._activeProject.graph.filepath)

        success, _ = QProcess.startDetached(program, programArgs, self._launchWorkingDir)
        if not success:
            self.showMessage("Could not restart Meshroom", "error")
            return
        self.quit()

    def terminateManual(self):
        self.engine.clearComponentCache()
        self.engine.collectGarbage()
        self.engine.deleteLater()

    def _pipelineTemplateFiles(self):
        """ Return the registered templates as {"name", "key", "path", "label", "category", "color", "icon",
        "description"}, sorted by key.

        The name is derived from the key, so it is unique; the label is the one of the template metadata, the name
        when it has none. The template files are read once, then again after `reloadTemplateList`.
        """
        if self._pipelineTemplates is None:
            self._pipelineTemplates = []
            for key in sorted(meshroom.core.pipelineTemplates.keys()):
                # A broken template file must not prevent the application from starting
                try:
                    info = getTemplateInfo(key)
                except Exception as e:
                    logging.warning(f"Could not read the metadata of the template '{key}': {e}")
                    info = {}

                def text(field):
                    # Template headers can be edited by hand: ignore values that are not text
                    value = info.get(field)
                    return value.strip() if isinstance(value, str) else ""

                # e.g: the template "panoramaHdr" is named "Panorama Hdr"
                name = templateInfo.defaultTemplateLabel(key)
                self._pipelineTemplates.append({
                    "name": name,
                    "key": key,
                    "label": text("label") or name,
                    "path": meshroom.core.pipelineTemplates[key],
                    "category": text("category"),
                    "color": templateInfo.categoryColor(text("category"), self._templateCategoryColors),
                    "icon": text("icon"),
                    "description": text("description"),
                })
        return self._pipelineTemplates

    def _pipelineTemplateNames(self):
        return [p["name"] for p in self.pipelineTemplateFiles]

    @Slot()
    def reloadTemplateList(self):
        meshroom.core.initPipelines()
        self._pipelineTemplates = None
        self.pipelineTemplateFilesChanged.emit()

    @Slot(result="QVariantList")
    def templateCategories(self) -> list:
        """ Return the categories offered for a template: the built-in ones, then those of the registered templates.

        Read from the cached template list (see `_pipelineTemplateFiles`), invalid templates have no category.
        """
        usedCategories = sorted(t["category"] for t in self.pipelineTemplateFiles)
        return templateInfo.mergeCategories(self._templateCategoryColors.keys(), usedCategories)

    @Slot(str, result=str)
    def templateCategoryColor(self, category: str) -> str:
        """ Return the color of a template category: built-in if listed, otherwise hashed from its lower-case name. """
        return templateInfo.categoryColor(category, self._templateCategoryColors)

    @Slot(str, result=str)
    def defaultTemplateLabel(self, key: str) -> str:
        return templateInfo.defaultTemplateLabel(key)

    @Slot("QVariantList", int, "QVariantList", result="QVariantList")
    def layoutPipelineCategories(self, categories: list, columns: int, expanded: list) -> list:
        """ Return the rows of pipeline categories of the homepage for `columns` columns (see templateInfo.layoutCategories). """
        return templateInfo.layoutCategories(categories, columns, expanded)

    @Slot(str, result="QVariantList")
    def searchTemplateIcons(self, query: str) -> list:
        """ Return the names of the MaterialIcons matching all the words of `query`. """
        return templateInfo.searchIcons(query)

    @Slot()
    def forceUIUpdate(self):
        """ Force UI to process pending events
        Necessary when we want to update the UI while a trigger is still running (e.g. reloadPlugins)
        """
        self.processEvents()

    def showMessage(self, message, status=None, duration=5000):
        self._messageController.sendMessage(message, status, duration)

    @staticmethod
    def _isComputableNodeType(nodeType: str) -> bool:
        """ Return whether nodes of type `nodeType` are computed. Unknown types (missing plugin) are counted. """
        provider = pluginManager.getNodeDescProviders().get(nodeType)
        if provider is None:
            return True
        return provider.nodeDescClass._mrNodeType in (MrNodeType.NODE, MrNodeType.COMMANDLINE)

    @classmethod
    def _readProjectInfo(cls, path: str) -> dict:
        """ Return the `projectInfo.readProjectInfo` of the project file at `path`, only the MISSING status if the file
        is missing. Slow on network storage (it reads the status files of all the nodes): called from a thread. """
        if not os.path.isfile(path):
            return {"status": projectInfo.ProjectStatus.MISSING}
        return projectInfo.readProjectInfo(path, cls._isComputableNodeType)

    def _projectFileEntry(self, path: str, info: dict = None) -> dict:
        """
        Return the entry of the recent project file at `path`: {"path", "status" (FileStatus value), "thumbnail",
        "info" (`_readProjectInfo`: image count, computation status...), "pipeline" (the label of the template it was
        created from, empty if unknown), "pipelineColor" (the color of the template category)}.
        Without `info`, the project file is not read yet: "info" is empty until `_readProjectInfosAsync` reads it.
        The template is matched by its key only: templates of different plugins sharing a key are not told apart.
        """
        if info is None:
            exists = os.path.isfile(path)
            info = {}
        else:
            exists = info["status"] != projectInfo.ProjectStatus.MISSING
        entry = {"path": path, "status": (FileStatus.EXISTS if exists else FileStatus.MISSING).value,
                 "thumbnail": info.get("thumbnail", ""), "info": info}
        source = info.get("sourceTemplate") or {}
        template = next((t for t in self.pipelineTemplateFiles if t["key"] == source.get("name")), None)
        entry["pipeline"] = template["label"] if template else templateInfo.defaultTemplateLabel(source.get("name", ""))
        entry["pipelineColor"] = template["color"] if template else templateInfo.UNCATEGORIZED_COLOR
        return entry

    def _getRecentProjectFilesFromSettings(self) -> list[dict[str, str]]:
        """
        Read the list of recent project files from the QSettings, without reading the files.

        Returns:
            The list of the recent projects stored in the QSettings, as returned by `_projectFileEntry` without info.
        """
        projects = []
        settings = QSettings()
        settings.beginGroup("RecentFiles")
        size = settings.beginReadArray("Projects")
        for i in range(size):
            settings.setArrayIndex(i)
            path = settings.value("filepath")
            if path:
                projects.append(self._projectFileEntry(path))
        settings.endArray()
        settings.endGroup()
        return projects

    def _getRecentTemplateFilesFromSettings(self) -> list[dict[str, str]]:
        """
        Read the list of recent template files from QSettings.

        Returns:
            The list containing dictionaries of the form {"path": "/path/to/template/file", "status": 1}.
        """
        templates = []
        settings = QSettings()
        settings.beginGroup("RecentFiles")
        size = settings.beginReadArray("Templates")
        for i in range(size):
            settings.setArrayIndex(i)
            path = settings.value("filepath")
            if path:
                fileStatus = FileStatus.EXISTS if os.path.isfile(path) else FileStatus.MISSING
                templates.append({"path": path, "status": fileStatus.value})
        settings.endArray()
        settings.endGroup()
        return templates

    def _readProjectInfosAsync(self, paths: list) -> int:
        """ Read the project files at `paths` in a thread, then update their entries with `_applyProjectInfos`.

        A project file is read again only if it was modified since its last read or if it was being computed:
        the status of a project computed without saving it is not updated. Return the id of the read request.
        """
        self._lastProjectInfoRequest += 1
        request = self._lastProjectInfoRequest
        for path in paths:
            self._projectInfoRequests[path] = request
        knownInfos = {p["path"]: p["info"] for p in self._recentProjectFiles if p["info"]}
        activeStatuses = (projectInfo.ProjectStatus.RUNNING, projectInfo.ProjectStatus.SCHEDULED)

        def read():
            infos = {}
            for path in paths:
                info = knownInfos.get(path, {})
                try:
                    modified = int(os.path.getmtime(path) * 1000)
                except OSError:
                    modified = None
                if modified is None or info.get("modified") != modified or info.get("status") in activeStatuses:
                    # An unexpected error must not prevent the other projects from being updated
                    try:
                        info = self._readProjectInfo(path)
                    except Exception:
                        logging.exception(f"Could not read the project file {path}")
                        info = {"status": projectInfo.ProjectStatus.UNKNOWN}
                infos[path] = info
            self._projectInfosRead.emit(request, infos)

        # Daemon: a read still running on network storage must not prevent Meshroom from closing
        Thread(target=read, daemon=True).start()
        return request

    def _applyProjectInfos(self, request: int, infos: dict) -> None:
        """ Update the entries of the project files read by `request`, except the ones read again since. """
        if request == self._refreshRequest:
            self._refreshRequest = 0
        paths = [path for path, r in self._projectInfoRequests.items() if r == request and path in infos]
        for path in paths:
            del self._projectInfoRequests[path]
        # Only the changed entries are updated: an update recreates all the project cards of the homepage
        changed = {p["path"] for p in self._recentProjectFiles if p["path"] in paths and p["info"] != infos[p["path"]]}
        if not changed:
            return
        self._recentProjectFiles = [self._projectFileEntry(p["path"], infos[p["path"]]) if p["path"] in changed else p
                                    for p in self._recentProjectFiles]
        self.recentProjectFilesChanged.emit()

    @Slot()
    def refreshRecentProjectFiles(self) -> None:
        """ Read the recent project files again in a thread to update their computation status, thumbnail and info.
        Ignored while the previous refresh is still running. """
        if not self._refreshRequest:
            self._refreshRequest = self._readProjectInfosAsync([p["path"] for p in self._recentProjectFiles])

    @Slot(str)
    @Slot(QUrl)
    def addRecentProjectFile(self, projectFile) -> None:
        """
        Add a project file to the list of recent project files.
        The function ensures that the file is not present more than once in the list and trims it so it
        never exceeds a set number of projects.
        QSettings are updated accordingly.
        The added project file is read in a thread to show its thumbnail and info.

        Args:
            projectFile (str or QUrl): path to the project file to add to the list
        """
        projectFileNorm = self._normalizeFilepath(projectFile)

        # Get the list of recent projects without re-reading the QSettings
        projects = self._recentProjectFiles

        # Move the entry to the top of the list if it is already in it (its info is shown until it is read again)
        filepaths = [p["path"] for p in projects]
        if projectFileNorm in filepaths:
            entry = projects.pop(filepaths.index(projectFileNorm))
        else:
            entry = self._projectFileEntry(projectFileNorm)
        projects.insert(0, entry)

        # Only keep the first 40 projects
        maxNbProjects = 40
        if len(projects) > maxNbProjects:
            projects = projects[0:maxNbProjects]

        # Update the general settings
        settings = QSettings()
        settings.beginGroup("RecentFiles")
        settings.beginWriteArray("Projects")
        for i, p in enumerate(projects):
            settings.setArrayIndex(i)
            settings.setValue("filepath", p["path"])
        settings.endArray()
        settings.endGroup()
        settings.sync()

        # Update the final list of recent projects
        self._recentProjectFiles = projects
        self.recentProjectFilesChanged.emit()
        self._readProjectInfosAsync([projectFileNorm])

    @Slot(str)
    @Slot(QUrl)
    def addRecentTemplateFile(self, templateFile) -> None:
        """
        Add a template file to the list of recent template files.
        """
        templateFileNorm = self._normalizeFilepath(templateFile)

        templates = self._recentTemplateFiles
        filepaths = [t["path"] for t in templates]
        if templateFileNorm in filepaths:
            idx = filepaths.index(templateFileNorm)
            del templates[idx]

        templates.insert(0, {"path": templateFileNorm, "status": FileStatus.EXISTS.value})

        maxNbTemplates = 40
        if len(templates) > maxNbTemplates:
            templates = templates[0:maxNbTemplates]

        settings = QSettings()
        settings.beginGroup("RecentFiles")
        settings.beginWriteArray("Templates")
        for i, t in enumerate(templates):
            settings.setArrayIndex(i)
            settings.setValue("filepath", t["path"])
        settings.endArray()
        settings.endGroup()
        settings.sync()

        self._recentTemplateFiles = templates
        self.recentTemplateFilesChanged.emit()

    @Slot(str)
    @Slot(QUrl)
    def removeRecentProjectFile(self, projectFile) -> None:
        """
        Remove a given project file from the list of recent project files.
        If the provided filepath is not already present in the list of recent project files, nothing is done.
        Otherwise, it is effectively removed and the QSettings are updated accordingly.
        """
        projectFileNorm = self._normalizeFilepath(projectFile)

        # Get the list of recent projects without re-reading the QSettings
        projects = self._recentProjectFiles

        # Ensure the filepath is in the list of recent projects
        filepaths = [p["path"] for p in projects]
        if projectFileNorm not in filepaths:
            return

        # Delete it from the list
        idx = filepaths.index(projectFileNorm)
        del projects[idx]

        # Update the general settings
        settings = QSettings()
        settings.beginGroup("RecentFiles")
        settings.beginWriteArray("Projects")
        for i, p in enumerate(projects):
            settings.setArrayIndex(i)
            settings.setValue("filepath", p["path"])
        settings.endArray()
        settings.sync()

        # Update the final list of recent projects
        self._recentProjectFiles = projects
        self.recentProjectFilesChanged.emit()

    @staticmethod
    def _normalizeFilepath(filepath) -> str:
        if not isinstance(filepath, (QUrl, str)):
            raise TypeError(f"Unexpected data type: {filepath.__class__}")
        if isinstance(filepath, QUrl):
            filepathNorm = filepath.toLocalFile()
            if not filepathNorm:
                filepathNorm = filepath.toString()
        else:
            filepathNorm = QUrl(filepath).toLocalFile()
            if not filepathNorm:
                filepathNorm = QUrl.fromLocalFile(filepath).toLocalFile()
        return filepathNorm

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
            raise TypeError(f"Unexpected data type: {imagesFolder.__class__}")

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
            raise TypeError(f"Unexpected data type: {imagesFolder.__class__}")

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

    def _systemInfo(self):
        import platform
        import sys
        return {
            'platform': f'{platform.system()} {platform.release()}',
            'python': f"Python {sys.version.split(' ')[0]}",
            'pyside': f'PySide6 {PySideVersion}'
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
        return self._getEnvironmentVariableValue("MESHROOM_USE_8BIT_VIEWER", False)

    def _defaultSequencePlayerEnabled(self):
        return self._getEnvironmentVariableValue("MESHROOM_USE_SEQUENCE_PLAYER", True)

    def _getEnvironmentVariableValue(self, key: str, defaultValue: bool) -> bool:
        """
        Fetch the value of a provided environment variable if it exists, and ensure it is correctly
        evaluated.

        Args:
            key: the key for the environment variable
            defaultValue: the value to use if the key does not exist
        """
        val = os.environ.get(key, defaultValue)
        # os.environ.get returns a string if the key exists, no matter its value, and converting a
        # string to a bool always evaluates to "True"
        if val != True and str(val).lower() in ("0", "false", "off"):
            return False
        return True

    def _submittersList(self):
        """
        Get the list of available submitters
        Model provides :
            name : the name of the submitter
            isDefault : True if this is the current submitter
        """
        submittersList = []
        for i, s in enumerate(meshroom.core.submitters):
            submitterName = s.name if isinstance(s, BaseSubmitter) else s
            # If no explicit default submitter, this will be the first one
            isDefault = (i == 0)
            if self._defaultSubmitterName:
                isDefault = (submitterName == self._defaultSubmitterName)
            submittersList.append({
                "name": submitterName,
                "isDefault": isDefault
            })
        return submittersList

    @Slot(str)
    def setDefaultSubmitter(self, name):
        logging.info(f"Submitter is now set to : {name}")
        self._defaultSubmitterName = name

    activeProjectChanged = Signal()
    activeProject = Property(Variant, lambda self: self._activeProject, notify=activeProjectChanged)

    changelogModel = Property("QVariantList", _changelogModel, constant=True)
    licensesModel = Property("QVariantList", _licensesModel, constant=True)
    pipelineTemplateFilesChanged = Signal()
    recentProjectFilesChanged = Signal()
    # Emitted from a thread with the id of a read request and the info of its project files by path
    _projectInfosRead = Signal(int, object)
    recentTemplateFilesChanged = Signal()
    recentImportedImagesFoldersChanged = Signal()
    pipelineTemplateFiles = Property("QVariantList", _pipelineTemplateFiles, notify=pipelineTemplateFilesChanged)
    pipelineTemplateNames = Property("QVariantList", _pipelineTemplateNames, notify=pipelineTemplateFilesChanged)
    # Templates grouped by category for the homepage: [{"name", "color", "templates"}]
    pipelineTemplateCategories = Property("QVariantList",
                                          lambda self: templateInfo.groupByCategory(self.pipelineTemplateFiles,
                                                                                    self._templateCategoryColors.keys()),
                                          notify=pipelineTemplateFilesChanged)
    recentProjectFiles = Property("QVariantList", lambda self: self._recentProjectFiles, notify=recentProjectFilesChanged)
    recentTemplateFiles = Property("QVariantList", lambda self: self._recentTemplateFiles, notify=recentTemplateFilesChanged)
    recentImportedImagesFolders = Property("QVariantList", _recentImportedImagesFolders, notify=recentImportedImagesFoldersChanged)
    default8bitViewerEnabled = Property(bool, _default8bitViewerEnabled, constant=True)
    defaultSequencePlayerEnabled = Property(bool, _defaultSequencePlayerEnabled, constant=True)
    submittersListModel = Property("QVariantList", _submittersList, constant=True)
