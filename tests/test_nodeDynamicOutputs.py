import pytest

from meshroom.core import desc
from meshroom.core import pluginManager
from meshroom.core.exception import UnknownNodeTypeError
from meshroom.core.graph import Graph, loadGraph
from meshroom.core.plugins import NodePluginStatus

from .utils import registerNodeDesc, unregisterNodeDesc


class NodeWithDynamicOutputs(desc.Node):
    inputs = [
        desc.BoolParam(
            name="boolInput",
            label="Bool Input",
            description="A boolean input.",
            value=False,
        ),
        desc.File(
            name="fileInput",
            label="File Input",
            description="A file input.",
            value="testFile",
        ),
        desc.StringParam(
            name="stringInput",
            label="String Input",
            description="A string input.",
            value="testString",
        ),
        desc.IntParam(
            name="intInput",
            label="Int Input",
            description="An integer input.",
            value=1,
        ),
        desc.FloatParam(
            name="floatInput",
            label="Float Input",
            description="A floating input.",
            value=5.0,
        ),
    ]

    outputs = [
        desc.BoolParam(
            name="boolOutput",
            label="Bool Output",
            description="A boolean output.",
            value=None,
        ),
        desc.File(
            name="fileOutput",
            label="File Output",
            description="A file Output.",
            value=None,
        ),
        desc.StringParam(
            name="stringOutput",
            label="String Output",
            description="A string output.",
            value=None,
        ),
        desc.IntParam(
            name="intOutput",
            label="Int Output",
            description="An integer output.",
            value=None,
        ),
        desc.FloatParam(
            name="floatOutput",
            label="Float Output",
            description="A floating output.",
            value=None,
        ),
    ]

    def process(self, node):
        print("Processing NodeWithDynamicOutputs")
        node.boolOutput.value = not node.boolInput.value
        node.fileOutput.value = node.fileInput.value + ".ext"
        node.stringOutput.value = node.stringInput.value.upper()
        node.intOutput.value = node.intInput.value + 1
        node.floatOutput.value = node.floatInput.value * 2.0


class NodeWithDynamicListOutput(desc.Node):
    """Node with a dynamic output ListAttribute set during processChunk."""
    inputs = [
        desc.ListAttribute(
            name="listInput",
            label="List Input",
            description="A list of strings as input.",
            elementDesc=desc.StringParam(name="value", label="Value", description="", value=""),
        ),
    ]

    outputs = [
        desc.ListAttribute(
            name="listOutput",
            label="List Output",
            description="A dynamic list output set during processing.",
            elementDesc=desc.StringParam(name="value", label="Value", description="", value=""),
            value=None,
        ),
    ]

    def processChunk(self, chunk):
        # Read input list and produce an output list with uppercased values
        inputValues = [attr.value for attr in chunk.node.listInput.value]
        outputValues = [v.upper() for v in inputValues]
        chunk.node.listOutput.value = outputValues


class InputNodeWithDynamicOutputs(desc.InputNode):
    inputs = [
        desc.File(
            name="fileInput",
            label="File Input",
            description="A file input.",
            value="testFile",
        ),
    ]

    outputs = [
        desc.File(
            name="fileOutput",
            label="File Output",
            description="A file Output.",
            value=None,
        ),
    ]


class TestNodesWithDynamicOutputs:
    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithDynamicOutputs)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithDynamicOutputs)

    def test_processWithDynamicOutputs(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithDynamicOutputs.__name__)

        # Execute the node to compute dynamic outputs
        node.process(inCurrentEnv=True)

        assert node.boolOutput.value
        assert node.fileOutput.value == "testFile.ext"
        assert node.stringOutput.value == "TESTSTRING"
        assert node.intOutput.value == 2
        assert node.floatOutput.value == 10.0

    def test_processWithDynamicOutputsNonDefaultInputs(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithDynamicOutputs.__name__)

        node.boolInput.value = True
        node.fileInput.value = "anotherTestFile"
        node.stringInput.value = "anotherTestString"
        node.intInput.value = 10
        node.floatInput.value = 3.5

        # Execute the node to compute dynamic outputs
        node.process(inCurrentEnv=True)

        assert not node.boolOutput.value
        assert node.fileOutput.value == "anotherTestFile.ext"
        assert node.stringOutput.value == "ANOTHERTESTSTRING"
        assert node.intOutput.value == 11
        assert node.floatOutput.value == 7.0

    def test_loadGraphWithUncomputedDynamicOutputs(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithDynamicOutputs.__name__)
        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        loadedNode = loadedGraph.node(node.name)

        assert loadedNode
        assert loadedNode.boolOutput.value is None
        assert loadedNode.fileOutput.value is None
        assert loadedNode.stringOutput.value is None
        assert loadedNode.intOutput.value is None
        assert loadedNode.floatOutput.value is None

    def test_loadGraphWithComputedDynamicOutputs(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithDynamicOutputs.__name__)
        name = node.name
        graph.save()

        # Execute the node to compute dynamic outputs
        node.process(inCurrentEnv=True)

        # Check that the values have been correctly set
        assert node.boolOutput.value
        assert node.fileOutput.value == "testFile.ext"
        assert node.stringOutput.value == "TESTSTRING"
        assert node.intOutput.value == 2
        assert node.floatOutput.value == 10.0

        # Reload the graph from disk
        loadedGraph = loadGraph(graph.filepath)
        loadedNode = loadedGraph.node(name)

        # Check that the dynamic outputs have been correctly deserialized
        assert loadedNode
        assert loadedNode.boolOutput.value
        assert loadedNode.fileOutput.value == "testFile.ext"
        assert loadedNode.stringOutput.value == "TESTSTRING"
        assert loadedNode.intOutput.value == 2
        assert loadedNode.floatOutput.value == 10.0


