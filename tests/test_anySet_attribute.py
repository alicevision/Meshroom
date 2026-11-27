"""Tests for the AnySet feature."""

import json
from types import SimpleNamespace

import pytest

from meshroom.core import desc
from meshroom.core.attribute import AnySet, Attribute, attributeFactory
from meshroom.core.desc import AnySet as AnySetDesc
from meshroom.core.graph import Graph, loadGraph
from meshroom.core.node import CompatibilityNode

from .utils import registeredNodeTypes


def anyset_child(serializedAnySet, name):
    return next(attribute for attribute in anyset_children(serializedAnySet) if attribute.get("name") == name)


def anyset_children(serializedAnySet):
    if isinstance(serializedAnySet, dict):
        return serializedAnySet["children"]
    return serializedAnySet


def initGraphAndNode():
    graph = Graph("test")
    node = graph.addNewNode("DynamicNode")
    return graph, node

# ---------------------------------------------------------------------------
# Descriptor tests
# ---------------------------------------------------------------------------

def test_dynamic_attribute_desc_type():
    """descriptor has the correct type string."""
    d = AnySetDesc(name="customInputs")
    assert d.type == "AnySet"


def test_dynamic_attribute_desc_instance_type():
    """descriptor returns the correct instance class."""
    d = AnySetDesc(name="customInputs")
    assert d.instanceType is AnySet


def test_anyset_desc_clone():
    """Cloning an AnySet descriptor creates a distinct AnySet descriptor with the same properties."""
    d = AnySetDesc(name="customInputs", label="Custom Inputs", description="Some description",
                   commandLineGroup="customGroup", advanced=True, semantic="someSemantic", enabled=False,
                   visible=False, exposed=True, editable=False)
    clone = d.clone()

    assert clone is not d
    assert isinstance(clone, AnySetDesc)
    for prop in ("name", "label", "description", "commandLineGroup", "advanced", "semantic", "enabled",
                 "visible", "exposed", "editable", "items"):
        assert getattr(clone, prop) == getattr(d, prop), prop


def test_anyset_desc_is_editable_by_default():
    assert AnySetDesc(name="customInputs").editable


def test_duplicate_anyset_into_anyset():
    """An AnySet can be duplicated as a child of another AnySet."""
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("DynamicNode")

    newAttr = dynamicNode.ins.duplicateAttribute(srcNode.ins)
    assert isinstance(newAttr, AnySet)
    assert newAttr.desc is not srcNode.ins.desc


# ---------------------------------------------------------------------------
# Node / attribute creation tests
# ---------------------------------------------------------------------------

def test_dynamic_attribute_present_on_node():
    """A node that declares a DynamicAttribute exposes it as an attribute."""
    graph, node = initGraphAndNode()
    assert node.hasAttribute("ins")
    customInputsAttrs = node.attribute("ins")
    assert isinstance(customInputsAttrs, AnySet)

    assert node.hasAttribute("outs")
    customOuputsAttrs = node.attribute("outs")
    assert isinstance(customOuputsAttrs, AnySet)


def test_dynamic_attribute_validates_any_connection():
    """DynamicAttribute.validateIncomingConnection returns True for any type."""
    graph, node = initGraphAndNode()
    dynAttr = node.attribute("ins")

    # Build a fake source attribute of type File
    srcNode = graph.addNewNode("Ls", input="/fakeDirectory")
    assert dynAttr.validateIncomingConnection(srcNode.output)


# ---------------------------------------------------------------------------
# Dynamic input creation tests
# ---------------------------------------------------------------------------

def test_add_dynamic_input_creates_sibling_attribute():
    """Adding a dynamic input inserts a new attribute before the DynamicAttribute."""
    graph, dstNode = initGraphAndNode()

    srcNode = graph.addNewNode("Ls", input="/fakeDirectory")
    dynAttr = dstNode.attribute("ins")

    attributeSrc = srcNode.attribute("input")
    assert(isinstance(attributeSrc, Attribute))

    newAttr = dynAttr.duplicateAttribute(attributeSrc, isOutput=False)
    assert(newAttr is not None)
    assert(dstNode.ins.input is not None)
    assert(isinstance(dstNode.ins.input, Attribute))

    # Check renaming auto when concurrent naming
    input_0 = dynAttr.duplicateAttribute(attributeSrc, isOutput=False)
    assert(input_0 is not None)
    assert(dstNode.ins.input_0 is not None)
    assert(isinstance(dstNode.ins.input_0, Attribute))

    input_1 = dynAttr.duplicateAttribute(attributeSrc, isOutput=False)
    assert(input_1 is not None)
    assert(dstNode.ins.input_1 is not None)
    assert(isinstance(dstNode.ins.input_1, Attribute))


def test_remove_dynamic_input():
    """Removing a dynamic input deletes the attribute from the node."""

    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("Ls", input="/fakeDirectory")

    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)

    assert(dynamicNode.ins.input is not None)
    assert(isinstance(dynamicNode.ins.input, Attribute))

    # When
    dynamicNode.ins.removeAttribute(dynamicNode.ins.input)

    # Then
    assert(dynamicNode.ins.input is None)


def test_anyset_attribute_can_be_restored_with_edges():
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("Ls", input="/fakeDirectory")

    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)
    srcNode.input.connectTo(dynamicNode.ins.input)

    serializedAttribute = dynamicNode.ins.input.asDict()
    index = list(dynamicNode.ins.value).index(dynamicNode.ins.input)
    edgeNames = [(edge.src.fullName, edge.dst.fullName) for edge in graph.edges.values()]

    graph.removeEdge(dynamicNode.ins.input)
    dynamicNode.ins.removeAttribute(dynamicNode.ins.input)

    assert dynamicNode.ins.input is None
    assert not graph.edges

    dynamicNode.ins.insertAttribute(serializedAttribute, index)
    for srcName, dstName in edgeNames:
        graph.addEdge(graph.anyAttribute(srcName), graph.anyAttribute(dstName))

    assert isinstance(dynamicNode.ins.input, Attribute)
    assert dynamicNode.ins.input.isLink
    assert dynamicNode.ins.input.inputLink is srcNode.input


def test_move_anyset_attribute_updates_order():
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("Ls", input="/fakeDirectory")

    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)
    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)
    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)

    initialOrder = [attribute.name for attribute in dynamicNode.ins.value]
    attributeToMove = list(dynamicNode.ins.value)[-1]

    dynamicNode.ins.moveAttribute(attributeToMove, 0)

    assert [attribute.name for attribute in dynamicNode.ins.value] == [initialOrder[-1], *initialOrder[:-1]]

    dynamicNode.ins.moveAttribute(attributeToMove, 99)

    assert [attribute.name for attribute in dynamicNode.ins.value] == initialOrder


def test_new_anyset_attribute_data_has_unique_name_and_defaults():
    graph, dynamicNode = initGraphAndNode()

    floatData = dynamicNode.ins.getNewAttributeData("FloatParam")
    assert floatData["name"] == "float"
    assert floatData["type"] == "FloatParam"
    dynamicNode.ins.insertAttribute(floatData, 0)

    floatData0 = dynamicNode.ins.getNewAttributeData("FloatParam")
    assert floatData0["name"] == "float_0"
    floatAttr0 = dynamicNode.ins.insertAttribute(floatData0, 1)
    assert floatAttr0.label == "Float 0"
    assert floatAttr0.desc.range == [0.0, 1.0, 0.01]
    assert floatAttr0.isDefault

    choiceAttr = dynamicNode.ins.insertAttribute(dynamicNode.ins.getNewAttributeData("ChoiceParam"), 2)
    assert choiceAttr.desc.values == ["optionA", "optionB"]

    try:
        dynamicNode.ins.getNewAttributeData("AnySet")
    except ValueError:
        pass
    else:
        raise AssertionError("Only parameter types can be created from the UI.")

    # Every type offered by the menu model can be created
    for item in dynamicNode.ins.newAttributeTypes:
        assert dynamicNode.ins.insertAttribute(dynamicNode.ins.getNewAttributeData(item["type"]), 0).type == item["type"]


def test_edit_anyset_attribute_updates_description_and_keeps_position():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    anySet.insertAttribute(anySet.getNewAttributeData("StringParam"), 0)
    intAttr = anySet.insertAttribute(anySet.getNewAttributeData("IntParam"), 1)
    anySet.insertAttribute(anySet.getNewAttributeData("BoolParam"), 2)

    data = anySet.getEditedAttributeData(intAttr, {
        "name": "downscale", "label": "Downscale", "description": "Downscale factor",
        "advanced": True, "defaultValue": "2", "range": [1, 8.0, 1]
    })
    newAttr = anySet.replaceAttribute(intAttr, data)

    assert [attribute.name for attribute in anySet.value] == ["string", "downscale", "bool"]
    assert anySet.int is None
    assert newAttr.label == "Downscale"
    assert newAttr.desc.description == "Downscale factor"
    assert newAttr.desc.advanced
    assert newAttr.desc.range == [1, 8, 1]
    # The attribute was at its default value: it follows the new default value
    assert newAttr.value == 2
    assert newAttr.isDefault


def test_edit_anyset_attribute_keeps_modified_value():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    choiceAttr = anySet.insertAttribute(anySet.getNewAttributeData("ChoiceParam"), 0)
    choiceAttr.value = "optionB"

    data = anySet.getEditedAttributeData(choiceAttr, {"defaultValue": "low", "values": ["low", "optionB"]})
    newAttr = anySet.replaceAttribute(choiceAttr, data)

    assert newAttr.desc.values == ["low", "optionB"]
    assert newAttr.desc.value == "low"
    assert newAttr.value == "optionB"
    assert not newAttr.isDefault


def test_edit_anyset_choice_values_drops_unavailable_value():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    choiceAttr = anySet.insertAttribute(anySet.getNewAttributeData("ChoiceParam"), 0)
    choiceAttr.value = "optionB"
    multiChoiceAttr = anySet.insertAttribute({"name": "multi", "label": "Multi", "type": "ChoiceParam",
                                              "value": ["a", "b"], "values": ["a", "b", "c"], "exclusive": False}, 1)

    choiceData = anySet.getEditedAttributeData(choiceAttr, {"defaultValue": "y", "values": ["x", "y"]})
    multiChoiceData = anySet.getEditedAttributeData(multiChoiceAttr, {"values": ["b", "c"]})

    # The current value is no longer available: the choice follows its default value
    assert anySet.replaceAttribute(choiceAttr, choiceData).value == "y"
    assert anySet.replaceAttribute(multiChoiceAttr, multiChoiceData).value == ["b"]


def test_edit_anyset_attribute_rejects_invalid_parameters():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    anySet.insertAttribute(anySet.getNewAttributeData("FloatParam"), 0)
    stringAttr = anySet.insertAttribute(anySet.getNewAttributeData("StringParam"), 1)
    floatAttr = anySet.float

    for parameters in ({"name": "float"}, {"name": "1invalid"}, {"label": " "}):
        try:
            anySet.getEditedAttributeData(stringAttr, parameters)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Editing with {parameters} should fail.")

    try:
        anySet.getEditedAttributeData(floatAttr, {"defaultValue": "notANumber"})
    except ValueError:
        pass
    else:
        raise AssertionError("An invalid default value should be rejected.")


