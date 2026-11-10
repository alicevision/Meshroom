from pathlib import Path
from types import SimpleNamespace

import pytest

from meshroom.core import desc, pluginManager
from meshroom.core.exception import InvalidEdgeError
from meshroom.core.graph import Graph, loadGraph
from meshroom.core.node import ConversionNode
from meshroom.core.plugins.base import NodeDescProviderStatus
from meshroom.nodes.general.FloatToInt import FloatToInt

from .utils import registeredNodeTypes, registerNodeDesc, unregisterNodeDesc


class FloatSource(desc.Node):
    inputs = [
        desc.FloatParam(name="value", label="Value", description="", value=2.5),
    ]
    outputs = [
        desc.FloatParam(name="dynamicValue", label="Dynamic Value", description="", value=None),
    ]

    def process(self, node):
        node.dynamicValue.value = node.value.value * 2


class IntTarget(desc.Node):
    inputs = [
        desc.IntParam(name="value", label="Value", description="", value=0),
        desc.IntParam(name="otherValue", label="Other Value", description="", value=0),
        desc.FloatParam(name="floatValue", label="Float Value", description="", value=0.0),
        desc.ListAttribute(
            name="values", label="Values", description="",
            elementDesc=desc.IntParam(name="value", label="Value", description="", value=0),
        ),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/value.txt"),
    ]

    def process(self, node):
        Path(node.output.value).write_text(str(node.value.value))


