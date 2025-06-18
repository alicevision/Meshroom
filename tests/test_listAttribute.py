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

        graph.addEdge(nodeA.listInput, nodeB.listInput)

        nodeA.listInput.append("test")

        assert len(nodeB.listInput) == 1

    def test_iterationUsesLinkParam(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithListAttribute.__name__)
        nodeB = graph.addNewNode(NodeWithListAttribute.__name__)

        graph.addEdge(nodeA.listInput, nodeB.listInput)

        nodeA.listInput.extend(["A", "B", "C"])

        for value in nodeB.listInput:
            assert value.node == nodeA

    def test_elementAccessUsesLinkParam(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithListAttribute.__name__)
        nodeB = graph.addNewNode(NodeWithListAttribute.__name__)

        graph.addEdge(nodeA.listInput, nodeB.listInput)

        nodeA.listInput.extend(["A", "B", "C"])

        assert nodeB.listInput.at(0).node == nodeA
        assert nodeB.listInput.index(nodeB.listInput.at(0)) == 0