def test_edit_anyset_attribute_ignores_parameters_of_other_types():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    intAttr = anySet.insertAttribute(anySet.getNewAttributeData("IntParam"), 0)
    stringAttr = anySet.insertAttribute(anySet.getNewAttributeData("StringParam"), 1)

    intData = anySet.getEditedAttributeData(intAttr, {"label": "New", "values": ["a"]})
    assert intData["label"] == "New" and "values" not in intData
    stringData = anySet.getEditedAttributeData(stringAttr, {"label": "New", "range": [0, 10, 1]})
    assert stringData["label"] == "New" and "range" not in stringData


def test_edited_anyset_attribute_restored_after_load(tmp_path):
    from meshroom.core.graph import loadGraph

    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    floatAttr = anySet.insertAttribute(anySet.getNewAttributeData("FloatParam"), 0)
    floatAttr = anySet.replaceAttribute(floatAttr, anySet.getEditedAttributeData(floatAttr, {
        "name": "blend", "label": "Blend Weight", "description": "Weight of the secondary input",
        "advanced": True, "defaultValue": 0.5, "range": [0.0, 2.0, 0.1]
    }))
    floatAttr.value = 0.65

    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)

    loadedAttr = loadGraph(graphFile).node(dynamicNode.name).ins.blend
    assert loadedAttr.label == "Blend Weight"
    assert loadedAttr.desc.description == "Weight of the secondary input"
    assert loadedAttr.desc.advanced
    assert loadedAttr.desc.range == [0.0, 2.0, 0.1]
    assert loadedAttr.desc.value == 0.5
    assert loadedAttr.value == 0.65
    assert not loadedAttr.isDefault


def test_edit_anyset_attribute_keeps_edges(tmp_path):
    """Editing and renaming connected children reconnects their edges, as inputs, as outputs and on their own children."""
    from meshroom.core.graph import loadGraph

    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("DynamicNode")
    dstNode = graph.addNewNode("DynamicNode")
    srcFloat = srcNode.outs.insertAttribute(srcNode.outs.getNewAttributeData("FloatParam"), 0)

    stringAttr = dynamicNode.ins.insertAttribute(dynamicNode.ins.getNewAttributeData("StringParam"), 0)
    vectorAttr = dynamicNode.ins.duplicateAttribute(graph.addNewNode("Position").xyz)
    outputAttr = dynamicNode.outs.insertAttribute(dynamicNode.outs.getNewAttributeData("StringParam"), 0)
    srcNode.code.connectTo(stringAttr)
    srcFloat.connectTo(vectorAttr.x)
    outputAttr.connectTo(dstNode.code)

    for anySet, attribute, name in [
        (dynamicNode.ins, stringAttr, "text"),
        (dynamicNode.ins, vectorAttr, "offset"),
        (dynamicNode.outs, outputAttr, "result"),
    ]:
        data = anySet.getEditedAttributeData(attribute, {"name": name, "label": name.capitalize()})
        assert anySet.replaceAttributeWithEdges(attribute, data).name == name

    def checkEdges(graph):
        node = graph.node(dynamicNode.name)
        assert sorted(attribute.name for attribute in node.ins.value) == ["offset", "text"]
        assert node.ins.text.inputLink is graph.node(srcNode.name).code
        assert node.ins.offset.x.inputLink is graph.node(srcNode.name).outs.float
        assert graph.node(dstNode.name).code.inputLink is node.outs.result
        assert len(graph.edges) == 3

    checkEdges(graph)
    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)
    checkEdges(loadGraph(graphFile))


def test_edit_anyset_attribute_failure_keeps_attribute_and_edges():
    """When the edited attribute cannot be created, the AnySet and the edges are left unchanged."""
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("DynamicNode")
    anySet = dynamicNode.ins
    anySet.insertAttribute(anySet.getNewAttributeData("BoolParam"), 0)
    stringAttr = anySet.insertAttribute(anySet.getNewAttributeData("StringParam"), 1)
    anySet.insertAttribute(anySet.getNewAttributeData("IntParam"), 2)
    srcNode.code.connectTo(stringAttr)

    data = anySet.getEditedAttributeData(stringAttr, {"name": "text"})
    data["type"] = "UnknownParam"
    try:
        anySet.replaceAttributeWithEdges(stringAttr, data)
    except AttributeError:
        pass
    else:
        raise AssertionError("An attribute of an unknown type should not be created.")

    assert [attribute.name for attribute in anySet.value] == ["bool", "string", "int"]
    assert anySet.string is stringAttr
    assert stringAttr.inputLink is srcNode.code
    assert len(graph.edges) == 1


def test_edit_anyset_group_and_list_keep_values():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    vectorAttr = anySet.duplicateAttribute(graph.addNewNode("Position").xyz)
    vectorAttr.x.value = 3.0
    elementDesc = {"name": "float", "label": "Float", "type": "FloatParam", "value": 0.0}
    listAttr = anySet.insertAttribute({"name": "list", "label": "List", "type": "ListAttribute", "value": [], "elementDesc": elementDesc}, 1)
    listAttr.append(1.5)

    vectorData = anySet.getEditedAttributeData(vectorAttr, {"name": "offset", "label": "Offset"})
    newVector = anySet.replaceAttribute(vectorAttr, vectorData)
    assert newVector.label == "Offset"
    assert newVector.x.value == 3.0

    newList = anySet.replaceAttribute(listAttr, anySet.getEditedAttributeData(listAttr, {"description": "Weights"}))
    assert newList.desc.description == "Weights"
    assert newList.desc.elementDesc.type == "FloatParam"
    assert [element.value for element in newList.value] == [1.5]


# ---------------------------------------------------------------------------
# Serialization / deserialization tests
# ---------------------------------------------------------------------------

def test_upgrading_compatibility_node_keeps_anyset_children_and_edges(tmp_path):
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("DynamicNode")
    intChild = dynamicNode.ins.insertAttribute({"name": "int", "label": "Int", "type": "IntParam", "value": 0}, 0)
    intChild.value = 7
    stringChild = dynamicNode.ins.insertAttribute({"name": "string", "label": "String", "type": "StringParam", "value": ""}, 1)
    srcNode.code.connectTo(stringChild)

    # A UID that does not match the node makes it a compatibility node, as with a file saved by an older version
    graphFile = tmp_path / "graph.mg"
    graph.save(str(graphFile))
    graphContent = json.loads(graphFile.read_text())
    graphContent["graph"][dynamicNode.name]["uid"] = "olderUid"
    graphFile.write_text(json.dumps(graphContent))

    loadedGraph = loadGraph(str(graphFile))
    assert isinstance(loadedGraph.node(dynamicNode.name), CompatibilityNode)

    upgradedNode = loadedGraph.upgradeNode(dynamicNode.name)
    assert [child.name for child in upgradedNode.ins.value] == ["int", "string"]
    assert upgradedNode.ins.int.value == 7
    assert upgradedNode.ins.string.inputLink is loadedGraph.node(srcNode.name).code


def test_duplicated_attributes_are_added_at_the_end():
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("AllAttributesNode")
    for attribute in (srcNode.stringParam, srcNode.intParam, srcNode.boolParam):
        dynamicNode.ins.duplicateAttribute(attribute)
    assert [attribute.name for attribute in dynamicNode.ins.value] == ["stringParam", "intParam", "boolParam"]


def test_anyset_group_values_restored_after_load(tmp_path):
    from meshroom.core.graph import loadGraph

    graph, dynamicNode = initGraphAndNode()
    groupAttr = dynamicNode.ins.duplicateAttribute(graph.addNewNode("Position").xyz)
    groupAttr.x.value = 0.3

    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)
    loadedAttr = loadGraph(graphFile).node(dynamicNode.name).ins.xyz
    assert loadedAttr.x.value == 0.3
    assert loadedAttr.x.desc.value == 0.0


def test_anyset_child_description_restored_after_load(tmp_path):
    graph, dynamicNode = initGraphAndNode()
    child = dynamicNode.ins.insertAttribute({
        "name": "count", "label": "Count", "type": "IntParam", "value": 7, "defaultValue": 3,
        "description": "Number of items", "advanced": True, "semantic": "custom"
    }, 0)
    assert child.desc.value == 3
    assert child.value == 7

    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)
    loadedChild = loadGraph(graphFile).node(dynamicNode.name).ins.count
    assert loadedChild.value == 7
    assert loadedChild.desc.value == 3
    assert loadedChild.desc.description == "Number of items"
    assert loadedChild.desc.advanced
    assert loadedChild.desc.semantic == "custom"



def test_anyset_linked_attribute_keeps_default_value(tmp_path):
    from meshroom.core.graph import loadGraph

    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("DynamicNode")
    anySet = dynamicNode.ins
    stringAttr = anySet.insertAttribute(anySet.getNewAttributeData("StringParam"), 0)
    stringAttr = anySet.replaceAttribute(stringAttr, anySet.getEditedAttributeData(stringAttr, {"defaultValue": "hello"}))
    srcNode.code.connectTo(stringAttr)

    # When restored from its serialized data, as when undoing an edition or a removal
    data = stringAttr.asDict()
    graph.removeEdge(stringAttr)
    assert anySet.replaceAttribute(stringAttr, data).desc.value == "hello"

    # When saved and loaded
    srcNode.code.connectTo(anySet.string)
    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)
    loadedGraph = loadGraph(graphFile)
    loadedAttr = loadedGraph.node(dynamicNode.name).ins.string
    assert loadedAttr.desc.value == "hello"
    loadedGraph.removeEdge(loadedAttr)
    assert loadedAttr.value == "hello"


def test_edit_anyset_nested_group_keeps_values(tmp_path):
    from meshroom.core.graph import loadGraph

    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    groupAttr = anySet.duplicateAttribute(graph.addNewNode("NestedTest").xyz)
    groupAttr.x.value = 0.3
    groupAttr.test.y.value = 0.4

    newGroup = anySet.replaceAttribute(groupAttr, anySet.getEditedAttributeData(groupAttr, {"label": "New"}))
    assert newGroup.label == "New"
    assert newGroup.x.value == 0.3
    assert newGroup.test.y.value == 0.4

    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)
    loadedAttr = loadGraph(graphFile).node(dynamicNode.name).ins.xyz
    assert loadedAttr.x.value == 0.3
    assert loadedAttr.test.y.value == 0.4


