"""Tests for the AnySet feature."""

from types import SimpleNamespace

import pytest

from meshroom.core import desc
from meshroom.core.attribute import AnySet, Attribute
from meshroom.core.desc import AnySet as AnySetDesc
from meshroom.core.graph import Graph


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
                   visible=False, exposed=True)
    clone = d.clone()

    assert clone is not d
    assert isinstance(clone, AnySetDesc)
    for prop in ("name", "label", "description", "commandLineGroup", "advanced", "semantic", "enabled",
                 "visible", "exposed", "items"):
        assert getattr(clone, prop) == getattr(d, prop), prop


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


def test_rename_anyset_attribute_updates_name_label_and_keeps_edges():
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("Ls", input="/fakeDirectory")

    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)
    srcNode.input.connectTo(dynamicNode.ins.input)

    dynamicNode.ins.renameAttribute(dynamicNode.ins.input, "customInput", "Custom Input")

    assert dynamicNode.ins.input is None
    assert isinstance(dynamicNode.ins.customInput, Attribute)
    assert dynamicNode.ins.customInput.name == "customInput"
    assert dynamicNode.ins.customInput.label == "Custom Input"
    assert dynamicNode.ins.customInput.isLink
    assert dynamicNode.ins.customInput.inputLink is srcNode.input
    assert graph.attribute(f"{dynamicNode.ins.fullName}.customInput") is dynamicNode.ins.customInput


def test_rename_anyset_attribute_rejects_duplicate_name():
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("Ls", input="/fakeDirectory")

    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)
    dynamicNode.ins.duplicateAttribute(srcNode.input, isOutput=False)

    try:
        dynamicNode.ins.renameAttribute(dynamicNode.ins.input_0, "input", "Input")
    except ValueError:
        pass
    else:
        raise AssertionError("Renaming an AnySet child to an existing name should fail.")


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


# ---------------------------------------------------------------------------
# Serialization / deserialization tests
# ---------------------------------------------------------------------------

def test_duplicated_attributes_are_added_at_the_end():
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("AllAttributesNode")
    for attribute in (srcNode.stringParam, srcNode.intParam, srcNode.boolParam):
        dynamicNode.ins.duplicateAttribute(attribute)
    assert [attribute.name for attribute in dynamicNode.ins.value] == ["stringParam", "intParam", "boolParam"]


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

    from meshroom.core.graph import loadGraph

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
    from meshroom.core.graph import loadGraph

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
    from meshroom.core.graph import loadGraph

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


def test_anyset_children_preserved_when_resaving_loaded_template(tmp_path):
    """AnySet children survive a template save/load cycle, and a second one after the template has been loaded."""
    from meshroom.core.graph import loadGraph

    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("AllAttributesNode")

    dynamicNode.ins.duplicateAttribute(srcNode.stringParam)
    dynamicNode.ins.duplicateAttribute(srcNode.intParam)
    dynamicNode.ins.stringParam.value = "someString"
    dynamicNode.ins.intParam.value = 11
    expectedChildren = [(attribute.name, attribute.desc.type, attribute.value) for attribute in dynamicNode.ins.value]

    templateFile = str(tmp_path / "template.mg")
    graph.save(templateFile, template=True)

    loadedGraph = loadGraph(templateFile)
    loadedDynamicNode = loadedGraph.node(dynamicNode.name)
    assert [(attribute.name, attribute.desc.type, attribute.value)
            for attribute in loadedDynamicNode.ins.value] == expectedChildren

    # Save the loaded graph as a template again, without any modification
    resavedTemplateFile = str(tmp_path / "resavedTemplate.mg")
    loadedGraph.save(resavedTemplateFile, template=True)

    reloadedGraph = loadGraph(resavedTemplateFile)
    reloadedDynamicNode = reloadedGraph.node(dynamicNode.name)
    assert [(attribute.name, attribute.desc.type, attribute.value)
            for attribute in reloadedDynamicNode.ins.value] == expectedChildren


def test_legacy_dict_anyset_serialization_still_loads(tmp_path):
    import json
    from meshroom.core.graph import loadGraph

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
    import json
    from meshroom.core.graph import loadGraph

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
    import json
    from meshroom.core.graph import loadGraph

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


