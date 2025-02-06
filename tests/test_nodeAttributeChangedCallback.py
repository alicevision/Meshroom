# coding:utf-8

from meshroom.core.graph import Graph, loadGraph, executeGraph
from meshroom.core import desc, registerNodeType, unregisterNodeType
from meshroom.core.node import Node


class NodeWithAttributeChangedCallback(desc.Node):
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
        registerNodeType(NodeWithAttributeChangedCallback)

    @classmethod
    def teardown_class(cls):
        unregisterNodeType(NodeWithAttributeChangedCallback)

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
        registerNodeType(NodeWithAttributeChangedCallback)

    @classmethod
    def teardown_class(cls):
        unregisterNodeType(NodeWithAttributeChangedCallback)

    def test_connectionTriggersCallback(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        assert nodeA.affectedInput.value == nodeB.affectedInput.value == 0

        nodeA.input.value = 1
        graph.addEdge(nodeA.input, nodeB.input)

        assert nodeA.affectedInput.value == nodeB.affectedInput.value == 2

    def test_connectedValueChangeTriggersCallback(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        assert nodeA.affectedInput.value == nodeB.affectedInput.value == 0

        graph.addEdge(nodeA.input, nodeB.input)
        nodeA.input.value = 1

        assert nodeA.affectedInput.value == 2
        assert nodeB.affectedInput.value == 2

    def test_defaultValueOnlyTriggersCallbackDownstream(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__, input=1)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        assert nodeA.affectedInput.value == 0
        assert nodeB.affectedInput.value == 0

        graph.addEdge(nodeA.input, nodeB.input)

        assert nodeA.affectedInput.value == 0
        assert nodeB.affectedInput.value == 2

    def test_valueChangeIsPropagatedAlongNodeChain(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeC = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeD = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        graph.addEdges(
            (nodeA.affectedInput, nodeB.input),
            (nodeB.affectedInput, nodeC.input),
            (nodeC.affectedInput, nodeD.input),
        )

        nodeA.input.value = 5

        assert nodeA.affectedInput.value == nodeB.input.value == 10
        assert nodeB.affectedInput.value == nodeC.input.value == 20
        assert nodeC.affectedInput.value == nodeD.input.value == 40
        assert nodeD.affectedInput.value == 80

    def test_disconnectionTriggersCallback(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        graph.addEdge(nodeA.input, nodeB.input)
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

        graph.addEdge(nodeA.input, nodeB.input)
        nodeA.input.value = 5
        assert nodeB.affectedInput.value == nodeB.input.value * 2

        nodeB.affectedInput.value = 2

        graph.save()

        loadedGraph = loadGraph(graph.filepath, strictCompatibility=True)
        loadedNodeB = loadedGraph.node(nodeB.name)
        assert loadedNodeB
        assert loadedNodeB.affectedInput.value == 2


class NodeWithCompoundAttributes(desc.Node):
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
            groupDesc=[
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
                groupDesc=[
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
            groupDesc=[
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
        registerNodeType(NodeWithAttributeChangedCallback)
        registerNodeType(NodeWithCompoundAttributes)

    @classmethod
    def teardown_class(cls):
        unregisterNodeType(NodeWithAttributeChangedCallback)
        unregisterNodeType(NodeWithCompoundAttributes)

    def test_connectionToListElement(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithCompoundAttributes.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.listInput.append(0)
        attr = nodeA.listInput.at(0)

        graph.addEdge(attr, nodeB.input)

        attr.value = 10

        assert nodeB.input.value == 10
        assert nodeB.affectedInput.value == 20

    def test_connectionToGroupElement(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithCompoundAttributes.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        graph.addEdge(nodeA.groupInput.int, nodeB.input)

        nodeA.groupInput.int.value = 10

        assert nodeB.input.value == 10
        assert nodeB.affectedInput.value == 20

    def test_connectionToGroupElementInList(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithCompoundAttributes.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.listOfGroupsInput.append({})

        attr = nodeA.listOfGroupsInput.at(0)

        graph.addEdge(attr.int, nodeB.input)

        attr.int.value = 10

        assert nodeB.input.value == 10
        assert nodeB.affectedInput.value == 20

    def test_connectionToListElementInGroup(self):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithCompoundAttributes.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.groupWithListInput.subList.append(0)

        attr = nodeA.groupWithListInput.subList.at(0)

        graph.addEdge(attr, nodeB.input)

        attr.value = 10

        assert nodeB.input.value == 10
        assert nodeB.affectedInput.value == 20


class NodeWithDynamicOutputValue(desc.Node):
    """
    A Node containing an output attribute which value is computed dynamically during graph execution.
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
        registerNodeType(NodeWithAttributeChangedCallback)
        registerNodeType(NodeWithDynamicOutputValue)

    @classmethod
    def teardown_class(cls):
        unregisterNodeType(NodeWithAttributeChangedCallback)
        unregisterNodeType(NodeWithDynamicOutputValue)

    def test_connectingUncomputedDynamicOutputDoesNotTriggerDownstreamAttributeChangedCallback(
        self,
    ):
        graph = Graph("")
        nodeA = graph.addNewNode(NodeWithDynamicOutputValue.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.input.value = 10
        graph.addEdge(nodeA.output, nodeB.input)

        assert nodeB.affectedInput.value == 0

    def test_connectingComputedDynamicOutputTriggersDownstreamAttributeChangedCallback(
        self, graphWithIsolatedCache
    ):
        graph: Graph = graphWithIsolatedCache
        nodeA = graph.addNewNode(NodeWithDynamicOutputValue.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.input.value = 10
        executeGraph(graph)

        graph.addEdge(nodeA.output, nodeB.input)
        assert nodeA.output.value == nodeB.input.value == 20
        assert nodeB.affectedInput.value == 40

    def test_dynamicOutputValueComputeDoesNotTriggerDownstreamAttributeChangedCallback(
        self, graphWithIsolatedCache
    ):
        graph: Graph = graphWithIsolatedCache
        nodeA = graph.addNewNode(NodeWithDynamicOutputValue.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        graph.addEdge(nodeA.output, nodeB.input)
        nodeA.input.value = 10
        executeGraph(graph)

        assert nodeB.input.value == 20
        assert nodeB.affectedInput.value == 0

        
    def test_clearingDynamicOutputValueDoesNotTriggerDownstreamAttributeChangedCallback(
        self, graphWithIsolatedCache
    ):
        graph: Graph = graphWithIsolatedCache
        nodeA = graph.addNewNode(NodeWithDynamicOutputValue.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        nodeA.input.value = 10
        executeGraph(graph)

        graph.addEdge(nodeA.output, nodeB.input)

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
        graph.addEdge(nodeA.output, nodeB.input)
        executeGraph(graph)

        assert nodeA.output.value == nodeB.input.value == 20
        assert nodeB.affectedInput.value == 0

        graph.save()

        loadGraph(graph.filepath, strictCompatibility=True)

        assert nodeB.affectedInput.value == 0


class TestAttributeCallbackBehaviorOnGraphImport:
    @classmethod
    def setup_class(cls):
        registerNodeType(NodeWithAttributeChangedCallback)

    @classmethod
    def teardown_class(cls):
        unregisterNodeType(NodeWithAttributeChangedCallback)

    def test_importingGraphDoesNotTriggerAttributeChangedCallbacks(self):
        graph = Graph("")

        nodeA = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)
        nodeB = graph.addNewNode(NodeWithAttributeChangedCallback.__name__)

        graph.addEdge(nodeA.affectedInput, nodeB.input)

        nodeA.input.value = 5
        nodeB.affectedInput.value = 2
        
        otherGraph = Graph("")
        otherGraph.importGraphContent(graph)

        assert otherGraph.node(nodeB.name).affectedInput.value == 2

