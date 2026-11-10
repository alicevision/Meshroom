#!/usr/bin/env python
# coding:utf-8

import os
import tempfile

from meshroom.core.graph import Graph, loadGraph
from meshroom.core.node import CompatibilityNode
from meshroom.core.attribute import GroupAttribute

# 1 int, 1 exclusive choice param, 1 choice param, 1 bool, 1 group, 1 float nested in the group, 2 lists
GROUPATTRIBUTES_FIRSTGROUP_NB_CHILDREN = 8

GROUPATTRIBUTES_FIRSTGROUP_NESTED_NB_CHILDREN = 1  # 1 float
GROUPATTRIBUTES_OUTPUTGROUP_NB_CHILDREN = 1  # 1 bool
GROUPATTRIBUTES_FIRSTGROUP_DEPTHS = [1, 1, 1, 1, 1, 2, 1, 1]


class TestGroupAttributes:
    def test_saveLoadGroupDirectConnections(self):
        """
        Ensure that connecting GroupAttributes does not cause their nodes to have CompatibilityIssues
        when re-opening them.
        """
        graph = Graph("Connections between GroupAttributes")

        # Create two "GroupAttributes" nodes with their default parameters
        nodeA = graph.addNewNode("GroupAttributes")
        nodeB = graph.addNewNode("GroupAttributes")

        # Connect attributes within groups at different depth levels
        nodeA.firstGroup.connectTo(nodeB.firstGroup)

        # Save the graph in a file
        graphFile = os.path.join(tempfile.mkdtemp(), "test_io_group_connections.mg")
        graph.save(graphFile)

        # Reload the graph
        graph = loadGraph(graphFile)

        assert graph.node("GroupAttributes_1").firstGroup.inputLink == graph.node("GroupAttributes").firstGroup

    def test_saveLoadGroupConnections(self):
        """
        Ensure that connecting attributes that are part of GroupAttributes does not cause their nodes to have
        CompatibilityIssues when re-opening them.
        """
        graph = Graph("Connections between subattributes in GroupAttributes")

        # Create two "GroupAttributes" nodes with their default parameters
        nodeA = graph.addNewNode("GroupAttributes")
        nodeB = graph.addNewNode("GroupAttributes")

        # Connect attributes within groups at different depth levels
        nodeA.firstGroup.firstGroupIntA.connectTo(nodeB.firstGroup.firstGroupIntA)
        nodeA.firstGroup.nestedGroup.nestedGroupFloat.connectTo(
            nodeB.firstGroup.nestedGroup.nestedGroupFloat)

        # Save the graph in a file
        graphFile = os.path.join(tempfile.mkdtemp(), "test_io_group_connections.mg")
        graph.save(graphFile)

        # Reload the graph
        graph = loadGraph(graphFile)

        # Ensure the nodes are not CompatibilityNodes
        for node in graph.nodes:
            assert not isinstance(node, CompatibilityNode)

    def test_groupAttributesFlatChildren(self):
        """
        Check that the list of static flat children is correct, even with list elements.
        """
        graph = Graph("Children of GroupAttributes")

        # Create two "GroupAttributes" nodes with their default parameters
        node = graph.addNewNode("GroupAttributes")

        intAttr = node.attribute("exposedInt")
        assert not isinstance(intAttr, GroupAttribute)
        assert len(intAttr.flatStaticChildren) == 0  # Not a Group, cannot have any child

        inputGroup = node.attribute("firstGroup")
        assert isinstance(inputGroup, GroupAttribute)
        assert len(inputGroup.flatStaticChildren) == GROUPATTRIBUTES_FIRSTGROUP_NB_CHILDREN

        # Add an element to a list within the group and check the number of children has not changed
        groupedList = node.attribute("firstGroup.singleGroupedList")
        groupedList.insert(0, 30)
        assert len(groupedList.flatStaticChildren) == 0  # Not a Group, elements are not counted as children
        assert len(inputGroup.flatStaticChildren) == GROUPATTRIBUTES_FIRSTGROUP_NB_CHILDREN

        nestedGroup = node.attribute("firstGroup.nestedGroup")
        assert isinstance(nestedGroup, GroupAttribute)
        assert len(nestedGroup.flatStaticChildren) == GROUPATTRIBUTES_FIRSTGROUP_NESTED_NB_CHILDREN

        outputGroup = node.attribute("outputGroup")
        assert isinstance(outputGroup, GroupAttribute)
        assert len(outputGroup.flatStaticChildren) == GROUPATTRIBUTES_OUTPUTGROUP_NB_CHILDREN

    def test_groupAttributesDepthLevels(self):
        """
        Check that the depth level of children attributes is correctly set.
        """
        graph = Graph("Children of GroupAttributes")

        # Create two "GroupAttributes" nodes with their default parameters
        node = graph.addNewNode("GroupAttributes")
        inputGroup = node.attribute("firstGroup")
        assert isinstance(inputGroup, GroupAttribute)
        assert inputGroup.depth == 0  # Root level

        cnt = 0
        for child in inputGroup.flatStaticChildren:
            assert child.depth == GROUPATTRIBUTES_FIRSTGROUP_DEPTHS[cnt]
            cnt = cnt + 1

        outputGroup = node.attribute("outputGroup")
        assert isinstance(outputGroup, GroupAttribute)
        assert outputGroup.depth == 0
        for child in outputGroup.flatStaticChildren:  # Single element in the group
            assert child.depth == 1

        intAttr = node.attribute("exposedInt")
        assert not isinstance(intAttr, GroupAttribute)
        assert intAttr.depth == 0

    def test_groupAttributesWithMatchingStructure(self):
        """
        Check that two different GroupAttributes can be connected if they have a matching structure.
        """
        # Given
        graph = Graph()
        nestedPosition = graph.addNewNode("NestedPosition")
        nestedColor = graph.addNewNode("NestedColor")

        # When
        acceptedConnection = nestedPosition.xyz.validateIncomingConnection(nestedColor.rgb)

        # Then
        assert acceptedConnection

    def test_groupAttributesWithDifferentStructures(self):
        """
        Check that two different GroupAttributes cannot be connected if they have different structures.
        """
        # Given
        graph = Graph()
        nestedPosition = graph.addNewNode("NestedPosition")
        nestedTest = graph.addNewNode("NestedTest")

        # When
        acceptedConnection = nestedPosition.xyz.validateIncomingConnection(nestedTest.xyz)

        # Then
        assert not acceptedConnection

    def test_connectGroupsWithSubAttributes(self):
        """
        Check that when a group is connected to another group, all the sub-attributes are connected
        together automatically.
        """
        # Given
        graph = Graph()

        nestedColor = graph.addNewNode("NestedColor")
        nestedPosition = graph.addNewNode("NestedPosition")

        assert not nestedPosition.xyz.isLink
        assert not nestedPosition.xyz.x.isLink
        assert not nestedPosition.xyz.y.isLink
        assert not nestedPosition.xyz.z.isLink
        assert not nestedPosition.xyz.test.isLink
        assert not nestedPosition.xyz.test.x.isLink
        assert not nestedPosition.xyz.test.y.isLink
        assert not nestedPosition.xyz.test.z.isLink

        # When
        nestedColor.rgb.connectTo(nestedPosition.xyz)

        # Then
        assert nestedPosition.xyz.isLink and \
            nestedPosition.xyz.inputLink.asLinkExpr() == nestedColor.rgb.asLinkExpr()
        assert nestedPosition.xyz.x.isLink and \
            nestedPosition.xyz.x.inputLink.asLinkExpr() == nestedColor.rgb.r.asLinkExpr()
        assert nestedPosition.xyz.y.isLink and \
            nestedPosition.xyz.y.inputLink.asLinkExpr() == nestedColor.rgb.g.asLinkExpr()
        assert nestedPosition.xyz.z.isLink and \
            nestedPosition.xyz.z.inputLink.asLinkExpr() == nestedColor.rgb.b.asLinkExpr()
        assert nestedPosition.xyz.test.isLink and \
            nestedPosition.xyz.test.inputLink.asLinkExpr() == nestedColor.rgb.test.asLinkExpr()
        assert nestedPosition.xyz.test.x.isLink and \
            nestedPosition.xyz.test.x.inputLink.asLinkExpr() == nestedColor.rgb.test.r.asLinkExpr()
        assert nestedPosition.xyz.test.y.isLink and \
            nestedPosition.xyz.test.y.inputLink.asLinkExpr() == nestedColor.rgb.test.g.asLinkExpr()
        assert nestedPosition.xyz.test.z.isLink and \
            nestedPosition.xyz.test.z.inputLink.asLinkExpr() == nestedColor.rgb.test.b.asLinkExpr()

        # Save the graph in a file
        graphFile = os.path.join(tempfile.mkdtemp(), "test_io_group_connections.mg")
        graph.save(graphFile)

        # Reload the graph
        graph = loadGraph(graphFile)
        nestedPosition = graph.node("NestedPosition")
        nestedColor = graph.node("NestedColor")

        assert nestedPosition.xyz.isLink and \
            nestedPosition.xyz.inputLink.asLinkExpr() == nestedColor.rgb.asLinkExpr()
        assert nestedPosition.xyz.x.isLink and \
            nestedPosition.xyz.x.inputLink.asLinkExpr() == nestedColor.rgb.r.asLinkExpr()
        assert nestedPosition.xyz.y.isLink and \
            nestedPosition.xyz.y.inputLink.asLinkExpr() == nestedColor.rgb.g.asLinkExpr()
        assert nestedPosition.xyz.z.isLink and \
            nestedPosition.xyz.z.inputLink.asLinkExpr() == nestedColor.rgb.b.asLinkExpr()
        assert nestedPosition.xyz.test.isLink and \
            nestedPosition.xyz.test.inputLink.asLinkExpr() == nestedColor.rgb.test.asLinkExpr()
        assert nestedPosition.xyz.test.x.isLink and \
            nestedPosition.xyz.test.x.inputLink.asLinkExpr() == nestedColor.rgb.test.r.asLinkExpr()
        assert nestedPosition.xyz.test.y.isLink and \
            nestedPosition.xyz.test.y.inputLink.asLinkExpr() == nestedColor.rgb.test.g.asLinkExpr()
        assert nestedPosition.xyz.test.z.isLink and \
            nestedPosition.xyz.test.z.inputLink.asLinkExpr() == nestedColor.rgb.test.b.asLinkExpr()

    def test_connectSubAttributes(self):
        """
        After a group has been connected to another group, connecting individually a sub-attribute
        should disconnect the group itself.
        """
        # Given
        graph = Graph()

        nestedColor = graph.addNewNode("NestedColor")
        nestedPosition = graph.addNewNode("NestedPosition")

        nestedColor.rgb.connectTo(nestedPosition.xyz)

        assert nestedPosition.xyz.isLink and \
            nestedPosition.xyz.inputLink.asLinkExpr() == nestedColor.rgb.asLinkExpr()
        assert nestedPosition.xyz.x.isLink and \
            nestedPosition.xyz.x.inputLink.asLinkExpr() == nestedColor.rgb.r.asLinkExpr()
        assert nestedPosition.xyz.y.isLink and \
            nestedPosition.xyz.y.inputLink.asLinkExpr() == nestedColor.rgb.g.asLinkExpr()
        assert nestedPosition.xyz.z.isLink and \
            nestedPosition.xyz.z.inputLink.asLinkExpr() == nestedColor.rgb.b.asLinkExpr()
        assert nestedPosition.xyz.test.isLink and \
            nestedPosition.xyz.test.inputLink.asLinkExpr() == nestedColor.rgb.test.asLinkExpr()
        assert nestedPosition.xyz.test.x.isLink and \
            nestedPosition.xyz.test.x.inputLink.asLinkExpr() == nestedColor.rgb.test.r.asLinkExpr()
        assert nestedPosition.xyz.test.y.isLink and \
            nestedPosition.xyz.test.y.inputLink.asLinkExpr() == nestedColor.rgb.test.g.asLinkExpr()
        assert nestedPosition.xyz.test.z.isLink and \
            nestedPosition.xyz.test.z.inputLink.asLinkExpr() == nestedColor.rgb.test.b.asLinkExpr()

        # When
        r = nestedColor.rgb.r
        z = nestedPosition.xyz.test.z
        r.connectTo(z)

        # Then
        assert not nestedPosition.xyz.isLink  # Disconnected because sub GroupAttribute has been disconnected
        assert nestedPosition.xyz.x.isLink and \
            nestedPosition.xyz.x.inputLink.asLinkExpr() == nestedColor.rgb.r.asLinkExpr()
        assert nestedPosition.xyz.y.isLink and \
            nestedPosition.xyz.y.inputLink.asLinkExpr() == nestedColor.rgb.g.asLinkExpr()
        assert nestedPosition.xyz.z.isLink and \
            nestedPosition.xyz.z.inputLink.asLinkExpr() == nestedColor.rgb.b.asLinkExpr()
        assert not nestedPosition.xyz.test.isLink  # Disconnected because nestedPosition.xyz.test.z has been reconnected
        assert nestedPosition.xyz.test.x.isLink and \
            nestedPosition.xyz.test.x.inputLink.asLinkExpr() == nestedColor.rgb.test.r.asLinkExpr()
        assert nestedPosition.xyz.test.y.isLink and \
            nestedPosition.xyz.test.y.inputLink.asLinkExpr() == nestedColor.rgb.test.g.asLinkExpr()
        assert nestedPosition.xyz.test.z.isLink and \
            nestedPosition.xyz.test.z.inputLink.asLinkExpr() == r.asLinkExpr() == nestedColor.rgb.r.asLinkExpr()

    def test_connectGroupSubAttributesByValue(self):
        """
        Check that sub-attributes are connected by value and not by reference. When connected to another sub-attribute
        through a group connection, a given sub-attribute should have an address that differs from the incoming sub-attribute.
        """
        graph = Graph()
        groupA = graph.addNewNode("GroupAttributes")
        groupB = graph.addNewNode("GroupAttributes")

        groupA.firstGroup.firstGroupIntA.value = 1234
        assert groupA.firstGroup.firstGroupIntA.value != groupB.firstGroup.firstGroupIntA.value

        # Connect the groups
        groupA.firstGroup.connectTo(groupB.firstGroup)

        subAttributeA = groupA.firstGroup.firstGroupIntA
        subAttributeB = groupB.firstGroup.firstGroupIntA
        assert subAttributeA != subAttributeB
        assert subAttributeB.isLink
        assert subAttributeA.fullName != subAttributeB.fullName
        assert groupA.firstGroup.firstGroupIntA.value == groupB.firstGroup.firstGroupIntA.value == 1234

    def test_listOfGroupsInsideGroupAttributeAccess(self):
        """
        Check that elements of a list-of-groups nested inside a GroupAttribute are accessible
        via the 'group.list[idx].field' path notation.
        """
        graph = Graph("List of groups inside group")
        node = graph.addNewNode("GroupAttributes")

        # groupedList is initially empty; append two group elements
        node.firstGroup.groupedList.append({"listedGroupInt": 7})
        node.firstGroup.groupedList.append({"listedGroupInt": 42})

        # Access via direct attribute traversal
        assert node.firstGroup.groupedList.at(0).listedGroupInt.value == 7
        assert node.firstGroup.groupedList.at(1).listedGroupInt.value == 42

        # Access via node.attribute() path notation: group . list[idx] . group_field
        assert node.attribute("firstGroup.groupedList[0].listedGroupInt").value == 7
        assert node.attribute("firstGroup.groupedList[1].listedGroupInt").value == 42

    def test_listOfGroupsInsideGroupAttributeModify(self):
        """
        Check that fields of group elements in a list-of-groups nested inside a GroupAttribute
        can be mutated via the path notation.
        """
        graph = Graph("Modify list of groups inside group")
        node = graph.addNewNode("GroupAttributes")

        node.firstGroup.groupedList.append({"listedGroupInt": 0})

        node.attribute("firstGroup.groupedList[0].listedGroupInt").value = 99

        assert node.firstGroup.groupedList.at(0).listedGroupInt.value == 99

    def test_listInsideGroupAttributeAccess(self):
        """
        Check that elements of a simple list nested inside a GroupAttribute are accessible
        via the 'group.list[idx]' path notation.
        The 'GroupAttributes' node has firstGroup.singleGroupedList, a ListAttribute of IntParam.
        """
        graph = Graph("List inside group")
        node = graph.addNewNode("GroupAttributes")

        node.firstGroup.singleGroupedList.extend([10, 20, 30])

        # Access via direct attribute traversal
        assert node.firstGroup.singleGroupedList.at(0).value == 10
        assert node.firstGroup.singleGroupedList.at(2).value == 30

        # Access via node.attribute() path notation: group . list[idx]
        assert node.attribute("firstGroup.singleGroupedList[0]").value == 10
        assert node.attribute("firstGroup.singleGroupedList[1]").value == 20
        assert node.attribute("firstGroup.singleGroupedList[2]").value == 30

    def test_listInsideGroupAttributeModify(self):
        """
        Check that elements of a list nested inside a GroupAttribute can be mutated
        via the 'group.list[idx]' path notation.
        """
        graph = Graph("Modify list inside group")
        node = graph.addNewNode("GroupAttributes")

        node.firstGroup.singleGroupedList.extend([1, 2, 3])
        node.attribute("firstGroup.singleGroupedList[1]").value = 999

        assert node.firstGroup.singleGroupedList.at(1).value == 999
        # Neighbours should be unaffected
        assert node.firstGroup.singleGroupedList.at(0).value == 1
        assert node.firstGroup.singleGroupedList.at(2).value == 3

    def test_listInsideGroupRemove(self):
        """
        Check that removing an element from a list nested inside a GroupAttribute
        shifts subsequent elements correctly.
        """
        graph = Graph("Remove from list inside group")
        node = graph.addNewNode("GroupAttributes")

        node.firstGroup.singleGroupedList.extend([100, 200, 300])
        node.firstGroup.singleGroupedList.remove(0)

        assert len(node.firstGroup.singleGroupedList) == 2
        assert node.attribute("firstGroup.singleGroupedList[0]").value == 200
        assert node.attribute("firstGroup.singleGroupedList[1]").value == 300

    def test_nestedGroupAttributePathAccess(self):
        """
        Check that a field inside a GroupAttribute nested within another GroupAttribute is
        accessible via the 'outerGroup.innerGroup.field' path notation.
        The 'GroupAttributes' node has firstGroup.nestedGroup.nestedGroupFloat.
        """
        graph = Graph("Nested group path access")
        node = graph.addNewNode("GroupAttributes")

        # Default value check via path string
        assert node.attribute("firstGroup.nestedGroup.nestedGroupFloat").value == 1.0

        # Mutation via path string
        node.attribute("firstGroup.nestedGroup.nestedGroupFloat").value = 3.14

        assert node.firstGroup.nestedGroup.nestedGroupFloat.value == 3.14
        assert node.attribute("firstGroup.nestedGroup.nestedGroupFloat").value == 3.14

    def test_listOfGroupsInsideNestedGroupPathAccess(self):
        """
        Check that elements of a list-of-groups that is itself inside a nested GroupAttribute
        are reachable via the full 'outerGroup.list[idx].field' path.
        """
        graph = Graph("List of groups inside nested group path access")
        node = graph.addNewNode("GroupAttributes")

        node.firstGroup.groupedList.extend([
            {"listedGroupInt": 5},
            {"listedGroupInt": 15},
            {"listedGroupInt": 25},
        ])

        # Full path: outerGroup . list[idx] . innerGroup_field
        assert node.attribute("firstGroup.groupedList[0].listedGroupInt").value == 5
        assert node.attribute("firstGroup.groupedList[1].listedGroupInt").value == 15
        assert node.attribute("firstGroup.groupedList[2].listedGroupInt").value == 25

        # Mutate via full path and verify via direct traversal
        node.attribute("firstGroup.groupedList[1].listedGroupInt").value = 99
        assert node.firstGroup.groupedList.at(1).listedGroupInt.value == 99