def test_anyset_uid_depends_on_children_types():
    """AnySets with children of different types but with the same name and string representation have different UIDs."""
    graph = Graph("test")
    srcNode = graph.addNewNode("AllAttributesNode")
    intNode = graph.addNewNode("DynamicNode")
    stringNode = graph.addNewNode("DynamicNode")

    intNode.ins.duplicateAttribute(srcNode.intParam)
    intNode.ins.renameAttribute(intNode.ins.intParam, "param", "Param")
    intNode.ins.param.value = 5
    stringNode.ins.duplicateAttribute(srcNode.stringParam)
    stringNode.ins.renameAttribute(stringNode.ins.stringParam, "param", "Param")
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


def test_anyset_child_duplicated_from_non_invalidating_attribute_contributes_to_uid():
    """
    A child duplicated into an input AnySet from a non-invalidating attribute contributes to the node UID:
    the 'invalidate' flag is not serialized, so the children restored when loading a graph are invalidating.
    """
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("AllAttributesNode")
    nonInvalidatingDesc = srcNode.intParam.desc.clone()
    nonInvalidatingDesc._invalidate = False

    child = dynamicNode.ins.duplicateAttribute(SimpleNamespace(desc=nonInvalidatingDesc))
    graph.update()
    assert child.invalidate

    uidBefore = dynamicNode._uid
    child.value = 42
    assert dynamicNode._uid != uidBefore


def test_anyset_child_duplicated_from_disabled_attribute_contributes_to_uid():
    """
    A child duplicated into an input AnySet from a disabled attribute contributes to the node UID:
    the 'enabled' flag is not serialized, so the children restored when loading a graph are enabled.
    """
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("AllAttributesNode")
    for enabled in (False, lambda node: False):
        disabledDesc = srcNode.intParam.desc.clone()
        disabledDesc._enabled = enabled

        child = dynamicNode.ins.duplicateAttribute(SimpleNamespace(desc=disabledDesc))
        graph.update()
        assert child.enabled

        uidBefore = dynamicNode._uid
        child.value = 42
        assert dynamicNode._uid != uidBefore


def test_anyset_structural_changes_update_node_uid():
    """Adding, renaming, moving and removing AnySet children updates the node UID without an explicit update."""
    graph, dynamicNode = initGraphAndNode()
    srcNode = graph.addNewNode("AllAttributesNode")

    uidBefore = dynamicNode._uid
    dynamicNode.ins.duplicateAttribute(srcNode.intParam)
    assert dynamicNode._uid != uidBefore, "Adding a child should update the node UID"

    dynamicNode.ins.duplicateAttribute(srcNode.floatParam)
    assert [attribute.name for attribute in dynamicNode.ins.value] == ["intParam", "floatParam"]

    uidBefore = dynamicNode._uid
    dynamicNode.ins.renameAttribute(dynamicNode.ins.intParam, "renamedParam", "Renamed Param")
    assert dynamicNode._uid != uidBefore, "Renaming a child should update the node UID"

    uidBefore = dynamicNode._uid
    dynamicNode.ins.moveAttribute(dynamicNode.ins.floatParam, 0)
    assert [attribute.name for attribute in dynamicNode.ins.value] == ["floatParam", "renamedParam"]
    assert dynamicNode._uid != uidBefore, "Moving a child should update the node UID"

    uidBefore = dynamicNode._uid
    dynamicNode.ins.removeAttribute(dynamicNode.ins.floatParam)
    assert dynamicNode._uid != uidBefore, "Removing a child should update the node UID"


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

    dynamicNode.outs.renameAttribute(dynamicNode.outs.a, "renamed", "Renamed")
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


def renameOutputChild(node):
    node.outs.renameAttribute(node.outs.a, "b", "b")


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
    anySet.renameAttribute(anySet.a, "b", "b")


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
                         [attributeDesc for pair in COMPOUND_CHILDREN_WITH_DIFFERENT_STRUCTURES for attributeDesc in pair])
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

    node.outs.renameAttribute(node.outs.a, "b", "b")
    assert node.globalStatus == "NONE"

    node.outs.renameAttribute(node.outs.b, "a", "a")
    assert node._uid == computedUid
    assert node.globalStatus == "SUCCESS"
    assert node.outs.a.value == 7