class RoundFloat(desc.ConversionNode):
    inputs = [
        desc.FloatParam(name="input", label="Input", description="", value=0.0),
        desc.ChoiceParam(name="mode", label="Mode", description="", values=["round", "floor"], value="round"),
    ]
    outputs = [
        desc.IntParam(name="output", label="Output", description="", value=None),
    ]

    def convert(self, node, value):
        return int(value // 1) if node.mode.value == "floor" else int(round(value))


class TruncateFloat(desc.ConversionNode):
    inputs = [
        desc.FloatParam(name="input", label="Input", description="", value=0.0),
    ]
    outputs = [
        desc.IntParam(name="output", label="Output", description="", value=None),
    ]

    def convert(self, node, value):
        return int(value)


class IntToHalf(desc.ConversionNode):
    inputs = [
        desc.IntParam(name="input", label="Input", description="", value=0),
    ]
    outputs = [
        desc.FloatParam(name="output", label="Output", description="", value=None),
    ]

    def convert(self, node, value):
        return value / 2


class FailingConversion(desc.ConversionNode):
    inputs = [
        desc.IntParam(name="input", label="Input", description="", value=0),
    ]
    outputs = [
        desc.FloatParam(name="output", label="Output", description="", value=None),
    ]

    def convert(self, node, value):
        raise ValueError("Conversion error")


class ConversionWithoutDynamicOutput(desc.ConversionNode):
    inputs = [
        desc.FloatParam(name="input", label="Input", description="", value=0.0),
    ]
    outputs = [
        desc.IntParam(name="output", label="Output", description="", value=0),
    ]


class ConversionWithoutInput(desc.ConversionNode):
    inputs = [
        desc.FloatParam(name="value", label="Value", description="", value=0.0),
    ]
    outputs = [
        desc.IntParam(name="output", label="Output", description="", value=None),
    ]


NODE_TYPES = [FloatSource, IntTarget, RoundFloat, TruncateFloat, IntToHalf]


@pytest.fixture
def conversionNodeTypes():
    with registeredNodeTypes(NODE_TYPES):
        yield


@pytest.mark.usefixtures("conversionNodeTypes")
class TestConversionLookup:
    def test_conversionNodeTypesMatchAttributeTypes(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)

        assert graph.getConversionNodeTypes(source.value, target.value) == ["RoundFloat", "TruncateFloat"]
        assert graph.getConversionNodeTypes(target.value, source.value) == ["IntToHalf"]

    def test_noConversionNodeTypeForUnsupportedAttributes(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)

        # Same types: no conversion needed
        assert graph.getConversionNodeTypes(source.value, target.floatValue) == []
        # List attributes are not converted
        assert graph.getConversionNodeTypes(source.value, target.values) == []
        # Output file to integer: no conversion available
        assert graph.getConversionNodeTypes(target.output, target.value) == []


@pytest.mark.usefixtures("conversionNodeTypes")
class TestConnectWithConversion:
    def test_conversionNodeIsInsertedBetweenAttributes(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)

        conversion = graph.connectWithConversion(source.value, target.value)

        assert isinstance(conversion, ConversionNode)
        assert conversion.isConversionNode
        assert conversion.nodeType == "RoundFloat"
        assert conversion.inputAttribute.inputLink == source.value
        assert target.value.inputLink == conversion.outputAttribute
        assert len(graph.edges) == 2

    def test_conversionNodeTypeCanBeChosen(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)

        conversion = graph.connectWithConversion(source.value, target.value, TruncateFloat.__name__)
        assert conversion.nodeType == "TruncateFloat"

    def test_invalidConversionRaises(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)

        with pytest.raises(InvalidEdgeError):
            graph.connectWithConversion(source.value, target.floatValue)
        with pytest.raises(InvalidEdgeError):
            graph.connectWithConversion(source.value, target.value, IntToHalf.__name__)
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 0


@pytest.mark.usefixtures("conversionNodeTypes")
class TestConversionValue:
    def test_outputValueIsConvertedOnTheFly(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)
        conversion = graph.connectWithConversion(source.value, target.value)

        assert target.value.value == 2

        source.value.value = 3.7
        assert conversion.outputAttribute.value == 4
        assert target.value.value == 4

        conversion.mode.value = "floor"
        assert target.value.value == 3

    def test_downstreamAttributeIsNotifiedOfConvertedValueChanges(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)
        conversion = graph.connectWithConversion(source.value, target.value)

        notifications = []
        target.value.valueChanged.connect(lambda: notifications.append(target.value.value))
        conversion.mode.value = "floor"

        assert notifications and notifications[-1] == 2

    def test_dynamicInputValueIsNotConvertedBeforeComputation(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)
        graph.connectWithConversion(source.dynamicValue, target.value)

        assert target.value.value is None

    def test_conversionErrorGivesNoValue(self):
        with registeredNodeTypes([FailingConversion]):
            graph = Graph("")
            target = graph.addNewNode(IntTarget.__name__)
            source = graph.addNewNode(FloatSource.__name__)
            graph.connectWithConversion(target.value, source.value, FailingConversion.__name__)

            assert source.value.value is None

    def test_conversionsCanBeChained(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)
        other = graph.addNewNode(FloatSource.__name__)
        source.value.value = 7.0

        # float -> int -> float
        graph.connectWithConversion(source.value, target.value)
        graph.connectWithConversion(target.value, other.value)

        assert other.value.value == 3.5


@pytest.mark.usefixtures("conversionNodeTypes")
class TestConversionInGraph:
    def test_conversionNodeIsNotComputable(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)
        conversion = graph.connectWithConversion(source.dynamicValue, target.value)

        assert not conversion.isComputableType
        assert conversion.isComputed
        nodesToProcess, _ = graph.dfsToProcess(startNodes=[target])
        assert conversion not in nodesToProcess
        assert set(nodesToProcess) == {source, target}

    def test_dependenciesGoThroughConversionNodes(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)
        conversion = graph.connectWithConversion(source.dynamicValue, target.value)

        dependencyEdges = [(edge.src, edge.dst) for edge in graph.getEdges(dependenciesOnly=True)]
        assert dependencyEdges == [(source.dynamicValue, target.value)]
        assert target.getInputNodes(recursive=False, dependenciesOnly=True) == {source}
        assert conversion.getInputNodes(recursive=False, dependenciesOnly=True) == set()

    def test_conversionNodeHasTheDepthOfItsInputNode(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)
        conversion = graph.connectWithConversion(source.dynamicValue, target.value)
        graph.update()

        assert conversion.depth == source.depth
        assert target.depth == source.depth + 1

    def test_conversionChangesInvalidateDownstreamNodes(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)
        conversion = graph.connectWithConversion(source.dynamicValue, target.value)
        uid = target._uid

        conversion.mode.value = "floor"
        assert target._uid != uid

        conversion.mode.value = "round"
        assert target._uid == uid

        source.value.value = 10.0
        assert target._uid != uid

    def test_identicalConversionsAreNotDuplicates(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)
        conversionA = graph.connectWithConversion(source.dynamicValue, target.value)
        conversionB = graph.connectWithConversion(source.dynamicValue, target.otherValue)
        graph.update()

        assert conversionA._uid == conversionB._uid
        assert not conversionA.hasDuplicates
        assert not conversionB.hasDuplicates


@pytest.mark.usefixtures("conversionNodeTypes")
class TestConversionSerialization:
    def test_conversionIsRestoredOnLoad(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)
        conversion = graph.connectWithConversion(source.value, target.value)
        conversion.mode.value = "floor"
        source.value.value = 4.9
        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        loadedConversion = loadedGraph.node(conversion.name)
        loadedTarget = loadedGraph.node(target.name)

        assert isinstance(loadedConversion, ConversionNode)
        assert loadedConversion.mode.value == "floor"
        assert loadedTarget.value.inputLink == loadedConversion.outputAttribute
        assert loadedTarget.value.value == 4
        assert loadedTarget._uid == target._uid

    def test_conversionNodeWithDescriptionConflictIsUpgraded(self):
        graph = Graph("")
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)
        conversion = graph.connectWithConversion(source.value, target.value)
        graphData = graph.serialize()
        # Add an attribute which is not part of the conversion node description anymore
        graphData["graph"][conversion.name]["inputs"]["removedAttribute"] = 1

        loadedGraph = Graph("")
        loadedGraph._deserialize(graphData)
        loadedConversion = loadedGraph.node(conversion.name)

        assert isinstance(loadedConversion, ConversionNode)
        assert loadedGraph.node(target.name).value.inputLink == loadedConversion.outputAttribute

    def test_computedValueIsConvertedForDownstreamNode(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        source = graph.addNewNode(FloatSource.__name__)
        target = graph.addNewNode(IntTarget.__name__)
        graph.connectWithConversion(source.dynamicValue, target.value)
        source.value.value = 1.6
        graph.save()

        source.process(inCurrentEnv=True)

        # The dynamic output is loaded from the cache, then converted for the downstream node
        loadedGraph = loadGraph(graph.filepath)
        loadedTarget = loadedGraph.node(target.name)
        assert loadedTarget.value.value == 3

        Path(loadedTarget.internalFolder).mkdir(parents=True)
        loadedTarget.process(inCurrentEnv=True)
        assert Path(loadedTarget.output.value).read_text() == "3"


class TestConversionNodeDescription:
    @pytest.mark.parametrize("nodeDesc", [ConversionWithoutDynamicOutput, ConversionWithoutInput])
    def test_invalidConversionNodeDescriptionIsRejected(self, nodeDesc):
        registerNodeDesc(nodeDesc)
        try:
            provider = pluginManager.getNodeDescProvider(nodeDesc.__name__)
            assert provider.status == NodeDescProviderStatus.DESC_ERROR
        finally:
            unregisterNodeDesc(nodeDesc)

    def test_validConversionNodeDescription(self):
        with registeredNodeTypes([RoundFloat]):
            provider = pluginManager.getNodeDescProvider(RoundFloat.__name__)
            assert provider.status == NodeDescProviderStatus.VALID

    @pytest.mark.parametrize("mode,value,expected", [
        ("round", 2.5, 3), ("round", -2.5, -3), ("round", 2.4, 2),
        ("floor", 2.7, 2), ("floor", -2.2, -3),
        ("ceil", 2.2, 3), ("ceil", -2.7, -2),
        ("trunc", 2.7, 2), ("trunc", -2.7, -2),
    ])
    def test_floatToIntModes(self, mode, value, expected):
        node = SimpleNamespace(mode=SimpleNamespace(value=mode))
        assert FloatToInt().convert(node, value) == expected
