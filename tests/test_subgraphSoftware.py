"""Contexts of other software for the subgraphs: SceneContext, and the tasks started in the environment of their nodes."""
import json
from types import SimpleNamespace

from meshroom.core import desc
from meshroom.core.graph import Graph
from meshroom.core.subgraph import registerContext, run
from meshroom.core.subgraph.contexts import _CONTEXTS, SceneContext
from meshroom.core.subgraph.executor import contextOf
from meshroom.nodes.subgraph.GraphInput import GraphInput
from meshroom.nodes.subgraph.GraphOutput import GraphOutput
from meshroom.nodes.subgraph.SubGraph import SubGraph

from .utils import registerNodeDesc, unregisterNodeDesc


class FakeSoftware:
    """ The module of a software working on scene files: load / save functions, and the open scene. """

    def __init__(self):
        self.scene = ""
        self.loaded, self.saved, self.frames = [], [], []

    def load(self, path):
        self.loaded.append(path)
        self.scene = path

    def save(self, path=None):
        self.saved.append(path or self.scene)

    def clear(self):
        self.scene = ""


SOFTWARE = FakeSoftware()


class FakeSceneContext(SceneContext):
    """ The context of FakeSoftware: its load / save functions are intercepted during a run. """
    interpreterVariable = "MESHROOM_FAKESOFTWARE"
    defaultInterpreter = "fakesoftware-python"
    executables = ("fakesoftware",)

    def open(self):
        self.session = SOFTWARE
        super().open()

    def currentScene(self):
        return self.session.scene

    def _installGuard(self):
        context = self

        def loadWrapper(original):
            def load(path):
                if not context.skipLoad(path):
                    original(path)
            return load

        def saveWrapper(original):
            def save(path=None):
                context.deferSave(path)
            return save

        self._patch(self.session, "load", loadWrapper)
        self._patch(self.session, "save", saveWrapper)

    def _load(self, path):
        self._original("load", self.session.load)(path)

    def _save(self, path):
        self._original("save", self.session.save)(path)

    def _clear(self):
        self.session.clear()

    def beginStep(self, iteration, frame):
        if frame is not None:
            self.session.frames.append(frame)


class SoftwareTask(desc.Node):
    """ A task node of a plugin written for the software: loads the scene, changes it, saves it. """
    __test__ = False
    pythonExecutable = "fakesoftware-python"
    inputs = [desc.File(name="scene", label="Scene", description="", value="/shots/sh010-v001.scn")]
    outputs = []

    def processChunk(self, chunk):
        SOFTWARE.load(chunk.node.scene.value)
        SOFTWARE.save()


_NODE_DESCS = [GraphInput, GraphOutput, SubGraph, SoftwareTask]


def setup_module():
    for nodeDesc in _NODE_DESCS:
        registerNodeDesc(nodeDesc)
    registerContext("fakeSoftware", FakeSceneContext)


def teardown_module():
    for nodeDesc in _NODE_DESCS:
        unregisterNodeDesc(nodeDesc)
    _CONTEXTS.pop("fakeSoftware", None)


def test_taskNodeNeedsTheContextOfItsInterpreter():
    assert contextOf(SoftwareTask()) == ("fakeSoftware",)


def test_scenesLoadedOnceAndSavedOnceInATask():
    """ In a Meshroom task, the nodes loading the open scene do not load it again; their saves are done once. """
    graph = Graph("")
    graph.addNewNode("SoftwareTask")
    graph.addNewNode("SoftwareTask")
    SOFTWARE.__init__()
    run(graph.serialize(asTemplate=True), ownsSession=True)
    assert SOFTWARE.loaded == ["/shots/sh010-v001.scn"]
    assert SOFTWARE.saved == ["/shots/sh010-v001.scn"]
    # The functions of the software are restored, the session owned by the task is cleared
    assert SOFTWARE.load.__name__ == "load" and SOFTWARE.scene == ""


