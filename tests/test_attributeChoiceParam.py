from meshroom.core import desc, pluginManager
from meshroom.core.graph import Graph, loadGraph

from .utils import registerNodeDesc, unregisterNodeDesc

class NodeWithChoiceParams(desc.Node):
    inputs = [
        desc.ChoiceParam(
            name="choice",
            label="Choice Default Serialization",
            description="A choice parameter with standard serialization",
            value="A",
            values=["A", "B", "C"],
            saveValuesOverride=False,
            exclusive=True,
            exposed=True,
        ),
        desc.ChoiceParam(
            name="choiceMulti",
            label="Choice Default Serialization",
            description="A choice parameter with standard serialization",
            value=["A"],
            values=["A", "B", "C"],
            saveValuesOverride=False,
            exclusive=False,
            exposed=True,
        ),
    ]

class NodeWithChoiceParamsSavingValuesOverride(desc.Node):
    inputs = [
        desc.ChoiceParam(
            name="choice",
            label="Choice Custom Serialization",
            description="A choice parameter with serialization of overriden values",
            value="A",
            values=["A", "B", "C"],
            saveValuesOverride=True,
            exclusive=True,
            exposed=True,
        ),
        desc.ChoiceParam(
            name="choiceMulti",
            label="Choice Custom Serialization",
            description="A choice parameter with serialization of overriden values",
            value=["A"],
            values=["A", "B", "C"],
            saveValuesOverride=True,
            exclusive=False,
            exposed=True,
        )
    ]


class TestChoiceParam:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithChoiceParams)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithChoiceParams)

    def test_customValueIsSerialized(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        node = graph.addNewNode(NodeWithChoiceParams.__name__)
        node.choice.value = "CustomValue"
        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        assert loadedGraph.node(node.name).choice.value == "CustomValue"

    def test_customMultiValueIsSerialized(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        node = graph.addNewNode(NodeWithChoiceParams.__name__)
        node.choiceMulti.value = ["custom", "value"]
        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        assert loadedGraph.node(node.name).choiceMulti.value == ["custom", "value"]

    def test_overridenValuesAreNotSerialized(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithChoiceParams.__name__)
        node.choice.values = ["D", "E", "F"]

        graph.save()
        loadedGraph = loadGraph(graph.filepath)

        assert loadedGraph.node(node.name).choice.values == ["A", "B", "C"]

    def test_connectionPropagatesOverridenValues(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithChoiceParams.__name__)
        nodeB = graph.addNewNode(NodeWithChoiceParams.__name__)
        nodeA.choice.values = ["D", "E", "F"]
        graph.addEdge(nodeA.choice, nodeB.choice)

        assert nodeB.choice.values == ["D", "E", "F"]

    def test_connectionsAreSerialized(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        nodeA = graph.addNewNode(NodeWithChoiceParams.__name__)
        nodeB = graph.addNewNode(NodeWithChoiceParams.__name__)
        graph.addEdge(nodeA.choice, nodeB.choice)
        graph.addEdge(nodeA.choiceMulti, nodeB.choiceMulti)

        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        loadedNodeA = loadedGraph.node(nodeA.name)
        loadedNodeB = loadedGraph.node(nodeB.name)
        assert loadedNodeB.choice.linkParam == loadedNodeA.choice
        assert loadedNodeB.choiceMulti.linkParam == loadedNodeA.choiceMulti


class TestChoiceParamSavingCustomValues:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithChoiceParamsSavingValuesOverride)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithChoiceParamsSavingValuesOverride)

    def test_customValueIsSerialized(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        node = graph.addNewNode(NodeWithChoiceParamsSavingValuesOverride.__name__)
        node.choice.value = "CustomValue"
        node.choiceMulti.value = ["custom", "value"]
        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        assert loadedGraph.node(node.name).choice.value == "CustomValue"
        assert loadedGraph.node(node.name).choiceMulti.value == ["custom", "value"]


    def test_overridenValuesAreSerialized(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithChoiceParamsSavingValuesOverride.__name__)
        node.choice.values = ["D", "E", "F"]
        node.choiceMulti.values = ["D", "E", "F"]

        graph.save()
        loadedGraph = loadGraph(graph.filepath)

        loadedNode = loadedGraph.node(node.name)

        assert loadedNode.choice.values == ["D", "E", "F"]
        assert loadedNode.choiceMulti.values == ["D", "E", "F"]


    def test_connectionsAreSerialized(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        nodeA = graph.addNewNode(NodeWithChoiceParamsSavingValuesOverride.__name__)
        nodeB = graph.addNewNode(NodeWithChoiceParamsSavingValuesOverride.__name__)
        graph.addEdge(nodeA.choice, nodeB.choice)
        graph.addEdge(nodeA.choiceMulti, nodeB.choiceMulti)

        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        loadedNodeA = loadedGraph.node(nodeA.name)
        loadedNodeB = loadedGraph.node(nodeB.name)
        assert loadedNodeB.choice.linkParam == loadedNodeA.choice
        assert loadedNodeB.choiceMulti.linkParam == loadedNodeA.choiceMulti
