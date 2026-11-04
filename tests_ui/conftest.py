"""
Tests of the UI layer (meshroom/ui/*.py), run without QML: `QT_QPA_PLATFORM=offscreen pytest tests_ui/`.

They need the PySide backend, which must be chosen before any import of meshroom.core, as its
BaseObject/Signal types are bound at import time. That choice applies to the whole process and the core
tests do not all pass with it: these tests run in their own pytest session, separately from tests/.
"""
import sys
import warnings

import pytest

import meshroom
from meshroom.common import Backend

if "meshroom.core" in sys.modules:
    # meshroom.core has already been imported with the standalone backend (e.g. `pytest` run from the root,
    # which collects tests/ first): the UI tests cannot run in this session
    warnings.warn("The UI tests are skipped: run them separately with `pytest tests_ui/`.")
    collect_ignore_glob = ["test_*.py"]
else:
    meshroom.setupEnvironment(backend=Backend.PYSIDE)

    from PySide6.QtCore import QCoreApplication

    from meshroom.core.taskManager import TaskManager
    from meshroom.ui import commands
    from meshroom.ui.graph import UIGraph

    @pytest.fixture(scope="session")
    def qApp():
        """ The Qt application, required by the Qt objects of the UI layer. """
        return QCoreApplication.instance() or QCoreApplication([])

    @pytest.fixture
    def undoStack(qApp):
        return commands.UndoStack()

    @pytest.fixture
    def uiGraph(undoStack):
        """ An empty UIGraph, whose modifications are pushed on 'undoStack'. """
        return UIGraph(undoStack, TaskManager())