def test_edit_anyset_group_keeps_default_values_of_items():
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("DynamicNode")
    srcFloat = srcNode.outs.insertAttribute(srcNode.outs.getNewAttributeData("FloatParam"), 0)
    anySet = dynamicNode.ins

    # An item without any default value does not get its current value as default value
    sizeAttr = anySet.insertAttribute({"name": "size", "label": "Size", "type": "Size2d"}, 0)
    sizeAttr.width.value = 7.0
    newSize = anySet.replaceAttribute(sizeAttr, anySet.getEditedAttributeData(sizeAttr, {"label": "New"}))
    assert newSize.width.value == 7.0
    assert newSize.width.desc.value is None
    assert not newSize.width.isDefault

    # An item with a link does not get the link expression as default value
    groupAttr = anySet.duplicateAttribute(graph.addNewNode("Position").xyz)
    srcFloat.connectTo(groupAttr.x)
    newGroup = anySet.replaceAttributeWithEdges(groupAttr, anySet.getEditedAttributeData(groupAttr, {"label": "New"}))
    assert newGroup.x.desc.value == 0.0
    assert newGroup.x.isLink


def test_edit_anyset_list_keeps_edges_of_elements(tmp_path):
    from meshroom.core.graph import loadGraph

    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("DynamicNode")
    dstNode = graph.addNewNode("DynamicNode")
    anySet = dynamicNode.ins
    elementDesc = {"name": "string", "label": "String", "type": "StringParam", "value": ""}
    listAttr = anySet.insertAttribute({"name": "list", "label": "List", "type": "ListAttribute", "value": [], "elementDesc": elementDesc}, 0)
    listAttr.extend(["a", "b"])
    srcNode.code.connectTo(listAttr.at(0))
    listAttr.at(1).connectTo(dstNode.code)

    newList = anySet.replaceAttributeWithEdges(listAttr, anySet.getEditedAttributeData(listAttr, {"name": "renamed"}))

    def edgeNames(graph):
        return sorted((edge.src.fullName, edge.dst.fullName) for edge in graph.edges.values())

    expected = sorted([
        (srcNode.code.fullName, f"{dynamicNode.name}.ins.renamed[0]"),
        (f"{dynamicNode.name}.ins.renamed[1]", dstNode.code.fullName),
    ])
    assert edgeNames(graph) == expected
    assert newList.at(0).inputLink is srcNode.code
    assert dstNode.code.inputLink is newList.at(1)

    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)
    assert edgeNames(loadGraph(graphFile)) == expected


def test_edit_anyset_attribute_rejects_invalid_ranges():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    intAttr = anySet.insertAttribute(anySet.getNewAttributeData("IntParam"), 0)

    for valueRange in ([10, 0, 1], [5, 5, 1], [0, 10, 0], [0, 10]):
        try:
            anySet.getEditedAttributeData(intAttr, {"range": valueRange})
        except ValueError:
            pass
        else:
            raise AssertionError(f"The range {valueRange} should be rejected.")

    assert anySet.getEditedAttributeData(intAttr, {"range": []})


def test_edit_anyset_attribute_without_changes_keeps_same_data():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    for attributeType, defaultValue, otherParameters in [
        ("StringParam", "", {}),
        ("IntParam", 0, {"range": [0, 10, 1]}),
        ("FloatParam", 0.5, {"range": [0.0, 1.0, 0.01]}),
        ("ChoiceParam", "optionA", {"values": ["optionA", "optionB"]}),
    ]:
        attribute = anySet.insertAttribute(anySet.getNewAttributeData(attributeType), 0)
        # The parameters sent by the edition form
        parameters = {"name": attribute.name, "label": attribute.label, "description": "", "advanced": False,
                      "defaultValue": defaultValue, **otherParameters}
        assert anySet.getEditedAttributeData(attribute, parameters) == attribute.asDict()

    # Also when the value differs from the default value
    anySet.int.value = 5
    parameters = {"name": "int", "label": anySet.int.label, "defaultValue": 0, "range": [0, 10, 1]}
    assert anySet.getEditedAttributeData(anySet.int, parameters) == anySet.int.asDict()

    # A number without a range, e.g. copied from a node attribute declared without one
    noRange = anySet.insertAttribute({"name": "noRange", "label": "No Range", "type": "IntParam", "value": 3}, 0)
    parameters = {"name": "noRange", "label": "No Range", "description": "", "advanced": False,
                  "defaultValue": 3, "range": []}
    assert anySet.getEditedAttributeData(noRange, parameters) == noRange.asDict()


@pytest.mark.parametrize("attributeDesc", [
    desc.FloatParam(name="child", label="Child", description="", value=1.0, keyable=True, keyType="viewId"),
    desc.Point2d(name="child", label="Child", description=""),
    desc.Point2d(name="child", label="Child", description="", keyable=True, keyType="viewId"),
    desc.Line2d(name="child", label="Child", description=""),
    desc.Rectangle(name="child", label="Child", description=""),
    desc.Circle(name="child", label="Child", description=""),
    desc.ShapeList(shape=desc.Point2d(name="point", label="Point", description=""), name="child", label="Child", description=""),
    desc.ShapeList(shape=desc.Point2d(name="point", label="Point", description="", keyable=True, keyType="viewId"), name="child", label="Child", description=""),
])
def test_anyset_shape_and_keyable_children_can_be_edited_and_loaded(attributeDesc, tmp_path):
    from meshroom.core.graph import loadGraph

    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    child = attributeFactory(attributeDesc.clone(), None, False, dynamicNode, root=anySet)
    anySet.value.insert(0, child)

    expected = {**child.asDict(), "label": "Edited"}

    edited = anySet.replaceAttribute(child, anySet.getEditedAttributeData(child, {"label": "Edited"}))
    assert edited.asDict() == expected

    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)
    assert loadGraph(graphFile).node(dynamicNode.name).ins.child.asDict() == expected


def test_edit_default_value_of_keyable_anyset_child_keeps_it_keyable():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    attributeDesc = desc.FloatParam(name="child", label="Child", description="", value=1.0, keyable=True, keyType="viewId")
    child = attributeFactory(attributeDesc, None, False, dynamicNode, root=anySet)
    anySet.value.insert(0, child)

    edited = anySet.replaceAttribute(child, anySet.getEditedAttributeData(child, {"defaultValue": 2.0}))
    assert edited.keyable
    assert edited.desc.value == 2.0


def test_edit_anyset_attribute_ignores_default_value_that_is_not_editable():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins

    def addChild(attributeDesc):
        child = attributeFactory(attributeDesc, None, False, dynamicNode, root=anySet)
        anySet.value.insert(anySet.value.count, child)
        return child

    computedDefault = addChild(desc.IntParam(name="computed", label="Computed", description="", value=lambda attr: 3))
    noDefault = addChild(desc.FloatParam(name="noDefault", label="No Default", description="", value=None))

    newAttr = anySet.replaceAttribute(computedDefault, anySet.getEditedAttributeData(computedDefault, {"label": "New", "defaultValue": -1}))
    assert newAttr.label == "New"
    assert newAttr.value == 3

    newAttr = anySet.replaceAttribute(noDefault, anySet.getEditedAttributeData(noDefault, {"label": "New", "defaultValue": float("nan")}))
    assert newAttr.label == "New"
    assert newAttr.value == 0.0


def test_edit_anyset_attribute_keeps_value_from_before_the_link():
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("DynamicNode")
    srcFloat = srcNode.outs.insertAttribute(srcNode.outs.getNewAttributeData("FloatParam"), 0)
    anySet = dynamicNode.ins

    intAttr = anySet.insertAttribute(anySet.getNewAttributeData("IntParam"), 0)
    intAttr.value = 7
    srcInt = srcNode.outs.insertAttribute(srcNode.outs.getNewAttributeData("IntParam"), 1)
    srcInt.connectTo(intAttr)
    groupAttr = anySet.duplicateAttribute(graph.addNewNode("Position").xyz)
    groupAttr.x.value = 0.3
    srcFloat.connectTo(groupAttr.x)

    newInt = anySet.replaceAttributeWithEdges(intAttr, anySet.getEditedAttributeData(intAttr, {"label": "New"}))
    newGroup = anySet.replaceAttributeWithEdges(groupAttr, anySet.getEditedAttributeData(groupAttr, {"label": "New"}))
    assert newInt.isLink
    assert newGroup.x.isLink

    graph.removeEdge(newInt)
    graph.removeEdge(newGroup.x)
    assert newInt.value == 7
    assert newGroup.x.value == 0.3


def test_edit_anyset_attribute_keeps_link_of_whole_group():
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("Position")
    anySet = dynamicNode.ins
    groupAttr = anySet.duplicateAttribute(srcNode.xyz)
    srcNode.xyz.connectTo(groupAttr)

    newGroup = anySet.replaceAttributeWithEdges(groupAttr, anySet.getEditedAttributeData(groupAttr, {"label": "New"}))
    assert newGroup.inputLink is srcNode.xyz
    assert [item.name for item in newGroup.value] == ["x", "y", "z"]


def test_edit_anyset_linked_list_stays_disconnected():
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("DynamicNode")
    elementDesc = {"name": "string", "label": "String", "type": "StringParam", "value": ""}
    listData = {"label": "List", "type": "ListAttribute", "value": [], "elementDesc": elementDesc}
    srcList = srcNode.ins.insertAttribute({"name": "src", **listData}, 0)
    srcList.extend(["a", "b"])
    linkedList = dynamicNode.ins.insertAttribute({"name": "linked", **listData}, 0)
    srcList.connectTo(linkedList)

    editedList = dynamicNode.ins.replaceAttributeWithEdges(
        linkedList, dynamicNode.ins.getEditedAttributeData(linkedList, {"label": "Edited"}))
    assert editedList.inputLink is srcList

    graph.removeEdge(editedList)
    editedList.append("c")

    assert not editedList.isLink
    assert len(graph.edges) == 0
    assert [element.value for element in editedList.value] == ["c"]


def test_connected_edge_names_include_list_elements():
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("DynamicNode")
    dstNode = graph.addNewNode("DynamicNode")
    elementDesc = {"name": "string", "label": "String", "type": "StringParam", "value": ""}
    listAttr = dynamicNode.ins.insertAttribute({"name": "list", "label": "List", "type": "ListAttribute", "value": [], "elementDesc": elementDesc}, 0)
    listAttr.extend(["a", "b"])
    srcNode.code.connectTo(listAttr.at(0))
    listAttr.at(1).connectTo(dstNode.code)

    assert sorted(dynamicNode.ins.connectedEdgeNames(listAttr)) == sorted([
        (srcNode.code.fullName, listAttr.at(0).fullName),
        (listAttr.at(1).fullName, dstNode.code.fullName),
    ])


def test_changing_anyset_children_changes_node_uid():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    seenUids = [dynamicNode._uid]

    def assertUidChanged():
        assert dynamicNode._uid not in seenUids
        seenUids.append(dynamicNode._uid)

    child = anySet.insertAttribute(anySet.getNewAttributeData("IntParam"), 0)
    assertUidChanged()

    child.value = 5
    assertUidChanged()

    child = anySet.replaceAttributeWithEdges(child, anySet.getEditedAttributeData(child, {"name": "renamed"}))
    assertUidChanged()

    anySet.removeAttribute(child)
    assert dynamicNode._uid == seenUids[0]


