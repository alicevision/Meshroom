"""Tests of the subgraphs: live nodes run in memory by meshroom.core.subgraph, and the nodes running them."""
import json
import os

import pytest

from meshroom.core import desc
from meshroom.core.graph import Graph, loadGraph
from meshroom.core.node import Status
from meshroom.core.subgraph import Loop, SubGraphError, SubGraphPlan, registerContext, run
from meshroom.core.subgraph.contexts import LiveContext, _CONTEXTS
from meshroom.core.subgraph.ports import anySetValues, formatPortSpec, parsePortSpec
from meshroom.nodes.subgraph.GraphInput import GraphInput
from meshroom.nodes.subgraph.GraphOutput import GraphOutput
from meshroom.nodes.subgraph.LiveScript import LiveScript
from meshroom.nodes.subgraph.SubGraph import SubGraph

from .utils import registerNodeDesc, unregisterNodeDesc


class LiveAdd(desc.LiveNode):
    """ sum = a + b """
    __test__ = False
    inputs = [
        desc.LiveValue(name="a", label="A", description="", value=0),
        desc.LiveValue(name="b", label="B", description="", value=0),
    ]
    outputs = [
        desc.LiveValue(name="sum", label="Sum", description=""),
    ]

    def execute(self, ctx, inputs):
        return {"sum": inputs["a"] + inputs["b"]}


class LiveRecord(desc.LiveNode):
    """ Appends (iteration, frame, value) to ctx.variables["records"] and passes the value through. """
    __test__ = False
    inputs = [
        desc.LiveValue(name="value", label="Value", description=""),
    ]
    outputs = [
        desc.LiveValue(name="out", label="Out", description=""),
    ]

    def execute(self, ctx, inputs):
        ctx.variables.setdefault("records", []).append((ctx.iteration, ctx.frame, inputs["value"]))
        return {"out": inputs["value"]}


class LiveFail(desc.LiveNode):
    __test__ = False
    inputs = []
    outputs = []

    def execute(self, ctx, inputs):
        raise ValueError("broken")


class LiveDccOnly(desc.LiveNode):
    __test__ = False
    context = "fakeDcc"
    inputs = []
    outputs = [
        desc.LiveValue(name="session", label="Session", description=""),
    ]

    def execute(self, ctx, inputs):
        return {"session": ctx.context.session}


class FakeDccContext(LiveContext):
    """ A context recording its opening and closing. """
    events = []

    def open(self):
        super().open()
        self.session = "fakeSession"
        FakeDccContext.events.append("open")

    def close(self):
        super().close()
        FakeDccContext.events.append("close")


class TaskShotScene(desc.Node):
    """ A task node computing a value (like a pipeline node giving the scene of a shot). """
    __test__ = False
    runs = 0
    inputs = [
        desc.StringParam(name="shot", label="Shot", description="", value="sh010"),
    ]
    outputs = [
        desc.File(name="scene", label="Scene", description="", value=None),
    ]

    def process(self, node):
        TaskShotScene.runs += 1
        node.scene.value = f"/shots/{node.shot.value}.hip"


_NODE_DESCS = [GraphInput, GraphOutput, LiveScript, SubGraph, LiveAdd, LiveRecord, LiveFail, LiveDccOnly,
               TaskShotScene]


def setup_module():
    for nodeDesc in _NODE_DESCS:
        registerNodeDesc(nodeDesc)
    registerContext("fakeDcc", FakeDccContext)


def teardown_module():
    for nodeDesc in _NODE_DESCS:
        unregisterNodeDesc(nodeDesc)
    _CONTEXTS.pop("fakeDcc", None)


def port(node, anySetName, name):
    return node.attribute(anySetName).value.get(name)


def addOneGraph():
    """ GraphInput(x) -> LiveAdd(x + 1) -> GraphOutput(x) """
    graph = Graph("addOne")
    graphInput = graph.addNewNode("GraphInput", portSpec="x")
    add = graph.addNewNode("LiveAdd", b=1)
    graphOutput = graph.addNewNode("GraphOutput", portSpec="x")
    graph.addEdge(port(graphInput, "ports", "x"), add.a)
    graph.addEdge(add.sum, port(graphOutput, "ports", "x"))
    return graph


# ---------------------------------------------------------------------------
# Ports
# ---------------------------------------------------------------------------

def test_parsePortSpec():
    assert parsePortSpec("a, b:IntParam\nc;d:Unknown, 1bad, a") == [
        ("a", "LiveValue", "a"), ("b", "IntParam", "b"), ("c", "LiveValue", "c"), ("d", "LiveValue", "d")]
    assert parsePortSpec(None) == []
    spec = formatPortSpec([("a", "LiveValue", "Shot Name"), ("b", "ChoiceParam")])
    assert parsePortSpec(spec) == [("a", "LiveValue", "Shot Name"), ("b", "LiveValue", "b")]


def test_anySetValues():
    assert anySetValues({"expanded": True, "children": [{"name": "a", "value": 1}]}) == {"a": 1}
    assert anySetValues([{"name": "a", "value": 1}]) == {"a": 1}
    assert anySetValues({"a": 1}) == {"a": 1}
    assert anySetValues(None) == {}


