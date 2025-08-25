import logging
import os
import re
import argparse
import json

from PySide6 import __version__ as PySideVersion
from PySide6 import QtCore
from PySide6.QtCore import QUrl, QJsonValue, qInstallMessageHandler, QtMsgType, QSettings, Qt
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlDebuggingEnabler
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication

import meshroom
from meshroom.core import pluginManager
from meshroom.core.taskManager import TaskManager
from meshroom.common import Property, Variant, Signal, Slot

from meshroom.env import EnvVar, EnvVarHelpAction

from meshroom.ui import components
from meshroom.ui.components.clipboard import ClipboardHelper
from meshroom.ui.components.filepath import FilepathHelper
from meshroom.ui.components.scene3D import Scene3DHelper, Transformations3DHelper
from meshroom.ui.components.scriptEditor import ScriptEditorManager
from meshroom.ui.components.thumbnail import ThumbnailCache
from meshroom.ui.palette import PaletteManager
from meshroom.ui.reconstruction import Reconstruction
from meshroom.ui.utils import QmlInstantEngine
from meshroom.ui import commands


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

        # Enable high-DPI scaling before creating QApplication
        QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        super().__init__(inputArgs[:1] + qtArgs)

        # Get DPI information and calculate scaling factors
        self._dpiInfo = self._getDpiInfo()
        self._scalingSettings = self._loadScalingSettings()

        self.setOrganizationName('AliceVision')
        self.setApplicationName('Meshroom')
        self.setApplicationVersion(meshroom.__version_label__)

        # Apply font scaling
        font = self.font()
        basePointSize = 9
        scaledPointSize = int(basePointSize * self._scalingSettings["fontScale"])
        font.setPointSize(scaledPointSize)
        self.setFont(font)

        # Use Fusion style by default.
        QQuickStyle.setStyle("Fusion")

        pwd = os.path.dirname(__file__)
        self.setWindowIcon(QIcon(os.path.join(pwd, "img/meshroom.svg")))

        # Initialize thumbnail cache:
        # - read related environment variables
        # - clean cache directory and make sure it exists on disk
        ThumbnailCache.initialize()

        meshroom.core.initPlugins()
        meshroom.core.initNodes()
        meshroom.core.initSubmitters()

        # Initialize the list of recent project files
        self._recentProjectFiles = self._getRecentProjectFilesFromSettings()
        # Flag set to True if, for all the project files in the list, thumbnails have been retrieved when they
        # are available. If set to False, then all the paths in the list are accurate, but some thumbnails might
        # be retrievable
        self._updatedRecentProjectFilesThumbnails = True

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

        # expose available node types that can be instantiated
        self.engine.rootContext().setContextProperty("_nodeTypes", {n: {"category": pluginManager.getRegisteredNodePlugins()[n].nodeDescriptor.category} for n in sorted(pluginManager.getRegisteredNodePlugins().keys())})

        # instantiate Reconstruction object
        self._undoStack = commands.UndoStack(self)
        self._taskManager = TaskManager(self)
        self._activeProject = Reconstruction(undoStack=self._undoStack, taskManager=self._taskManager, defaultPipeline=args.pipeline, parent=self)
        self._activeProject.setSubmitLabel(args.submitLabel)
        self.engine.rootContext().setContextProperty("_reconstruction", self._activeProject)

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
            projects = self._recentProjectFiles
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

    def _getDpiInfo(self):
        """Get DPI information from the primary screen."""
        screen = self.primaryScreen()
        if screen:
            dpi = screen.logicalDotsPerInch()
            physicalDpi = screen.physicalDotsPerInch()
            devicePixelRatio = screen.devicePixelRatio()
            return {
                "logicalDpi": dpi,
                "physicalDpi": physicalDpi, 
                "devicePixelRatio": devicePixelRatio,
                "isHighDpi": dpi > 96 or devicePixelRatio > 1.0
            }
        return {"logicalDpi": 96, "physicalDpi": 96, "devicePixelRatio": 1.0, "isHighDpi": False}

    def _calculateAutoScaleFactor(self):
        """Calculate automatic UI scale factor based on DPI."""
        dpi = self._dpiInfo["logicalDpi"]
        deviceRatio = self._dpiInfo["devicePixelRatio"]
        
        # Base DPI is 96 (typical for 1x scaling)
        baseDpi = 96
        
        # Calculate scale factor from DPI
        dpiScale = dpi / baseDpi
        
        # Use the maximum of DPI scale and device pixel ratio
        autoScale = max(dpiScale, deviceRatio)
        
        # Clamp to reasonable values (0.5x to 4.0x)
        return max(0.5, min(4.0, autoScale))

    def _loadScalingSettings(self):
        """Load scaling settings from QSettings with automatic defaults."""
        settings = QSettings()
        settings.beginGroup("Display")
        
        autoScale = self._calculateAutoScaleFactor()
        
        scalingSettings = {
            "uiScale": settings.value("uiScale", autoScale, type=float),
            "fontScale": settings.value("fontScale", autoScale, type=float),
            "autoDetect": settings.value("autoDetect", True, type=bool)
        }
        
        settings.endGroup()
        return scalingSettings

    def _saveScalingSettings(self):
        """Save current scaling settings to QSettings."""
        settings = QSettings()
        settings.beginGroup("Display")
        
        settings.setValue("uiScale", self._scalingSettings["uiScale"])
        settings.setValue("fontScale", self._scalingSettings["fontScale"])
        settings.setValue("autoDetect", self._scalingSettings["autoDetect"])
        
        settings.endGroup()
        settings.sync()

    @Slot(float)
    def setUiScale(self, scale):
        """Set UI scale factor."""
        self._scalingSettings["uiScale"] = max(0.5, min(4.0, scale))
        self._saveScalingSettings()
        self.scalingSettingsChanged.emit()

    @Slot(float)
    def setFontScale(self, scale):
        """Set font scale factor."""
        self._scalingSettings["fontScale"] = max(0.5, min(4.0, scale))
        
        # Apply font scaling immediately
        font = self.font()
        basePointSize = 9
        scaledPointSize = int(basePointSize * scale)
        font.setPointSize(scaledPointSize)
        self.setFont(font)
        
        self._saveScalingSettings()
        self.scalingSettingsChanged.emit()

    @Slot(bool)
    def setAutoDetect(self, autoDetect):
        """Enable/disable automatic DPI detection."""
        self._scalingSettings["autoDetect"] = autoDetect
        
        if autoDetect:
            autoScale = self._calculateAutoScaleFactor()
            self.setUiScale(autoScale)
            self.setFontScale(autoScale)
        
        self._saveScalingSettings()

    @Slot()
    def resetScalingToDefaults(self):
        """Reset scaling settings to automatic defaults."""
        autoScale = self._calculateAutoScaleFactor()
        self._scalingSettings = {
            "uiScale": autoScale,
            "fontScale": autoScale,
            "autoDetect": True
        }
        
        # Apply font scaling immediately
        font = self.font()
        basePointSize = 9
        scaledPointSize = int(basePointSize * autoScale)
        font.setPointSize(scaledPointSize)
        self.setFont(font)
        
        self._saveScalingSettings()
        self.scalingSettingsChanged.emit()

    def terminateManual(self):
        self.engine.clearComponentCache()
        self.engine.collectGarbage()
        self.engine.deleteLater()

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

    def _retrieveThumbnailPath(self, filepath: str) -> str:
        """
        Given the path of a project file, load this file and try to retrieve the path to its thumbnail, i.e. its
        first viewpoint image.

        Args:
            filepath: the path of the project file to retrieve the thumbnail from

        Returns:
            The path to the thumbnail if it could be found, an empty string otherwise
        """
        try:
            with open(filepath) as file:
                fileData = json.load(file)

            graphData = fileData.get("graph", {})
            for node in graphData.values():
                if node.get("nodeType") != "CameraInit":
                    continue
                if viewpoints := node.get("inputs", {}).get("viewpoints"):
                    return viewpoints[0].get("path", "")

        except FileNotFoundError:
            logging.info(f"File {filepath} not found on disk.")
        except (json.JSONDecodeError, UnicodeDecodeError):
            logging.info(f"Error while loading file {filepath}.")
        except KeyError as err:
            logging.info(f"The following key does not exist: {str(err)}")
        except Exception as err:
            logging.info(f"Exception: {str(err)}")

        return ""

    def _getRecentProjectFilesFromSettings(self) -> list[dict[str, str]]:
        """
        Read the list of recent project files from the QSettings, retrieve their filepath, and if it exists, their
        thumbnail.

        Returns:
            The list containing dictionaries of the form {"path": "/path/to/project/file", "thumbnail":
            "/path/to/thumbnail"} based on the recent projects stored in the QSettings.
        """
        projects = []
        settings = QSettings()
        settings.beginGroup("RecentFiles")
        size = settings.beginReadArray("Projects")
        for i in range(size):
            settings.setArrayIndex(i)
            path = settings.value("filepath")
            if path:
                p = {"path": path, "thumbnail": self._retrieveThumbnailPath(path)}
                projects.append(p)
        settings.endArray()
        settings.endGroup()
        return projects

    @Slot()
    def updateRecentProjectFilesThumbnails(self) -> None:
        """
        If there are thumbnails that may be retrievable (meaning the list of projects has been updated minimally),
        update the list of recent project files by reading the QSettings and retrieving the thumbnails if they are
        available.
        """
        if not self._updatedRecentProjectFilesThumbnails:
            self._updateRecentProjectFilesThumbnails()
            self._updatedRecentProjectFilesThumbnails = True

    def _updateRecentProjectFilesThumbnails(self) -> None:
        for project in self._recentProjectFiles:
            path = project["path"]
            project["thumbnail"] = self._retrieveThumbnailPath(path)

    @Slot(str)
    @Slot(QUrl)
    def addRecentProjectFile(self, projectFile) -> None:
        """
        Add a project file to the list of recent project files.
        The function ensures that the file is not present more than once in the list and trims it so it
        never exceeds a set number of projects.
        QSettings are updated accordingly.
        The update of the list of recent projects files is minimal: the filepath is added, but there is no
        attempt to retrieve its corresponding thumbnail.

        Args:
            projectFile (str or QUrl): path to the project file to add to the list
        """
        if not isinstance(projectFile, (QUrl, str)):
            raise TypeError(f"Unexpected data type: {projectFile.__class__}")
        if isinstance(projectFile, QUrl):
            projectFileNorm = projectFile.toLocalFile()
            if not projectFileNorm:
                projectFileNorm = projectFile.toString()
        else:
            projectFileNorm = QUrl(projectFile).toLocalFile()
            if not projectFileNorm:
                projectFileNorm = QUrl.fromLocalFile(projectFile).toLocalFile()

        # Get the list of recent projects without re-reading the QSettings
        projects = self._recentProjectFiles

        # Checks whether the path is already in the list of recent projects
        filepaths = [p["path"] for p in projects]
        if projectFileNorm in filepaths:
            idx = filepaths.index(projectFileNorm)
            del projects[idx]  # If so, delete its entry

        # Insert the newest entry at the top of the list
        projects.insert(0, {"path": projectFileNorm, "thumbnail": ""})

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
        self._updatedRecentProjectFilesThumbnails = False  # Thumbnails may not be up-to-date
        self.recentProjectFilesChanged.emit()

    @Slot(str)
    @Slot(QUrl)
    def removeRecentProjectFile(self, projectFile) -> None:
        """
        Remove a given project file from the list of recent project files.
        If the provided filepath is not already present in the list of recent project files, nothing is done.
        Otherwise, it is effectively removed and the QSettings are updated accordingly.
        """
        if not isinstance(projectFile, (QUrl, str)):
            raise TypeError(f"Unexpected data type: {projectFile.__class__}")
        if isinstance(projectFile, QUrl):
            projectFileNorm = projectFile.toLocalFile()
            if not projectFileNorm:
                projectFileNorm = projectFile.toString()
        else:
            projectFileNorm = QUrl(projectFile).toLocalFile()
            if not projectFileNorm:
                projectFileNorm = QUrl.fromLocalFile(projectFile).toLocalFile()

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

    activeProjectChanged = Signal()
    activeProject = Property(Variant, lambda self: self._activeProject, notify=activeProjectChanged)

    scalingSettingsChanged = Signal()
    dpiInfo = Property("QVariantMap", lambda self: self._dpiInfo, constant=True)
    uiScale = Property(float, lambda self: self._scalingSettings["uiScale"], notify=scalingSettingsChanged)
    fontScale = Property(float, lambda self: self._scalingSettings["fontScale"], notify=scalingSettingsChanged)
    autoDetectDpi = Property(bool, lambda self: self._scalingSettings["autoDetect"], notify=scalingSettingsChanged)

    changelogModel = Property("QVariantList", _changelogModel, constant=True)
    licensesModel = Property("QVariantList", _licensesModel, constant=True)
    pipelineTemplateFilesChanged = Signal()
    recentProjectFilesChanged = Signal()
    recentImportedImagesFoldersChanged = Signal()
    pipelineTemplateFiles = Property("QVariantList", _pipelineTemplateFiles, notify=pipelineTemplateFilesChanged)
    pipelineTemplateNames = Property("QVariantList", _pipelineTemplateNames, notify=pipelineTemplateFilesChanged)
    recentProjectFiles = Property("QVariantList", lambda self: self._recentProjectFiles, notify=recentProjectFilesChanged)
    recentImportedImagesFolders = Property("QVariantList", _recentImportedImagesFolders, notify=recentImportedImagesFoldersChanged)
    default8bitViewerEnabled = Property(bool, _default8bitViewerEnabled, constant=True)
    defaultSequencePlayerEnabled = Property(bool, _defaultSequencePlayerEnabled, constant=True)
