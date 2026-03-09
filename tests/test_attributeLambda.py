from meshroom.core import desc
from meshroom.core.graph import Graph

from .utils import registerNodeDesc, unregisterNodeDesc


class NodeWithCallableValue(desc.Node):
    """Test node with callable default values to test executeValue."""
    inputs = [
        desc.IntParam(
            name="fixedInput",
            label="Fixed Input",
            description="A simple integer input.",
            value=10,
            range=(0, 100, 1),
        ),
        desc.IntParam(
            name="callableNodeInput",
            label="Callable Node Input",
            description="Input with a callable default that receives the node.",
            value=lambda node: node.fixedInput.value * 2,
            range=(0, 200, 1),
        ),
        desc.StringParam(
            name="callableAttrInput",
            label="Callable Attr Input (Compatibility)",
            description="Input with a callable default that receives the attribute for compatibility with the old behavior.",
            value=lambda attr: f"attr_{attr.name}",
        ),
    ]
    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="",
            value="{nodeCacheFolder}/output.txt",
        )
    ]


class TestExecuteValue:
    """Tests for the Attribute.executeValue method and callable value handling."""

    @classmethod
    def setup_class(cls):
        registerNodeDesc(NodeWithCallableValue)

    @classmethod
    def teardown_class(cls):
        unregisterNodeDesc(NodeWithCallableValue)

    def test_executeValue_with_node_parameter(self):
        """executeValue should pass the node when the callable parameter is named 'node'."""
        graph = Graph("")
        node = graph.addNewNode("NodeWithCallableValue")

        result = node.callableNodeInput.executeValue(lambda node: node.fixedInput.value + 5)
        assert result == 15

    def test_executeValue_with_attr_parameter(self):
        """executeValue should pass the attribute when the parameter is not named 'node'."""
        graph = Graph("")
        node = graph.addNewNode("NodeWithCallableValue")

        result = node.fixedInput.executeValue(lambda attr: attr.name)
        assert result == "fixedInput"

    def test_callable_default_value_with_node_param(self):
        """getDefaultValue should evaluate a callable descriptor value using node parameter."""
        graph = Graph("")
        node = graph.addNewNode("NodeWithCallableValue")

        # The default value for callableNodeInput is lambda node: node.fixedInput.value * 2
        default = node.callableNodeInput.getDefaultValue()
        assert default == 20  # 10 * 2

    def test_callable_default_value_with_attr_param(self):
        """getDefaultValue should evaluate a callable descriptor value using attr parameter."""
        graph = Graph("")
        node = graph.addNewNode("NodeWithCallableValue")

        # The default value for callableAttrInput is lambda attr: f"attr_{attr.name}"
        default = node.callableAttrInput.getDefaultValue()
        assert default == "attr_callableAttrInput"

    def test_set_value_with_callable(self):
        """Setting a callable value should evaluate it via executeValue."""
        graph = Graph("")
        node = graph.addNewNode("NodeWithCallableValue")

        node.fixedInput.value = lambda node: 42
        assert node.fixedInput.value == 42

    def test_set_value_with_attr_callable(self):
        """Setting a callable value using attr parameter should evaluate correctly."""
        graph = Graph("")
        node = graph.addNewNode("NodeWithCallableValue")

        node.fixedInput.value = lambda attr: 99
        assert node.fixedInput.value == 99

    def test_callable_default_reflects_current_state(self):
        """Callable default values should reflect the current node state when evaluated."""
        graph = Graph("")
        node = graph.addNewNode("NodeWithCallableValue")

        # Change the fixedInput value
        node.fixedInput.value = 25

        # Re-evaluate the callable default for callableNodeInput
        default = node.callableNodeInput.getDefaultValue()
        assert default == 50  # 25 * 2

    def test_reset_to_default_with_callable(self):
        """resetToDefaultValue should correctly evaluate callable defaults."""
        graph = Graph("")
        node = graph.addNewNode("NodeWithCallableValue")

        # Change value away from default
        node.callableAttrInput.value = "custom_value"
        assert node.callableAttrInput.value == "custom_value"

        # Reset should re-evaluate the callable
        node.callableAttrInput.resetToDefaultValue()
        assert node.callableAttrInput.value == "attr_callableAttrInput"
