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


class NodeWithListOfGroupsAttribute(desc.Node):
    """Node with a ListAttribute whose elements are GroupAttributes (list of groups)."""
    inputs = [
        desc.ListAttribute(
            name="listOfGroups",
            label="List of Groups",
            description="ListAttribute of GroupAttributes, each group containing a string and an int.",
            elementDesc=desc.GroupAttribute(
                name="item",
                label="Item",
                description="A group item with a name and a value.",
                items=[
                    desc.StringParam(
                        name="itemLabel",
                        label="Item Label",
                        description="String field in the group.",
                        value="",
                    ),
                    desc.IntParam(
                        name="count",
                        label="Count",
                        description="Integer field in the group.",
                        value=0,
                        range=(0, 1000, 1),
                    ),
                ],
            ),
        ),
    ]


class NodeWithNestedListOfGroupsAttribute(desc.Node):
    """
    Node with a ListAttribute of ListAttribute of GroupAttribute.
    Accessing a leaf field requires two index levels: list[outer][inner].field
    """
    inputs = [
        desc.ListAttribute(
            name="nestedListOfGroups",
            label="Nested List of Groups",
            description="Outer list whose elements are inner lists of GroupAttributes.",
            elementDesc=desc.ListAttribute(
                name="innerListOfGroups",
                label="Inner List of Groups",
                description="Inner list of GroupAttributes.",
                elementDesc=desc.GroupAttribute(
                    name="item",
                    label="Item",
                    description="A group with two fields.",
                    items=[
                        desc.StringParam(
                            name="itemName",
                            label="Item Name",
                            description="Name of the item.",
                            value="",
                        ),
                        desc.IntParam(
                            name="itemValue",
                            label="Item Value",
                            description="Value of the item.",
                            value=0,
                            range=(0, 9999, 1),
                        ),
                    ],
                ),
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

    def test_valueAccessorsMatch(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithListAttribute.__name__)
        nodeA.listInput.extend(["A", "B", "C"])
        assert nodeA.listInput.at(0) == nodeA.listInput.value[0]
        assert nodeA.listInput.at(1).value == nodeA.listInput.value[1].value
        assert nodeA.listInput.at(2).value == nodeA.listInput.value[2].value == "C"


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


class TestListOfGroupsAttribute:
    """
    Tests for a ListAttribute whose elements are GroupAttributes (flat list[idx].field pattern).
    """

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithListOfGroupsAttribute)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithListOfGroupsAttribute)

    def test_appendGroupElement(self):
        """ Appending a dict to a list-of-groups creates a GroupAttribute element. """
        from meshroom.core.attribute import GroupAttribute
        graph = Graph("")
        node = graph.addNewNode(NodeWithListOfGroupsAttribute.__name__)

        node.listOfGroups.append({"itemLabel": "hello", "count": 3})

        assert len(node.listOfGroups) == 1
        elem = node.listOfGroups.at(0)
        assert isinstance(elem, GroupAttribute)

    def test_groupElementFieldValues(self):
        """ Fields within a list-of-groups element have the correct values. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithListOfGroupsAttribute.__name__)

        node.listOfGroups.extend([
            {"itemLabel": "foo", "count": 10},
            {"itemLabel": "bar", "count": 20},
        ])

        assert node.listOfGroups.at(0).itemLabel.value == "foo"
        assert node.listOfGroups.at(0).count.value == 10
        assert node.listOfGroups.at(1).itemLabel.value == "bar"
        assert node.listOfGroups.at(1).count.value == 20

    def test_listOfGroupsAttributeAccessByName(self):
        """ node.attribute('listOfGroups[0].label') resolves to the correct leaf attribute. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithListOfGroupsAttribute.__name__)

        node.listOfGroups.extend([
            {"itemLabel": "alpha", "count": 1},
            {"itemLabel": "beta", "count": 2},
        ])

        assert node.attribute("listOfGroups[0].itemLabel").value == "alpha"
        assert node.attribute("listOfGroups[0].count").value == 1
        assert node.attribute("listOfGroups[1].itemLabel").value == "beta"
        assert node.attribute("listOfGroups[1].count").value == 2

    def test_modifyGroupElementFieldViaAttributePath(self):
        """ A field retrieved via 'listOfGroups[idx].field' path notation can be mutated. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithListOfGroupsAttribute.__name__)

        node.listOfGroups.append({"itemLabel": "original", "count": 0})

        node.attribute("listOfGroups[0].itemLabel").value = "updated"
        node.attribute("listOfGroups[0].count").value = 99

        assert node.listOfGroups.at(0).itemLabel.value == "updated"
        assert node.listOfGroups.at(0).count.value == 99

    def test_removeGroupElement(self):
        """ Removing an element from a list of groups shifts subsequent elements correctly. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithListOfGroupsAttribute.__name__)

        node.listOfGroups.extend([
            {"itemLabel": "A", "count": 1},
            {"itemLabel": "B", "count": 2},
            {"itemLabel": "C", "count": 3},
        ])

        node.listOfGroups.remove(1)  # Remove "B"

        assert len(node.listOfGroups) == 2
        assert node.attribute("listOfGroups[0].itemLabel").value == "A"
        assert node.attribute("listOfGroups[1].itemLabel").value == "C"