def test_portSpecSyncsAnySet():
    graph = Graph("")
    node = graph.addNewNode("GraphInput", portSpec="a, b:IntParam")
    assert [(c.name, type(c.desc).__name__) for c in node.ports.value] == [("a", "LiveValue"), ("b", "IntParam")]
    add = graph.addNewNode("LiveAdd")
    graph.addEdge(port(node, "ports", "a"), add.a)

    node.portSpec.value = "b, c"
    assert [c.name for c in node.ports.value] == ["b", "c"]
    # The connection to the removed port is removed
    assert not add.a.isLink


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def test_runChain():
    graph = Graph("")
    graphInput = graph.addNewNode("GraphInput", portSpec="a, b")
    script = graph.addNewNode("LiveScript", inSpec="x, y", outSpec="product",
                              code="outs['product'] = ins['x'] * ins['y']")
    add = graph.addNewNode("LiveAdd", b=10)
    graphOutput = graph.addNewNode("GraphOutput", portSpec="result, product")
    graph.addEdge(port(graphInput, "ports", "a"), port(script, "ins", "x"))
    graph.addEdge(port(graphInput, "ports", "b"), port(script, "ins", "y"))
    graph.addEdge(port(script, "outs", "product"), add.a)
    graph.addEdge(add.sum, port(graphOutput, "ports", "result"))
    graph.addEdge(port(script, "outs", "product"), port(graphOutput, "ports", "product"))

    assert run(graph.toDict(), {"a": 3, "b": 4}) == {"result": 22, "product": 12}
    # Any Python object goes through the nodes
    assert run(graph.toDict(), {"a": 1.5, "b": 2}) == {"result": 13.0, "product": 3.0}


def test_runTemplateFile(tmp_path):
    graph = addOneGraph()
    templatePath = str(tmp_path / "addOne.mgt")
    graph.save(templatePath, template=True)
    assert run(templatePath, {"x": 1}) == {"x": 2}

    # Loading the template restores the ports and their connections
    loaded = loadGraph(templatePath)
    assert port(loaded.node("GraphOutput_1"), "ports", "x").isLink
    assert run(loaded.toDict(), {"x": 5}) == {"x": 6}


def test_countLoopFeedback():
    graph = addOneGraph()
    assert run(graph.toDict(), {"x": 0}, loop=Loop("count", iterations=5)) == {"x": 5}
    assert run(graph.toDict(), {"x": 0}, loop=Loop("count", iterations=0)) == {}


def test_frameLoop():
    graph = Graph("")
    graphInput = graph.addNewNode("GraphInput")
    record = graph.addNewNode("LiveRecord")
    graph.addEdge(graphInput.frame, record.value)
    variables = {}
    run(graph.toDict(), loop=Loop("frames", first=1001, last=1005, step=2), variables=variables)
    assert variables["records"] == [(0, 1001, 1001), (1, 1003, 1003), (2, 1005, 1005)]

    loop = Loop("frames", first=1, last=10).subset(4, 8)
    assert loop.frames == [5, 6, 7, 8]
    assert Loop.fromDict(loop.asDict()).frames == [5, 6, 7, 8]


def test_taskNodesRunInTheSubGraph():
    """ A task node runs in the process of the subgraph; its outputs go to the next nodes in memory. """
    TaskShotScene.runs = 0
    graph = Graph("")
    shotScene = graph.addNewNode("TaskShotScene", shot="sh020")
    script = graph.addNewNode("LiveScript", inSpec="scene", outSpec="upper", code="outs['upper'] = ins['scene'].upper()")
    graphOutput = graph.addNewNode("GraphOutput", portSpec="upper")
    graph.addEdge(shotScene.scene, port(script, "ins", "scene"))
    graph.addEdge(port(script, "outs", "upper"), port(graphOutput, "ports", "upper"))
    assert run(graph.toDict()) == {"upper": "/SHOTS/SH020.HIP"}
    assert TaskShotScene.runs == 1
    # A value set at launch, without declaring a port
    assert run(graph.toDict(), overrides={"TaskShotScene_1.shot": "sh030"}) == {"upper": "/SHOTS/SH030.HIP"}


def test_nestedSubGraph():
    inner = addOneGraph().toDict()
    graph = Graph("")
    graphInput = graph.addNewNode("GraphInput", portSpec="x")
    nested = graph.addNewNode("SubGraph", subGraph=json.dumps(inner), loopMode="count", iterations=3)
    graphOutput = graph.addNewNode("GraphOutput", portSpec="x")
    # The ports of the nested subgraph are its attributes
    assert [c.name for c in nested.ins.value] == ["x"]
    assert [c.name for c in nested.outs.value] == ["x"]
    graph.addEdge(port(graphInput, "ports", "x"), port(nested, "ins", "x"))
    graph.addEdge(port(nested, "outs", "x"), port(graphOutput, "ports", "x"))

    # 3 inner iterations per outer one, 2 outer iterations
    assert run(graph.toDict(), {"x": 0}, loop=Loop("count", iterations=2)) == {"x": 6}


def test_nestedSubGraphSeesParentFrame():
    inner = Graph("")
    innerInput = inner.addNewNode("GraphInput")
    record = inner.addNewNode("LiveRecord")
    inner.addEdge(innerInput.frame, record.value)
    graph = Graph("")
    graph.addNewNode("SubGraph", subGraph=json.dumps(inner.toDict()))
    variables = {}
    run(graph.toDict(), loop=Loop("frames", first=10, last=11), variables=variables)
    assert [frame for _, frame, _ in variables["records"]] == [10, 11]


def test_contextOpenedOnce():
    FakeDccContext.events.clear()
    graph = Graph("")
    dcc = graph.addNewNode("LiveDccOnly")
    graphOutput = graph.addNewNode("GraphOutput", portSpec="session")
    graph.addEdge(dcc.session, port(graphOutput, "ports", "session"))
    # The context needed by the nodes is chosen
    assert run(graph.toDict(), loop=Loop("count", iterations=3)) == {"session": "fakeSession"}
    assert FakeDccContext.events == ["open", "close"]

    with pytest.raises(SubGraphError, match="cannot run in the 'python' context"):
        run(graph.toDict(), context="python")


