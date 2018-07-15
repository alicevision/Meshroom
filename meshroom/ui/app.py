import os

from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication

import meshroom
from meshroom.core import nodesDesc
from meshroom.ui import components
from meshroom.ui.components.filepath import FilepathHelper
from meshroom.ui.palette import PaletteManager
from meshroom.ui.reconstruction import Reconstruction
from meshroom.ui.utils import QmlInstantEngine


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
        self.engine.setOutputWarningsToStandardError(bool(os.environ.get("MESHROOM_OUTPUT_QML_WARNINGS", False)))
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

        # Request any potential computation to stop on exit
        self.aboutToQuit.connect(r.stopExecution)

        self.engine.load(os.path.normpath(url))