def test_nodes_with_different_anyset_values_have_different_uids():
    graph, node1 = initGraphAndNode()
    node2 = graph.addNewNode("DynamicNode")
    child1 = node1.ins.insertAttribute(node1.ins.getNewAttributeData("IntParam"), 0)
    child2 = node2.ins.insertAttribute(node2.ins.getNewAttributeData("IntParam"), 0)
    assert node1._uid == node2._uid

    child1.value = 1
    child2.value = 9
    assert node1._uid != node2._uid


def test_dynamic_inputs_serialized_in_todict():
    """Dynamic inputs are included in the node's serialized form."""

    graph, dynamicNode = initGraphAndNode()

    lsNode = graph.addNewNode("Ls", input="/fakeDirectory")
    lsNode2 = graph.addNewNode("Ls", input="/fakeDirectory2")
    lsNode3 = graph.addNewNode("Ls", input="/fakeDirectory3")
    colorNode = graph.addNewNode("Color")

    dynamicNode.ins.duplicateAttribute(lsNode.input)
    dynamicNode.ins.duplicateAttribute(colorNode.rgb)
    dynamicNode.outs.duplicateAttribute(lsNode2.input, isOutput=True)

    dynamicNode.ins.input.value = "/somePath"

    assert isinstance(dynamicNode.outs.input, Attribute)
    dynamicNode.outs.input.connectTo(lsNode3.input)

    nodeDict = dynamicNode.toDict()
    dynInputs = nodeDict.get('inputs', {}).get('ins')

    inputAttribute = anyset_child(dynInputs, "input")
    assert inputAttribute.get('name') == 'input'
    assert inputAttribute.get('label') == 'Input'
    assert inputAttribute.get('type') == 'File'
    assert inputAttribute.get('value') == '/somePath'

    dynOutputs = nodeDict.get('outputs', {}).get('outs')

    outputAttribute = anyset_child(dynOutputs, "input")
    assert outputAttribute.get('name') == 'input'
    assert outputAttribute.get('label') == 'Input'
    assert outputAttribute.get('type') == 'File'
    assert outputAttribute.get('value') == ''

    assert lsNode3.toDict().get('inputs').get('input') == '{DynamicNode_1.outs.input}'  # Check for connection

def test_dynamic_inputs_restored_after_load(tmp_path):
    """Dynamic inputs survive a graph save/load cycle."""

    graph, dynamicNode = initGraphAndNode()

    lsNode = graph.addNewNode("Ls", input="/fakeDirectory")
    lsNode2 = graph.addNewNode("Ls", input="/fakeDirectory2")
    lsNode3 = graph.addNewNode("Ls", input="/fakeDirectory3")
    colorNode = graph.addNewNode("Color")

    dynamicNode.ins.duplicateAttribute(lsNode.input)
    dynamicNode.ins.duplicateAttribute(colorNode.rgb)
    dynamicNode.outs.duplicateAttribute(lsNode2.input, isOutput=True)
    dynamicNode.outs.input.connectTo(lsNode3.input)

    dynamicNode.ins.input.value = "/somePath"

    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)

    # Reload
    loadedGraph = loadGraph(graphFile)
    loadedDstNode = loadedGraph.node(dynamicNode.name)

    assert loadedDstNode.ins.input.value == "/somePath"
    assert loadedDstNode.outs.input is not None
    assert lsNode3.input.isLink, "Dynamic output should still be connected after load"


def test_moved_anyset_attribute_order_restored_after_load(tmp_path):
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("Ls", input="/fakeDirectory")

    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)
    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)
    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)

    initialOrder = [attribute.name for attribute in dynamicNode.ins.value]
    attributeToMove = list(dynamicNode.ins.value)[-1]
    dynamicNode.ins.moveAttribute(attributeToMove, 0)
    movedOrder = [attribute.name for attribute in dynamicNode.ins.value]

    assert movedOrder == [initialOrder[-1], *initialOrder[:-1]]

    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)

    serializedIns = graph.serialize()["graph"][dynamicNode.name]["inputs"]["ins"]
    assert [attribute["name"] for attribute in anyset_children(serializedIns)] == movedOrder

    loadedGraph = loadGraph(graphFile)
    loadedDynamicNode = loadedGraph.node(dynamicNode.name)

    assert [attribute.name for attribute in loadedDynamicNode.ins.value] == movedOrder


def test_anyset_expanded_state_restored_after_load(tmp_path):
    graph, dynamicNode = initGraphAndNode()
    dynamicNode.ins.expanded = True
    dynamicNode.outs.expanded = False

    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)

    serializedNode = graph.serialize()["graph"][dynamicNode.name]
    assert serializedNode["inputs"]["ins"]["expanded"] is True
    assert serializedNode["outputs"]["outs"]["expanded"] is False

    loadedGraph = loadGraph(graphFile)
    loadedDynamicNode = loadedGraph.node(dynamicNode.name)

    assert loadedDynamicNode.ins.expanded is True
    assert loadedDynamicNode.outs.expanded is False


def test_legacy_dict_anyset_serialization_still_loads(tmp_path):
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("Ls", input="/fakeDirectory")

    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)
    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)

    graphData = graph.serialize()
    serializedIns = graphData["graph"][dynamicNode.name]["inputs"]["ins"]
    graphData["graph"][dynamicNode.name]["inputs"]["ins"] = {
        attribute["name"]: attribute for attribute in anyset_children(serializedIns)
    }

    graphFile = tmp_path / "legacy_dict_anyset.mg"
    graphFile.write_text(json.dumps(graphData), encoding="utf-8")

    loadedGraph = loadGraph(str(graphFile))
    loadedDynamicNode = loadedGraph.node(dynamicNode.name)

    assert [attribute.name for attribute in loadedDynamicNode.ins.value] == [
        attribute["name"] for attribute in anyset_children(serializedIns)
    ]


def test_legacy_list_anyset_serialization_still_loads(tmp_path):
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("Ls", input="/fakeDirectory")

    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)
    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)

    graphData = graph.serialize()
    serializedIns = graphData["graph"][dynamicNode.name]["inputs"]["ins"]
    graphData["graph"][dynamicNode.name]["inputs"]["ins"] = anyset_children(serializedIns)

    graphFile = tmp_path / "legacy_list_anyset.mg"
    graphFile.write_text(json.dumps(graphData), encoding="utf-8")

    loadedGraph = loadGraph(str(graphFile))
    loadedDynamicNode = loadedGraph.node(dynamicNode.name)

    assert [attribute.name for attribute in loadedDynamicNode.ins.value] == [
        attribute["name"] for attribute in anyset_children(serializedIns)
    ]


def test_legacy_group_anyset_child_with_value_still_loads(tmp_path):
    """GroupAttribute children used to be serialized with both their items and their value."""
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("AllAttributesNode")

    groupAttr = dynamicNode.ins.duplicateAttribute(srcNode.paramGroup, isOutput=False)
    groupAttr.value.get("groupInt").value = 12

    graphData = graph.serialize()
    serializedGroup = anyset_child(graphData["graph"][dynamicNode.name]["inputs"]["ins"], groupAttr.name)
    assert "value" not in serializedGroup
    serializedGroup["value"] = groupAttr.getSerializedValue()

    graphFile = tmp_path / "legacy_group_anyset.mg"
    graphFile.write_text(json.dumps(graphData), encoding="utf-8")

    loadedGraph = loadGraph(str(graphFile))
    loadedGroup = loadedGraph.node(dynamicNode.name).ins.value.get(groupAttr.name)

    assert loadedGroup.desc.type == "GroupAttribute"
    assert [attribute.name for attribute in loadedGroup.value] == [attribute.name for attribute in groupAttr.value]
    assert loadedGroup.value.get("groupInt").value == 12


class AnySetWithInitialChildrenNode(desc.Node):
    """Node whose AnySet description declares initial children, with non-falsy default values."""
    inputs = [
        desc.AnySet(name="ins", label="Inputs", description="", items=[
            desc.BoolParam(name="flag", label="Flag", description="", value=True),
            desc.IntParam(name="count", label="Count", description="", value=5, range=(0, 10, 1)),
            desc.FloatParam(name="ratio", label="Ratio", description="", value=0.5, range=(0.0, 1.0, 0.1)),
            desc.StringParam(name="text", label="Text", description="", value="default"),
            desc.ChoiceParam(name="choices", label="Choices", description="", value=["a"], values=["a", "b"],
                             exclusive=False),
        ])
    ]
    outputs = []


@pytest.mark.parametrize("template", [False, True], ids=["project", "template"])
@pytest.mark.parametrize("childName,value", [("flag", False), ("count", 0), ("ratio", 0.0), ("text", ""), ("choices", [])])
def test_initial_anyset_child_falsy_value_restored_after_load(tmp_path, childName, value, template):
    """A falsy value set on an initial child of an AnySet description is restored when loading the graph."""
    with registeredNodeTypes([AnySetWithInitialChildrenNode]):
        graph = Graph("test")
        node = graph.addNewNode("AnySetWithInitialChildrenNode")
        node.ins.childAttribute(childName).value = value
        graphFile = str(tmp_path / "graph.mg")
        graph.save(graphFile, template=template)

        loadedNode = loadGraph(graphFile).node(node.name)

        assert not isinstance(loadedNode, CompatibilityNode), loadedNode.issueDetails
        assert loadedNode.ins.childAttribute(childName).getPrimitiveValue() == value
        assert loadedNode._uid == node._uid


def test_clone_attributes():
    graph = Graph("test")
    node = graph.addNewNode("AllAttributesNode")

    for attribute in node.attributes:
        assert(attribute.desc.clone() is not None)  # Check clone doesn't raise


# ---------------------------------------------------------------------------
# UID tests
# ---------------------------------------------------------------------------

def test_anyset_input_contributes_to_node_uid():
    """An input AnySet is an invalidating attribute: changing a child value changes the node UID."""
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("AllAttributesNode")

    dynamicNode.ins.duplicateAttribute(srcNode.intParam)
    graph.update()

    assert dynamicNode.ins in dynamicNode.invalidatingAttributes

    uidBefore = dynamicNode._uid
    dynamicNode.ins.intParam.value = 42
    assert dynamicNode._uid != uidBefore


def test_anyset_children_order_does_not_contribute_to_node_uid():
    """Nodes holding the same AnySet children in different orders have the same UID."""
    graph = Graph("test")
    srcNode = graph.addNewNode("AllAttributesNode")
    firstNode = graph.addNewNode("DynamicNode")
    secondNode = graph.addNewNode("DynamicNode")

    for node, sourceAttributes in ((firstNode, (srcNode.intParam, srcNode.floatParam, srcNode.stringParam)),
                                   (secondNode, (srcNode.stringParam, srcNode.floatParam, srcNode.intParam))):
        for sourceAttribute in sourceAttributes:
            node.ins.duplicateAttribute(sourceAttribute)
        node.ins.intParam.value = 1
        node.ins.floatParam.value = 2.0
    graph.update()

    assert [child.name for child in firstNode.ins.value] != [child.name for child in secondNode.ins.value]
    assert firstNode.ins.uid() == secondNode.ins.uid()
    assert firstNode._uid == secondNode._uid

    # The values are still bound to the names: swapping them changes the UID
    secondNode.ins.intParam.value = 2
    secondNode.ins.floatParam.value = 1.0
    assert firstNode._uid != secondNode._uid


