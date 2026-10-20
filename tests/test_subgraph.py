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
        ("a", "LiveValue", "a", None), ("b", "IntParam", "b", None), ("c", "LiveValue", "c", None),
        ("d", "LiveValue", "d", None)]
    assert parsePortSpec(None) == []
    # A type that is not a simple one needs its full description, else it holds any value
    spec = formatPortSpec([("a", "LiveValue", "Shot Name"), ("b", "ChoiceParam")])
    assert parsePortSpec(spec) == [("a", "LiveValue", "Shot Name", None), ("b", "LiveValue", "b", None)]
    choice = {"type": "ChoiceParam", "name": "b", "values": ["abc", "usd"], "exclusive": False, "value": ["abc"]}
    ports = [("b", "ChoiceParam", "Formats", choice)]
    assert parsePortSpec(formatPortSpec(ports)) == ports


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
    """ A task node with a frame range group (start, stop). """
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

    # The step is an output of GraphInput, also in a task of a farm (subset of the frames)
    graph = Graph("")
    graphInput = graph.addNewNode("GraphInput")
    graphOutput = graph.addNewNode("GraphOutput", portSpec="step")
    graph.addEdge(graphInput.frameStep, port(graphOutput, "ports", "step"))
    assert run(graph.toDict(), loop=loop.subset(1, 3)) == {"step": 0.25}


class TaskExportCamera(desc.Node):
    """ A task node with inputs of complex types (choices, groups, lists). """
    __test__ = False
    seen = []
    inputs = [
        desc.GroupAttribute(name="frameRange", label="Frame Range", description="", exposed=True, items=[
            desc.IntParam(name="start", label="start frame", description="", value=1, range=(1, 999999, 1)),
            desc.IntParam(name="stop", label="stop frame", description="", value=2, range=(1, 999999, 1)),
        ]),
        desc.FloatParam(name="frameStep", label="Step Frame", description="", value=1.0, range=(0.01, 10.0, 0.01)),
        desc.ChoiceParam(name="formats", label="Formats", description="", value=["abc"],
                         values=["abc", "usd", "fbx"], exclusive=False),
        desc.ChoiceParam(name="destination", label="Destination", description="", value="common/camera",
                         values=["common/camera", "lighting/camera"]),
    ]
    outputs = []

    def process(self, node):
        TaskExportCamera.seen.append((node.frameRange.start.value, node.frameRange.stop.value, node.frameStep.value,
                                      list(node.formats.value), node.destination.value))


def test_complexTypePorts(tmp_path):
    from meshroom.core.subgraph.editing import SubGraphStack
    registerNodeDesc(TaskExportCamera)
    try:
        TaskExportCamera.seen = []
        project = Graph("project")
        source = project.addNewNode("TaskExportCamera", frameStep=0.5, formats=["abc", "usd"], destination="lighting/camera")
        source.frameRange.start.value = 1001
        source.frameRange.stop.value = 1003
        node = project.addNewNode("SubGraph")
        names = ["frameRange", "frameStep", "formats", "destination"]
        for name in names:
            connectToAnySet(project, source.attribute(name), node.ins)
        assert type(port(node, "ins", "frameRange").desc).__name__ == "GroupAttribute"

        # The ports keep their types in the subgraph: they connect to the attributes of the same type
        stack = SubGraphStack()
        inner = stack.enter(project, node)
        graphInput = inner.node("GraphInput_1")
        types = {"frameRange": "GroupAttribute", "frameStep": "FloatParam",
                 "formats": "ChoiceParam", "destination": "ChoiceParam"}
        assert {c.name: type(c.desc).__name__ for c in graphInput.ports.value} == types
        assert port(graphInput, "ports", "frameRange").value.get("start").value == 1001
        task = inner.addNewNode("TaskExportCamera")
        for name in names:
            inner.addEdge(port(graphInput, "ports", name), task.attribute(name))
        stack.exit(inner)

        # Saved and reloaded: the ports, their connections and the subgraph are kept
        projectPath = str(tmp_path / "project.mg")
        project.save(projectPath)
        project = loadGraph(projectPath)
        node = project.node("SubGraph_1")
        assert {c.name: type(c.desc).__name__ for c in node.ins.value} == types
        assert all(c.isLink for c in node.ins.value)
        inner = SubGraphStack().enter(project, node)
        assert inner.node("TaskExportCamera_1").frameRange.inputLink.node.nodeType == "GraphInput"

        # The node runs the subgraph with the values of its inputs
        from meshroom.core.subgraph.executor import plainValue
        inputs = {child.name: plainValue(child) for child in node.ins.value}
        run(node.subGraph.value, inputs)
        assert TaskExportCamera.seen == [(1001, 1003, 0.5, ["abc", "usd"], "lighting/camera")]
    finally:
        unregisterNodeDesc(TaskExportCamera)


def test_attributeDescriptionSerialization():
    from meshroom.core.desc.serialization import buildAttributeDesc, describeAttribute
    files = desc.ListAttribute(name="files", elementDesc=desc.File(name="file", value=""))
    for attributeDesc in TaskExportCamera.inputs + [files]:
        data = describeAttribute(attributeDesc)
        assert describeAttribute(buildAttributeDesc(data)) == data
    # A type that cannot be rebuilt holds any value
    assert type(buildAttributeDesc({"type": "Nope", "name": "x"})).__name__ == "LiveValue"


