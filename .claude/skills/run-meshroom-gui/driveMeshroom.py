#!/usr/bin/env python
"""
Start the Meshroom GUI, optionally drive it with a scenario, then quit cleanly.

Usage: driveMeshroom.py [--scenario FILE] [--delay SECONDS] [--watchdog SECONDS] [MESHROOM_ARGS...]

A scenario is a Python file defining `run(app, done)`. It is called once the UI is loaded
(after --delay seconds), with `app` the MeshroomApp and `done` a callable to invoke when finished
(possibly later, e.g. from a QTimer). Without a scenario, the GUI is started then quit (smoke test).
"""
import argparse
import faulthandler
import runpy
import signal
import sys

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--scenario", default=None)
parser.add_argument("--delay", type=float, default=8.0)
parser.add_argument("--watchdog", type=float, default=180.0)
args, meshroomArgs = parser.parse_known_args()

# Same as meshroom/ui/__main__.py: without it, SIGINT is swallowed in Qt callbacks and the GUI survives as an orphan
signal.signal(signal.SIGINT, signal.SIG_DFL)
# Dump all stacks and exit if the run hangs, even when the event loop is blocked
faulthandler.dump_traceback_later(args.watchdog, exit=True)

import meshroom
from meshroom.common import Backend
meshroom.setupEnvironment(backend=Backend.PYSIDE)

from PySide6.QtCore import QTimer
import meshroom.ui
import meshroom.ui.app

app = meshroom.ui.app.MeshroomApp([sys.argv[0]] + meshroomArgs)
meshroom.ui.uiInstance = app
app.aboutToQuit.connect(app.terminateManual)


def done(exitCode=0):
    print(f"=== DRIVE: done ({exitCode})", flush=True)
    app.exit(exitCode)


def start():
    print("=== DRIVE: UI loaded", flush=True)
    if not args.scenario:
        done()
        return
    try:
        runpy.run_path(args.scenario)["run"](app, done)
    except Exception:
        import traceback
        traceback.print_exc()
        done(1)


QTimer.singleShot(int(args.delay * 1000), start)
sys.exit(app.exec())