def test_anyset_uid_depends_on_children_types():
    """AnySets with children of different types but with the same name and string representation have different UIDs."""
    graph = Graph("test")
    srcNode = graph.addNewNode("AllAttributesNode")
    intNode = graph.addNewNode("DynamicNode")
    stringNode = graph.addNewNode("DynamicNode")

    intNode.ins.duplicateAttribute(srcNode.intParam)
    intNode.ins.replaceAttributeWithEdges(intNode.ins.intParam, intNode.ins.getEditedAttributeData(intNode.ins.intParam, {"name": "param", "label": "Param"}))
    intNode.ins.param.value = 5
    stringNode.ins.duplicateAttribute(srcNode.stringParam)
    stringNode.ins.replaceAttributeWithEdges(stringNode.ins.stringParam, stringNode.ins.getEditedAttributeData(stringNode.ins.stringParam, {"name": "param", "label": "Param"}))
    stringNode.ins.param.value = "5"

    assert intNode.ins.uid() != stringNode.ins.uid()


def compoundChildrenWithDifferentStructures():
    """
    Return pairs of compound child descriptions with the same name and the same value,
    but with a different structure (types or names of their descendants).
    """
    def intParam(name):
        return desc.IntParam(name=name, label=name, description="", value=1, range=(0, 100, 1))

    def floatParam(name):
        return desc.FloatParam(name=name, label=name, description="", value=1.0, range=(0.0, 100.0, 1.0))

    def listOf(elementDesc):
        return desc.ListAttribute(name="param", label="param", description="", elementDesc=elementDesc)

    def groupOf(items, name="param"):
        return desc.GroupAttribute(name=name, label=name, description="", items=items)

    return [
        # Empty lists, whose elements have different types
        (listOf(intParam("element")), listOf(floatParam("element"))),
        # Groups whose items have different names but the same values
        (groupOf([intParam("a")]), groupOf([intParam("b")])),
        # Groups whose items have different types but the same values
        (groupOf([intParam("a")]), groupOf([floatParam("a")])),
        # Empty lists of groups, whose items have different names
        (listOf(groupOf([intParam("a")], "group")), listOf(groupOf([intParam("b")], "group"))),
        # Groups holding empty lists, whose elements have different types
        (groupOf([desc.ListAttribute(name="list", label="list", description="", elementDesc=intParam("element"))]),
         groupOf([desc.ListAttribute(name="list", label="list", description="", elementDesc=floatParam("element"))])),
    ]


COMPOUND_CHILDREN_WITH_DIFFERENT_STRUCTURES = compoundChildrenWithDifferentStructures()


@pytest.mark.parametrize("firstDesc,secondDesc", COMPOUND_CHILDREN_WITH_DIFFERENT_STRUCTURES,
                         ids=["emptyListElementType", "groupItemName", "groupItemType", "emptyListOfGroupsItemName",
                              "groupOfEmptyListElementType"])
def test_anyset_uid_depends_on_compound_children_structure(firstDesc, secondDesc):
    """
    AnySets with compound children (groups, lists) of the same name and value, but with a different structure
    (types or names of their descendants), have different UIDs.
    """
    graph = Graph("test")
    firstNode = graph.addNewNode("DynamicNode")
    secondNode = graph.addNewNode("DynamicNode")
    firstNode.ins.duplicateAttribute(SimpleNamespace(desc=firstDesc))
    secondNode.ins.duplicateAttribute(SimpleNamespace(desc=secondDesc))
    graph.update()

    def valuesOnly(value):
        """Return the values held by 'value', without the names of the group items."""
        if isinstance(value, dict):
            return [valuesOnly(itemValue) for itemValue in value.values()]
        if isinstance(value, list):
            return [valuesOnly(elementValue) for elementValue in value]
        return value

    assert valuesOnly(firstNode.ins.param.getPrimitiveValue()) == valuesOnly(secondNode.ins.param.getPrimitiveValue())
    assert firstNode.ins.uid() != secondNode.ins.uid()
    assert firstNode._uid != secondNode._uid


def descWithFlag(attributeDesc, flagName, value):
    """
    Return a clone of 'attributeDesc' with the private flag 'flagName' set to 'value' on the clone
    and on all its descendants (group items, list elements), without modifying 'attributeDesc'.
    """
    clone = attributeDesc.clone()
    setattr(clone, flagName, value)
    # Recursively set the flag on independent clones of the descendant descriptions
    if isinstance(clone, desc.ListAttribute):
        clone._elementDesc = descWithFlag(clone.elementDesc, flagName, value)
    elif isinstance(clone, desc.GroupAttribute):
        clone._items = [descWithFlag(item, flagName, value) for item in clone.items]
    return clone


def assertDescInvalidatingAndEnabled(attributeDesc):
    """
    Assert that 'attributeDesc' and all its descendant descriptions (group items, list elements) are invalidating and enabled.
    The private flags are checked, as the public 'invalidate' of a group or a list is derived from its descendants:
    the own invalidate flag of a group or a list is not relevant (their constructors set it to False), so it is not checked.
    """
    if not isinstance(attributeDesc, (desc.ListAttribute, desc.GroupAttribute)):
        assert attributeDesc._invalidate is True, attributeDesc.name
    assert attributeDesc._enabled is True, attributeDesc.name
    if isinstance(attributeDesc, desc.ListAttribute):
        assertDescInvalidatingAndEnabled(attributeDesc.elementDesc)
    elif isinstance(attributeDesc, desc.GroupAttribute):
        for item in attributeDesc.items:
            assertDescInvalidatingAndEnabled(item)


def assertInvalidatingAndEnabled(attribute):
    """Assert that the live 'attribute', its description and all its descendants are invalidating and enabled."""
    assertDescInvalidatingAndEnabled(attribute.desc)
    assert attribute.invalidate and attribute.enabled, attribute.fullName
    if isinstance(attribute, AnySet) or isinstance(attribute.desc, desc.ListAttribute):
        children = list(attribute.value)
    elif isinstance(attribute.desc, desc.GroupAttribute):
        children = list(attribute.value.values())
    else:
        children = []
    for child in children:
        assertInvalidatingAndEnabled(child)


def test_anyset_structural_changes_update_node_uid():
    """Adding, renaming and removing AnySet children updates the node UID without an explicit update, but moving them does not."""
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("AllAttributesNode")

    uidBefore = dynamicNode._uid
    dynamicNode.ins.duplicateAttribute(srcNode.intParam)
    assert dynamicNode._uid != uidBefore, "Adding a child should update the node UID"

    dynamicNode.ins.duplicateAttribute(srcNode.floatParam)
    assert [attribute.name for attribute in dynamicNode.ins.value] == ["intParam", "floatParam"]

    uidBefore = dynamicNode._uid
    dynamicNode.ins.replaceAttributeWithEdges(dynamicNode.ins.intParam, dynamicNode.ins.getEditedAttributeData(dynamicNode.ins.intParam, {"name": "renamedParam", "label": "Renamed Param"}))
    assert dynamicNode._uid != uidBefore, "Renaming a child should update the node UID"

    uidBefore = dynamicNode._uid
    dynamicNode.ins.moveAttribute(dynamicNode.ins.floatParam, 0)
    assert [attribute.name for attribute in dynamicNode.ins.value] == ["floatParam", "renamedParam"]
    assert dynamicNode._uid == uidBefore, "Moving a child should not update the node UID"

    uidBefore = dynamicNode._uid
    dynamicNode.ins.removeAttribute(dynamicNode.ins.floatParam)
    assert dynamicNode._uid != uidBefore, "Removing a child should update the node UID"


# ---------------------------------------------------------------------------
# Children types save/load tests
# ---------------------------------------------------------------------------

# AnySet children types, along with a non-default value to set on each of them.
ANYSET_CHILDREN = [
    (desc.StringParam(name="stringChild", label="String Child", description="", value="defaultString"),
     "someString"),
    (desc.IntParam(name="intChild", label="Int Child", description="", value=1, range=(0, 100, 1)),
     42),
    (desc.FloatParam(name="floatChild", label="Float Child", description="", value=0.5, range=(0.0, 10.0, 0.1)),
     3.25),
    (desc.BoolParam(name="boolChild", label="Bool Child", description="", value=False),
     True),
    (desc.ChoiceParam(name="exclusiveChoiceChild", label="Exclusive Choice Child", description="", value="a",
                      values=["a", "b", "c"], exclusive=True),
     "b"),
    (desc.ChoiceParam(name="multiChoiceChild", label="Multi Choice Child", description="", value=["a"],
                      values=["a", "b", "c"], exclusive=False),
     ["b", "c"]),
    (desc.File(name="fileChild", label="File Child", description="", value="/default/path"),
     "/some/other/path"),
    (desc.ColorParam(name="colorChild", label="Color Child", description="", value="#000000"),
     "#ff8000"),
    (desc.GroupAttribute(name="groupChild", label="Group Child", description="", items=[
        desc.IntParam(name="groupInt", label="Group Int", description="", value=1, range=(0, 100, 1)),
        desc.ChoiceParam(name="groupChoice", label="Group Choice", description="", value="a",
                         values=["a", "b", "c"], exclusive=True),
     ]),
     {"groupInt": 42, "groupChoice": "b"}),
    (desc.ListAttribute(name="listChild", label="List Child", description="",
                        elementDesc=desc.FloatParam(name="listFloat", label="List Float", description="", value=0.5,
                                                    range=(0.0, 10.0, 0.1))),
     [1.5, 3.25]),
    # Deeper nesting: a list of groups, each holding a list
    (desc.ListAttribute(name="listOfGroupsChild", label="List Of Groups Child", description="",
                        elementDesc=desc.GroupAttribute(name="nestedGroup", label="Nested Group", description="", items=[
                            desc.IntParam(name="nestedInt", label="Nested Int", description="", value=1, range=(0, 100, 1)),
                            desc.ListAttribute(name="nestedList", label="Nested List", description="",
                                               elementDesc=desc.IntParam(name="nestedListInt", label="Nested List Int",
                                                                         description="", value=0, range=(0, 100, 1))),
                        ])),
     [{"nestedInt": 3, "nestedList": [4, 5]}, {"nestedInt": 6, "nestedList": [7]}]),
    (desc.AnySet(name="anySetChild", label="AnySet Child", description="", items=[
        desc.StringParam(name="anySetString", label="AnySet String", description="", value="defaultString"),
     ]),
     None),
]
ANYSET_CHILDREN_IDS = [attributeDesc.name for attributeDesc, _ in ANYSET_CHILDREN]