def test_errors():
    graph = Graph("")
    graph.addNewNode("LiveFail")
    with pytest.raises(SubGraphError, match="LiveFail_1: ValueError: broken"):
        run(graph.toDict())

    with pytest.raises(SubGraphError, match="Unknown node type 'Missing'"):
        SubGraphPlan({"Missing_1": {"nodeType": "Missing", "inputs": {}}})

    with pytest.raises(SubGraphError, match="No attribute 'LiveAdd_1.nope'"):
        run(addOneGraph().toDict(), {"x": 1}, overrides={"LiveAdd_1.nope": 1})

    with pytest.raises(SubGraphError, match="at most one GraphInput"):
        SubGraphPlan({"GraphInput_1": {"nodeType": "GraphInput", "inputs": {}},
                      "GraphInput_2": {"nodeType": "GraphInput", "inputs": {}}})


def test_liveNodesAreNotComputed():
    graph = addOneGraph()
    for node in graph.nodes:
        assert not node._isComputableType()


# ---------------------------------------------------------------------------
# SubGraph node
# ---------------------------------------------------------------------------

def test_subGraphNodePorts(tmp_path):
    templatePath = str(tmp_path / "addOne.mgt")
    addOneGraph().save(templatePath, template=True)

    graph = Graph("")
    node = graph.addNewNode("SubGraph", template=templatePath)
    assert [c.name for c in node.ins.value] == ["x"]
    assert [c.name for c in node.outs.value] == ["x"]

    node.onAttributeClicked(node.makeLocal)
    assert node.template.value == ""
    assert "GraphInput_1" in json.loads(node.subGraph.value)
    assert [c.name for c in node.ins.value] == ["x"]

    node.subGraph.value = ""
    assert len(node.ins.value) == 0


def test_subGraphNodeFrameChunks():
    graph = Graph("")
    node = graph.addNewNode("SubGraph", subGraph=json.dumps(addOneGraph().toDict()), loopMode="frames",
                            frameRange={"start": 1001, "stop": 1010}, framesPerTask=4)
    node.createChunks()
    ranges = [(chunk.range.start, chunk.range.end) for chunk in node.chunks]
    frames = [Loop("frames", first=1001, last=1010).subset(start, end).frames for start, end in ranges]
    assert frames == [[1001, 1002, 1003, 1004], [1005, 1006, 1007, 1008], [1009, 1010]]


def test_subGraphNodeCompute(graphSavedOnDisk):
    graph: Graph = graphSavedOnDisk
    node = graph.addNewNode("SubGraph", subGraph=json.dumps(addOneGraph().toDict()), loopMode="count",
                            iterations=4)
    port(node, "ins", "x").value = 10
    graph.save()
    os.makedirs(node.internalFolder, exist_ok=True)
    node.createChunks()
    node.prepareLogger(0)
    node.chunks[0].process(True, True)
    node.restoreLogger()
    assert node.chunks[0].status.status == Status.SUCCESS
    assert port(node, "outs", "x").value == 14


# ---------------------------------------------------------------------------
# Houdini (with a fake hou module)
# ---------------------------------------------------------------------------

class FakeParm:
    def __init__(self, value=None):
        self.value, self.expression, self.locked = value, None, False

    def set(self, value):
        self.value = value

    def setExpression(self, expression, language=None):
        self.expression = expression

    def isLocked(self):
        return self.locked

    def lock(self, locked):
        self.locked = locked

    def deleteAllKeyframes(self):
        self.expression = None

    def eval(self):
        return self.value

    def evalAtFrame(self, frame):
        return self.value.replace("$F4", f"{frame:04d}")


class FakeRop:
    def __init__(self, hou):
        self.hou, self.renders = hou, []
        self.parms = {"vm_picture": FakeParm("/render/beauty.$F4.exr")}

    def path(self):
        return "/out/mantra1"

    def parm(self, name):
        return self.parms.get(name)

    def render(self, **kwargs):
        self.renders.append(kwargs.get("frame_range"))

    def errors(self):
        return ()


class FakeHou:
    """ The parts of the hou module used by the Houdini live nodes. """

    class exprLanguage:
        Hscript = "hscript"

    def __init__(self):
        hou = self
        self.frames, self.loaded, self.saved = [], [], []
        self.parms = {"/obj/geo1/tx": FakeParm(0), "/obj/geo1/ry": FakeParm(0)}
        self.tuples = {}
        self.rop = FakeRop(self)

        class HipFile:
            current = "/scenes/untitled.hip"

            def path(self):
                return self.current

            def load(self, path, **kwargs):
                hou.loaded.append(path)
                self.current = path

            def save(self, path=None):
                self.current = path or self.current
                hou.saved.append(self.current)

            def clear(self, **kwargs):
                hou.loaded.append("clear")

        self.hipFile = HipFile()

    def parm(self, path):
        return self.parms.get(path)

    def parmTuple(self, path):
        return self.tuples.setdefault(path, FakeParm())

    def node(self, path):
        return self.rop if path == "/out/mantra1" else None

    def setFrame(self, frame):
        self.frames.append(frame)


@pytest.fixture
def fakeHou(monkeypatch):
    import sys
    from meshroom.nodes.houdini.HoudiniScene import HoudiniScene
    from meshroom.nodes.houdini.HoudiniSave import HoudiniSave
    from meshroom.nodes.houdini.HoudiniRender import HoudiniRender
    from meshroom.nodes.houdini.HoudiniSetParms import HoudiniSetParms
    nodeDescs = [HoudiniScene, HoudiniSave, HoudiniRender, HoudiniSetParms, BatchSetParm]
    for nodeDesc in nodeDescs:
        registerNodeDesc(nodeDesc)
    hou = FakeHou()
    monkeypatch.setitem(sys.modules, "hou", hou)
    yield hou
    for nodeDesc in nodeDescs:
        unregisterNodeDesc(nodeDesc)