class TestNestedListOfGroupsAttribute:
    """
    Tests for GroupAttributes accessed through two levels of ListAttribute indexing:
    list[outer][inner].field  (ListAttribute of ListAttribute of GroupAttribute).
    """

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithNestedListOfGroupsAttribute)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithNestedListOfGroupsAttribute)

    def test_appendInnerListOfGroups(self):
        """
        Appending an inner list of group dicts creates inner ListAttribute elements
        that are themselves GroupAttributes.
        """
        from meshroom.core.attribute import GroupAttribute as GA
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListOfGroupsAttribute.__name__)

        node.nestedListOfGroups.append([{"itemName": "a", "itemValue": 1}])

        assert len(node.nestedListOfGroups) == 1
        inner = node.nestedListOfGroups.at(0)
        assert isinstance(inner, ListAttribute)
        assert len(inner) == 1
        assert isinstance(inner.at(0), GA)

    def test_innerGroupFieldValues(self):
        """ Group fields are accessible via direct attribute traversal through two list levels. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListOfGroupsAttribute.__name__)

        node.nestedListOfGroups.extend([
            [{"itemName": "x", "itemValue": 10}, {"itemName": "y", "itemValue": 20}],
            [{"itemName": "z", "itemValue": 30}],
        ])

        assert node.nestedListOfGroups.at(0).at(0).itemName.value == "x"
        assert node.nestedListOfGroups.at(0).at(0).itemValue.value == 10
        assert node.nestedListOfGroups.at(0).at(1).itemName.value == "y"
        assert node.nestedListOfGroups.at(0).at(1).itemValue.value == 20
        assert node.nestedListOfGroups.at(1).at(0).itemName.value == "z"
        assert node.nestedListOfGroups.at(1).at(0).itemValue.value == 30

    def test_nestedListOfGroupsAttributeAccessByName(self):
        """ node.attribute('nestedListOfGroups[outer][inner].field') resolves correctly. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListOfGroupsAttribute.__name__)

        node.nestedListOfGroups.extend([
            [{"itemName": "alpha", "itemValue": 1}, {"itemName": "beta", "itemValue": 2}],
            [{"itemName": "gamma", "itemValue": 3}],
        ])

        assert node.attribute("nestedListOfGroups[0][0].itemName").value == "alpha"
        assert node.attribute("nestedListOfGroups[0][0].itemValue").value == 1
        assert node.attribute("nestedListOfGroups[0][1].itemName").value == "beta"
        assert node.attribute("nestedListOfGroups[0][1].itemValue").value == 2
        assert node.attribute("nestedListOfGroups[1][0].itemName").value == "gamma"
        assert node.attribute("nestedListOfGroups[1][0].itemValue").value == 3

    def test_modifyGroupFieldViaNestedPath(self):
        """ Fields reached through list[outer][inner].field path notation can be mutated. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListOfGroupsAttribute.__name__)

        node.nestedListOfGroups.append([{"itemName": "old", "itemValue": 0}])

        node.attribute("nestedListOfGroups[0][0].itemName").value = "new"
        node.attribute("nestedListOfGroups[0][0].itemValue").value = 42

        assert node.nestedListOfGroups.at(0).at(0).itemName.value == "new"
        assert node.nestedListOfGroups.at(0).at(0).itemValue.value == 42

    def test_multipleInnerGroupsPerOuterElement(self):
        """ Multiple groups in the same inner list are all independently accessible. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListOfGroupsAttribute.__name__)

        inner = [{"itemName": str(i), "itemValue": i * 10} for i in range(4)]
        node.nestedListOfGroups.append(inner)

        for i in range(4):
            assert node.attribute(f"nestedListOfGroups[0][{i}].itemName").value == str(i)
            assert node.attribute(f"nestedListOfGroups[0][{i}].itemValue").value == i * 10

    def test_removeOuterListReducesLength(self):
        """ Removing an outer element and verifying the remaining inner groups are correct. """
        graph = Graph("")
        node = graph.addNewNode(NodeWithNestedListOfGroupsAttribute.__name__)

        node.nestedListOfGroups.extend([
            [{"itemName": "keep", "itemValue": 1}],
            [{"itemName": "remove", "itemValue": 2}],
        ])

        node.nestedListOfGroups.remove(1)

        assert len(node.nestedListOfGroups) == 1
        assert node.attribute("nestedListOfGroups[0][0].itemName").value == "keep"
