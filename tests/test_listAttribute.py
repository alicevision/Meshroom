from meshroom.core import desc
from meshroom.core.attribute import ListAttribute
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

class NodeWithNestedListAttribute(desc.Node):
    inputs = [
        desc.ListAttribute(
            name="nestedListInput",
            label="Nested List Input",
            description="ListAttribute whose elements are themselves ListAttributes of StringParams.",
            elementDesc=desc.ListAttribute(
                name="innerList",
                label="Inner List",
                description="Inner list of strings.",
                elementDesc=desc.StringParam(name="value", label="Value", description="", value=""),
            ),
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


class TestNestedListAttribute:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithNestedListAttribute)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithNestedListAttribute)

    def test_appendInnerList(self):
        """ Appending a list value to a nested ListAttribute creates an inner ListAttribute element. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListAttribute.__name__)

        node.nestedListInput.append(["a", "b", "c"])

        assert len(node.nestedListInput) == 1
        inner = node.nestedListInput.at(0)
        assert isinstance(inner, ListAttribute)
        assert len(inner) == 3

    def test_extendInnerLists(self):
        """ Extending a nested ListAttribute with multiple inner lists works correctly. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListAttribute.__name__)

        node.nestedListInput.extend([["a", "b"], ["c", "d", "e"]])

        assert len(node.nestedListInput) == 2
        assert len(node.nestedListInput.at(0)) == 2
        assert len(node.nestedListInput.at(1)) == 3

    def test_innerListValues(self):
        """ Values stored in an inner list are accessible and correct. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListAttribute.__name__)

        node.nestedListInput.append(["x", "y", "z"])

        inner = node.nestedListInput.at(0)
        assert inner.at(0).value == "x"
        assert inner.at(1).value == "y"
        assert inner.at(2).value == "z"

    def test_nodeAttributeAccessByName(self):
        """ node.attribute('nestedListInput[0][1]') resolves to the correct inner element. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListAttribute.__name__)

        node.nestedListInput.append(["alpha", "beta", "gamma"])

        # Access via node.attribute() path notation
        att = node.attribute("nestedListInput[0][0]")
        assert att.value == "alpha"

        att = node.attribute("nestedListInput[0][1]")
        assert att.value == "beta"

        att = node.attribute("nestedListInput[0][2]")
        assert att.value == "gamma"

    def test_nodeAttributeAccessMultipleOuterElements(self):
        """ node.attribute() resolves nested indices across different outer elements. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListAttribute.__name__)

        node.nestedListInput.extend([["first", "second"], ["third"]])

        assert node.attribute("nestedListInput[0][0]").value == "first"
        assert node.attribute("nestedListInput[0][1]").value == "second"
        assert node.attribute("nestedListInput[1][0]").value == "third"

    def test_modifyInnerElementViaAttribute(self):
        """ An inner element retrieved via node.attribute() can have its value changed. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListAttribute.__name__)

        node.nestedListInput.append(["original"])

        att = node.attribute("nestedListInput[0][0]")
        att.value = "modified"

        assert node.nestedListInput.at(0).at(0).value == "modified"

    def test_emptyInnerList(self):
        """ An empty inner list can be appended and has length zero. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListAttribute.__name__)

        node.nestedListInput.append([])

        assert len(node.nestedListInput) == 1
        assert len(node.nestedListInput.at(0)) == 0

    def test_removeInnerList(self):
        """ Removing an outer element reduces the outer list length. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListAttribute.__name__)

        node.nestedListInput.extend([["a"], ["b"], ["c"]])
        assert len(node.nestedListInput) == 3

        node.nestedListInput.remove(1)
        assert len(node.nestedListInput) == 2
        # Remaining elements are at indices 0 and 1
        assert node.nestedListInput.at(0).at(0).value == "a"
        assert node.nestedListInput.at(1).at(0).value == "c"