def test_houdiniChain(fakeHou):
    graph = Graph("")
    graphInput = graph.addNewNode("GraphInput", portSpec="hip, offset")
    openScene = graph.addNewNode("HoudiniScene")
    setParms = graph.addNewNode("HoudiniSetParms", parms="/obj/geo1/ry := $F * 2\n/obj/geo1/t = (1, 2, 3)",
                                parmPath="/obj/geo1/tx")
    render = graph.addNewNode("HoudiniRender")
    graphOutput = graph.addNewNode("GraphOutput", portSpec="image")
    graph.addEdge(port(graphInput, "ports", "hip"), openScene.hipFile)
    graph.addEdge(port(graphInput, "ports", "offset"), setParms.value)
    graph.addEdge(openScene.scene, setParms.scene)
    graph.addEdge(setParms.sceneOut, render.scene)
    graph.addEdge(render.outputFile, port(graphOutput, "ports", "image"))

    # A Meshroom task: the scene is opened once (then it is the current scene), the frame follows the loop
    outputs = run(graph.toDict(), {"hip": "/scenes/shot.hip", "offset": 5}, loop=Loop("frames", first=1, last=3),
                  ownsSession=True)
    assert outputs == {"image": "/render/beauty.0003.exr"}
    assert fakeHou.loaded == ["/scenes/shot.hip", "clear"]
    assert fakeHou.frames == [1, 2, 3]
    assert fakeHou.rop.renders == [(1, 1), (2, 2), (3, 3)]
    assert fakeHou.parms["/obj/geo1/tx"].value == 5
    assert fakeHou.parms["/obj/geo1/ry"].expression == "$F * 2"
    assert fakeHou.tuples["/obj/geo1/t"].value == (1, 2, 3)


class BatchSetParm(desc.Node):
    """ A Houdini task node written as usual: it loads the scene, changes it, saves it. """
    __test__ = False
    pythonExecutable = "hython"
    inputs = [
        desc.File(name="scene", label="Scene", description="", value=""),
        desc.StringParam(name="parmPath", label="Parm", description="", value="/obj/geo1/tx"),
        desc.FloatParam(name="value", label="Value", description="", value=1.0),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value=None),
    ]

    def process(self, node):
        import hou
        hou.hipFile.load(node.scene.value, suppress_save_prompt=True)
        hou.parm(node.parmPath.value).set(node.value.value)
        hou.hipFile.save(node.scene.value)
        node.output.value = node.scene.value


def houdiniSceneGraph():
    """ TaskShotScene -> HoudiniScene -> BatchSetParm (tx) -> BatchSetParm (ry) -> HoudiniSave """
    TaskShotScene.runs = 0
    graph = Graph("")
    shotScene = graph.addNewNode("TaskShotScene", shot="sh010")
    scene = graph.addNewNode("HoudiniScene")
    tx = graph.addNewNode("BatchSetParm", parmPath="/obj/geo1/tx", value=2.0)
    ry = graph.addNewNode("BatchSetParm", parmPath="/obj/geo1/ry", value=45.0)
    save = graph.addNewNode("HoudiniSave")
    graph.addEdge(shotScene.scene, scene.hipFile)
    graph.addEdge(scene.scene, tx.scene)
    graph.addEdge(tx.output, ry.scene)
    graph.addEdge(ry.output, save.scene)
    return graph


def test_houdiniMeshroomTask(fakeHou):
    """ In a Meshroom task: the pipeline node gives the scene, opened once, saved once at the end. """
    assert run(houdiniSceneGraph().toDict(), ownsSession=True) == {}
    assert TaskShotScene.runs == 1
    assert fakeHou.loaded == ["/shots/sh010.hip", "clear"]
    assert fakeHou.saved == ["/shots/sh010.hip"]
    assert fakeHou.parms["/obj/geo1/tx"].value == 2.0 and fakeHou.parms["/obj/geo1/ry"].value == 45.0
    # The real load / save are back after the run
    assert fakeHou.hipFile.load.__name__ == "load" and "HipFile" in type(fakeHou.hipFile).__name__


def test_houdiniSession(fakeHou):
    """ In a Houdini session: the open scene prevails, the pipeline node is not run, nothing is saved. """
    import meshroom.subgraph
    fakeHou.hipFile.current = "/shots/current.hip"
    meshroom.subgraph.run(houdiniSceneGraph().toDict())
    assert TaskShotScene.runs == 0
    assert fakeHou.loaded == [] and fakeHou.saved == []
    assert fakeHou.parms["/obj/geo1/tx"].value == 2.0 and fakeHou.parms["/obj/geo1/ry"].value == 45.0

    # Save In Houdini Session: saved once
    graph = houdiniSceneGraph()
    graph.node("HoudiniSave_1").saveInSession.value = True
    meshroom.subgraph.run(graph.toDict())
    assert fakeHou.saved == ["/shots/current.hip"]


def test_flowDependencies():
    """ A flow connection runs a node after another one, without passing a value. """
    from meshroom.core.subgraph.contexts import createContext
    from meshroom.core.subgraph.executor import RunContext, executionOrder
    graph = SubGraphPlan({
        "LiveAdd_1": {"nodeType": "LiveAdd", "inputs": {}, "internalInputs": {"flowInputs": ["{LiveAdd_2.flowOutput}"]}},
        "LiveAdd_2": {"nodeType": "LiveAdd", "inputs": {}},
    }).build()
    order = executionOrder(graph, RunContext(createContext("python"), Loop()))
    assert [node.name for node in order] == ["LiveAdd_2", "LiveAdd_1"]


# ---------------------------------------------------------------------------
# Editing (enter / leave a subgraph)
# ---------------------------------------------------------------------------

