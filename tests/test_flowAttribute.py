"""Tests for the Flow attribute type and automatic internal flow attributes."""

import json
import tempfile
import os

import pytest

from meshroom.core import desc
from meshroom.core.graph import Graph
from meshroom.core.node import CompatibilityIssue

from .utils import registeredNodeTypes


class SimpleNode(desc.Node):
    """A basic test node with no manually-defined flow attributes."""
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value=""),
    ]


class NodeWithMixedAttributes(desc.Node):
    """A test node with regular attributes (gets flow attrs automatically)."""
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value=""),
    ]


class TestFlowDescriptor:
    """Tests for the Flow descriptor class."""

    def test_type(self):
        attr_desc = desc.Flow(name="flow", label="Flow", description="")
        assert attr_desc.type == "Flow"

    def test_backward_compat_alias(self):
        """FlowAttribute should be an alias for Flow."""
        assert desc.FlowAttribute is desc.Flow

    def test_default_value_is_none(self):
        attr_desc = desc.Flow(name="flow", label="Flow", description="")
        assert attr_desc.value is None

    def test_invalidate_is_false(self):
        """Flow should not invalidate by default since it carries no data."""
        attr_desc = desc.Flow(name="flow", label="Flow", description="")
        assert attr_desc.invalidate is False

    def test_validate_value(self):
        attr_desc = desc.Flow(name="flow", label="Flow", description="")
        assert attr_desc.validateValue(None) is None
        assert attr_desc.validateValue("anything") is None

    def test_check_value_types(self):
        attr_desc = desc.Flow(name="flow", label="Flow", description="")
        name, error = attr_desc.checkValueTypes()
        assert name == ""
        from meshroom.core.desc.attribute import ValueTypeErrors
        assert error == ValueTypeErrors.NONE


class TestAutomaticFlowAttributes:
    """Tests verifying that every node automatically receives flowIn and flowOut."""

    def test_every_node_has_flow_attributes(self):
        """Every node should automatically have flowIn (input) and flowOut (output)."""
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            node = graph.addNewNode("SimpleNode")
            assert node.internalAttribute("flowIn") is not None
            assert node.internalAttribute("flowOut") is not None

    def test_flow_in_is_input(self):
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            node = graph.addNewNode("SimpleNode")
            assert node.internalAttribute("flowIn").isInput
            assert not node.internalAttribute("flowIn").isOutput

    def test_flow_out_is_output(self):
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            node = graph.addNewNode("SimpleNode")
            assert node.internalAttribute("flowOut").isOutput
            assert not node.internalAttribute("flowOut").isInput

    def test_flow_attribute_type(self):
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            node = graph.addNewNode("SimpleNode")
            assert node.internalAttribute("flowIn").type == "Flow"
            assert node.internalAttribute("flowOut").type == "Flow"

    def test_flow_not_in_regular_attributes(self):
        """Flow attrs should be in internalAttributes, not regular attributes."""
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            node = graph.addNewNode("SimpleNode")
            assert not node.hasAttribute("flowIn")
            assert not node.hasAttribute("flowOut")
            assert node.hasInternalAttribute("flowIn")
            assert node.hasInternalAttribute("flowOut")

    def test_flow_input_not_connected_by_default(self):
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            node = graph.addNewNode("SimpleNode")
            assert not node.internalAttribute("flowIn").isLink
            assert not node.internalAttribute("flowOut").hasAnyOutputLinks

    def test_flow_attribute_is_default_when_not_connected(self):
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            node = graph.addNewNode("SimpleNode")
            assert node.internalAttribute("flowIn").isDefault

    def test_connect_flow_attributes(self):
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            nodeA = graph.addNewNode("SimpleNode")
            nodeB = graph.addNewNode("SimpleNode")

            graph.addEdge(nodeA.internalAttribute("flowOut"), nodeB.internalAttribute("flowIn"))

            assert nodeB.internalAttribute("flowIn").isLink
            assert nodeA.internalAttribute("flowOut").hasAnyOutputLinks

    def test_flow_attributes_only_connect_to_flow(self):
        """Flow should only connect to other Flow attributes."""
        with registeredNodeTypes([NodeWithMixedAttributes]):
            from meshroom.core.exception import InvalidEdgeError
            graph = Graph("")
            nodeA = graph.addNewNode("NodeWithMixedAttributes")
            nodeB = graph.addNewNode("NodeWithMixedAttributes")

            # Cannot connect flow output to regular input
            with pytest.raises(InvalidEdgeError):
                graph.addEdge(nodeA.internalAttribute("flowOut"), nodeB.attribute("input"))

            # Cannot connect regular output to flow input
            with pytest.raises(InvalidEdgeError):
                graph.addEdge(nodeA.attribute("output"), nodeB.internalAttribute("flowIn"))

    def test_flow_serialized_value_is_none_when_not_connected(self):
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            node = graph.addNewNode("SimpleNode")
            assert node.internalAttribute("flowIn").getSerializedValue() is None
            assert node.internalAttribute("flowOut").getSerializedValue() is None

    def test_flow_serialized_value_is_link_when_connected(self):
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            nodeA = graph.addNewNode("SimpleNode")
            nodeB = graph.addNewNode("SimpleNode")

            graph.addEdge(nodeA.internalAttribute("flowOut"), nodeB.internalAttribute("flowIn"))

            serialized = nodeB.internalAttribute("flowIn").getSerializedValue()
            assert serialized is not None
            assert "{" in serialized  # Should be a link expression

    def test_flow_attribute_is_not_default_when_connected(self):
        """Flow is not default when connected."""
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            nodeA = graph.addNewNode("SimpleNode")
            nodeB = graph.addNewNode("SimpleNode")

            graph.addEdge(nodeA.internalAttribute("flowOut"), nodeB.internalAttribute("flowIn"))

            assert not nodeB.internalAttribute("flowIn").isDefault