def descSpecificArgs(attributeDesc):
    """
    Return the description arguments specific to the type of 'attributeDesc': choices, ranges,
    and recursively the descriptions of the items of a group or of the elements of a list.
    The items of an AnySet description are only its initial children: its actual children are compared through its value.
    """
    if isinstance(attributeDesc, desc.AnySet):
        return {}
    if isinstance(attributeDesc, desc.ChoiceParam):
        return {"values": list(attributeDesc.values), "exclusive": attributeDesc.exclusive}
    if isinstance(attributeDesc, (desc.IntParam, desc.FloatParam)):
        return {"range": list(attributeDesc.range)}
    if isinstance(attributeDesc, desc.ListAttribute):
        elementDesc = attributeDesc.elementDesc
        return {"elementDesc": (elementDesc.name, elementDesc.type, descSpecificArgs(elementDesc))}
    if isinstance(attributeDesc, desc.GroupAttribute):
        return {"items": [(item.name, item.type, descSpecificArgs(item)) for item in attributeDesc.items]}
    return {}


def childState(child, withLabel=True):
    """Return the name, (label,) type, type-specific description arguments and primitive value of an AnySet child."""
    state = (child.name, child.desc.type, descSpecificArgs(child.desc), child.getPrimitiveValue())
    return (child.name, child.label) + state[1:] if withLabel else state


def addAnySetChild(anySet, attributeDesc):
    """
    Add a child to 'anySet' from the given description, through the same duplication path as the UI.

    Args:
        anySet: the AnySet attribute to add the child to.
        attributeDesc: the description of the child to create.

    Returns:
        Attribute: the created child.
    """
    # duplicateAttribute only relies on the description of the source attribute
    return anySet.duplicateAttribute(SimpleNamespace(desc=attributeDesc))


def assertGraphRoundTrip(tmp_path, graph, node, getState, template=False):
    """
    Save 'graph', reload it twice (load, then save and reload the loaded graph) and check that 'node' is not loaded
    as a CompatibilityNode and that its state and its UID are preserved.

    Args:
        tmp_path: directory in which the graph files are saved.
        graph: the graph to save.
        node: the node to check in the loaded graphs.
        getState: function returning the state of a node to compare with the loaded one.
        template: whether to save the graph as a template.
    """
    expectedState = getState(node)
    expectedUid = node._uid
    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile, template=template)

    for _ in range(2):
        loadedGraph = loadGraph(graphFile)
        loadedNode = loadedGraph.node(node.name)

        assert not isinstance(loadedNode, CompatibilityNode), loadedNode.issueDetails
        assert getState(loadedNode) == expectedState
        assert loadedNode._uid == expectedUid

        # Save the loaded graph to check the next iteration against a resaved file
        graphFile = str(tmp_path / "resaved_graph.mg")
        loadedGraph.save(graphFile, template=template)


def assertAnySetNodeRoundTrip(tmp_path, children, template=False):
    """
    Create a DynamicNode whose input AnySet holds the given children, save the graph, reload it twice
    (load, then save and reload the loaded graph) and check that the node, its children and its UID are preserved.

    Args:
        tmp_path: directory in which the graph files are saved.
        children: list of (description, value) for the children to create; a None value keeps the default one.
        template: whether to save the graph as a template, which does not keep the labels of the children.
    """
    graph, dynamicNode = initGraphAndNode()
    for attributeDesc, value in children:
        child = addAnySetChild(dynamicNode.ins, attributeDesc)
        if value is not None:
            child.value = value
    graph.update()

    # The type-specific description arguments (choices, ranges, items, elements) are kept when duplicating the child
    assert {child.name: descSpecificArgs(child.desc) for child in dynamicNode.ins.value} == \
        {attributeDesc.name: descSpecificArgs(attributeDesc) for attributeDesc, _ in children}
    assert len(dynamicNode.ins.value) == len(children)

    assertGraphRoundTrip(tmp_path, graph, dynamicNode,
                         lambda node: ([childState(child, withLabel=not template) for child in node.ins.value],
                                       node.ins.uid()),
                         template=template)


@pytest.mark.parametrize("attributeDesc,value", ANYSET_CHILDREN, ids=ANYSET_CHILDREN_IDS)
def test_anyset_child_type_save_load_preserves_uid(tmp_path, attributeDesc, value):
    """An AnySet child of each type keeps its type, value and the node UID across save/load cycles."""
    assertAnySetNodeRoundTrip(tmp_path, [(attributeDesc, value)])


@pytest.mark.parametrize("attributeDesc", [attributeDesc for attributeDesc, _ in ANYSET_CHILDREN], ids=ANYSET_CHILDREN_IDS)
def test_anyset_child_type_default_value_save_load_preserves_uid(tmp_path, attributeDesc):
    """An AnySet child of each type left at its default value is preserved across save/load cycles."""
    assertAnySetNodeRoundTrip(tmp_path, [(attributeDesc, None)])


def test_anyset_all_child_types_save_load_preserves_uid(tmp_path):
    """An AnySet holding children of all the types is preserved across save/load cycles."""
    assertAnySetNodeRoundTrip(tmp_path, ANYSET_CHILDREN)


def test_anyset_all_child_types_template_save_load(tmp_path):
    """
    An AnySet holding children of all the types is preserved when saved as a template,
    and when saving the loaded template again.
    """
    assertAnySetNodeRoundTrip(tmp_path, ANYSET_CHILDREN, template=True)


@pytest.mark.parametrize("attributeDesc", [attributeDesc for attributeDesc, _ in ANYSET_CHILDREN], ids=ANYSET_CHILDREN_IDS)
def test_child_type_desc_clone_keeps_type_specific_args(attributeDesc):
    """
    Cloning a description keeps the arguments specific to its type (choices of a ChoiceParam, range of a numeric parameter,
    items of a group, element of a list), with independent copies of the descendant descriptions.
    """
    clone = attributeDesc.clone()
    assert descSpecificArgs(clone) == descSpecificArgs(attributeDesc)
    if isinstance(attributeDesc, desc.ChoiceParam):
        assert clone.values == attributeDesc.values and clone.values is not attributeDesc.values
        assert clone.exclusive == attributeDesc.exclusive
    elif isinstance(attributeDesc, (desc.IntParam, desc.FloatParam)):
        assert list(clone.range) == list(attributeDesc.range) and clone.range
    elif isinstance(attributeDesc, desc.ListAttribute):
        assert clone.elementDesc is not attributeDesc.elementDesc
    elif isinstance(attributeDesc, desc.GroupAttribute):
        assert all(cloneItem is not item for cloneItem, item in zip(clone.items, attributeDesc.items))


def nonInvalidatingDesc(attributeDesc):
    """Return a clone of 'attributeDesc', whose descendants included, that does not invalidate the node UID."""
    return descWithFlag(attributeDesc, "_invalidate", False)


def disabledDesc(attributeDesc, enabled):
    """
    Return a clone of 'attributeDesc', whose descendants included, with the given disabled 'enabled' state
    (False or a callable returning False).
    """
    return descWithFlag(attributeDesc, "_enabled", enabled)


@pytest.mark.parametrize("makeDesc", [nonInvalidatingDesc, lambda d: disabledDesc(d, False),
                                      lambda d: disabledDesc(d, lambda node: False)],
                         ids=["nonInvalidating", "disabled", "disabledByCallable"])
@pytest.mark.parametrize("attributeDesc,value", ANYSET_CHILDREN, ids=ANYSET_CHILDREN_IDS)
def test_anyset_child_duplication_resets_invalidate_and_enabled_flags(attributeDesc, value, makeDesc):
    """
    A child duplicated into an AnySet, its description and all its descendants (group items, list elements)
    are invalidating and enabled, whatever the flags of the source description.
    """
    graph, dynamicNode = initGraphAndNode()
    child = addAnySetChild(dynamicNode.ins, makeDesc(attributeDesc))
    if value is not None:
        child.value = value
    graph.update()
    assertInvalidatingAndEnabled(child)


@pytest.mark.parametrize("makeDesc", [nonInvalidatingDesc, lambda d: disabledDesc(d, False),
                                      lambda d: disabledDesc(d, lambda node: False)],
                         ids=["nonInvalidating", "disabled", "disabledByCallable"])
@pytest.mark.parametrize("attributeDesc,value", ANYSET_CHILDREN, ids=ANYSET_CHILDREN_IDS)
def test_anyset_child_inserted_from_serialized_attribute_save_load_preserves_uid(tmp_path, attributeDesc, value, makeDesc):
    """
    A child inserted into an AnySet from the serialization of an attribute (e.g. when exposing the attributes of a
    scene, or when undoing the removal of a child) is invalidating and enabled, as well as all its descendants,
    whatever the flags of the source attribute description, and is preserved across save/load cycles.
    """
    graph, dynamicNode = initGraphAndNode()
    sourceAttribute = attributeFactory(makeDesc(attributeDesc), value=None, isOutput=False, node=dynamicNode)
    if value is not None:
        sourceAttribute.value = value
    child = dynamicNode.ins.insertAttribute(sourceAttribute.asDict(), dynamicNode.ins.value.count)
    graph.update()
    assertInvalidatingAndEnabled(child)
    assertGraphRoundTrip(tmp_path, graph, dynamicNode, lambda node: [childState(child) for child in node.ins.value])


@pytest.mark.parametrize("attributeDesc,value", ANYSET_CHILDREN, ids=ANYSET_CHILDREN_IDS)
def test_nested_anyset_child_type_save_load_preserves_uid(tmp_path, attributeDesc, value):
    """A child of each type added to an AnySet nested in an AnySet keeps its type, value and the node UID across save/load cycles."""
    graph, dynamicNode = initGraphAndNode()
    nestedAnySet = addAnySetChild(dynamicNode.ins, desc.AnySet(name="nestedAnySet", label="Nested AnySet", description=""))
    child = addAnySetChild(nestedAnySet, attributeDesc)
    if value is not None:
        child.value = value
    graph.update()
    assertGraphRoundTrip(tmp_path, graph, dynamicNode,
                         lambda node: [childState(child) for child in node.ins.nestedAnySet.value])