def test_editEmbeddedSubGraph():
    from meshroom.core.subgraph.editing import SubGraphStack
    project = Graph("project")
    node = project.addNewNode("SubGraph", subGraph=json.dumps(addOneGraph().toDict()))
    stack = SubGraphStack()
    inner = stack.enter(project, node)
    assert stack.names() == [node.name]
    assert sorted(n.name for n in inner.nodes) == ["GraphInput_1", "GraphOutput_1", "LiveAdd_1"]

    # Leaving without changes keeps the node as it is
    content = node.subGraph.value
    assert stack.exit(inner) is project
    assert node.subGraph.value == content

    # A new port in the subgraph becomes an input of the node
    inner = stack.enter(project, node)
    inner.node("GraphInput_1").portSpec.value = "x, y"
    assert stack.commitAll(inner) is project
    assert [c.name for c in node.ins.value] == ["x", "y"]
    stack.exit(inner)
    assert len(stack) == 0
    assert run(node.subGraph.value, {"x": 1}) == {"x": 2}


def test_editNestedAndTemplateSubGraph(tmp_path):
    from meshroom.core.subgraph.editing import SubGraphStack
    templatePath = str(tmp_path / "addOne.mgt")
    addOneGraph().save(templatePath, template=True)
    project = Graph("project")
    outer = project.addNewNode("SubGraph")
    stack = SubGraphStack()
    level1 = stack.enter(project, outer)
    # A new SubGraph node starts with a GraphInput and a GraphOutput
    assert sorted(n.nodeType for n in level1.nodes) == ["GraphInput", "GraphOutput"]
    nested = level1.addNewNode("SubGraph", template=templatePath)
    level2 = stack.enter(level1, nested)
    assert stack.names() == [outer.name, nested.name]
    level2.node("LiveAdd_1").b.value = 100

    # Saving the project writes every level back: the template file, then the embedded subgraph
    assert stack.commitAll(level2) is project
    assert run(templatePath, {"x": 1}) == {"x": 101}
    assert "SubGraph_1" in json.loads(outer.subGraph.value)["graph"]
    assert stack.exit(level2) is level1
    assert stack.exit(level1) is project


# ---------------------------------------------------------------------------
# Run Live (in the interpreter of the context)
# ---------------------------------------------------------------------------

def scriptGraph():
    graph = Graph("")
    graphInput = graph.addNewNode("GraphInput", portSpec="x")
    script = graph.addNewNode("LiveScript", inSpec="x", outSpec="y", code="outs['y'] = ins['x'] * 3")
    graphOutput = graph.addNewNode("GraphOutput", portSpec="y, obj")
    graph.addEdge(port(graphInput, "ports", "x"), port(script, "ins", "x"))
    graph.addEdge(port(script, "outs", "y"), port(graphOutput, "ports", "y"))
    return graph


def test_runLiveInProcess():
    from meshroom.core.subgraph.runner import runLive
    result = runLive(scriptGraph().serialize(asTemplate=True), {"x": 2})
    assert result["outputs"] == {"y": 6, "obj": None}
    assert result["interpreter"] == ""


def test_runLiveInInterpreter(monkeypatch):
    """ A context not available here runs in its interpreter (here another Python). """
    import sys
    from meshroom.core.subgraph.contexts import PythonContext
    from meshroom.core.subgraph.runner import runLive
    monkeypatch.setattr(PythonContext, "isAvailable", classmethod(lambda cls: False))
    monkeypatch.setattr(PythonContext, "interpreter", classmethod(lambda cls: [sys.executable]))
    result = runLive(scriptGraph().serialize(asTemplate=True), {"x": 5}, context="python")
    assert result["outputs"] == {"y": 15, "obj": None}
    assert result["interpreter"] == sys.executable

    graph = scriptGraph()
    graph.node("LiveScript_1").code.value = "raise RuntimeError('boom')"
    with pytest.raises(SubGraphError, match="LiveScript_1: RuntimeError: boom"):
        runLive(graph.serialize(asTemplate=True), {"x": 5}, context="python")


# ---------------------------------------------------------------------------
# Ports edited on the node or in the subgraph
# ---------------------------------------------------------------------------

def connectToAnySet(graph, src, anySet):
    """ What the user interface does when an attribute is connected to an AnySet (ConnectAnySetCommand). """
    child = anySet.duplicateAttribute(src, isOutput=anySet.isOutput)
    if anySet.isOutput:
        graph.addEdge(child, src)
    else:
        graph.addEdge(src, child)
    return child


def test_portsAddedOnTheNodeGoIntoTheSubGraph():
    from meshroom.core.subgraph.editing import SubGraphStack
    project = Graph("project")
    upstream = project.addNewNode("Ls", input="/folder")
    node = project.addNewNode("SubGraph")
    child = connectToAnySet(project, upstream.input, node.ins)
    child.root.renameAttribute(child, child.name, "Shot Folder")

    stack = SubGraphStack()
    inner = stack.enter(project, node)
    graphInput = inner.node("GraphInput_1")
    assert [(c.name, c.label) for c in graphInput.ports.value] == [(child.name, "Shot Folder")]

    # The label changed in the subgraph comes back on the node, the connection stays
    port(graphInput, "ports", child.name).root.renameAttribute(port(graphInput, "ports", child.name), child.name, "Folder")
    stack.exit(inner)
    newChild = port(node, "ins", child.name)
    assert newChild.label == "Folder"
    assert newChild.isLink and newChild.inputLink is upstream.input


