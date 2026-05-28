# coding:utf-8

from meshroom.core.graph import Graph, loadGraph, executeGraph
from meshroom.core import desc
from meshroom.core.node import Node

from .utils import registerNodeDesc, unregisterNodeDesc


class NodeWithAttributeChangedCallback(desc.BaseNode):
    """
    A Node containing an input Attribute with an 'on{Attribute}Changed' method,
    called whenever the value of this attribute is changed explicitly.
    """

    inputs = [
        desc.IntParam(
            name="input",
            label="Input",
            description="Attribute with a value changed callback (onInputChanged)",
            value=0,
            range=None,
        ),
        desc.IntParam(
            name="affectedInput",
            label="Affected Input",
            description="Updated to input.value * 2 whenever 'input' is explicitly modified",
            value=0,
            range=None,
        ),
    ]

    def onInputChanged(self, instance: Node):
        instance.affectedInput.value = instance.input.value * 2

    def processChunk(self, chunk):
        pass  # No-op.


class TestNodeWithAttributeChangedCallback:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithAttributeChangedCallback)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithAttributeChangedCallback)

    def test_assignValueTriggersCallback(self):
        node = Node(NodeWithAttributeChangedCallback.__name__)
        assert node.affectedInput.value == 0

        node.input.value = 10
        assert node.affectedInput.value == 20

    def test_specifyDefaultValueDoesNotTriggerCallback(self):
        node = Node(NodeWithAttributeChangedCallback.__name__, input=10)
        assert node.affectedInput.value == 0

    def test_assignDefaultValueDoesNotTriggerCallback(self):
        node = Node(NodeWithAttributeChangedCallback.__name__, input=10)
        node.input.value = 10
        assert node.affectedInput.value == 0

    def test_assignNonDefaultValueTriggersCallback(self):
        node = Node(NodeWithAttributeChangedCallback.__name__, input=10)
        node.input.value = 2
        assert node.affectedInput.value == 4


