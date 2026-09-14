import pytest

from meshroom.core import desc
from meshroom.core.exception import InvalidEdgeError
from meshroom.core.graph import Graph, loadGraph

from .utils import registeredNodeTypes, registerNodeDesc, unregisterNodeDesc

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


class NodeWithScalarOutputs(desc.Node):
    outputs = [
        desc.IntParam(name="intOut", value=0, range=None),
        desc.FloatParam(name="floatOut", value=0.0, range=None),
        desc.StringParam(name="stringOut", value=""),
        desc.BoolParam(name="boolOut", value=False),
    ]


class NodeWithTypedChoices(desc.Node):
    inputs = [
        desc.ChoiceParam(name="intChoice", value=1, values=[1, 2, 3], exclusive=True),
        desc.ChoiceParam(name="floatChoice", value=1.0, values=[1.0, 2.0], exclusive=True),
        desc.ChoiceParam(name="stringChoice", value="a", values=["a", "b"], exclusive=True),
        desc.ChoiceParam(name="intChoiceMulti", value=["1"], values=["1", "2", "3"], exclusive=False),
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
        nodeA.choice.connectTo(nodeB.choice)

        assert nodeB.choice.values == ["D", "E", "F"]

    def test_connectionsAreSerialized(self, graphSavedOnDisk):
        graph: Graph = graphSavedOnDisk
        nodeA = graph.addNewNode(NodeWithChoiceParams.__name__)
        nodeB = graph.addNewNode(NodeWithChoiceParams.__name__)
        nodeA.choice.connectTo(nodeB.choice)
        nodeA.choiceMulti.connectTo(nodeB.choiceMulti)

        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        loadedNodeA = loadedGraph.node(nodeA.name)
        loadedNodeB = loadedGraph.node(nodeB.name)
        assert loadedNodeB.choice.inputLink == loadedNodeA.choice
        assert loadedNodeB.choiceMulti.inputLink == loadedNodeA.choiceMulti


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
        nodeA.choice.connectTo(nodeB.choice)
        nodeA.choiceMulti.connectTo(nodeB.choiceMulti)

        graph.save()

        loadedGraph = loadGraph(graph.filepath)
        loadedNodeA = loadedGraph.node(nodeA.name)
        loadedNodeB = loadedGraph.node(nodeB.name)
        assert loadedNodeB.choice.inputLink == loadedNodeA.choice
        assert loadedNodeB.choiceMulti.inputLink == loadedNodeA.choiceMulti


class TestChoiceParamScalarLinks:
    """
    Tests for connecting scalar Param types (IntParam/FloatParam/StringParam) to a matching ChoiceParam.
    """

    def test_intParamConnectsToIntChoice(self):
        with registeredNodeTypes([NodeWithScalarOutputs, NodeWithTypedChoices]):
            graph = Graph("")
            nodeA = graph.addNewNode(NodeWithScalarOutputs.__name__)
            nodeB = graph.addNewNode(NodeWithTypedChoices.__name__)

            nodeA.intOut.connectTo(nodeB.intChoice)

            assert nodeB.intChoice.isLink
            assert nodeB.intChoice.value == 0
            assert type(nodeB.intChoice.value) is int

    def test_floatParamConnectsToFloatChoice(self):
        with registeredNodeTypes([NodeWithScalarOutputs, NodeWithTypedChoices]):
            graph = Graph("")
            nodeA = graph.addNewNode(NodeWithScalarOutputs.__name__)
            nodeB = graph.addNewNode(NodeWithTypedChoices.__name__)

            nodeA.floatOut.connectTo(nodeB.floatChoice)

            assert nodeB.floatChoice.isLink
            assert nodeB.floatChoice.value == 0.0
            assert type(nodeB.floatChoice.value) is float

    def test_stringParamConnectsToStringChoice(self):
        with registeredNodeTypes([NodeWithScalarOutputs, NodeWithTypedChoices]):
            graph = Graph("")
            nodeA = graph.addNewNode(NodeWithScalarOutputs.__name__)
            nodeB = graph.addNewNode(NodeWithTypedChoices.__name__)

            nodeA.stringOut.connectTo(nodeB.stringChoice)

            assert nodeB.stringChoice.isLink
            assert nodeB.stringChoice.value == ""
            assert type(nodeB.stringChoice.value) is str

    def test_linkedValueUpdatesLive(self):
        with registeredNodeTypes([NodeWithScalarOutputs, NodeWithTypedChoices]):
            graph = Graph("")
            nodeA = graph.addNewNode(NodeWithScalarOutputs.__name__)
            nodeB = graph.addNewNode(NodeWithTypedChoices.__name__)

            nodeA.intOut.connectTo(nodeB.intChoice)
            nodeA.intOut.value = 2

            assert nodeB.intChoice.value == 2

    @pytest.mark.parametrize(
        "srcAttrName,dstAttrName",
        [
            ("stringOut", "intChoice"),
            ("floatOut", "intChoice"),
            ("intOut", "stringChoice"),
            ("boolOut", "intChoice"),
            ("intOut", "floatChoice"),
        ],
    )
    def test_mismatchedTypesRaiseInvalidEdgeError(self, srcAttrName, dstAttrName):
        with registeredNodeTypes([NodeWithScalarOutputs, NodeWithTypedChoices]):
            graph = Graph("")
            nodeA = graph.addNewNode(NodeWithScalarOutputs.__name__)
            nodeB = graph.addNewNode(NodeWithTypedChoices.__name__)

            with pytest.raises(InvalidEdgeError):
                getattr(nodeA, srcAttrName).connectTo(getattr(nodeB, dstAttrName))

    def test_choiceParamToChoiceParamOfDifferentTypeIsStillAccepted(self):
        """
        ChoiceParam-to-ChoiceParam links intentionally ignore the underlying value type,
        since a ChoiceParam's values/type can be fully overridden at runtime by the link.
        """
        with registeredNodeTypes([NodeWithTypedChoices]):
            graph = Graph("")
            nodeA = graph.addNewNode(NodeWithTypedChoices.__name__)
            nodeB = graph.addNewNode(NodeWithTypedChoices.__name__)

            nodeA.intChoice.connectTo(nodeB.stringChoice)

            assert nodeB.stringChoice.isLink

    def test_scalarParamRejectedByNonExclusiveChoice(self):
        with registeredNodeTypes([NodeWithScalarOutputs, NodeWithTypedChoices]):
            graph = Graph("")
            nodeA = graph.addNewNode(NodeWithScalarOutputs.__name__)
            nodeB = graph.addNewNode(NodeWithTypedChoices.__name__)

            with pytest.raises(InvalidEdgeError):
                nodeA.intOut.connectTo(nodeB.intChoiceMulti)

    def test_validateIncomingConnectionDirect(self):
        with registeredNodeTypes([NodeWithScalarOutputs, NodeWithTypedChoices]):
            graph = Graph("")
            nodeA = graph.addNewNode(NodeWithScalarOutputs.__name__)
            nodeB = graph.addNewNode(NodeWithTypedChoices.__name__)

            result = nodeB.intChoice.validateIncomingConnection(nodeA.intOut)
            assert result is True
            assert isinstance(result, bool)

            result = nodeB.intChoice.validateIncomingConnection(nodeA.stringOut)
            assert result is False
            assert isinstance(result, bool)

    def test_validateIncomingConnectionWithFalsyValue(self):
        """
        Regression test: a falsy value (0, 0.0, '') on the source attribute must not be
        mistaken for an invalid connection.
        """
        with registeredNodeTypes([NodeWithScalarOutputs, NodeWithTypedChoices]):
            graph = Graph("")
            nodeA = graph.addNewNode(NodeWithScalarOutputs.__name__)
            nodeB = graph.addNewNode(NodeWithTypedChoices.__name__)

            nodeA.intOut.value = 0
            nodeA.floatOut.value = 0.0
            nodeA.stringOut.value = ""

            assert nodeB.intChoice.validateIncomingConnection(nodeA.intOut) is True
            assert nodeB.floatChoice.validateIncomingConnection(nodeA.floatOut) is True
            assert nodeB.stringChoice.validateIncomingConnection(nodeA.stringOut) is True

    def test_getValuesDoesNotRaiseWhenLinkedToScalarParam(self):
        """
        Regression test: ChoiceParam.getValues() used to assume any input link was itself
        a ChoiceParam and crash on IntParam/FloatParam/StringParam links.
        """
        with registeredNodeTypes([NodeWithScalarOutputs, NodeWithTypedChoices]):
            graph = Graph("")
            nodeA = graph.addNewNode(NodeWithScalarOutputs.__name__)
            nodeB = graph.addNewNode(NodeWithTypedChoices.__name__)

            nodeA.intOut.connectTo(nodeB.intChoice)

            assert nodeB.intChoice.values == [1, 2, 3]

    def test_disconnectResetsToDefaultValues(self):
        with registeredNodeTypes([NodeWithScalarOutputs, NodeWithTypedChoices]):
            graph = Graph("")
            nodeA = graph.addNewNode(NodeWithScalarOutputs.__name__)
            nodeB = graph.addNewNode(NodeWithTypedChoices.__name__)

            nodeA.intOut.connectTo(nodeB.intChoice)
            nodeB.intChoice.disconnectEdge()

            assert not nodeB.intChoice.isLink
            assert nodeB.intChoice.values == [1, 2, 3]
            assert nodeB.intChoice.value == 1

    def test_connectionIsSerialized(self, graphSavedOnDisk):
        with registeredNodeTypes([NodeWithScalarOutputs, NodeWithTypedChoices]):
            graph: Graph = graphSavedOnDisk
            nodeA = graph.addNewNode(NodeWithScalarOutputs.__name__)
            nodeB = graph.addNewNode(NodeWithTypedChoices.__name__)

            nodeA.intOut.connectTo(nodeB.intChoice)
            graph.save()

            loadedGraph = loadGraph(graph.filepath)
            loadedNodeA = loadedGraph.node(nodeA.name)
            loadedNodeB = loadedGraph.node(nodeB.name)

            assert loadedNodeB.intChoice.inputLink == loadedNodeA.intOut
