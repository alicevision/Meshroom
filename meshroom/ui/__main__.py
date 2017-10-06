import os
import sys

from PySide2.QtGui import QGuiApplication
from PySide2.QtQml import QQmlApplicationEngine

from meshroom.ui.reconstruction import Reconstruction
from meshroom.ui.utils import QmlInstantEngine



if __name__ == "__main__":
    app = QGuiApplication(sys.argv)

    qmlDir = os.path.join(os.path.dirname(__file__), "qml")
    url = os.path.join(qmlDir, "main.qml")
    engine = QmlInstantEngine()
    engine.addFilesFromDirectory(qmlDir)
    engine.setWatching(os.environ.get("MESHROOM_INSTANT_CODING", False))
    r = Reconstruction()
    engine.rootContext().setContextProperty("_reconstruction", r)

    engine.load(os.path.normpath(url))
    app.exec_()

