"""
TaskManager computing for real. It needs the PySide backend of meshroom.common (QThread), chosen once per process:
the test suite (standalone backend) runs this file again in a subprocess with the PySide backend.
"""
import os
import shutil
import subprocess
import sys
import tempfile
import time

import pytest

import meshroom.common
from meshroom.core import desc

PYSIDE_BACKEND = meshroom.common.BaseObject.__module__ != "meshroom.common.core"
SUBPROCESS_FLAG = "MESHROOM_TASKMANAGER_SUBPROCESS"


@pytest.mark.skipif(PYSIDE_BACKEND or os.environ.get(SUBPROCESS_FLAG) == "1",
                    reason="Already running with the PySide backend")
def test_taskManagerWithThePySideBackend():
    runner = ("import sys, meshroom; from meshroom.common import Backend; "
              "meshroom.setupEnvironment(backend=Backend.PYSIDE); "
              "import pytest; sys.exit(pytest.main(sys.argv[1:]))")
    result = subprocess.run([sys.executable, "-c", runner, __file__, "-q", "-p", "no:cacheprovider"],
                            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            env=dict(os.environ, **{SUBPROCESS_FLAG: "1"}),
                            capture_output=True, text=True, timeout=600)
    assert result.returncode == 0, result.stdout[-5000:] + result.stderr[-5000:]


class CountRuns(desc.BaseNode):
    """ Computed in the Meshroom process: appends a line to its output file at each run. """
    inputs = [desc.StringParam(name="text", label="Text", description="", value="run")]
    outputs = [desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/runs.txt")]

    def processChunk(self, chunk):
        with open(chunk.node.output.value, "a") as f:
            f.write(chunk.node.text.value + "\n")


@pytest.mark.skipif(not PYSIDE_BACKEND, reason="Runs in a subprocess with the PySide backend")
def test_computeWithForceCompute():
    from PySide6.QtCore import QCoreApplication
    from meshroom.core.graph import Graph
    from meshroom.core.taskManager import TaskManager
    from tests.utils import registeredNodeTypes

    app = QCoreApplication.instance() or QCoreApplication([])
    folder = tempfile.mkdtemp()
    taskManager = TaskManager()
    try:
        with registeredNodeTypes([CountRuns]):
            graph = Graph("")
            node = graph.addNewNode("CountRuns")
            graph.save(os.path.join(folder, "project.mg"))

            def computeAndWait(forceCompute):
                taskManager.compute(graph, [node], forceCompute=forceCompute)
                deadline = time.monotonic() + 30
                while node.globalStatus != "SUCCESS" or taskManager._thread.isRunning():
                    assert time.monotonic() < deadline, node.globalStatus
                    app.processEvents()
                    time.sleep(0.01)

            computeAndWait(forceCompute=False)
            # Used to raise UnboundLocalError ('allReady') once the computation had started
            computeAndWait(forceCompute=True)
            with open(node.output.value) as f:
                assert f.read() == "run\nrun\n"
            graph.clear()
    finally:
        taskManager.join()
        shutil.rmtree(folder, ignore_errors=True)


@pytest.mark.skipif(not PYSIDE_BACKEND, reason="Runs in a subprocess with the PySide backend")
def test_computeFinishedSignal():
    from PySide6.QtCore import QCoreApplication, QThread
    from meshroom.core.graph import Graph
    from meshroom.core.taskManager import TaskManager
    from tests.utils import registeredNodeTypes

    app = QCoreApplication.instance() or QCoreApplication([])
    folder = tempfile.mkdtemp()
    taskManager = TaskManager()
    finished = []
    # A plain callable, without receiver object: still called in the main thread
    taskManager.computeFinished.connect(lambda: finished.append(QThread.currentThread()))

    def waitFor(condition):
        deadline = time.monotonic() + 30
        while not condition():
            assert time.monotonic() < deadline
            app.processEvents()
            time.sleep(0.01)
    try:
        with registeredNodeTypes([CountRuns]):
            graph = Graph("")
            countRuns = graph.addNewNode("CountRuns")
            # A process running until it is stopped: 'cat' waits for a writer on a FIFO
            blocked = graph.addNewNode("AppendText")
            fifo = os.path.join(folder, "blocking.fifo")
            os.mkfifo(fifo)
            blocked.input.value = fifo
            graph.save(os.path.join(folder, "project.mg"))

            # A computation which ends by itself
            taskManager.compute(graph, [countRuns])
            waitFor(lambda: finished)
            assert countRuns.globalStatus == "SUCCESS" and finished == [app.thread()]

            # A computation stopped as the Stop button does (UIGraph.stopExecution)
            taskManager.compute(graph, [blocked])
            waitFor(lambda: blocked.chunksCreated and blocked.chunks[0].isRunning()
                    and getattr(blocked.chunks[0], "subprocess", None) is not None)
            taskManager.requestBlockRestart()
            graph.stopExecution()
            taskManager.join()
            waitFor(lambda: len(finished) == 2)
            assert finished[1] == app.thread()
            taskManager.clear()  # As UIGraph.clear: the TaskManager watches the nodes
            graph.clear()
    finally:
        taskManager.join()
        shutil.rmtree(folder, ignore_errors=True)
