import signal
import sys

from meshroom.ui.app import MeshroomApp


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = MeshroomApp(sys.argv)
    app.exec_()