def test_sessionOfTheSoftwarePrevails():
    """ From the session of the software: the open scene is never replaced, nothing is saved. """
    graph = Graph("")
    graph.addNewNode("SoftwareTask")
    SOFTWARE.__init__()
    SOFTWARE.scene = "/shots/open.scn"
    run(graph.serialize(asTemplate=True))
    assert SOFTWARE.loaded == [] and SOFTWARE.saved == []
    assert SOFTWARE.scene == "/shots/open.scn"


class FakeDccTask(desc.Node):
    """ A task node of a plugin needing the fakeSoftware context, whose plugin gives the process environment. """
    __test__ = False
    pythonExecutable = "fakesoftware-python"
    inputs = []
    outputs = []

    def process(self, node):
        pass


def test_subGraphStartedLikeItsTaskNodes():
    """ A subgraph task is started with the interpreter and environment of its task nodes needing its context. """
    from meshroom.core import pluginManager
    registerNodeDesc(FakeDccTask)
    try:
        inner = Graph("")
        inner.addNewNode("FakeDccTask")
        project = Graph("project")
        node = project.addNewNode("SubGraph", subGraph=json.dumps(inner.serialize(asTemplate=True)))
        chunk = SimpleNamespace(node=node)
        assert node.nodeDesc.getPythonExecutable(chunk) == "fakesoftware-python"
        assert node.nodeDesc.getProcessProvider(chunk) is pluginManager.getNodeDescProvider("FakeDccTask")
    finally:
        unregisterNodeDesc(FakeDccTask)


def test_runLiveInTheEnvironmentOfItsNodes(monkeypatch):
    """ Run Live starts the interpreter of a task node of the subgraph, in the process environment of its plugin. """
    import subprocess
    from meshroom.core import pluginManager
    from meshroom.core.subgraph.runner import EVENT_MARK, runLive
    registerNodeDesc(FakeDccTask)
    try:
        monkeypatch.setattr(FakeSceneContext, "isAvailable", classmethod(lambda cls: False))
        provider = pluginManager.getNodeDescProvider("FakeDccTask")
        processEnv = type("Env", (), {"getCommandPrefix": lambda self: "rez env fakesoftware -- ",
                                      "getCommandSuffix": lambda self: "", "getEnvDict": lambda self: None})()
        monkeypatch.setattr(type(provider), "processEnv", property(lambda self: processEnv))
        calls = []

        class FakePopen:
            """ The process of the subgraph: reports a node status, then writes its result. """

            def __init__(self, command, **kwargs):
                calls.append((command, kwargs))
                resultPath = command[-1]
                with open(resultPath, "w") as f:
                    json.dump({"outputs": {}, "elapsed": 0.1}, f)
                self.stdout = iter(["some output\n", EVENT_MARK + json.dumps(["FakeDccTask_1", "SUCCESS", "Done"]) + "\n"])

            def wait(self):
                return 0

        monkeypatch.setattr(subprocess, "Popen", FakePopen)
        graph = Graph("")
        graph.addNewNode("FakeDccTask")
        events = []
        result = runLive(graph.serialize(asTemplate=True), onNode=lambda *event: events.append(event))
        assert events == [("FakeDccTask_1", "SUCCESS", "Done")] and result["nodes"] == {"FakeDccTask_1": "SUCCESS"}
        command, kwargs = calls[0]
        assert command[:5] == ["rez", "env", "fakesoftware", "--", "fakesoftware-python"]
        assert command[-1].endswith("result.json") and "shell" not in kwargs
        assert result["interpreter"] == "fakesoftware-python"
    finally:
        unregisterNodeDesc(FakeDccTask)


def test_frameLoopSetsTheFrameOfTheSoftware():
    graph = Graph("")
    graph.addNewNode("SoftwareTask")
    SOFTWARE.__init__()
    from meshroom.core.subgraph import Loop
    run(graph.serialize(asTemplate=True), context="fakeSoftware", loop=Loop("frames", first=1001, last=1003),
        ownsSession=True)
    assert SOFTWARE.frames == [1001, 1002, 1003]
