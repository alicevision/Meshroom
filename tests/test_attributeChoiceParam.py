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