def test_portsConnectedInTheSubGraphKeepTheirChoices():
    """ Inputs of a node of the subgraph connected to the GraphInput: the node gets the same choices, defaults... """
    from meshroom.core.subgraph.editing import SubGraphStack
    registerNodeDesc(TaskExportCamera)
    try:
        project = Graph("project")
        node = project.addNewNode("SubGraph")
        stack = SubGraphStack()
        inner = stack.enter(project, node)
        task = inner.addNewNode("TaskExportCamera")
        graphInput = inner.node("GraphInput_1")
        for name in ("frameRange", "frameStep", "formats", "destination"):
            connectToAnySet(inner, task.attribute(name), graphInput.ports)
        stack.exit(inner)

        formats, destination, frameStep = (port(node, "ins", name) for name in ("formats", "destination", "frameStep"))
        assert formats.desc.exclusive is False and formats.desc.values == ["abc", "usd", "fbx"]
        assert formats.value == ["abc"]
        assert destination.desc.values == ["common/camera", "lighting/camera"]
        assert destination.value == "common/camera"
        assert frameStep.value == 1.0 and list(frameStep.desc.range) == [0.01, 10.0, 0.01]
        assert port(node, "ins", "frameRange").value.get("start").value == 1

    finally:
        unregisterNodeDesc(TaskExportCamera)


def test_subGraphWithUnknownNodesIsNotEntered():
    """ A subgraph whose nodes come from a plugin not loaded is not opened (writing it back would lose its links). """
    from meshroom.core.subgraph.editing import SubGraphStack
    project = Graph("project")
    node = project.addNewNode("SubGraph")
    data = json.loads(node.subGraph.value)
    data["graph"]["Missing_1"] = {"nodeType": "MissingPluginNode", "position": [0, 0],
                                  "inputs": {"scene": "{GraphInput_1.ports.x}"}}
    node.subGraph.value = json.dumps(data)
    content = node.subGraph.value
    with pytest.raises(ValueError, match="Missing_1 \\(MissingPluginNode\\)"):
        SubGraphStack().enter(project, node)
    assert node.subGraph.value == content


def test_inputValuesKeptWhenEnteringAndLeaving():
    """ The values typed on the inputs of the node stay when its subgraph is entered and left. """
    from meshroom.core.subgraph.editing import SubGraphStack
    registerNodeDesc(TaskShotScene)
    project = Graph("project")
    node = project.addNewNode("SubGraph")
    stack = SubGraphStack()
    inner = stack.enter(project, node)
    task = inner.addNewNode("TaskShotScene")
    connectToAnySet(inner, task.shot, inner.node("GraphInput_1").ports)
    stack.exit(inner)
    port(node, "ins", "shot").value = "sh020"
    for _ in range(2):
        inner = stack.enter(project, node)
        assert port(inner.node("GraphInput_1"), "ports", "shot").value == "sh020"
        stack.exit(inner)
        assert port(node, "ins", "shot").value == "sh020"
    # The port recreated with another description
    from meshroom.core.subgraph.ports import anySetPorts, syncAnySet
    ports = anySetPorts(node.ins)
    description = dict(ports[0][3], description="Another description")
    syncAnySet(node.ins, [(ports[0][0], ports[0][1], ports[0][2], description)])
    assert port(node, "ins", "shot").desc.description == "Another description"
    assert port(node, "ins", "shot").value == "sh020"


def test_nodeStatusesReported():
    """ The statuses of the nodes are reported as they run (shown on the nodes by Run Live). """
    events = []
    assert run(addOneGraph().toDict(), {"x": 1}, onNode=lambda *event: events.append(event[:2])) == {"x": 2}
    assert events == [("GraphInput_1", "RUNNING"), ("GraphInput_1", "SUCCESS"), ("LiveAdd_1", "RUNNING"),
                      ("LiveAdd_1", "SUCCESS"), ("GraphOutput_1", "RUNNING"), ("GraphOutput_1", "SUCCESS")]

    graph = addOneGraph()
    graph.addNewNode("LiveFail")
    events = []
    with pytest.raises(SubGraphError):
        run(graph.toDict(), {"x": 1}, onNode=lambda *event: events.append(event))
    statuses = {name: status for name, status, _ in events}
    assert statuses["LiveFail_1"] == "ERROR"
    message = next(message for name, status, message in events if status == "ERROR")
    assert "broken" in message


def test_runFromSoftwareReportsNodes():
    import meshroom.subgraph
    events = []
    meshroom.subgraph.run(addOneGraph().toDict(), {"x": 1}, onNode=lambda *event: events.append(event[:2]))
    assert ("LiveAdd_1", "SUCCESS") in events


def test_pluginsLoadedWhenTheirVariablesAreSetLater(monkeypatch):
    """ From a software: plugin variables set after a first run (e.g. by a script) load the plugins. """
    import meshroom.core
    import meshroom.subgraph
    calls = []
    monkeypatch.setattr(meshroom.core, "initPlugins", lambda: calls.append("plugins"))
    monkeypatch.setattr(meshroom.core, "initNodes", lambda: calls.append("nodes"))
    monkeypatch.setattr(meshroom.subgraph, "_nodesLoaded", True)
    monkeypatch.setattr(meshroom.subgraph, "_loadedPluginVariables", ("",) * 5)
    monkeypatch.setenv("MESHROOM_USER_REZ_PLUGINS", "mr_batch_plugin=/path")
    meshroom.subgraph.ensureNodes()
    assert calls == ["nodes", "plugins"]
    meshroom.subgraph.ensureNodes()
    assert calls == ["nodes", "plugins"]
