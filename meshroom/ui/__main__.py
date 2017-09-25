import PySide2
import os
import sys

from PySide2.QtGui import QGuiApplication
from PySide2.QtQml import QQmlApplicationEngine

from meshroom.ui.reconstruction import Reconstruction

# TODO: remove this
pysideDir = os.path.dirname(PySide2.__file__)
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = pysideDir + '/plugins/platforms'


if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    url = os.path.join(os.path.dirname(__file__), "qml", "main.qml")
    engine = QQmlApplicationEngine()

    r = Reconstruction()
    engine.rootContext().setContextProperty("_reconstruction", r)

    engine.addImportPath(pysideDir + "/qml/")  # TODO: remove this
    engine.load(os.path.normpath(url))
    app.exec_()