@pytest.mark.parametrize("attributeDesc,value", ANYSET_CHILDREN, ids=ANYSET_CHILDREN_IDS)
def test_anyset_nested_in_group_child_type_save_load_preserves_uid(tmp_path, attributeDesc, value):
    """
    A child of each type added to an AnySet nested in a group child of an AnySet keeps its type, value and the node UID
    across save/load cycles, and is not serialized as an item of the group.
    """
    graph, dynamicNode = initGraphAndNode()
    group = addAnySetChild(dynamicNode.ins, desc.GroupAttribute(name="group", label="Group", description="", items=[
        desc.IntParam(name="groupInt", label="Group Int", description="", value=1, range=(0, 100, 1)),
        desc.AnySet(name="nestedAnySet", label="Nested AnySet", description="")]))
    group.groupInt.value = 2
    child = addAnySetChild(group.nestedAnySet, attributeDesc)
    if value is not None:
        child.value = value
    graph.update()
    assert [item["name"] for item in group.asDict()["items"]] == ["groupInt", "nestedAnySet"]

    def groupState(node):
        """Return the item names, the int value and the nested AnySet children of the group child of 'node'."""
        group = node.ins.group
        return list(group.value.keys()), group.groupInt.value, [childState(child) for child in group.nestedAnySet.value]

    assert groupState(dynamicNode)[:2] == (["groupInt", "nestedAnySet"], 2)
    assertGraphRoundTrip(tmp_path, graph, dynamicNode, groupState)


# ---------------------------------------------------------------------------
# Shape children tests
# ---------------------------------------------------------------------------

def shapeChildren():
    """
    Return a description of each shape type and of a ShapeList, keyable or not, along with a partial observation
    to set on the shape (or on the first shape of the ShapeList).
    """
    shapeChildren = []
    for keyable in (False, True):
        prefix = "keyable" if keyable else ""
        kwargs = {"label": "", "description": "", "keyable": keyable, "keyType": "viewId" if keyable else None}
        shapeChildren += [
            (desc.Point2d(name=f"{prefix}point2d", **kwargs), {"x": 2.0}),
            (desc.Line2d(name=f"{prefix}line2d", **kwargs), {"a": {"x": 2.0, "y": 2.0}}),
            (desc.Rectangle(name=f"{prefix}rectangle", **kwargs), {"center": {"x": 20.0, "y": 20.0}}),
            (desc.Circle(name=f"{prefix}circle", **kwargs), {"radius": 40.0}),
            (desc.SurveyPoint(name=f"{prefix}surveyPoint", **kwargs), {"X": 2.0}),
            (desc.ShapeList(name=f"{prefix}shapeList", label="", description="",
                            shape=desc.Point2d(name="point2d", **kwargs)), {"x": 2.0}),
        ]
    return shapeChildren


SHAPE_CHILDREN = shapeChildren()
SHAPE_CHILDREN_IDS = [attributeDesc.name for attributeDesc, _ in SHAPE_CHILDREN]


def shapeChildState(child):
    """
    Return the serialization of a shape child, which holds its type, keyable state, key type and value, as a string
    for the NaN values (e.g. SurveyPoint) to be comparable.
    """
    return json.dumps(child.asDict(), sort_keys=True)


@pytest.mark.parametrize("modified", [False, True], ids=["default", "modified"])
@pytest.mark.parametrize("attributeDesc,observation", SHAPE_CHILDREN, ids=SHAPE_CHILDREN_IDS)
def test_anyset_shape_child_save_load_preserves_uid(tmp_path, attributeDesc, observation, modified):
    """
    A shape or a ShapeList child, keyable or not, keeps its type, keyable state, value and the node UID across
    save/load cycles.
    """
    graph, dynamicNode = initGraphAndNode()
    child = addAnySetChild(dynamicNode.ins, attributeDesc)
    if modified:
        shape = child
        if isinstance(attributeDesc, desc.ShapeList):
            child.append({})
            shape = child.at(0)
        shape.childAttribute("userName").value = "someShape"
        shape.geometry.setObservation("0", observation)
    graph.update()
    assertGraphRoundTrip(tmp_path, graph, dynamicNode, lambda node: [shapeChildState(child) for child in node.ins.value])


# ---------------------------------------------------------------------------
# Keyable children tests
# ---------------------------------------------------------------------------

# Keyable parameters, along with a key value to set on them.
KEYABLE_CHILDREN = [
    (desc.IntParam(name="keyableInt", label="Keyable Int", description="", value=1, range=(0, 100, 1),
                   keyable=True, keyType="viewId"),
     42),
    (desc.FloatParam(name="keyableFloat", label="Keyable Float", description="", value=0.5, range=(0.0, 10.0, 0.1),
                     keyable=True, keyType="viewId"),
     3.25),
]
KEYABLE_CHILDREN_IDS = [attributeDesc.name for attributeDesc, _ in KEYABLE_CHILDREN]


class KeyableAttributesNode(desc.Node):
    """Node holding keyable parameters and a keyable shape, to connect to an AnySet."""
    inputs = [attributeDesc for attributeDesc, _ in KEYABLE_CHILDREN] + [
        desc.Rectangle(name="keyableRectangle", label="Keyable Rectangle", description="", keyable=True, keyType="viewId"),
    ]
    outputs = []


KEYABLE_ATTRIBUTE_NAMES = [attributeDesc.name for attributeDesc in KeyableAttributesNode.inputs]


def keyableState(attribute):
    """
    Return the name, type, keyable state, key type and serialized value of a keyable parameter or shape attribute:
    its key values, or its link expression when it is connected.
    """
    geometry = getattr(attribute, "geometry", None)
    keyable = geometry.observationKeyable if geometry is not None else attribute.keyable
    return (attribute.name, attribute.desc.type, keyable, attribute.desc.keyType,
            json.dumps(attribute.getSerializedValue(), sort_keys=True))


def setKey(attribute, value):
    """Set a key on a keyable parameter, or an observation on a keyable shape."""
    if getattr(attribute, "geometry", None) is not None:
        attribute.geometry.setObservation("0", {"center": {"x": 20.0, "y": 20.0}})
    else:
        attribute.keyValues.add("0", value)


@pytest.mark.parametrize("modified", [False, True], ids=["default", "modified"])
@pytest.mark.parametrize("attributeDesc,value", KEYABLE_CHILDREN, ids=KEYABLE_CHILDREN_IDS)
def test_anyset_keyable_child_save_load_preserves_uid(tmp_path, attributeDesc, value, modified):
    """A keyable parameter child keeps its keyable state, its key values and the node UID across save/load cycles."""
    graph, dynamicNode = initGraphAndNode()
    child = addAnySetChild(dynamicNode.ins, attributeDesc)
    assert child.keyable
    if modified:
        setKey(child, value)
    graph.update()
    assertGraphRoundTrip(tmp_path, graph, dynamicNode, lambda node: [keyableState(child) for child in node.ins.value])


@pytest.mark.parametrize("modified", [False, True], ids=["default", "modified"])
@pytest.mark.parametrize("attributeName", KEYABLE_ATTRIBUTE_NAMES)
def test_keyable_attribute_connected_to_input_anyset_save_load_preserves_uid(tmp_path, attributeName, modified):
    """
    A keyable attribute connected to an input AnySet creates a keyable child linked to it, which keeps its keyable
    state, its link and the node UID across save/load cycles.
    """
    with registeredNodeTypes([KeyableAttributesNode]):
        graph, dynamicNode = initGraphAndNode()
        srcAttribute = graph.addNewNode("KeyableAttributesNode").attribute(attributeName)
        if modified:
            setKey(srcAttribute, 42)

        # Same path as the UI connection to an AnySet (see ConnectToAnySetCommand)
        child = dynamicNode.ins.duplicateAttribute(srcAttribute, isOutput=False)
        graph.addEdge(srcAttribute, child)
        graph.update()
        assert child.inputLink is srcAttribute

        assertGraphRoundTrip(tmp_path, graph, dynamicNode, lambda node: [keyableState(child) for child in node.ins.value])


@pytest.mark.parametrize("attributeName", KEYABLE_ATTRIBUTE_NAMES)
def test_output_anyset_connected_to_keyable_attribute_save_load_preserves_uid(tmp_path, attributeName):
    """
    An output AnySet connected to a keyable attribute creates a keyable output child linked to it: both keep
    their keyable state, the link and the UID of the connected node across save/load cycles.
    """
    with registeredNodeTypes([KeyableAttributesNode]):
        graph, dynamicNode = initGraphAndNode()
        dstNode = graph.addNewNode("KeyableAttributesNode")
        dstAttribute = dstNode.attribute(attributeName)

        # Same path as the UI connection from an output AnySet (see ConnectToAnySetCommand)
        child = dynamicNode.outs.duplicateAttribute(dstAttribute, isOutput=True)
        graph.addEdge(child, dstAttribute)
        graph.update()
        assert dstAttribute.inputLink is child

        def state(node):
            """Return the state of the connected keyable attribute of 'node' and of the output AnySet children."""
            return (keyableState(node.attribute(attributeName)),
                    [keyableState(child) for child in node.graph.node(dynamicNode.name).outs.value])

        assertGraphRoundTrip(tmp_path, graph, dstNode, state)


@pytest.mark.parametrize("attributeDesc", [attributeDesc for attributeDesc, _ in ANYSET_CHILDREN + SHAPE_CHILDREN],
                         ids=ANYSET_CHILDREN_IDS + SHAPE_CHILDREN_IDS)
def test_anyset_child_duplication_does_not_modify_source_desc(attributeDesc):
    """
    Duplicating an attribute of each type into an AnySet, shapes and ShapeLists included, does not modify the invalidate
    and enabled flags of the source description or of its descendants (group items, list elements, shape of a ShapeList),
    while the child and its descendants are invalidating and enabled.
    """
    def flags(attributeDesc):
        """Return the invalidate and enabled flags of 'attributeDesc' and of its descendants."""
        children = []
        if isinstance(attributeDesc, desc.ListAttribute):
            children = [attributeDesc.elementDesc]
        elif isinstance(attributeDesc, desc.GroupAttribute):
            children = attributeDesc.items
        return (attributeDesc._invalidate, attributeDesc._enabled, [flags(child) for child in children])

    sourceDesc = disabledDesc(nonInvalidatingDesc(attributeDesc), False)
    expectedFlags = flags(sourceDesc)
    _, dynamicNode = initGraphAndNode()
    child = addAnySetChild(dynamicNode.ins, sourceDesc)
    assert flags(sourceDesc) == expectedFlags
    assertInvalidatingAndEnabled(child)


# ---------------------------------------------------------------------------
# Output AnySet tests
# ---------------------------------------------------------------------------

def intDesc(name):
    """Return an IntParam description named 'name'."""
    return desc.IntParam(name=name, label=name, description="", value=0, range=(0, 100, 1))


def addOutputChild(anySet, attributeDesc):
    """Add an output child to 'anySet' from the given description, through the same duplication path as the UI."""
    return anySet.duplicateAttribute(SimpleNamespace(desc=attributeDesc), isOutput=True)