class TestInputNodeWithDynamicOutputs:
    def test_registerInputNodeWithDynamicOutputs(self):
        """
        Force the registration of a node with an invalid description and check that its description is rejected
        and its status states it clearly.
        """
        registerNodeDesc(InputNodeWithDynamicOutputs)

        # Check that the plugin has been correctly registered (there has been attempt to load it)
        assert pluginManager.isRegistered(InputNodeWithDynamicOutputs.__name__)

        # Check that the plugin's status is DESC_ERROR, since the node description is invalid
        # Additionally, the list of errors should include an error about having a dynamic output in an InputNode
        plugin = pluginManager.getRegisteredNodePlugin(InputNodeWithDynamicOutputs.__name__)
        assert plugin
        assert plugin.status == NodePluginStatus.DESC_ERROR
        assert len(plugin.errors) == 1
        errType = plugin.errors[0][1]
        assert errType == desc.ValueTypeErrors.DYNAMIC_OUTPUT

        unregisterNodeDesc(InputNodeWithDynamicOutputs)

    def test_registerInputNodeWithDynamicOutputsV2(self):
        """" Check that an input node with dynamic outputs has not been registered because it is invalid. """
        graph = Graph("")
        with pytest.raises(UnknownNodeTypeError):
            # InputDynamicOutputs is located in tests/nodes/test/InputDynamicOutputs.py
            # InputDynamicOutputs has the same description as InputNodeWithDynamicOutputs: had it been valid, it would
            # have been loaded and registered by the plugin manager at the upper level of the test suite.
            graph.addNewNode("InputDynamicOutputs")


class TestDynamicListOutputs:
    """Tests for dynamic output ListAttribute support."""

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithDynamicListOutput)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithDynamicListOutput)

    def test_dynamicListOutputDescriptor(self):
        """Check that a ListAttribute with value=None is correctly flagged as dynamic."""
        nodeDesc = NodeWithDynamicListOutput()
        assert nodeDesc.hasDynamicOutputAttribute
        listOutputDesc = nodeDesc.outputs[0]
        assert listOutputDesc.isDynamicValue

    def test_processWithDynamicListOutput(self, graphSavedOnDisk):
        """Process a node that sets a dynamic output ListAttribute during processChunk."""
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithDynamicListOutput.__name__)

        node.listInput.value = ["hello", "world"]

        # Execute the node
        node.process(inCurrentEnv=True)

        # After processChunk, raw values are stored for serialization (thread-safe).
        # getPrimitiveValue returns the raw values without requiring QObject children.
        assert node.listOutput.getPrimitiveValue() == ["HELLO", "WORLD"]

        # loadOutputAttr materializes QObject children (normally on the main thread)
        node.loadOutputAttr()
        outputValues = [attr.value for attr in node.listOutput.value]
        assert outputValues == ["HELLO", "WORLD"]

    def test_loadGraphWithComputedDynamicListOutput(self, graphSavedOnDisk):
        """Check that dynamic list output values are persisted and reloaded correctly."""
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithDynamicListOutput.__name__)
        name = node.name

        node.listInput.value = ["foo", "bar", "baz"]
        graph.save()

        # Execute the node
        node.process(inCurrentEnv=True)

        # Verify raw output was stored
        assert node.listOutput.getPrimitiveValue() == ["FOO", "BAR", "BAZ"]

        # Reload the graph — loadOutputAttr populates the ListModel on the main thread
        loadedGraph = loadGraph(graph.filepath)
        loadedNode = loadedGraph.node(name)

        assert loadedNode
        loadedOutputValues = [attr.value for attr in loadedNode.listOutput.value]
        assert loadedOutputValues == ["FOO", "BAR", "BAZ"]

    def test_loadGraphWithUncomputedDynamicListOutput(self, graphSavedOnDisk):
        """Check that an uncomputed dynamic list output is empty after loading."""
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithDynamicListOutput.__name__)
        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        loadedNode = loadedGraph.node(node.name)

        assert loadedNode
        # Uncomputed dynamic list output should be empty
        assert len(loadedNode.listOutput) == 0
