from meshroom.core import desc
from meshroom.core.graph import Graph

from .utils import registeredNodeTypes


class SimpleNode(desc.Node):
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value=""),
    ]


def compareGraphsContent(graphA: Graph, graphB: Graph) -> bool:
    """Returns whether the content (node and deges) of two graphs are considered identical.

    Similar nodes: nodes with the same name, type and compatibility status.
    Similar edges: edges with the same source and destination attribute names.
    """

    def _buildNodesSet(graph: Graph):
        return set([(node.name, node.nodeType, node.isCompatibilityNode) for node in graph.nodes])

    def _buildEdgesSet(graph: Graph):
        return set([(edge.src.fullName, edge.dst.fullName) for edge in graph.edges])

    return _buildNodesSet(graphA) == _buildNodesSet(graphB) and _buildEdgesSet(graphA) == _buildEdgesSet(
        graphB
    )


class TestImportGraphContent:
    def test_importEmptyGraph(self):
        graph = Graph("")

        otherGraph = Graph("")
        nodes = otherGraph.importGraphContent(graph)

        assert len(nodes) == 0
        assert len(graph.nodes) == 0

    def test_importGraphWithSingleNode(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            graph.addNewNode(SimpleNode.__name__)

            otherGraph = Graph("")
            otherGraph.importGraphContent(graph)

            assert compareGraphsContent(graph, otherGraph)

    def test_importGraphWithSeveralNodes(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            graph.addNewNode(SimpleNode.__name__)
            graph.addNewNode(SimpleNode.__name__)

            otherGraph = Graph("")
            otherGraph.importGraphContent(graph)

            assert compareGraphsContent(graph, otherGraph)

    def test_importingGraphWithNodesAndEdges(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            nodeA_1 = graph.addNewNode(SimpleNode.__name__)
            nodeA_2 = graph.addNewNode(SimpleNode.__name__)

            graph.addEdge(nodeA_1.output, nodeA_2.input)

            otherGraph = Graph("")
            otherGraph.importGraphContent(graph)
            assert compareGraphsContent(graph, otherGraph)

    def test_edgeRemappingOnImportingGraphSeveralTimes(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            nodeA_1 = graph.addNewNode(SimpleNode.__name__)
            nodeA_2 = graph.addNewNode(SimpleNode.__name__)

            graph.addEdge(nodeA_1.output, nodeA_2.input)

            otherGraph = Graph("")
            otherGraph.importGraphContent(graph)
            otherGraph.importGraphContent(graph)

    def test_edgeRemappingOnImportingGraphWithUnkownNodeTypesSeveralTimes(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            nodeA_1 = graph.addNewNode(SimpleNode.__name__)
            nodeA_2 = graph.addNewNode(SimpleNode.__name__)

            graph.addEdge(nodeA_1.output, nodeA_2.input)

        otherGraph = Graph("")
        otherGraph.importGraphContent(graph)
        otherGraph.importGraphContent(graph)

        assert len(otherGraph.nodes) == 4
        assert len(otherGraph.compatibilityNodes) == 4
        assert len(otherGraph.edges) == 2

    def test_importGraphWithUnknownNodeTypesCreatesCompatibilityNodes(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            graph.addNewNode(SimpleNode.__name__)

        otherGraph = Graph("")
        importedNode = otherGraph.importGraphContent(graph)

        assert len(importedNode) == 1
        assert importedNode[0].isCompatibilityNode

    def test_importGraphContentInPlace(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            nodeA_1 = graph.addNewNode(SimpleNode.__name__)
            nodeA_2 = graph.addNewNode(SimpleNode.__name__)

            graph.addEdge(nodeA_1.output, nodeA_2.input)

            graph.importGraphContent(graph)

            assert len(graph.nodes) == 4

    def test_importGraphContentFromFile(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        with registeredNodeTypes([SimpleNode]):
            nodeA_1 = graph.addNewNode(SimpleNode.__name__)
            nodeA_2 = graph.addNewNode(SimpleNode.__name__)

            graph.addEdge(nodeA_1.output, nodeA_2.input)
            graph.save()

            otherGraph = Graph("")
            nodes = otherGraph.importGraphContentFromFile(graph.filepath)

            assert len(nodes) == 2

            assert compareGraphsContent(graph, otherGraph)

    def test_importGraphContentFromFileWithCompatibilityNodes(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        with registeredNodeTypes([SimpleNode]):
            nodeA_1 = graph.addNewNode(SimpleNode.__name__)
            nodeA_2 = graph.addNewNode(SimpleNode.__name__)

            graph.addEdge(nodeA_1.output, nodeA_2.input)
            graph.save()

        otherGraph = Graph("")
        nodes = otherGraph.importGraphContentFromFile(graph.filepath)

        assert len(nodes) == 2
        assert len(otherGraph.compatibilityNodes) == 2
        assert not compareGraphsContent(graph, otherGraph)