def test_output_anyset_schema_contributes_to_node_uid():
    """The names and types of the children of an output AnySet contribute to the node UID, but not their order or values."""
    graph, dynamicNode = initGraphAndNode()

    uidBefore = dynamicNode._uid
    addOutputChild(dynamicNode.outs, intDesc("a"))
    assert dynamicNode._uid != uidBefore, "Adding an output child should update the node UID"

    addOutputChild(dynamicNode.outs, intDesc("b"))
    uidBefore = dynamicNode._uid
    dynamicNode.outs.moveAttribute(dynamicNode.outs.a, 1)
    assert dynamicNode._uid == uidBefore, "Moving an output child should not update the node UID"

    dynamicNode.outs.a.value = 42
    graph.update()
    assert dynamicNode._uid == uidBefore, "The value of an output child should not contribute to the node UID"

    dynamicNode.outs.replaceAttributeWithEdges(dynamicNode.outs.a, dynamicNode.outs.getEditedAttributeData(dynamicNode.outs.a, {"name": "renamed", "label": "Renamed"}))
    assert dynamicNode._uid != uidBefore, "Renaming an output child should update the node UID"

    uidBefore = dynamicNode._uid
    dynamicNode.outs.removeAttribute(dynamicNode.outs.renamed)
    addOutputChild(dynamicNode.outs, desc.FloatParam(name="renamed", label="renamed", description="", value=0.0,
                                                     range=(0.0, 1.0, 0.1)))
    assert dynamicNode._uid != uidBefore, "Changing the type of an output child should update the node UID"

    uidBefore = dynamicNode._uid
    dynamicNode.outs.removeAttribute(dynamicNode.outs.renamed)
    assert dynamicNode._uid != uidBefore, "Removing an output child should update the node UID"


def test_empty_output_anyset_does_not_contribute_to_node_uid():
    """An empty output AnySet does not change the node UID, which is kept for existing projects."""
    graph, dynamicNode = initGraphAndNode()
    uidBefore = dynamicNode._uid

    addOutputChild(dynamicNode.outs, intDesc("a"))
    dynamicNode.outs.removeAttribute(dynamicNode.outs.a)
    assert dynamicNode._uid == uidBefore


def test_input_linked_to_output_anyset_depends_on_producer_uid():
    """
    An input linked to a whole output AnySet gets the UID of the producer: changing an input of the producer updates
    the UID of the consumer, so that the consumer does not reuse results computed from other outputs.
    """
    graph = Graph("test")
    producer = graph.addNewNode("DynamicNode")
    consumer = graph.addNewNode("DynamicNode")
    addOutputChild(producer.outs, intDesc("a"))
    linkedAnySet = consumer.ins.duplicateAttribute(SimpleNamespace(desc=desc.AnySet(name="linked", label="linked", description="")))
    graph.addEdge(producer.outs, linkedAnySet)
    graph.update()
    producerUid, consumerUid = producer._uid, consumer._uid

    producer.code.value = "node.outs.a.value = 7"
    graph.update()

    assert producer._uid != producerUid
    assert consumer._uid != consumerUid


@pytest.mark.parametrize("attributeDesc", [intDesc("a"), desc.File(name="a", label="a", description="", value="")],
                         ids=["int", "file"])
def test_input_linked_to_output_anyset_child_depends_on_producer_uid_after_load(tmp_path, attributeDesc):
    """
    An output AnySet child restored when loading a graph is still a dynamic output: an input linked to it keeps
    the UID of the producer, and changing an input of the producer updates the UID of the consumer.
    """
    graph = Graph("test")
    producer = graph.addNewNode("DynamicNode")
    consumer = graph.addNewNode("DynamicNode")
    output = addOutputChild(producer.outs, attributeDesc)
    graph.addEdge(output, consumer.ins.duplicateAttribute(SimpleNamespace(desc=attributeDesc)))
    graph.update()
    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)

    loadedGraph = loadGraph(graphFile)
    loadedProducer, loadedConsumer = loadedGraph.node(producer.name), loadedGraph.node(consumer.name)

    assert loadedProducer.outs.childAttribute("a").desc.isDynamicValue
    assert not isinstance(loadedConsumer, CompatibilityNode), loadedConsumer.issueDetails
    assert loadedConsumer._uid == consumer._uid

    loadedProducer.code.value = "node.outs.a.value = 7"
    loadedGraph.update()

    assert loadedConsumer._uid != consumer._uid


def renameOutputChild(node):
    node.outs.replaceAttributeWithEdges(node.outs.a, node.outs.getEditedAttributeData(node.outs.a, {"name": "b", "label": "b"}))


def removeOutputChild(node):
    """Remove the output child 'a' of 'node' along with its edges, as the UI does."""
    for edge in list(node.graph.edges.values()):
        if edge.src is node.outs.a:
            node.graph.removeEdge(edge.dst)
    node.outs.removeAttribute(node.outs.a)


def retypeOutputChild(node):
    removeOutputChild(node)
    addOutputChild(node.outs, desc.StringParam(name="a", label="a", description="", value=""))


def addOtherOutputChild(node):
    addOutputChild(node.outs, intDesc("b"))


def renameNestedOutputChild(anySet):
    anySet.replaceAttributeWithEdges(anySet.a, anySet.getEditedAttributeData(anySet.a, {"name": "b", "label": "b"}))


def removeNestedOutputChild(anySet):
    anySet.removeAttribute(anySet.a)


def retypeNestedOutputChild(anySet):
    anySet.removeAttribute(anySet.a)
    addOutputChild(anySet, desc.StringParam(name="a", label="a", description="", value=""))


def addOtherNestedOutputChild(anySet):
    addOutputChild(anySet, intDesc("b"))


def nestedAnySetDesc():
    return desc.AnySet(name="nested", label="nested", description="")


def addNestedAnySet(outputs):
    """Add an AnySet as a direct child of the output AnySet 'outputs' and return it."""
    return addOutputChild(outputs, nestedAnySetDesc())


def addNestedAnySetInGroup(outputs):
    """Add a group holding an AnySet to the output AnySet 'outputs' and return the AnySet."""
    group = addOutputChild(outputs, desc.GroupAttribute(name="group", label="group", description="",
                                                        items=[intDesc("value"), nestedAnySetDesc()]))
    return group.childAttribute("nested")


def addNestedAnySetInNestedGroup(outputs):
    """Add a group holding a group holding an AnySet to the output AnySet 'outputs' and return the AnySet."""
    innerGroup = desc.GroupAttribute(name="innerGroup", label="innerGroup", description="", items=[nestedAnySetDesc()])
    group = addOutputChild(outputs, desc.GroupAttribute(name="group", label="group", description="", items=[innerGroup]))
    return group.childAttribute("innerGroup").childAttribute("nested")


@pytest.mark.parametrize("addNestedOutputAnySet", [addNestedAnySet, addNestedAnySetInGroup, addNestedAnySetInNestedGroup],
                         ids=["anySet", "anySetInGroup", "anySetInNestedGroup"])
@pytest.mark.parametrize("editOutputs", [renameNestedOutputChild, removeNestedOutputChild, retypeNestedOutputChild,
                                         addOtherNestedOutputChild],
                         ids=["rename", "remove", "retype", "add"])
def test_nested_output_anyset_schema_change_updates_node_uid(editOutputs, addNestedOutputAnySet):
    """
    Changing the names or types of the children of an AnySet nested in an output AnySet, directly or through groups,
    updates the node UID.
    """
    graph, dynamicNode = initGraphAndNode()
    nestedAnySet = addNestedOutputAnySet(dynamicNode.outs)
    addOutputChild(nestedAnySet, intDesc("a"))
    graph.update()
    uidBefore = dynamicNode._uid

    editOutputs(nestedAnySet)
    graph.update()
    assert dynamicNode._uid != uidBefore


def test_output_list_elements_do_not_contribute_to_node_uid():
    """
    The elements of an output list are computed values: neither their number nor the children of the AnySets
    nested in them contribute to the node UID, which only depends on the description of the list.
    """
    graph, dynamicNode = initGraphAndNode()
    group = desc.GroupAttribute(name="group", label="group", description="", items=[intDesc("value"), nestedAnySetDesc()])
    outputList = addOutputChild(dynamicNode.outs, desc.ListAttribute(name="list", label="list", description="", elementDesc=group))
    graph.update()
    uidBefore = dynamicNode._uid

    outputList.append({"value": 1})
    addOutputChild(outputList.at(0).childAttribute("nested"), intDesc("a"))
    graph.update()
    assert dynamicNode._uid == uidBefore


@pytest.mark.parametrize("attributeDesc",
                         [attributeDesc for pair in COMPOUND_CHILDREN_WITH_DIFFERENT_STRUCTURES for attributeDesc in pair]
                         + [attributeDesc for attributeDesc, _ in SHAPE_CHILDREN])
def test_output_child_schema_key_without_nested_anyset_matches_desc_schema_key(attributeDesc):
    """The schema key of an output child that does not hold any AnySet is the one of its description, keeping the existing UIDs."""
    _, dynamicNode = initGraphAndNode()
    child = addOutputChild(dynamicNode.outs, attributeDesc)
    assert AnySet._childSchemaKey(child) == AnySet._schemaKey(child.desc)


@pytest.mark.parametrize("editOutputs", [renameOutputChild, removeOutputChild, retypeOutputChild, addOtherOutputChild],
                         ids=["rename", "remove", "retype", "add"])
def test_output_anyset_schema_change_resets_computed_node(graphSavedOnDisk, editOutputs):
    """Changing the names or types of the outputs of a computed node resets it, along with the nodes using its outputs."""
    graph = graphSavedOnDisk
    producer = graph.addNewNode("DynamicNode")
    consumer = graph.addNewNode("DynamicNode")
    addOutputChild(producer.outs, intDesc("a"))
    producer.code.value = "node.outs.a.value = 7"
    consumer.ins.duplicateAttribute(SimpleNamespace(desc=intDesc("x")))
    graph.addEdge(producer.outs.a, consumer.ins.x)
    graph.save()

    producer.process(inCurrentEnv=True)
    graph.update()
    assert producer.globalStatus == "SUCCESS"
    assert producer.outs.a.value == 7
    producerUid, consumerUid = producer._uid, consumer._uid

    # Without the output schema in the node UID, the node stayed computed and the computed values were reloaded
    # into the edited outputs, raising an AttributeError for a renamed or removed output
    editOutputs(producer)

    assert producer._uid != producerUid
    assert producer.globalStatus == "NONE"
    if consumer.ins.x.isLink:
        assert consumer._uid != consumerUid


def test_output_anyset_schema_restored_finds_computed_results(graphSavedOnDisk):
    """Restoring the outputs of a computed node to their computed names and types finds its computed results again."""
    graph = graphSavedOnDisk
    node = graph.addNewNode("DynamicNode")
    addOutputChild(node.outs, intDesc("a"))
    node.code.value = "node.outs.a.value = 7"
    graph.save()

    node.process(inCurrentEnv=True)
    graph.update()
    computedUid = node._uid

    node.outs.replaceAttributeWithEdges(node.outs.a, node.outs.getEditedAttributeData(node.outs.a, {"name": "b", "label": "b"}))
    assert node.globalStatus == "NONE"

    node.outs.replaceAttributeWithEdges(node.outs.b, node.outs.getEditedAttributeData(node.outs.b, {"name": "a", "label": "a"}))
    assert node._uid == computedUid
    assert node.globalStatus == "SUCCESS"
    assert node.outs.a.value == 7
