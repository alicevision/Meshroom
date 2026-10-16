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
from meshroom.nodes.subgraph.LiveSubGraph import LiveSubGraph
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


class NotLive(desc.Node):
    __test__ = False
    inputs = []
    outputs = []


_NODE_DESCS = [GraphInput, GraphOutput, LiveScript, LiveSubGraph, SubGraph, LiveAdd, LiveRecord, LiveFail,
               LiveDccOnly, NotLive]


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
        ("a", "LiveValue"), ("b", "IntParam"), ("c", "LiveValue"), ("d", "LiveValue")]
    assert parsePortSpec(None) == []
    assert formatPortSpec([("a", "LiveValue"), ("b", "IntParam")]) == "a, b:IntParam"


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


def test_nestedSubGraph():
    inner = addOneGraph().toDict()
    graph = Graph("")
    graphInput = graph.addNewNode("GraphInput", portSpec="x")
    nested = graph.addNewNode("LiveSubGraph", subGraph=json.dumps(inner), loopMode="count", iterations=3)
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
    graph.addNewNode("LiveSubGraph", subGraph=json.dumps(inner.toDict()))
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

    with pytest.raises(SubGraphError, match="not a live node"):
        SubGraphPlan({"NotLive_1": {"nodeType": "NotLive", "inputs": {}}})

    with pytest.raises(SubGraphError, match="unknown node 'Missing_1'"):
        SubGraphPlan({"LiveAdd_1": {"nodeType": "LiveAdd", "inputs": {"a": "{Missing_1.sum}"}}})

    with pytest.raises(SubGraphError, match="Cycle"):
        SubGraphPlan({"LiveAdd_1": {"nodeType": "LiveAdd", "inputs": {"a": "{LiveAdd_2.sum}"}},
                      "LiveAdd_2": {"nodeType": "LiveAdd", "inputs": {"a": "{LiveAdd_1.sum}"}}})

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
                            frameFirst=1001, frameLast=1010, framesPerTask=4)
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