def test_portsAddedInTheSubGraph():
    from meshroom.core.subgraph.editing import SubGraphStack
    project = Graph("project")
    node = project.addNewNode("SubGraph")
    stack = SubGraphStack()
    inner = stack.enter(project, node)
    add = inner.addNewNode("LiveAdd")
    connectToAnySet(inner, add.a, inner.node("GraphInput_1").ports)
    connectToAnySet(inner, add.sum, inner.node("GraphOutput_1").ports)
    stack.exit(inner)
    assert [c.name for c in node.ins.value] == ["a"]
    assert [c.name for c in node.outs.value] == ["sum"]
    # The ports are in the saved subgraph (template form, without the outputs)
    port(node, "ins", "a").value = 4
    assert run(node.subGraph.value, {"a": 4}) == {"sum": 4}


def test_portsAddedOnTemplateNodeMakeItLocal(tmp_path):
    templatePath = str(tmp_path / "addOne.mgt")
    addOneGraph().save(templatePath, template=True)
    project = Graph("project")
    upstream = project.addNewNode("Ls", input="/folder")
    node = project.addNewNode("SubGraph", template=templatePath)
    connectToAnySet(project, upstream.input, node.ins)
    assert node.template.value == ""
    assert sorted(c.name for c in node.ins.value) == ["input", "x"]
    with open(templatePath) as f:
        assert '"input"' not in f.read()


def test_graphInputLoopOutputs():
    from meshroom.core.subgraph.editing import SubGraphStack
    project = Graph("project")
    node = project.addNewNode("SubGraph", loopMode="frameRange", frameRange={"start": 10, "stop": 12})
    stack = SubGraphStack()
    inner = stack.enter(project, node)
    graphInput = inner.node("GraphInput_1")
    assert graphInput.frame.enabled and graphInput.frameRange.enabled
    assert not graphInput.iteration.enabled
    stack.exit(inner)

    record = Graph("")
    gi = record.addNewNode("GraphInput")
    rec = record.addNewNode("LiveRecord")
    record.addEdge(gi.frameRange.value.get("stop"), rec.value)
    variables = {}
    run(record.toDict(), loop=Loop("frameRange", first=10, last=12).subset(0, 1), variables=variables)
    assert variables["records"] == [(0, 10, 12)]


def test_runNodeOfProject(tmp_path):
    import meshroom.subgraph
    projectPath = str(tmp_path / "project.mg")
    project = Graph("project")
    project.addNewNode("SubGraph", subGraph=json.dumps(addOneGraph().toDict()))
    project.save(projectPath)
    assert meshroom.subgraph.run(projectPath, {"x": 1}, node="SubGraph_1") == {"x": 2}


def test_houdiniSessionReadsInputOfSkippedNode(fakeHou):
    """ A value typed in the pipeline node (the shot name) is read in memory, without running the node. """
    import meshroom.subgraph
    graph = houdiniSceneGraph()
    shotScene = graph.node("TaskShotScene_1")
    script = graph.addNewNode("LiveScript", inSpec="shot", outSpec="shot", code="outs['shot'] = ins['shot']")
    graphOutput = graph.addNewNode("GraphOutput", portSpec="shot")
    graph.addEdge(shotScene.shot, port(script, "ins", "shot"))
    graph.addEdge(port(script, "outs", "shot"), port(graphOutput, "ports", "shot"))
    assert meshroom.subgraph.run(graph.toDict()) == {"shot": "sh010"}
    assert TaskShotScene.runs == 0
    assert meshroom.subgraph.run(graph.toDict(), set={"TaskShotScene_1.shot": "sh020"}) == {"shot": "sh020"}
    assert TaskShotScene.runs == 0


def test_houdiniSessionSceneFile(fakeHou):
    """ "In Houdini Session: sceneFile": the pipeline node runs in the session and its scene is opened. """
    import meshroom.subgraph
    fakeHou.hipFile.current = "/shots/current.hip"
    graph = houdiniSceneGraph()
    graph.node("HoudiniScene_1").inSession.value = "sceneFile"
    meshroom.subgraph.run(graph.toDict())
    assert TaskShotScene.runs == 1
    assert fakeHou.loaded == ["/shots/sh010.hip"] and fakeHou.saved == []


def test_subGraphStartedLikeItsTaskNodes(fakeHou):
    """ A Houdini subgraph task is started with the interpreter and environment of its Houdini task nodes. """
    from types import SimpleNamespace
    project = Graph("project")
    node = project.addNewNode("SubGraph", subGraph=json.dumps(houdiniSceneGraph().serialize(asTemplate=True)))
    chunk = SimpleNamespace(node=node)
    assert node.nodeDesc.getPythonExecutable(chunk) == "hython"
    from meshroom.core import pluginManager
    assert node.nodeDesc.getProcessProvider(chunk) is pluginManager.getNodeDescProvider("BatchSetParm")


def test_enteredGraphInputShowsNodeValues():
    from meshroom.core.subgraph.editing import SubGraphStack
    project = Graph("project")
    upstream = project.addNewNode("Ls", input="/folder")
    node = project.addNewNode("SubGraph", loopMode="frameRange", frameRange={"start": 1001, "stop": 1002})
    child = connectToAnySet(project, upstream.input, node.ins)
    stack = SubGraphStack()
    inner = stack.enter(project, node)
    graphInput = inner.node("GraphInput_1")
    assert port(graphInput, "ports", child.name).value == "/folder"
    assert (graphInput.frame.value, graphInput.frameRange.value.get("start").value,
            graphInput.frameRange.value.get("stop").value) == (1001, 1001, 1002)
    # Shown only: leaving without other change does not change the subgraph
    content = node.subGraph.value
    stack.exit(inner)
    assert node.subGraph.value == content