class TestAttributeCallbackTriggerInGraph:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithAttributeChangedCallback)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithAttributeChangedCallback)

    def test_connectionTriggersCallback(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        assert nodeA.affectedInput.value == nodeB.affectedInput.value == 0

        nodeA.input.value = 1
        nodeA.input.connectTo(nodeB.input)

        assert nodeA.affectedInput.value == nodeB.affectedInput.value == 2

    def test_connectedValueChangeTriggersCallback(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        assert nodeA.affectedInput.value == nodeB.affectedInput.value == 0

        nodeA.input.connectTo(nodeB.input)
        nodeA.input.value = 1

        assert nodeA.affectedInput.value == 2
        assert nodeB.affectedInput.value == 2

    def test_defaultValueOnlyTriggersCallbackDownstream(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__, input=1)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        assert nodeA.affectedInput.value == 0
        assert nodeB.affectedInput.value == 0

        nodeA.input.connectTo(nodeB.input)

        assert nodeA.affectedInput.value == 0
        assert nodeB.affectedInput.value == 2

    def test_valueChangeIsPropagatedAlongNodeChain(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeC = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeD = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.affectedInput.connectTo(nodeB.input)
        nodeB.affectedInput.connectTo(nodeC.input)
        nodeC.affectedInput.connectTo(nodeD.input)

        nodeA.input.value = 5

        assert nodeA.affectedInput.value == nodeB.input.value == 10
        assert nodeB.affectedInput.value == nodeC.input.value == 20
        assert nodeC.affectedInput.value == nodeD.input.value == 40
        assert nodeD.affectedInput.value == 80

    def test_disconnectionTriggersCallback(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.input.connectTo(nodeB.input)
        nodeA.input.value = 5
        assert nodeB.affectedInput.value == 10

        graph.removeEdge(nodeB.input)

        assert nodeB.input.value == 0
        assert nodeB.affectedInput.value == 0

    def test_loadingGraphDoesNotTriggerCallback(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        node = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        node.input.value = 5
        node.affectedInput.value = 2
        graph.save()

        loadedGraph = loadGraph(graph.filepath, strictCompatibility=True)
        loadedNode = loadedGraph.node(node.name)
        assert loadedNode
        assert loadedNode.affectedInput.value == 2

    def test_loadingGraphDoesNotTriggerCallbackForConnectedAttributes(
        self, graphSavedOnDisk
    ):
        graph: Graph = graphSavedOnDisk
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.input.connectTo(nodeB.input)
        nodeA.input.value = 5
        assert nodeB.affectedInput.value == nodeB.input.value * 2

        nodeB.affectedInput.value = 2

        graph.save()

        loadedGraph = loadGraph(graph.filepath, strictCompatibility=True)
        loadedNodeB = loadedGraph.node(nodeB.name)
        assert loadedNodeB
        assert loadedNodeB.affectedInput.value == 2


class NodeWithGroupListAttributeChangedCallback(desc.BaseNode):
    """
    A Node containing a GroupAttribute with a nested IntParam that has an 'on{GroupName}{ChildName}Changed' callback,
    called whenever the nested attribute value is changed explicitly.
    It also contains a ListAttribute with an 'on{ListName}Changed' callback to verify that callbacks are not triggered
    for attributes nested inside a list (i.e. when ``isInsideList`` is True).
    """

    inputs = [
        desc.GroupAttribute(
            name="groupInput",
            label="Group Input",
            description="GroupAttribute with a nested IntParam that has a value changed callback.",
            items=[
                desc.IntParam(
                    name="int",
                    label="Int",
                    description="Attribute with a value changed callback (onGroupInputIntChanged).",
                    value=0,
                    range=None,
                )
            ],
        ),
        desc.ListAttribute(
            name="listInput",
            label="List Input",
            description="ListAttribute of FloatParams whose elements have isInsideList=True.",
            elementDesc=desc.FloatParam(
                name="float",
                label="Float",
                description="",
                value=0,
                range=None,
            ),
        ),
        desc.IntParam(
            name="affectedInt",
            label="Affected Int Input",
            description="Updated to groupInput.int * 2 whenever 'groupInput.int' is explicitly modified.",
            value=0,
            range=None,
        ),
        desc.FloatParam(
            name="affectedFloat",
            label="Affected Float Input",
            description="Updated to listInput.float * 2 whenever 'listInput.float' is explicitly modified",
            value=0.0,
            range=None,
        )
    ]

    def onGroupInputIntChanged(self, node: Node):
        node.affectedInt.value = node.groupInput.int.value * 2

    def onListInputChanged(self, node: Node):
        """
        This callback's name matches 'listInput' but not any indexed element.
        It can be triggered when the list content changes (e.g. append, remove).
        """
        node.affectedFloat.value = 999.0

    def onListInputFloatChanged(self, node: Node):
        """
        This callback's name matches the list elements' name, but since the elements have isInsideList=True,
        this callback should NOT be triggered when an element's value changes.
        """
        node.affectedFloat.value = 400.0


class TestAttributeCallbackForGroupListAttribute:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithGroupListAttributeChangedCallback)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithGroupListAttributeChangedCallback)

    def test_assignValueToNestedGroupAttributeTriggersCallback(self):
        node = Node(NodeWithGroupListAttributeChangedCallback.__name__)
        assert node.affectedInt.value == 0

        node.groupInput.int.value = 5
        assert node.affectedInt.value == 10

    def test_assignDefaultValueDoesNotTriggerCallback(self):
        node = Node(NodeWithGroupListAttributeChangedCallback.__name__)
        # Callback fires on the first assignment (3 → 6)
        node.groupInput.int.value = 3
        assert node.affectedInt.value == 6

        # Manually move affectedInt to a sentinel value so we can detect
        # whether the callback fires again when the same value is re-assigned.
        node.affectedInt.value = 100
        node.groupInput.int.value = 3  # Same value — same-value guard skips the callback
        assert node.affectedInt.value == 100

        node.groupInput.int.value = 4  # Different value — callback should fire
        assert node.affectedInt.value == 8

    def test_listElementIsInsideList(self):
        """ Elements appended to a ListAttribute must have isInsideList evaluate to True. """
        node = Node(NodeWithGroupListAttributeChangedCallback.__name__)
        assert node.affectedFloat.value == 0.0
        node.listInput.append(0.0)
        element = node.listInput.at(0)
        assert element.isInsideList
        assert not node.listInput.isInsideList

    def test_listStructureChangeTriggersListLevelCallback(self):
        """
        `onListInputChanged` should fire when the list structure itself changes (append/remove).
        """
        node = Node(NodeWithGroupListAttributeChangedCallback.__name__)
        assert node.affectedFloat.value == 0.0

        node.listInput.append(0.0)
        assert node.affectedFloat.value == 999.0

    def test_changingListElementValueDoesNotTriggerCallback(self):
        """
        Changing an element's value does NOT trigger ``onListInputChanged`` because
        the element has ``isInsideList=True``, which causes
        ``_getAttributeChangedCallback`` to return ``None`` and skip the dispatch.
        """
        node = Node(NodeWithGroupListAttributeChangedCallback.__name__)
        node.listInput.append(0.0)

        element = node.listInput.at(0)
        assert element.isInsideList
        assert node.affectedFloat.value == 999.0

        # Reset affectedFloat to isolate from the list-structure change above.
        node.affectedFloat.value = 0.0

        # Change the list element's value and verify that the list-level callback is NOT triggered.
        element.value = 42.0
        assert node.affectedFloat.value == 0.0

    def test_changingMultipleListElementValuesDoesNotTriggerCallback(self):
        """ Changing many elements' values never triggers the callback. """
        node = Node(NodeWithGroupListAttributeChangedCallback.__name__)
        node.listInput.extend([1.0, 2.0, 3.0])

        # Reset affectedFloat after the list-structure changes from extend.
        node.affectedFloat.value = 0.0

        for i in range(len(node.listInput)):
            node.listInput.at(i).value = i * 10.0

        assert node.affectedFloat.value == 0.0


class NodeWithCompoundAttributes(desc.BaseNode):
    """
    A Node containing a variation of compound attributes (List/Groups),
    called whenever the value of this attribute is changed explicitly.
    """

    inputs = [
        desc.ListAttribute(
            name="listInput",
            label="List Input",
            description="ListAttribute of IntParams.",
            elementDesc=desc.IntParam(
                name="int", label="Int", description="", value=0, range=None
            ),
        ),
        desc.GroupAttribute(
            name="groupInput",
            label="Group Input",
            description="GroupAttribute with a single 'IntParam' element.",
            items=[
                desc.IntParam(
                    name="int", label="Int", description="", value=0, range=None
                )
            ],
        ),
        desc.ListAttribute(
            name="listOfGroupsInput",
            label="List of Groups input",
            description="ListAttribute of GroupAttribute with a single 'IntParam' element.",
            elementDesc=desc.GroupAttribute(
                name="subGroup",
                label="SubGroup",
                description="",
                items=[
                    desc.IntParam(
                        name="int", label="Int", description="", value=0, range=None
                    )
                ],
            )
        ),
        desc.GroupAttribute(
            name="groupWithListInput",
            label="Group with List",
            description="GroupAttribute with a single 'ListAttribute of IntParam' element.",
            items=[
                desc.ListAttribute(
                    name="subList",
                    label="SubList",
                    description="",
                    elementDesc=desc.IntParam(
                        name="int", label="Int", description="", value=0, range=None
                    )
                )
            ]
        )
    ]


class TestAttributeCallbackBehaviorWithUpstreamCompoundAttributes:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithAttributeChangedCallback)
        registerNodeDesc(NodeWithCompoundAttributes)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithAttributeChangedCallback)
        unregisterNodeDesc(NodeWithCompoundAttributes)

    def test_connectionToListElement(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithCompoundAttributes.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.listInput.append(0)
        attr = nodeA.listInput.at(0)

        attr.connectTo(nodeB.input)

        attr.value = 10

        assert nodeB.input.value == 10
        assert nodeB.affectedInput.value == 20

    def test_connectionToGroupElement(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithCompoundAttributes.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.groupInput.int.connectTo(nodeB.input)

        nodeA.groupInput.int.value = 10

        assert nodeB.input.value == 10
        assert nodeB.affectedInput.value == 20

    def test_connectionToGroupElementInList(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithCompoundAttributes.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.listOfGroupsInput.append({})

        attr = nodeA.listOfGroupsInput.at(0)

        attr.int.connectTo(nodeB.input)

        attr.int.value = 10

        assert nodeB.input.value == 10
        assert nodeB.affectedInput.value == 20

    def test_connectionToListElementInGroup(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithCompoundAttributes.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.groupWithListInput.subList.append(0)

        attr = nodeA.groupWithListInput.subList.at(0)

        attr.connectTo(nodeB.input)

        attr.value = 10

        assert nodeB.input.value == 10
        assert nodeB.affectedInput.value == 20


class NodeWithDynamicOutputValue(desc.BaseNode):
    """
    A Node containing an output attribute which value is computed dynamically
    during graph execution.
    """

    inputs = [
        desc.IntParam(
            name="input",
            label="Input",
            description="Input used in the computation of 'output'",
            value=0,
        ),
    ]

    outputs = [
        desc.IntParam(
            name="output",
            label="Output",
            description="Dynamically computed output (input * 2)",
            # Setting value to None makes the attribute dynamic.
            value=None,
        ),
    ]

    def processChunk(self, chunk):
        chunk.node.output.value = chunk.node.input.value * 2


class TestAttributeCallbackBehaviorWithUpstreamDynamicOutputs:

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithAttributeChangedCallback)
        registerNodeDesc(NodeWithDynamicOutputValue)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithAttributeChangedCallback)
        unregisterNodeDesc(NodeWithDynamicOutputValue)

    def test_connectingUncomputedDynamicOutputDoesNotTriggerDownstreamAttributeChangedCallback(
        self,
    ):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithDynamicOutputValue.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.input.value = 10
        nodeA.output.connectTo(nodeB.input)

        assert nodeB.affectedInput.value == 0

    def test_connectingComputedDynamicOutputTriggersDownstreamAttributeChangedCallback(
        self, graphSavedOnDisk
    ):
        graph: Graph = graphSavedOnDisk
        nodeA = graph.addNewNode(NodeWithDynamicOutputValue.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.input.value = 10
        executeGraph(graph)

        nodeA.output.connectTo(nodeB.input)
        assert nodeA.output.value == nodeB.input.value == 20
        assert nodeB.affectedInput.value == 40

    def test_dynamicOutputValueComputeDoesNotTriggerDownstreamAttributeChangedCallback(
        self, graphSavedOnDisk
    ):
        graph: Graph = graphSavedOnDisk
        nodeA = graph.addNewNode(NodeWithDynamicOutputValue.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.output.connectTo(nodeB.input)
        nodeA.input.value = 10
        executeGraph(graph)

        assert nodeB.input.value == 20
        assert nodeB.affectedInput.value == 0

    def test_clearingDynamicOutputValueDoesNotTriggerDownstreamAttributeChangedCallback(
        self, graphSavedOnDisk
    ):
        graph: Graph = graphSavedOnDisk
        nodeA = graph.addNewNode(NodeWithDynamicOutputValue.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.input.value = 10
        executeGraph(graph)

        nodeA.output.connectTo(nodeB.input)

        expectedPreClearValue = nodeA.input.value * 2 * 2
        assert nodeB.affectedInput.value == expectedPreClearValue

        nodeA.clearData()
        assert nodeA.output.value == nodeB.input.value is None
        assert nodeB.affectedInput.value == expectedPreClearValue

    def test_loadingGraphWithComputedDynamicOutputValueDoesNotTriggerDownstreamAttributeChangedCallback(
        self, graphSavedOnDisk
    ):
        graph: Graph = graphSavedOnDisk
        nodeA = graph.addNewNode(NodeWithDynamicOutputValue.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.input.value = 10
        nodeA.output.connectTo(nodeB.input)
        executeGraph(graph)

        assert nodeA.output.value == nodeB.input.value == 20
        assert nodeB.affectedInput.value == 0

        graph.save()

        loadGraph(graph.filepath, strictCompatibility=True)

        assert nodeB.affectedInput.value == 0


class TestAttributeCallbackBehaviorOnGraphImport:
    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithAttributeChangedCallback)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithAttributeChangedCallback)

    def test_importingGraphDoesNotTriggerAttributeChangedCallbacks(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.affectedInput.connectTo(nodeB.input)

        nodeA.input.value = 5
        nodeB.affectedInput.value = 2

        otherGraph = Graph("")
        otherGraph.importGraphContent(graph)

        assert otherGraph.node(nodeB.name).affectedInput.value == 2
