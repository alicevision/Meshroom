from meshroom.core import desc
from meshroom.core.node import Node
from meshroom.core.graph import Graph, loadGraph

from .utils import registerNodeDesc, unregisterNodeDesc


class NodeWithCreationCallback(desc.InputNode):
    """Node defining an 'onNodeCreated' callback, triggered a new node is added to a Graph."""

    inputs = [
        desc.BoolParam(
            name="triggered",
            label="Triggered",
            description="Attribute impacted by the `onNodeCreated` callback",
            value=False,
        ),
    ]

    @classmethod
    def onNodeCreated(cls, node: Node):
        """Triggered when a new node is created within a Graph."""
        node.triggered.value = True


class TestNodeCreationCallback:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithCreationCallback)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithCreationCallback)

    def test_notTriggeredOnNodeInstantiation(self):
        node = Node(NodeWithCreationCallback.__name__)
        assert node.triggered.value is False

    def test_triggeredOnNewNodeCreationInGraph(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithCreationCallback.__name__)
        assert node.triggered.value is True

    def test_notTriggeredOnNodeDuplication(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithCreationCallback.__name__)
        node.triggered.resetToDefaultValue()

        duplicates = graph.duplicateNodes([node])
        assert duplicates[node][0].triggered.value is False

    def test_notTriggeredOnGraphLoad(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithCreationCallback.__name__)
        node.triggered.resetToDefaultValue()
        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        assert loadedGraph.node(node.name).triggered.value is False

    def test_triggeredOnGraphInitializationFromTemplate(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithCreationCallback.__name__)
        node.triggered.resetToDefaultValue()
        graph.save(template=True)

        graphFromTemplate = Graph("")
        graphFromTemplate.initFromTemplate(graph.filepath)

        assert graphFromTemplate.node(node.name).triggered.value is True
