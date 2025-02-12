import pytest
import types
from meshroom.core.attribute import attributeFactory, ChoiceParam, GroupAttribute, Attribute
from meshroom.common import DictModel  # needed for GroupAttribute initialization

def test_choice_param_validate_value_non_exclusive():
    """
    Test that a non-exclusive ChoiceParam correctly processes input values.
    Creates a dummy ChoiceParam with a lambda conformValue that trims and uppercases strings.
    Checks that both comma-separated string input and an iterable list input are processed as expected.
    """
    class DummyGraph:
        def __init__(self):
            self.name = "dummyGraph"
            self._edges = {}
            self.edges = {}
        def update(self):
            self.updated = True
        def markNodesDirty(self, node):
            node.dirty = True

    class DummyNode:
        def __init__(self, name, label, graph):
            self.name = name
            self.label = label
            self.graph = graph
        def _onAttributeChanged(self, attr):
            self.changed = True
        def updateInternalAttributes(self):
            self.updated = True

    dummy_graph = DummyGraph()
    dummy_node = DummyNode("dummyNode", "Dummy Node", dummy_graph)

    class DummyChoiceDesc:
        def __init__(self):
            self.name = "dummyChoice"
            self.label = "Dummy Choice"
            self.description = "A dummy choice parameter"
            self.value = ""  # default value
            self.enabled = True
            self.invalidate = True
            self.instanceType = ChoiceParam
            self.exclusive = False  # non-exclusive to allow multiple values
            self._values = ["A", "B", "C"]
            self.conformValue = lambda v: v.strip().upper()
            self.validateValue = lambda x: x
            self._valueType = lambda: ""

    dummy_choice_desc = DummyChoiceDesc()
    choice_param = attributeFactory(dummy_choice_desc, None, False, dummy_node)

    # Test with a comma-separated string input.
    result_string = choice_param.validateValue("a, b")
    assert result_string == ["A", "B"], "Expected list ['A', 'B'] from input 'a, b'"

    # Test with an iterable list input.
    result_list = choice_param.validateValue([" x ", "y"])
    assert result_list == ["X", "Y"], "Expected list ['X', 'Y'] from input [' x ', 'y']"

def test_group_attribute_set_and_get_export_value():
    """
    Test the GroupAttribute.
    Constructs a dummy group with two children. The default export value is checked and then the
    child attribute values are updated using a dictionary. The test verifies that getExportValue()
    and getValueStr() return the updated values.
    """
    class DummyGraph:
        def __init__(self):
            self.name = "dummyGraph"
            self._edges = {}
            self.edges = {}
        def update(self):
            self.updated = True
        def markNodesDirty(self, node):
            node.dirty = True

    class DummyNode:
        def __init__(self, name, label, graph):
            self.name = name
            self.label = label
            self.graph = graph
        def _onAttributeChanged(self, attr):
            self.changed = True
        def updateInternalAttributes(self):
            self.updated = True

    dummy_graph = DummyGraph()
    dummy_node = DummyNode("dummyNode", "Dummy Node", dummy_graph)

    class DummyChildDesc:
        def __init__(self, name, default):
            self.name = name
            self.label = name.capitalize()
            self.description = f"Dummy child {name}"
            self.value = default  # default value
            self.enabled = True
            self.invalidate = True
            self.instanceType = Attribute
            self._valueType = lambda: default
            self.validateValue = lambda x: int(x)
            self.conformValue = lambda x: int(x)

    child1 = DummyChildDesc("child1", 10)
    child2 = DummyChildDesc("child2", 20)

    class DummyGroupDesc:
        def __init__(self, children):
            self.name = "dummyGroup"
            self.label = "Dummy Group"
            self.description = "A dummy group parameter"
            self.value = {}  # default value is an empty dict
            self.enabled = True
            self.invalidate = True
            self.instanceType = GroupAttribute
            self.groupDesc = children
            self._groupDesc = children
            self.validateValue = lambda x: x
            self.joinChar = " "
            self.brackets = None

    dummy_group_desc = DummyGroupDesc([child1, child2])
    group_attr = attributeFactory(dummy_group_desc, None, False, dummy_node)

    # Check that the default export value contains the default values for children.
    export_default = group_attr.getExportValue()
    assert export_default == {'child1': 10, 'child2': 20}, "Expected default export values {'child1': 10, 'child2': 20}"

    # Set new values for the group attribute with a dictionary.
    new_values = {'child1': 100, 'child2': 200}
    group_attr.value = new_values

    # Verify that each child attribute reflects the new values.
    export_updated = group_attr.getExportValue()
    assert export_updated == new_values, "Expected export values to update after setting new values"

    # Verify that getValueStr returns a string representation including the new values.
    value_str = group_attr.getValueStr(withQuotes=False)
    assert "100" in value_str and "200" in value_str, "getValueStr should include updated values in its string"
