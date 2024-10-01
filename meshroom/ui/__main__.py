import signal
import sys
import meshroom
from meshroom.common import Backend

meshroom.setupEnvironment(backend=Backend.PYSIDE)

signal.signal(signal.SIGINT, signal.SIG_DFL)
import meshroom.ui
import meshroom.ui.app

meshroom.ui.uiInstance = meshroom.ui.app.MeshroomApp(sys.argv)
meshroom.ui.uiInstance.exec()
