import os
import sys

from PySide2.QtCore import Qt
from PySide2.QtGui import QGuiApplication

from meshroom.ui.reconstruction import Reconstruction
from meshroom.ui.utils import QmlInstantEngine

from meshroom.ui import components


if __name__ == "__main__":
    app = QGuiApplication([sys.argv[0], '-style', 'fusion'] + sys.argv[1:])  # force Fusion style as default
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    qmlDir = os.path.join(os.path.dirname(__file__), "qml")
    url = os.path.join(qmlDir, "main.qml")
    engine = QmlInstantEngine()
    engine.addFilesFromDirectory(qmlDir)
    engine.setWatching(os.environ.get("MESHROOM_INSTANT_CODING", False))
    components.registerTypes()

    r = Reconstruction(parent=app)
    engine.rootContext().setContextProperty("_reconstruction", r)

    # Request any potential computation to stop on exit
    app.aboutToQuit.connect(r.stopExecution)

    engine.load(os.path.normpath(url))
    app.exec_()

