#!/usr/bin/env python
"""
Smoke test of an installed PySide6, run by the CI on the PySide6 built from source (Linux nightly).

Checks, with the "offscreen" Qt platform:
 - Qt is bundled in the PySide6 package (standalone build);
 - the PySide6 modules used by Meshroom import;
 - Python signals are emitted to Python slots (the PyPI wheels crash on emit() with the Python of the
   AliceVision bundle), directly and through queued connections;
 - the QML modules imported by Meshroom load.

Usage:
    pyside6-smoke-test.py                Run the checks; any failure (or crash) gives a non-zero exit code.
    pyside6-smoke-test.py --python-info  Print the identity of the running interpreter (version and build
                                         configuration), to check that PySide6 runs with the interpreter it
                                         was built for.
"""

import importlib
import logging
import os
import sys
import sysconfig
from pathlib import Path

# PySide6 modules imported by Meshroom
PYSIDE6_MODULES = [
    "QtCore", "QtGui", "QtWidgets", "QtQml", "QtQuick", "QtQuickControls2",
    "QtCharts", "Qt3DCore", "Qt3DRender",
]

# QML modules imported by Meshroom (meshroom/ui/qml)
QML_IMPORTS = [
    "QtCore", "QtQml", "QtQml.Models", "QtQuick", "QtQuick.Controls", "QtQuick.Layouts", "QtQuick.Dialogs",
    "QtQuick.Shapes", "QtQuick.Effects", "QtQuick.Window", "QtCharts", "Qt5Compat.GraphicalEffects",
    "QtPositioning", "QtLocation", "Qt.labs.platform", "Qt.labs.qmlmodels", "Qt.labs.folderlistmodel",
]


def pythonInfo():
    """ Return the identity of the running interpreter: version, ABI and build configuration. """
    return "\n".join([
        sys.version,
        str(sysconfig.get_config_var("SOABI")),
        str(sysconfig.get_config_var("CONFIG_ARGS")),
    ])


def checkBundledQt():
    import PySide6
    from PySide6 import QtCore
    qtCore = Path(PySide6.__file__).parent / "Qt" / "lib" / "libQt6Core.so.6"
    if sys.platform.startswith("linux") and not qtCore.is_file():
        raise RuntimeError(f"Qt is not bundled in PySide6: {qtCore} is missing")
    # PySide6 X.Y.Z[.N] bundles Qt X.Y.Z: another version means another Qt (e.g. a system one) was loaded
    if QtCore.qVersion().split(".") != PySide6.__version__.split(".")[:3]:
        raise RuntimeError(f"Qt {QtCore.qVersion()} loaded instead of the Qt {PySide6.__version__} bundled in PySide6")
    logging.info("PySide6 %s, Qt %s: %s", PySide6.__version__, QtCore.qVersion(), Path(PySide6.__file__).parent)


def checkImports():
    for module in PYSIDE6_MODULES:
        importlib.import_module(f"PySide6.{module}")
        logging.info("import PySide6.%s: ok", module)
    import shiboken6
    logging.info("import shiboken6 %s: ok", shiboken6.__version__)


def checkSignals(app):
    """ Emit Python signals to Python slots (function, lambda, bound method), directly and queued. """
    from PySide6.QtCore import QObject, Qt, Signal, Slot

    class Emitter(QObject):
        noArg = Signal()
        text = Signal(str)
        values = Signal(int, "QVariant")
        pyObject = Signal(object)

    class Receiver(QObject):
        def __init__(self):
            super().__init__()
            self.received = []

        @Slot(str)
        def onText(self, value):
            self.received.append(value)

    received = []
    emitter = Emitter()
    receiver = Receiver()
    emitter.noArg.connect(lambda: received.append("noArg"))
    emitter.text.connect(receiver.onText)
    emitter.text.connect(lambda value: received.append(value))
    emitter.values.connect(lambda number, variant: received.append((number, variant)))
    emitter.pyObject.connect(received.append)

    payload = {"key": [1, 2.5, "three"]}
    emitter.noArg.emit()
    emitter.text.emit("hello")
    emitter.values.emit(42, {"a": 1})
    emitter.pyObject.emit(payload)
    expected = ["noArg", "hello", (42, {"a": 1}), payload]
    if received != expected or receiver.received != ["hello"]:
        raise RuntimeError(f"Direct signals: received {received} / {receiver.received}, expected {expected} / ['hello']")
    logging.info("Direct signal emission: ok")

    # Queued connection: the arguments are copied and delivered from the event loop
    queued = []
    emitter.text.connect(lambda value: queued.append(value), Qt.QueuedConnection)
    emitter.text.emit("queued")
    app.processEvents()
    if queued != ["queued"]:
        raise RuntimeError(f"Queued signal: received {queued}, expected ['queued']")
    logging.info("Queued signal emission: ok")


def checkQml():
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    imports = "\n".join(f"import {module}" for module in QML_IMPORTS)
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    component.setData(f"{imports}\nQtObject {{}}\n".encode(), QUrl("smokeTest.qml"))
    obj = component.create()
    if component.isError() or obj is None:
        errors = "\n".join(error.toString() for error in component.errors())
        raise RuntimeError(f"QML imports failed:\n{errors}")
    logging.info("QML imports: ok (%s)", ", ".join(QML_IMPORTS))
    obj.deleteLater()


def main():
    # stdout: the CI compares the output of --python-info
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    if "--python-info" in sys.argv[1:]:
        logging.info(pythonInfo())
        return

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    logging.info("Python: %s", pythonInfo().replace("\n", " | "))
    checkBundledQt()
    checkImports()

    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv[:1])  # QtCharts in QML needs a QApplication
    checkSignals(app)
    checkQml()
    logging.info("PySide6 smoke test passed")


if __name__ == "__main__":
    main()
