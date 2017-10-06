import os
import sys

from PySide2.QtGui import QGuiApplication
from PySide2.QtQml import QQmlApplicationEngine

from meshroom.ui.reconstruction import Reconstruction



if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    url = os.path.join(os.path.dirname(__file__), "qml", "main.qml")
    engine = QQmlApplicationEngine()

    r = Reconstruction()
    engine.rootContext().setContextProperty("_reconstruction", r)

    engine.load(os.path.normpath(url))
    app.exec_()

