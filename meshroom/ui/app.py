import logging
import os

from PySide2.QtCore import Qt, Slot, QJsonValue, Property, qInstallMessageHandler, QtMsgType
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication

import meshroom
from meshroom.core import nodesDesc
from meshroom.ui import components
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
        args = [args[0], '-style', 'fusion'] + args[1:]  # force Fusion style by default
        super(MeshroomApp, self).__init__(args)

        self.setOrganizationName('AliceVision')
        self.setApplicationName('Meshroom')
        self.setAttribute(Qt.AA_EnableHighDpiScaling)
        self.setApplicationVersion(meshroom.__version__)

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
        r = Reconstruction(parent=self)
        self.engine.rootContext().setContextProperty("_reconstruction", r)
        pm = PaletteManager(self.engine, parent=self)
        self.engine.rootContext().setContextProperty("_PaletteManager", pm)
        fpHelper = FilepathHelper(parent=self)
        self.engine.rootContext().setContextProperty("Filepath", fpHelper)
        scene3DHelper = Scene3DHelper(parent=self)
        self.engine.rootContext().setContextProperty("Scene3DHelper", scene3DHelper)
        self.engine.rootContext().setContextProperty("MeshroomApp", self)
        # Request any potential computation to stop on exit
        self.aboutToQuit.connect(r.stopExecution)

        self.engine.load(os.path.normpath(url))

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