def test_loopRunsOnceWhatDoesNotDependOnIt(fakeHou):
    """ In a frame loop, the pipeline node and the scene run once; the nodes reading the frame at each frame. """
    graph = houdiniSceneGraph()
    graphInput = graph.addNewNode("GraphInput")
    graph.addEdge(graphInput.frame, graph.node("BatchSetParm_2").value)
    run(graph.toDict(), loop=Loop("frameRange", first=1001, last=1003), ownsSession=True)
    assert TaskShotScene.runs == 1
    assert fakeHou.loaded == ["/shots/sh010.hip", "clear"]
    assert fakeHou.parms["/obj/geo1/ry"].value == 1003
    # The save at the end of each frame (HoudiniSave, live node)
    assert fakeHou.saved == ["/shots/sh010.hip"] * 3


def test_runNodeOfProjectUsesItsValuesAndLoop(tmp_path):
    import meshroom.subgraph
    projectPath = str(tmp_path / "project.mg")
    project = Graph("project")
    node = project.addNewNode("SubGraph", subGraph=json.dumps(addOneGraph().toDict()), loopMode="count", iterations=3)
    port(node, "ins", "x").value = 10
    project.save(projectPath)
    assert meshroom.subgraph.run(projectPath, node="SubGraph_1") == {"x": 13}
    assert meshroom.subgraph.run(projectPath, {"x": 0}, node="SubGraph_1", iterations=1) == {"x": 1}


def test_itemLoop(tmp_path):
    import meshroom.subgraph
    graph = Graph("")
    graphInput = graph.addNewNode("GraphInput")
    record = graph.addNewNode("LiveRecord")
    graphOutput = graph.addNewNode("GraphOutput", portSpec="last")
    graph.addEdge(graphInput.item, record.value)
    graph.addEdge(record.out, port(graphOutput, "ports", "last"))
    variables = {}
    assert meshroom.subgraph.run(graph.toDict(), items="mr_001, mr_002,\nmr_003", variables=variables) == {"last": "mr_003"}
    assert variables["records"] == [(0, None, "mr_001"), (1, None, "mr_002"), (2, None, "mr_003")]

    # SubGraph node: split in tasks of 2 items
    project = Graph("project")
    node = project.addNewNode("SubGraph", subGraph=json.dumps(graph.toDict()), loopMode="itemList",
                              items="a, b, c", framesPerTask=2)
    node.createChunks()
    from meshroom.core.subgraph.nodes import loopFromNode
    assert [loopFromNode(node).subset(c.range.start, c.range.end).items for c in node.chunks] == [["a", "b"], ["c"]]
    projectPath = str(tmp_path / "project.mg")
    project.save(projectPath)
    assert meshroom.subgraph.run(projectPath, node="SubGraph_1") == {"last": "c"}


class TaskFrameRange(desc.Node):
    """ A task node with a frame range group, like HoudiniSetFrameRange. """
    __test__ = False
    seen = []
    inputs = [
        desc.GroupAttribute(name="frameRange", label="Frame Range", description="", exposed=True, items=[
            desc.IntParam(name="start", label="start frame", description="", value=1, range=(1, 999999, 1)),
            desc.IntParam(name="stop", label="stop frame", description="", value=2, range=(1, 999999, 1)),
        ]),
    ]
    outputs = []

    def process(self, node):
        TaskFrameRange.seen.append((node.frameRange.start.value, node.frameRange.stop.value))


def test_frameRangeGroupConnectsToTheSameGroup():
    registerNodeDesc(TaskFrameRange)
    try:
        TaskFrameRange.seen = []
        graph = Graph("")
        graphInput = graph.addNewNode("GraphInput")
        task = graph.addNewNode("TaskFrameRange")
        assert task.frameRange.validateIncomingConnection(graphInput.frameRange)
        graph.addEdge(graphInput.frameRange, task.frameRange)
        run(graph.toDict(), loop=Loop("frameRange", first=1001, last=1003))
        # The frame range does not depend on the frame: run once
        assert TaskFrameRange.seen == [(1001, 1003)]
    finally:
        unregisterNodeDesc(TaskFrameRange)


# ---------------------------------------------------------------------------
# Maya and Nuke (fake modules): same scene logic as Houdini
# ---------------------------------------------------------------------------

class FakeCmds:
    """ The parts of maya.cmds used by the Maya context. """

    def __init__(self):
        self.scene, self.opened, self.saved, self.times = "", [], [], []

    def about(self, **kwargs):
        return "2025"

    def file(self, *args, **kwargs):
        if kwargs.get("query"):
            return self.scene
        if kwargs.get("open"):
            self.opened.append(args[0])
            self.scene = args[0]
        elif kwargs.get("rename"):
            self.scene = kwargs["rename"]
        elif kwargs.get("save"):
            self.saved.append(self.scene)
        elif kwargs.get("new"):
            self.opened.append("new")
        return self.scene

    def currentTime(self, frame, edit=True):
        self.times.append(frame)


class FakeNuke:
    """ The parts of the nuke module used by the Nuke context. """

    def __init__(self):
        self.script, self.opened, self.saved, self.frames = "", [], [], []

    def scriptName(self):
        if not self.script:
            raise RuntimeError("no script")
        return self.script

    def scriptOpen(self, filename):
        self.opened.append(filename)
        self.script = filename

    def scriptSave(self, filename=None):
        self.saved.append(filename or self.script)

    def scriptSaveAs(self, filename=None, overwrite=0):
        self.script = filename
        self.saved.append(filename)

    def scriptClear(self):
        self.opened.append("clear")

    def frame(self, frame):
        self.frames.append(frame)


class MayaBatch(desc.Node):
    """ A Maya task node written as usual: opens the scene, changes it, saves it. """
    __test__ = False
    pythonExecutable = "mayapy"
    inputs = [desc.File(name="scene", label="Scene", description="", value="")]
    outputs = [desc.File(name="output", label="Output", description="", value=None)]

    def process(self, node):
        from maya import cmds
        cmds.file(node.scene.value, open=True, force=True)
        cmds.file(save=True, force=True)
        node.output.value = node.scene.value


