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
    dynamicNode.ins.renameAttribute(dynamicNode.ins.intParam, "renamedParam", "Renamed Param")
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

    node.outs.renameAttribute(node.outs.a, "b", "b")
    assert node.globalStatus == "NONE"

    node.outs.renameAttribute(node.outs.b, "a", "a")
    assert node._uid == computedUid
    assert node.globalStatus == "SUCCESS"
    assert node.outs.a.value == 7
