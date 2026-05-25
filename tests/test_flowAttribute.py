"""Tests for the FlowAttribute type."""

import json
import tempfile
import os

import pytest

from meshroom.core import desc
from meshroom.core.graph import Graph
from meshroom.core.node import CompatibilityIssue

from .utils import registeredNodeTypes


class NodeWithFlowAttributes(desc.Node):
    """A test node with FlowAttribute inputs and outputs."""
    inputs = [
        desc.FlowAttribute(name="flowIn", label="Flow In", description="Flow input"),
    ]
    outputs = [
        desc.FlowAttribute(name="flowOut", label="Flow Out", description="Flow output"),
    ]


class NodeWithMixedAttributes(desc.Node):
    """A test node with both flow and regular attributes."""
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
        desc.FlowAttribute(name="flowIn", label="Flow In", description=""),
    ]
    outputs = [
        desc.File(name="output", label="Output", description="", value=""),
        desc.FlowAttribute(name="flowOut", label="Flow Out", description=""),
    ]


class TestFlowAttributeDescriptor:
    """Tests for the FlowAttribute descriptor class."""

    def test_type(self):
        attr_desc = desc.FlowAttribute(name="flow", label="Flow", description="")
        assert attr_desc.type == "FlowAttribute"

    def test_default_value_is_none(self):
        attr_desc = desc.FlowAttribute(name="flow", label="Flow", description="")
        assert attr_desc.value is None

    def test_invalidate_is_false(self):
        """FlowAttribute should not invalidate by default since it carries no data."""
        attr_desc = desc.FlowAttribute(name="flow", label="Flow", description="")
        assert attr_desc.invalidate is False

    def test_validate_value(self):
        attr_desc = desc.FlowAttribute(name="flow", label="Flow", description="")
        assert attr_desc.validateValue(None) is None
        assert attr_desc.validateValue("anything") is None

    def test_check_value_types(self):
        attr_desc = desc.FlowAttribute(name="flow", label="Flow", description="")
        name, error = attr_desc.checkValueTypes()
        assert name == ""
        from meshroom.core.desc.attribute import ValueTypeErrors
        assert error == ValueTypeErrors.NONE


class TestFlowAttributeInstance:
    """Tests for FlowAttribute instance behavior in a graph."""

    def test_create_node_with_flow_attributes(self):
        with registeredNodeTypes([NodeWithFlowAttributes]):
            graph = Graph("")
            node = graph.addNewNode("NodeWithFlowAttributes")
            assert node is not None
            assert node.attribute("flowIn") is not None
            assert node.attribute("flowOut") is not None

    def test_flow_attribute_type(self):
        with registeredNodeTypes([NodeWithFlowAttributes]):
            graph = Graph("")
            node = graph.addNewNode("NodeWithFlowAttributes")
            assert node.attribute("flowIn").type == "FlowAttribute"
            assert node.attribute("flowOut").type == "FlowAttribute"

    def test_flow_input_not_connected_by_default(self):
        with registeredNodeTypes([NodeWithFlowAttributes]):
            graph = Graph("")
            node = graph.addNewNode("NodeWithFlowAttributes")
            assert not node.attribute("flowIn").isLink
            assert not node.attribute("flowOut").hasAnyOutputLinks

    def test_flow_attribute_is_default_when_not_connected(self):
        with registeredNodeTypes([NodeWithFlowAttributes]):
            graph = Graph("")
            node = graph.addNewNode("NodeWithFlowAttributes")
            assert node.attribute("flowIn").isDefault

    def test_connect_flow_attributes(self):
        with registeredNodeTypes([NodeWithFlowAttributes]):
            graph = Graph("")
            nodeA = graph.addNewNode("NodeWithFlowAttributes")
            nodeB = graph.addNewNode("NodeWithFlowAttributes")

            graph.addEdge(nodeA.attribute("flowOut"), nodeB.attribute("flowIn"))

            assert nodeB.attribute("flowIn").isLink
            assert nodeA.attribute("flowOut").hasAnyOutputLinks

    def test_flow_attributes_only_connect_to_flow(self):
        """FlowAttribute should only connect to other FlowAttribute."""
        with registeredNodeTypes([NodeWithMixedAttributes]):
            from meshroom.core.exception import InvalidEdgeError
            graph = Graph("")
            nodeA = graph.addNewNode("NodeWithMixedAttributes")
            nodeB = graph.addNewNode("NodeWithMixedAttributes")

            # Cannot connect flow output to regular input
            with pytest.raises(InvalidEdgeError):
                graph.addEdge(nodeA.attribute("flowOut"), nodeB.attribute("input"))

            # Cannot connect regular output to flow input
            with pytest.raises(InvalidEdgeError):
                graph.addEdge(nodeA.attribute("output"), nodeB.attribute("flowIn"))

    def test_flow_serialized_value_is_none_when_not_connected(self):
        with registeredNodeTypes([NodeWithFlowAttributes]):
            graph = Graph("")
            node = graph.addNewNode("NodeWithFlowAttributes")
            assert node.attribute("flowIn").getSerializedValue() is None
            assert node.attribute("flowOut").getSerializedValue() is None

    def test_flow_serialized_value_is_link_when_connected(self):
        with registeredNodeTypes([NodeWithFlowAttributes]):
            graph = Graph("")
            nodeA = graph.addNewNode("NodeWithFlowAttributes")
            nodeB = graph.addNewNode("NodeWithFlowAttributes")

            graph.addEdge(nodeA.attribute("flowOut"), nodeB.attribute("flowIn"))

            serialized = nodeB.attribute("flowIn").getSerializedValue()
            assert serialized is not None
            assert "{" in serialized  # Should be a link expression

    def test_flow_attribute_is_default_when_connected(self):
        """FlowAttribute is not default when connected."""
        with registeredNodeTypes([NodeWithFlowAttributes]):
            graph = Graph("")
            nodeA = graph.addNewNode("NodeWithFlowAttributes")
            nodeB = graph.addNewNode("NodeWithFlowAttributes")

            graph.addEdge(nodeA.attribute("flowOut"), nodeB.attribute("flowIn"))

            assert not nodeB.attribute("flowIn").isDefault


