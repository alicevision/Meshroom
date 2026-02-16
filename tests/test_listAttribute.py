from meshroom.core import desc
from meshroom.core.graph import Graph

from .utils import registerNodeDesc, unregisterNodeDesc


class NodeWithListAttribute(desc.Node):
    inputs = [
        desc.ListAttribute(
            name="listInput",
            label="List Input",
            description="ListAttribute of StringParams.",
            elementDesc=desc.StringParam(name="value", label="Value", description="", value=""),
        )
    ]


class TestListAttribute:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithListAttribute)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithListAttribute)

    def test_lengthUsesLinkParam(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithListAttribute.__name__)
        nodeB = graph.addNewNode(NodeWithListAttribute.__name__)

        nodeA.listInput.connectTo(nodeB.listInput)

        nodeA.listInput.append("test")

        assert len(nodeB.listInput) == 1

    def test_iterationUsesLinkParam(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithListAttribute.__name__)
        nodeB = graph.addNewNode(NodeWithListAttribute.__name__)

        nodeA.listInput.connectTo(nodeB.listInput)

        nodeA.listInput.extend(["A", "B", "C"])

        for value in nodeB.listInput:
            assert value.node == nodeA

    def test_elementAccessUsesLinkParam(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithListAttribute.__name__)
        nodeB = graph.addNewNode(NodeWithListAttribute.__name__)

        nodeA.listInput.connectTo(nodeB.listInput)

        nodeA.listInput.extend(["A", "B", "C"])

        assert nodeB.listInput.at(0).node == nodeA
        assert nodeB.listInput.index(nodeB.listInput.at(0)) == 0

    def test_connectToTwoListAttributesReplacesLink(self):
        """
        Test that connecting two different ListAttributes to the same destination
        ListAttribute using connectTo replaces the first link with the second one.
        """
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithListAttribute.__name__)
        nodeB = graph.addNewNode(NodeWithListAttribute.__name__)
        nodeC = graph.addNewNode(NodeWithListAttribute.__name__)

        nodeA.listInput.extend(["A1", "A2", "A3"])
        nodeB.listInput.extend(["B1", "B2"])

        # First connection: nodeA.listInput -> nodeC.listInput
        nodeA.listInput.connectTo(nodeC.listInput)
        assert nodeC.listInput.isLink
        assert len(nodeC.listInput) == 3
        assert nodeC.listInput.at(0).node == nodeA

        # Second connection replaces the first (connectTo disconnects root)
        nodeB.listInput.connectTo(nodeC.listInput)
        assert nodeC.listInput.isLink
        assert len(nodeC.listInput) == 2
        assert nodeC.listInput.at(0).node == nodeB
        assert nodeC.listInput.at(1).node == nodeB
        assert not nodeA.listInput.hasAnyOutputLinks

    def test_addListEdgesAccumulatesElements(self):
        """
        Test that Graph.addListEdges correctly decomposes an existing list-level
        link and accumulates individual element-level links from multiple sources.
        """
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithListAttribute.__name__)
        nodeB = graph.addNewNode(NodeWithListAttribute.__name__)
        nodeC = graph.addNewNode(NodeWithListAttribute.__name__)

        nodeA.listInput.extend(["A1", "A2"])
        nodeB.listInput.extend(["B1", "B2"])

        # First addListEdges: nodeA -> nodeC
        createdEdges, deletedEdges = graph.addListEdges(nodeA.listInput, nodeC.listInput)
        assert len(createdEdges) == 2
        assert len(deletedEdges) == 0
        assert len(nodeC.listInput) == 2
        assert nodeC.listInput.at(0).isLink
        assert nodeC.listInput.at(1).isLink
        assert nodeC.listInput.at(0).inputLink.node == nodeA
        assert nodeC.listInput.at(1).inputLink.node == nodeA

        # Second addListEdges: nodeB -> nodeC (accumulates)
        createdEdges, deletedEdges = graph.addListEdges(nodeB.listInput, nodeC.listInput)
        assert len(createdEdges) == 2
        assert len(deletedEdges) == 0

        # All 4 element-level links should be preserved
        assert len(nodeC.listInput) == 4
        assert nodeC.listInput.at(0).inputLink.node == nodeA
        assert nodeC.listInput.at(1).inputLink.node == nodeA
        assert nodeC.listInput.at(2).inputLink.node == nodeB
        assert nodeC.listInput.at(3).inputLink.node == nodeB

    def test_addListEdgesDecomposesExistingViewLink(self):
        """
        Test that Graph.addListEdges decomposes an existing list-level 'view' link
        into individual element links before adding new ones.
        """
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithListAttribute.__name__)
        nodeB = graph.addNewNode(NodeWithListAttribute.__name__)
        nodeC = graph.addNewNode(NodeWithListAttribute.__name__)

        nodeA.listInput.extend(["A1", "A2"])
        nodeB.listInput.extend(["B1"])

        # Create a list-level "view" link: nodeA.listInput -> nodeC.listInput
        nodeA.listInput.connectTo(nodeC.listInput)
        assert nodeC.listInput.isLink
        assert len(nodeC.listInput) == 2

        # addListEdges should decompose the view and add nodeB's elements
        createdEdges, deletedEdges = graph.addListEdges(nodeB.listInput, nodeC.listInput)

        # The view link was deleted, individual links from nodeA were re-created,
        # plus a new link from nodeB
        assert len(nodeC.listInput) == 3
        assert nodeC.listInput.at(0).inputLink.node == nodeA
        assert nodeC.listInput.at(1).inputLink.node == nodeA
        assert nodeC.listInput.at(2).inputLink.node == nodeB
