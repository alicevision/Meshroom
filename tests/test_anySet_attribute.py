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

    floatData = dynamicNode.ins.newAttributeData("FloatParam")
    assert floatData["name"] == "float"
    assert floatData["type"] == "FloatParam"
    dynamicNode.ins.insertAttribute(floatData, 0)

    floatData0 = dynamicNode.ins.newAttributeData("FloatParam")
    assert floatData0["name"] == "float_0"
    floatAttr0 = dynamicNode.ins.insertAttribute(floatData0, 1)
    assert floatAttr0.label == "Float 0"
    assert floatAttr0.desc.range == [0.0, 1.0, 0.01]
    assert floatAttr0.isDefault

    choiceAttr = dynamicNode.ins.insertAttribute(dynamicNode.ins.newAttributeData("ChoiceParam"), 2)
    assert choiceAttr.desc.values == ["optionA", "optionB"]

    try:
        dynamicNode.ins.newAttributeData("AnySet")
    except ValueError:
        pass
    else:
        raise AssertionError("Only parameter types can be created from the UI.")


def test_edit_anyset_attribute_updates_description_and_keeps_position():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    anySet.insertAttribute(anySet.newAttributeData("StringParam"), 0)
    intAttr = anySet.insertAttribute(anySet.newAttributeData("IntParam"), 1)
    anySet.insertAttribute(anySet.newAttributeData("BoolParam"), 2)

    data = anySet.editedAttributeData(intAttr, {
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
    choiceAttr = anySet.insertAttribute(anySet.newAttributeData("ChoiceParam"), 0)
    choiceAttr.value = "optionB"

    data = anySet.editedAttributeData(choiceAttr, {"defaultValue": "low", "values": ["low", "optionB"]})
    newAttr = anySet.replaceAttribute(choiceAttr, data)

    assert newAttr.desc.values == ["low", "optionB"]
    assert newAttr.desc.value == "low"
    assert newAttr.value == "optionB"
    assert not newAttr.isDefault


def test_edit_anyset_attribute_rejects_invalid_parameters():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    anySet.insertAttribute(anySet.newAttributeData("FloatParam"), 0)
    stringAttr = anySet.insertAttribute(anySet.newAttributeData("StringParam"), 1)
    floatAttr = anySet.float

    for parameters in ({"name": "float"}, {"name": "1invalid"}, {"label": " "}):
        try:
            anySet.editedAttributeData(stringAttr, parameters)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Editing with {parameters} should fail.")

    try:
        anySet.editedAttributeData(floatAttr, {"defaultValue": "notANumber"})
    except ValueError:
        pass
    else:
        raise AssertionError("An invalid default value should be rejected.")


def test_edited_anyset_attribute_restored_after_load(tmp_path):
    from meshroom.core.graph import loadGraph

    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    floatAttr = anySet.insertAttribute(anySet.newAttributeData("FloatParam"), 0)
    floatAttr = anySet.replaceAttribute(floatAttr, anySet.editedAttributeData(floatAttr, {
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


def test_new_anyset_attribute_kinds():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins

    textAttr = anySet.insertAttribute(anySet.newAttributeData("TextParam"), 0)
    assert textAttr.type == "StringParam"
    assert textAttr.desc.semantic == "multiline"

    hueAttr = anySet.insertAttribute(anySet.newAttributeData("HueParam"), 1)
    assert hueAttr.type == "FloatParam"
    assert hueAttr.desc.semantic == "color/hue"

    choicesAttr = anySet.insertAttribute(anySet.newAttributeData("MultiChoiceParam"), 2)
    assert not choicesAttr.desc.exclusive
    assert choicesAttr.value == ["optionA"]

    listAttr = anySet.insertAttribute(anySet.newAttributeData("ListAttribute", "IntParam"), 3)
    assert listAttr.type == "ListAttribute"
    assert listAttr.desc.elementDesc.type == "IntParam"
    assert len(listAttr.value) == 0

    sizeAttr = anySet.insertAttribute(anySet.newAttributeData("Size2d"), 4)
    assert [item.name for item in sizeAttr.value] == ["width", "height"]
    vectorAttr = anySet.insertAttribute(anySet.newAttributeData("Vec2d"), 5)
    assert [item.name for item in vectorAttr.value] == ["x", "y"]

    flowAttr = anySet.insertAttribute(anySet.newAttributeData("Flow"), 6)
    assert flowAttr.type == "Flow"

    try:
        anySet.newAttributeData("ListAttribute", "ChoiceParam")
    except ValueError:
        pass
    else:
        # The values of a choice are not serialized with the element description of a list
        raise AssertionError("Lists of choices cannot be created.")


def test_edit_anyset_group_and_list_keep_values():
    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    vectorAttr = anySet.insertAttribute(anySet.newAttributeData("Vec2d"), 0)
    vectorAttr.x.value = 3.0
    listAttr = anySet.insertAttribute(anySet.newAttributeData("ListAttribute", "FloatParam"), 1)
    listAttr.append(1.5)

    vectorData = anySet.editedAttributeData(vectorAttr, {"name": "offset", "label": "Offset"})
    newVector = anySet.replaceAttribute(vectorAttr, vectorData)
    assert newVector.label == "Offset"
    assert newVector.x.value == 3.0

    newList = anySet.replaceAttribute(listAttr, anySet.editedAttributeData(listAttr, {"description": "Weights"}))
    assert newList.desc.description == "Weights"
    assert newList.desc.elementDesc.type == "FloatParam"
    assert [element.value for element in newList.value] == [1.5]


def test_new_anyset_attribute_kinds_restored_after_load(tmp_path):
    from meshroom.core.graph import loadGraph

    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    for kind in ("TextParam", "HueParam", "MultiChoiceParam", "Vec2d", "Flow"):
        anySet.insertAttribute(anySet.newAttributeData(kind), anySet.value.count)
    anySet.insertAttribute(anySet.newAttributeData("ListAttribute", "FloatParam"), anySet.value.count)
    anySet.text.value = "first line\nsecond line"
    anySet.hue.value = 0.25
    anySet.choices.value = ["optionA", "optionB"]
    anySet.vector.y.value = 2.0
    anySet.list.append(0.5)

    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)
    loadedAnySet = loadGraph(graphFile).node(dynamicNode.name).ins

    assert [attribute.name for attribute in loadedAnySet.value] == ["text", "hue", "choices", "vector", "flow", "list"]
    assert loadedAnySet.text.desc.semantic == "multiline"
    assert loadedAnySet.text.value == "first line\nsecond line"
    assert loadedAnySet.hue.desc.semantic == "color/hue"
    assert loadedAnySet.hue.value == 0.25
    assert not loadedAnySet.choices.desc.exclusive
    assert loadedAnySet.choices.value == ["optionA", "optionB"]
    assert loadedAnySet.vector.y.value == 2.0
    assert loadedAnySet.flow.type == "Flow"
    assert [element.value for element in loadedAnySet.list.value] == [0.5]


def test_anyset_lists_of_every_element_kind_restored_after_load(tmp_path):
    from meshroom.core.graph import loadGraph

    graph, dynamicNode = initGraphAndNode()
    anySet = dynamicNode.ins
    for elementKind in AnySet._listElementKinds:
        anySet.insertAttribute(anySet.newAttributeData("ListAttribute", elementKind), anySet.value.count)

    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)
    loadedAnySet = loadGraph(graphFile).node(dynamicNode.name).ins
    assert [attribute.desc.elementDesc.type for attribute in loadedAnySet.value] == list(AnySet._listElementKinds)


# ---------------------------------------------------------------------------
# Serialization / deserialization tests
# ---------------------------------------------------------------------------

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