class TestFlowAttributeSerialization:
    """Tests for FlowAttribute graph file serialization."""

    def test_unconnected_flow_not_in_serialized_inputs(self):
        """Unconnected FlowAttribute inputs should not appear in the serialized file."""
        with registeredNodeTypes([NodeWithFlowAttributes]):
            graph = Graph("")
            node = graph.addNewNode("NodeWithFlowAttributes")
            node_dict = node.toDict()
            # flowIn should not be in inputs since it has no value
            assert "flowIn" not in node_dict["inputs"]

    def test_unconnected_flow_not_in_serialized_outputs(self):
        """Unconnected FlowAttribute outputs should not appear in the serialized file."""
        with registeredNodeTypes([NodeWithFlowAttributes]):
            graph = Graph("")
            node = graph.addNewNode("NodeWithFlowAttributes")
            node_dict = node.toDict()
            # flowOut should not be in outputs since it has no value
            assert "flowOut" not in node_dict["outputs"]

    def test_connected_flow_in_serialized_inputs(self):
        """Connected FlowAttribute inputs should appear in the serialized file as link expressions."""
        with registeredNodeTypes([NodeWithFlowAttributes]):
            graph = Graph("")
            nodeA = graph.addNewNode("NodeWithFlowAttributes")
            nodeB = graph.addNewNode("NodeWithFlowAttributes")

            graph.addEdge(nodeA.attribute("flowOut"), nodeB.attribute("flowIn"))

            node_dict = nodeB.toDict()
            assert "flowIn" in node_dict["inputs"]
            assert "{" in node_dict["inputs"]["flowIn"]

    def test_save_and_load_graph_with_flow_connection(self):
        """Graph with flow connections should be correctly saved and reloaded."""
        with registeredNodeTypes([NodeWithFlowAttributes]):
            graph = Graph("")
            nodeA = graph.addNewNode("NodeWithFlowAttributes")
            nodeB = graph.addNewNode("NodeWithFlowAttributes")

            graph.addEdge(nodeA.attribute("flowOut"), nodeB.attribute("flowIn"))

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
                assert loadedNodeB.attribute("flowIn").isLink

            finally:
                os.unlink(tmpPath)

    def test_save_and_load_graph_no_data_for_unconnected_flow(self):
        """Unconnected FlowAttribute should not produce data in the saved file."""
        with registeredNodeTypes([NodeWithFlowAttributes]):
            graph = Graph("")
            graph.addNewNode("NodeWithFlowAttributes")

            with tempfile.NamedTemporaryFile(suffix=".mg", delete=False, mode='w') as tmp:
                tmpPath = tmp.name

            try:
                graph.save(tmpPath)

                with open(tmpPath, 'r') as f:
                    data = json.load(f)

                # Find node data
                node_data = list(data["graph"].values())[0]

                # Neither inputs nor outputs should contain flow attribute data
                assert "flowIn" not in node_data.get("inputs", {})
                assert "flowOut" not in node_data.get("outputs", {})

            finally:
                os.unlink(tmpPath)
