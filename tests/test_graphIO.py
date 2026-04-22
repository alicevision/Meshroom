import json
import os
from textwrap import dedent
from pathlib import Path

from meshroom.core import desc
from meshroom.core.graph import Graph
from meshroom.core.node import CompatibilityIssue

from .utils import registeredNodeTypes, overrideNodeTypeVersion


class SimpleNode(desc.Node):
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value=""),
    ]


class NodeWithListAttributes(desc.Node):
    inputs = [
        desc.ListAttribute(
            name="listInput",
            label="List Input",
            description="",
            elementDesc=desc.File(name="file", label="File", description="", value=""),
            exposed=True,
        ),
        desc.GroupAttribute(
            name="group",
            label="Group",
            description="",
            items=[
                desc.ListAttribute(
                    name="listInput",
                    label="List Input",
                    description="",
                    elementDesc=desc.File(name="file", label="File", description="", value=""),
                    exposed=True,
                ),
            ],
        ),
    ]


def assertPathsAreEqual(pathA, pathB):
    return Path(pathA).resolve().as_posix() == Path(pathB).resolve().as_posix()


def compareGraphsContent(graphA: Graph, graphB: Graph) -> bool:
    """Returns whether the content (node and deges) of two graphs are considered identical.

    Similar nodes: nodes with the same name, type and compatibility status.
    Similar edges: edges with the same source and destination attribute names.
    """

    def _buildNodesSet(graph: Graph):
        return set([(node.name, node.nodeType, node.isCompatibilityNode) for node in graph.nodes])

    def _buildEdgesSet(graph: Graph):
        return set([(edge.src.rootName, edge.dst.rootName) for edge in graph.edges])

    nodesSetA, edgesSetA = _buildNodesSet(graphA), _buildEdgesSet(graphA)
    nodesSetB, edgesSetB = _buildNodesSet(graphB), _buildEdgesSet(graphB)

    return nodesSetA == nodesSetB and edgesSetA == edgesSetB


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

            nodeA_1.output.connectTo(nodeA_2.input)

            otherGraph = Graph("")
            otherGraph.importGraphContent(graph)
            assert compareGraphsContent(graph, otherGraph)

    def test_edgeRemappingOnImportingGraphSeveralTimes(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            nodeA_1 = graph.addNewNode(SimpleNode.__name__)
            nodeA_2 = graph.addNewNode(SimpleNode.__name__)

            nodeA_1.output.connectTo(nodeA_2.input)

            otherGraph = Graph("")
            otherGraph.importGraphContent(graph)
            otherGraph.importGraphContent(graph)

    def test_edgeRemappingOnImportingGraphWithUnkownNodeTypesSeveralTimes(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            nodeA_1 = graph.addNewNode(SimpleNode.__name__)
            nodeA_2 = graph.addNewNode(SimpleNode.__name__)

            nodeA_1.output.connectTo(nodeA_2.input)

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

            nodeA_1.output.connectTo(nodeA_2.input)

            graph.importGraphContent(graph)

            assert len(graph.nodes) == 4

    def test_importGraphContentFromFile(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        with registeredNodeTypes([SimpleNode]):
            nodeA_1 = graph.addNewNode(SimpleNode.__name__)
            nodeA_2 = graph.addNewNode(SimpleNode.__name__)

            nodeA_1.output.connectTo(nodeA_2.input)
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

            nodeA_1.output.connectTo(nodeA_2.input)
            graph.save()

        otherGraph = Graph("")
        nodes = otherGraph.importGraphContentFromFile(graph.filepath)

        assert len(nodes) == 2
        assert len(otherGraph.compatibilityNodes) == 2
        assert not compareGraphsContent(graph, otherGraph)

    def test_importingDifferentNodeVersionCreatesCompatibilityNodes(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk

        with registeredNodeTypes([SimpleNode]):
            with overrideNodeTypeVersion(SimpleNode, "1.0"):
                node = graph.addNewNode(SimpleNode.__name__)
                graph.save()

            with overrideNodeTypeVersion(SimpleNode, "2.0"):
                otherGraph = Graph("")
                nodes = otherGraph.importGraphContentFromFile(graph.filepath)

        assert len(nodes) == 1
        assert len(otherGraph.compatibilityNodes) == 1
        assert otherGraph.node(node.name).issue is CompatibilityIssue.VersionConflict


class TestGraphSave:
    def test_generateNextPath(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        root = os.path.dirname(graph._filepath)
        # Files with no version number (e.g., "scene.mg" -> "scene1.mg")
        graph._filepath = os.path.join(root, "scene.mg")
        assertPathsAreEqual(graph._generateNextPath(), os.path.join(root, "scene1.mg"))
        # Files with existing version numbers (e.g., "scene1.mg" -> "scene2.mg")
        graph._filepath = os.path.join(root, "scene_1.mg")
        assertPathsAreEqual(graph._generateNextPath(), os.path.join(root, "scene_2.mg"))
        # Edge cases like filenames that are purely numeric (e.g., "123.mg")
        # Also test that the padding is kept ("001" -> "002" and not "2")
        graph._filepath = os.path.join(root, "0123.mg")
        assertPathsAreEqual(graph._generateNextPath(), os.path.join(root, "0124.mg"))
        graph._filepath = os.path.join(root, "scene_001.mg")
        assertPathsAreEqual(graph._generateNextPath(), os.path.join(root, "scene_002.mg"))
        # Files where the next version already exists (e.g., "scene1.mg" when "scene2.mg" exists -> "scene3.mg")
        graph._filepath = os.path.join(root, "scene1.mg")
        open(os.path.join(root, "scene2.mg"), 'a').close()
        assertPathsAreEqual(graph._generateNextPath(), os.path.join(root, "scene3.mg"))

    def test_saveAsNewVersion(self, tmp_path):
        graph = Graph("")
        with registeredNodeTypes([SimpleNode]):
            # Create scene
            nodeA = graph.addNewNode(SimpleNode.__name__)
            scenePath = os.path.join(tmp_path, "scene.mg")
            graph._filepath = scenePath
            graph.save()
            assert os.path.exists(scenePath)
            # Modify scene
            nodeB = graph.addNewNode(SimpleNode.__name__)
            nodeA.output.connectTo(nodeB.input)
            graph.saveAsNewVersion()
            newScenePath = os.path.join(tmp_path, "scene1.mg")
            assert os.path.exists(newScenePath)


class TestGraphPartialSerialization:
    def test_emptyGraph(self):
        graph = Graph("")
        serializedGraph = graph.serializePartial([])

        otherGraph = Graph("")
        otherGraph._deserialize(serializedGraph)
        assert compareGraphsContent(graph, otherGraph)

    def test_serializeAllNodesIsSimilarToStandardSerialization(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            nodeA = graph.addNewNode(SimpleNode.__name__)
            nodeB = graph.addNewNode(SimpleNode.__name__)

            nodeA.output.connectTo(nodeB.input)

            partialSerializedGraph = graph.serializePartial([nodeA, nodeB])
            standardSerializedGraph = graph.serialize()

            graphA = Graph("")
            graphA._deserialize(partialSerializedGraph)

            graphB = Graph("")
            graphB._deserialize(standardSerializedGraph)

            assert compareGraphsContent(graph, graphA)
            assert compareGraphsContent(graphA, graphB)

    def test_listAttributeToListAttributeConnectionIsSerialized(self):
        graph = Graph("")

        with registeredNodeTypes([NodeWithListAttributes]):
            nodeA = graph.addNewNode(NodeWithListAttributes.__name__)
            nodeB = graph.addNewNode(NodeWithListAttributes.__name__)

            nodeA.listInput.connectTo(nodeB.listInput)

            otherGraph = Graph("")
            otherGraph._deserialize(graph.serializePartial([nodeA, nodeB]))

            assert otherGraph.node(nodeB.name).listInput.inputLink == \
                otherGraph.node(nodeA.name).listInput

    def test_singleNodeWithInputConnectionFromNonSerializedNodeRemovesEdge(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            nodeA = graph.addNewNode(SimpleNode.__name__)
            nodeB = graph.addNewNode(SimpleNode.__name__)

            nodeA.output.connectTo(nodeB.input)

            serializedGraph = graph.serializePartial([nodeB])

            otherGraph = Graph("")
            otherGraph._deserialize(serializedGraph)

            assert len(otherGraph.compatibilityNodes) == 0
            assert len(otherGraph.nodes) == 1
            assert len(otherGraph.edges) == 0

    def test_serializeSingleNodeWithInputConnectionToListAttributeRemovesListEntry(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode, NodeWithListAttributes]):
            nodeA = graph.addNewNode(SimpleNode.__name__)
            nodeB = graph.addNewNode(NodeWithListAttributes.__name__)

            nodeB.listInput.append("")
            nodeA.output.connectTo(nodeB.listInput.at(0))

            otherGraph = Graph("")
            otherGraph._deserialize(graph.serializePartial([nodeB]))

            assert len(otherGraph.node(nodeB.name).listInput) == 0

    def test_serializeSingleNodeWithInputConnectionToNestedListAttributeRemovesListEntry(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode, NodeWithListAttributes]):
            nodeA = graph.addNewNode(SimpleNode.__name__)
            nodeB = graph.addNewNode(NodeWithListAttributes.__name__)

            nodeB.group.listInput.append("")
            nodeA.output.connectTo(nodeB.group.listInput.at(0))

            otherGraph = Graph("")
            otherGraph._deserialize(graph.serializePartial([nodeB]))

            assert len(otherGraph.node(nodeB.name).group.listInput) == 0


class TestGraphCopy:
    def test_graphCopyIsIdenticalToOriginalGraph(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            nodeA = graph.addNewNode(SimpleNode.__name__)
            nodeB = graph.addNewNode(SimpleNode.__name__)

            nodeA.output.connectTo(nodeB.input)

            graphCopy = graph.copy()
            assert compareGraphsContent(graph, graphCopy)

    def test_graphCopyWithUnknownNodeTypesDiffersFromOriginalGraph(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            nodeA = graph.addNewNode(SimpleNode.__name__)
            nodeB = graph.addNewNode(SimpleNode.__name__)

            nodeA.output.connectTo(nodeB.input)

        graphCopy = graph.copy()
        assert not compareGraphsContent(graph, graphCopy)


class TestImportGraphContentFromMinimalGraphData:
    def test_nodeWithoutVersionInfoIsUpgraded(self):
        graph = Graph("")

        with (
            registeredNodeTypes([SimpleNode]),
            overrideNodeTypeVersion(SimpleNode, "2.0"),
        ):
            sampleGraphContent = dedent("""
            {
                "SimpleNode_1": { "nodeType": "SimpleNode" }
            }
            """)
            graph._deserialize(json.loads(sampleGraphContent))

            assert len(graph.nodes) == 1
            assert len(graph.compatibilityNodes) == 0

    def test_connectionsToMissingNodesAreDiscarded(self):
        graph = Graph("")

        with registeredNodeTypes([SimpleNode]):
            sampleGraphContent = dedent("""
            {
                "SimpleNode_1": {
                    "nodeType": "SimpleNode", "inputs": { "input": "{NotSerializedNode.output}" }
                }
            }
            """)
            graph._deserialize(json.loads(sampleGraphContent))


class TestTemplateSerialization:

    def test_templateSerializationStripsOutputsUidAndParallelization(self):
        """Test that template serialization removes outputs, uid, and parallelization."""
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            graph.addNewNode("SimpleNode")

            data = graph.serialize(asTemplate=True)
            nodeData = data["graph"]["SimpleNode_1"]

            assert "outputs" not in nodeData
            assert "uid" not in nodeData
            assert "parallelization" not in nodeData

    def test_templateSerializationStripsDefaultInputs(self):
        """Test that default-valued inputs are stripped from template serialization."""
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            graph.addNewNode("SimpleNode")

            data = graph.serialize(asTemplate=True)
            nodeData = data["graph"]["SimpleNode_1"]

            # All inputs are at default, so inputs should be empty or absent
            assert nodeData.get("inputs", {}) == {}

    def test_templateSerializationPreservesNonDefaultInputs(self):
        """Test that non-default attribute values are preserved in template serialization."""
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            node = graph.addNewNode("SimpleNode")
            node.attribute("input").value = "/some/path"

            data = graph.serialize(asTemplate=True)
            nodeData = data["graph"]["SimpleNode_1"]

            assert nodeData["inputs"]["input"] == "/some/path"