class TestFlowAttributeSerialization:
    """Tests for Flow attribute graph file serialization."""

    def test_unconnected_flow_not_in_serialized_internal_inputs(self):
        """Unconnected Flow inputs should not appear in the serialized file."""
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            node = graph.addNewNode("SimpleNode")
            node_dict = node.toDict()
            # flowIn should not be in internalInputs since it has no value
            assert "flowIn" not in node_dict["internalInputs"]

    def test_unconnected_flow_not_in_serialized_inputs(self):
        """Flow inputs should not appear in the 'inputs' section (they are internal)."""
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            node = graph.addNewNode("SimpleNode")
            node_dict = node.toDict()
            assert "flowIn" not in node_dict["inputs"]

    def test_connected_flow_in_serialized_internal_inputs(self):
        """Connected Flow inputs should appear in internalInputs as link expressions."""
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            nodeA = graph.addNewNode("SimpleNode")
            nodeB = graph.addNewNode("SimpleNode")

            graph.addEdge(nodeA.internalAttribute("flowOut"), nodeB.internalAttribute("flowIn"))

            node_dict = nodeB.toDict()
            assert "flowIn" in node_dict["internalInputs"]
            assert "{" in node_dict["internalInputs"]["flowIn"]

    def test_save_and_load_graph_with_flow_connection(self):
        """Graph with flow connections should be correctly saved and reloaded."""
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            nodeA = graph.addNewNode("SimpleNode")
            nodeB = graph.addNewNode("SimpleNode")

            graph.addEdge(nodeA.internalAttribute("flowOut"), nodeB.internalAttribute("flowIn"))

            with tempfile.NamedTemporaryFile(suffix=".mg", delete=False) as tmp:
                tmpPath = tmp.name

            try:
                graph.save(tmpPath)

                # Load the saved graph
                from meshroom.core.graph import loadGraph
                loadedGraph = loadGraph(tmpPath)

                # Check that the connection is preserved
                loadedNodeB = loadedGraph.node(nodeB.name)
                assert loadedNodeB is not None
                assert loadedNodeB.internalAttribute("flowIn").isLink

            finally:
                os.unlink(tmpPath)

    def test_save_and_load_graph_no_data_for_unconnected_flow(self):
        """Unconnected Flow should not produce data in the saved file."""
        with registeredNodeTypes([SimpleNode]):
            graph = Graph("")
            graph.addNewNode("SimpleNode")

            with tempfile.NamedTemporaryFile(suffix=".mg", delete=False) as tmp:
                tmpPath = tmp.name

            try:
                graph.save(tmpPath)

                with open(tmpPath, 'r') as f:
                    data = json.load(f)

                # Find node data
                node_data = list(data["graph"].values())[0]

                # Neither inputs nor internalInputs should contain flow attribute data
                assert "flowIn" not in node_data.get("inputs", {})
                assert "flowIn" not in node_data.get("internalInputs", {})
                assert "flowOut" not in node_data.get("outputs", {})

            finally:
                os.unlink(tmpPath)
