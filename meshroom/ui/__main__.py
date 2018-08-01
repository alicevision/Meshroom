import signal
import sys
import meshroom


if __name__ == "__main__":
    meshroom.setupEnvironment()

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    from meshroom.ui.app import MeshroomApp
    app = MeshroomApp(sys.argv)
    app.exec_()