class NukeBatch(desc.Node):
    """ A Nuke task node written as usual: opens the script, changes it, saves it. """
    __test__ = False
    pythonExecutable = "nuke -t"
    inputs = [desc.File(name="scene", label="Scene", description="", value="")]
    outputs = [desc.File(name="output", label="Output", description="", value=None)]

    def process(self, node):
        import nuke
        nuke.scriptOpen(node.scene.value)
        nuke.scriptSave()
        node.output.value = node.scene.value


@pytest.fixture
def fakeMayaNuke(monkeypatch):
    import sys
    import types
    from meshroom.nodes.maya.MayaScene import MayaScene
    from meshroom.nodes.maya.MayaSave import MayaSave
    from meshroom.nodes.nuke.NukeScene import NukeScene
    from meshroom.nodes.nuke.NukeSave import NukeSave
    nodeDescs = [MayaScene, MayaSave, NukeScene, NukeSave, MayaBatch, NukeBatch]
    for nodeDesc in nodeDescs:
        registerNodeDesc(nodeDesc)
    cmds, nuke = FakeCmds(), FakeNuke()
    maya = types.ModuleType("maya")
    maya.cmds = cmds
    monkeypatch.setitem(sys.modules, "maya", maya)
    monkeypatch.setitem(sys.modules, "maya.cmds", cmds)
    monkeypatch.setitem(sys.modules, "nuke", nuke)
    yield cmds, nuke
    for nodeDesc in nodeDescs:
        unregisterNodeDesc(nodeDesc)


def softwareGraph(software: str):
    """ TaskShotScene -> <Software>Scene -> batch node x2 -> <Software>Save """
    TaskShotScene.runs = 0
    graph = Graph("")
    shotScene = graph.addNewNode("TaskShotScene", shot="sh010")
    scene = graph.addNewNode(f"{software}Scene")
    first = graph.addNewNode(f"{software}Batch")
    second = graph.addNewNode(f"{software}Batch")
    save = graph.addNewNode(f"{software}Save")
    graph.addEdge(shotScene.scene, scene.hipFile)
    graph.addEdge(scene.scene, first.scene)
    graph.addEdge(first.output, second.scene)
    graph.addEdge(second.output, save.scene)
    return graph


def test_mayaAndNukeTasks(fakeMayaNuke):
    cmds, nuke = fakeMayaNuke
    run(softwareGraph("Maya").toDict(), ownsSession=True)
    assert cmds.opened == ["/shots/sh010.hip", "new"] and cmds.saved == ["/shots/sh010.hip"]
    run(softwareGraph("Nuke").toDict(), ownsSession=True)
    assert nuke.opened == ["clear", "/shots/sh010.hip", "clear"] and nuke.saved == ["/shots/sh010.hip"]
    assert TaskShotScene.runs == 1


def test_mayaAndNukeSessions(fakeMayaNuke):
    import meshroom.subgraph
    cmds, nuke = fakeMayaNuke
    cmds.scene, nuke.script = "/shots/open.ma", "/shots/open.nk"
    meshroom.subgraph.run(softwareGraph("Maya").toDict())
    meshroom.subgraph.run(softwareGraph("Nuke").toDict())
    assert TaskShotScene.runs == 0
    assert cmds.opened == [] and cmds.saved == [] and nuke.opened == [] and nuke.saved == []


def test_collapseIntoSubGraph():
    from meshroom.core.subgraph.editing import collapseIntoSubGraph, restoreNodes
    project = Graph("project")
    upstream = project.addNewNode("LiveAdd", a=2, b=3)
    add1 = project.addNewNode("LiveAdd", b=1)
    add2 = project.addNewNode("LiveAdd", b=10)
    after = project.addNewNode("LiveScript", inSpec="v", code="")
    project.addEdge(upstream.sum, add1.a)
    project.addEdge(add1.sum, add2.a)
    project.addEdge(add2.sum, port(after, "ins", "v"))

    node, snapshot = collapseIntoSubGraph(project, [add1, add2])
    assert sorted(n.name for n in project.nodes) == ["LiveAdd_1", "LiveScript_1", "SubGraph_1"]
    assert [c.name for c in node.ins.value] == ["sum"] and [c.name for c in node.outs.value] == ["sum"]
    assert port(node, "ins", "sum").inputLink is upstream.sum
    assert port(after, "ins", "v").inputLink is port(node, "outs", "sum")
    # The subgraph runs as the nodes did: input + 1 + 10
    assert run(node.subGraph.value, {"sum": 5}) == {"sum": 16}

    # Undo: the nodes and their connections come back
    project.removeNode(node.name)
    restoreNodes(project, snapshot)
    assert add1.name == "LiveAdd_2" and project.node("LiveAdd_2").a.inputLink is upstream.sum
    assert port(after, "ins", "v").inputLink is project.node("LiveAdd_3").sum


def test_subFrameStep():
    loop = Loop("frameRange", first=1001, last=1002, step=0.25)
    assert loop.frames == [1001, 1001.25, 1001.5, 1001.75, 1002]
    tenth = Loop("frameRange", first=1, last=2, step=0.1).frames
    assert len(tenth) == 11 and tenth[1] == 1.1 and tenth[-1] == 2
    assert Loop("frameRange", first=1, last=5, step=2.0).frames == [1, 3, 5]
    assert Loop.fromDict(loop.subset(1, 3).asDict()).frames == [1001.25, 1001.5]
    with pytest.raises(ValueError):
        Loop("frameRange", first=1, last=2, step=0)
