"""Tests for the AnySet feature."""

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
