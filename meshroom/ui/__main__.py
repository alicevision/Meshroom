import signal
import sys
import meshroom
from meshroom.common import Backend

meshroom.setupEnvironment(backend=Backend.PYSIDE)

signal.signal(signal.SIGINT, signal.SIG_DFL)
from meshroom.ui.app import MeshroomApp
app = MeshroomApp(sys.argv)
app.exec()
