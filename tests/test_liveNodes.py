"""Live nodes (desc.LiveNode) and LiveValue attributes."""

from meshroom.core import desc
from meshroom.core.desc.serialization import buildAttributeDesc, describeAttribute
from meshroom.core.graph import Graph

from .utils import registeredNodeTypes


class LiveScale(desc.LiveNode):
    inputs = [
        desc.LiveValue(name="values", label="Values", description="A list of numbers."),
        desc.FloatParam(name="factor", label="Factor", description="", value=2.0, range=(0.0, 10.0, 0.1)),
        desc.ChoiceParam(name="formats", label="Formats", description="", value=["a"], values=["a", "b"],
                         exclusive=False),
    ]
    outputs = [
        desc.LiveValue(name="scaled", label="Scaled", description="The scaled numbers."),
    ]

    def execute(self, ctx, inputs):
        return {"scaled": [value * inputs["factor"] for value in inputs["values"]]}


class TaskNode(desc.Node):
    inputs = [desc.File(name="input", label="Input", description="", value="")]
    outputs = [desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out.txt")]


def test_liveNodeIsNotComputed():
    with registeredNodeTypes([LiveScale]):
        graph = Graph("")
        node = graph.addNewNode("LiveScale")
        assert not node.isComputableType
        assert node.getMrNodeType() == desc.MrNodeType.LIVE
        assert node.nodeDesc.execute(None, {"values": [1, 2], "factor": 3.0}) == {"scaled": [3.0, 6.0]}


def test_liveValueConnectsToAnyAttribute():
    with registeredNodeTypes([LiveScale, TaskNode]):
        graph = Graph("")
        live = graph.addNewNode("LiveScale")
        task = graph.addNewNode("TaskNode")
        assert live.values.validateIncomingConnection(task.output)
        assert task.input.validateIncomingConnection(live.scaled)
        graph.addEdge(task.output, live.values)
        graph.addEdge(live.scaled, task.input)
        assert live.values.isLink and task.input.isLink


def test_liveValueHoldsAnyJsonValue():
    with registeredNodeTypes([LiveScale]):
        graph = Graph("")
        node = graph.addNewNode("LiveScale")
        node.values.value = [1, 2.5, {"a": "b"}]
        assert node.values.value == [1, 2.5, {"a": "b"}]


def test_choiceWithoutValue():
    """ A non exclusive choice can have no value (set when its node runs): not the text "None". """
    with registeredNodeTypes([LiveScale]):
        graph = Graph("")
        node = graph.addNewNode("LiveScale")
        node.formats.value = None
        assert node.formats.value is None
        assert node.formats.getValueStr() == ""


def test_unknownTypeRecreatedAsLiveValue():
    attributeDesc = buildAttributeDesc({"type": "NoSuchParam", "name": "value", "label": "Value"})
    assert isinstance(attributeDesc, desc.LiveValue) and attributeDesc.name == "value"
    roundTrip = buildAttributeDesc(describeAttribute(desc.LiveValue(name="any", value=[1, 2])))
    assert isinstance(roundTrip, desc.LiveValue) and roundTrip.value == [1, 2]
