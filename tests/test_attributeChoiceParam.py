from meshroom.core import desc, registerNodeType, unregisterNodeType
from meshroom.core.graph import Graph, loadGraph


class NodeWithStaticChoiceParam(desc.Node):
    inputs = [
        desc.ChoiceParam(
            name="choice",
            label="Choice",
            description="A static choice parameter",
            value="A",
            values=["A", "B", "C"],
            exclusive=True,
            exposed=True,
        ),
    ]

class NodeWithDynamicChoiceParam(desc.Node):
    inputs = [
        desc.DynamicChoiceParam(
            name="dynChoice",
            label="Dynamic Choice",
            description="A dynamic choice parameter",
            value="A",
            values=["A", "B", "C"],
            exclusive=True,
            exposed=True,
        ),
    ]


class TestStaticChoiceParam:
    @classmethod
    def setup_class(cls):
        registerNodeType(NodeWithStaticChoiceParam)

    @classmethod
    def teardown_class(cls):
        unregisterNodeType(NodeWithStaticChoiceParam)

    def test_customValuesAreNotSerialized(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithStaticChoiceParam.__name__)
        node.choice.values = ["D", "E", "F"]
        
        graph.save()
        loadedGraph = loadGraph(graph.filepath)
        loadedNode = loadedGraph.node(node.name)

        assert loadedNode.choice.values == ["A", "B", "C"]

    def test_customValueIsSerialized(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        node = graph.addNewNode(NodeWithStaticChoiceParam.__name__)
        node.choice.value = "CustomValue"
        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        loadedNode = loadedGraph.node(node.name)

        assert loadedNode.choice.value == "CustomValue"


class TestDynamicChoiceParam:
    @classmethod
    def setup_class(cls):
        registerNodeType(NodeWithDynamicChoiceParam)

    @classmethod
    def teardown_class(cls):
        unregisterNodeType(NodeWithDynamicChoiceParam)

    def test_resetDefaultValues(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        node = graph.addNewNode(NodeWithDynamicChoiceParam.__name__)
        node.dynChoice.values = ["D", "E", "F"]
        node.dynChoice.value = "D"
        node.dynChoice.resetToDefaultValue()
        assert node.dynChoice.values == ["A", "B", "C"]
        assert node.dynChoice.value == "A"

    def test_customValueIsSerialized(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        node = graph.addNewNode(NodeWithDynamicChoiceParam.__name__)
        node.dynChoice.value = "CustomValue"
        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        loadedNode = loadedGraph.node(node.name)

        assert loadedNode.dynChoice.value == "CustomValue"

    def test_customValuesAreSerialized(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        node = graph.addNewNode(NodeWithDynamicChoiceParam.__name__)
        node.dynChoice.values = ["D", "E", "F"]

        graph.save()
        loadedGraph = loadGraph(graph.filepath)
        loadedNode = loadedGraph.node(node.name)

        assert loadedNode.dynChoice.values == ["D", "E", "F"]

    def test_duplicateNodeWithGroupAttributeDerivedAttribute(self):
        graph = Graph("")
        node = graph.addNewNode(NodeWithDynamicChoiceParam.__name__)
        node.dynChoice.values = ["D", "E", "F"]
        node.dynChoice.value = "G"
        duplicates = graph.duplicateNodes([node])
        duplicate = duplicates[node][0]
        assert duplicate.dynChoice.value == node.dynChoice.value
        assert duplicate.dynChoice.values == node.dynChoice.values
