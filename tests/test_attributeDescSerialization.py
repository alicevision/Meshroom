"""Tests for the serialization of the attribute descriptions (desc.Attribute.asDict / attributeDescriptionFactory)."""

import math

import pytest

from meshroom.core import desc
from meshroom.core.attribute import attributeDescriptionFactory
from meshroom.core.graph import Graph, loadGraph
from meshroom.core.node import CompatibilityNode
from types import SimpleNamespace


def stringDesc(name="string"):
    return desc.StringParam(name=name, label=name, description="", value="someString")


def intDesc(name="int", keyable=False, keyType=None):
    return desc.IntParam(name=name, label=name, description="", value=1, range=(0, 10, 1), keyable=keyable, keyType=keyType)


def floatDesc(name="float", keyable=False, keyType=None):
    return desc.FloatParam(name=name, label=name, description="", value=0.5, range=(0.0, 1.0, 0.1), keyable=keyable,
                           keyType=keyType)


def boolDesc(name="bool", keyable=False, keyType=None):
    return desc.BoolParam(name=name, label=name, description="", value=True, keyable=keyable, keyType=keyType)


def choiceDesc(name="choice"):
    return desc.ChoiceParam(name=name, label=name, description="", value="a", values=["a", "b"], exclusive=True)


def fileDesc(name="file"):
    return desc.File(name=name, label=name, description="", value="/some/path")


def colorDesc(name="color"):
    return desc.ColorParam(name=name, label=name, description="", value="#ff8000")


def groupDesc(name, items):
    return desc.GroupAttribute(name=name, label=name, description="", items=items)


def listDesc(name, elementDesc):
    return desc.ListAttribute(name=name, label=name, description="", elementDesc=elementDesc)


def scalarDescs():
    """Return a description of each scalar type, including the keyable ones."""
    return [stringDesc(), intDesc(), floatDesc(), boolDesc(), choiceDesc(), fileDesc(), colorDesc(),
            intDesc("keyableInt", keyable=True, keyType="viewId"), floatDesc("keyableFloat", keyable=True, keyType="viewId"),
            boolDesc("keyableBool", keyable=True, keyType="viewId")]


def shapeDescs(keyable):
    """Return a description of each geometry and shape type, keyable or not."""
    kwargs = {"label": "", "description": "", "keyable": keyable, "keyType": "viewId" if keyable else None}
    prefix = "keyable" if keyable else ""
    return [desc.Vec2d(name=f"{prefix}vec2d", **kwargs), desc.Size2d(name=f"{prefix}size2d", **kwargs),
            desc.Point2d(name=f"{prefix}point2d", **kwargs), desc.Line2d(name=f"{prefix}line2d", **kwargs),
            desc.Rectangle(name=f"{prefix}rectangle", **kwargs), desc.Circle(name=f"{prefix}circle", **kwargs),
            desc.SurveyPoint(name=f"{prefix}surveyPoint", **kwargs)]


DESCRIPTIONS = (
    scalarDescs()
    + [listDesc(f"{elementDesc.name}List", elementDesc) for elementDesc in scalarDescs()]
    + [
        groupDesc("group", scalarDescs()),
        listDesc("groupList", groupDesc("group", [intDesc(), stringDesc()])),
        groupDesc("groupOfList", [intDesc(), listDesc("stringList", stringDesc())]),
        listDesc("nestedList", listDesc("stringList", stringDesc())),
        groupDesc("nestedGroup", [groupDesc("group", [stringDesc(), choiceDesc()])]),
    ]
    + shapeDescs(keyable=False)
    + shapeDescs(keyable=True)
    + [listDesc(f"{shape.name}List", shape) for shape in shapeDescs(keyable=True)]
    + [desc.ShapeList(name="shapeList", label="", description="",
                      shape=desc.Point2d(name="point2d", label="", description="", keyable=True, keyType="viewId"))]
)
DESCRIPTION_IDS = [attributeDesc.name for attributeDesc in DESCRIPTIONS]


def descState(attributeDesc):
    """
    Return the state of 'attributeDesc' that its serialization must preserve: its type, name, keyable state and the
    arguments specific to its type, along with the state of its descendants (group items, list elements).
    """
    state = {"type": type(attributeDesc).__name__, "name": attributeDesc.name}
    if isinstance(attributeDesc, desc.ListAttribute):
        state["elementDesc"] = descState(attributeDesc.elementDesc)
    elif isinstance(attributeDesc, desc.GroupAttribute):
        state["items"] = [descState(item) for item in attributeDesc.items]
    else:
        value = attributeDesc.value
        # NaN default values (e.g. SurveyPoint) are not equal to themselves
        if isinstance(value, float) and math.isnan(value):
            value = "nan"
        state.update(keyable=attributeDesc.keyable, keyType=attributeDesc.keyType, value=value)
        if isinstance(attributeDesc, desc.ChoiceParam):
            state.update(values=list(attributeDesc.values), exclusive=attributeDesc.exclusive)
        if isinstance(attributeDesc, (desc.IntParam, desc.FloatParam)):
            state["range"] = list(attributeDesc.range)
    return state


@pytest.mark.parametrize("attributeDesc", DESCRIPTIONS, ids=DESCRIPTION_IDS)
def test_desc_serialization_round_trip(attributeDesc):
    """
    A description rebuilt from its serialization has the same type, keyable state and type-specific arguments,
    as well as its descendants (group items, list elements), recursively.
    """
    rebuiltDesc = attributeDescriptionFactory(attributeDesc.asDict())
    assert descState(rebuiltDesc) == descState(attributeDesc)


def descendantDescs(attributeDesc):
    """Return the descriptions of the descendants of 'attributeDesc' (group items, list elements), recursively."""
    if isinstance(attributeDesc, desc.ListAttribute):
        children = [attributeDesc.elementDesc]
    elif isinstance(attributeDesc, desc.GroupAttribute):
        children = attributeDesc.items
    else:
        children = []
    return [descendant for child in children for descendant in [child] + descendantDescs(child)]


@pytest.mark.parametrize("attributeDesc", DESCRIPTIONS, ids=DESCRIPTION_IDS)
def test_desc_clone_does_not_share_descendants(attributeDesc):
    """
    A cloned description has the same state as the source one, and does not share any descendant description with it
    (e.g. the shape of a ShapeList), so that modifying the clone does not modify the source.
    """
    clone = attributeDesc.clone()
    assert descState(clone) == descState(attributeDesc)
    sourceDescendants = {id(descendant) for descendant in descendantDescs(attributeDesc)}
    assert not any(id(descendant) in sourceDescendants for descendant in descendantDescs(clone))


@pytest.mark.parametrize("attributeDesc", [listDesc("list", stringDesc()), groupDesc("group", [stringDesc()])],
                         ids=["list", "group"])
def test_group_and_list_desc_serialization_omits_derived_keys(attributeDesc):
    """
    The keyable state and the invalidate flag of a group or a list are derived from its descendants, which are
    serialized instead: they are not serialized, as the group and list constructors do not accept them.
    The value of a group is defined by its items, so it is not serialized either.
    """
    serializedData = attributeDesc.asDict()
    assert not {"keyable", "keyType", "invalidate"} & serializedData.keys()
    if isinstance(attributeDesc, desc.GroupAttribute):
        assert "value" not in serializedData
        assert [item["name"] for item in serializedData["items"]] == [item.name for item in attributeDesc.items]
    else:
        assert serializedData["elementDesc"]["name"] == attributeDesc.elementDesc.name


def nestedCompoundAttributes():
    """Return compound descriptions holding compound descendants, along with a non-default value to set on each of them."""
    return [
        (groupDesc("groupOfGroup", [intDesc("a"), groupDesc("inner", [intDesc("b"), stringDesc()])]),
         {"a": 2, "inner": {"b": 3, "string": "otherString"}}),
        (groupDesc("groupOfList", [intDesc(), listDesc("intList", intDesc("element"))]),
         {"int": 2, "intList": [3, 4]}),
        (groupDesc("groupOfListOfGroups", [listDesc("groupList", groupDesc("group", [intDesc(), stringDesc()]))]),
         {"groupList": [{"int": 3, "string": "a"}, {"int": 4, "string": "b"}]}),
        (listDesc("listOfGroupsOfLists", groupDesc("group", [listDesc("intList", intDesc("element"))])),
         [{"intList": [3, 4]}, {"intList": [5]}]),
    ]


NESTED_COMPOUND_ATTRIBUTES = nestedCompoundAttributes()


@pytest.mark.parametrize("attributeDesc,value", NESTED_COMPOUND_ATTRIBUTES,
                         ids=[attributeDesc.name for attributeDesc, _ in NESTED_COMPOUND_ATTRIBUTES])
def test_nested_compound_attribute_serialization_round_trip(tmp_path, attributeDesc, value):
    """
    An attribute with compound descendants serialized along with its description (e.g. an AnySet child) is restored
    with the same structure and value, from its serialization (e.g. when undoing its removal) and when reloading a graph:
    a group serializes its direct items only, along with its value.
    """
    graph = Graph("test")
    node = graph.addNewNode("DynamicNode")
    attribute = node.ins.duplicateAttribute(SimpleNamespace(desc=attributeDesc))
    attribute.value = value
    graph.update()
    serializedData = attribute.asDict()
    if isinstance(attributeDesc, desc.GroupAttribute):
        assert [item["name"] for item in serializedData["items"]] == [item.name for item in attributeDesc.items]

    restoredAttribute = graph.addNewNode("DynamicNode").ins.insertAttribute(serializedData, 0)
    assert restoredAttribute.asDict() == serializedData
    assert restoredAttribute.getPrimitiveValue() == value

    graphFile = str(tmp_path / "graph.mg")
    graph.save(graphFile)
    loadedNode = loadGraph(graphFile).node(node.name)
    assert not isinstance(loadedNode, CompatibilityNode), loadedNode.issueDetails
    assert loadedNode.ins.childAttribute(attributeDesc.name).getPrimitiveValue() == value
    assert loadedNode._uid == node._uid


def legacyFlattenedGroup(serializedData):
    """
    Return the serialization of a group as written by older versions, which serialized the items of a group flattened:
    each group item followed by a copy of all its descendants.
    """
    if not isinstance(serializedData.get("items"), list):
        return serializedData
    items = []
    for item in serializedData["items"]:
        legacyItem = legacyFlattenedGroup(item)
        items.append(legacyItem)
        items += legacyItem.get("items", [])
    return dict(serializedData, items=items)


def test_legacy_flattened_group_anyset_child_loads(tmp_path):
    """
    A group with compound descendants saved as an AnySet child by older versions, which serialized the items of
    a group flattened, is restored with its direct items only, along with its value.
    """
    import json

    attributeDesc = groupDesc("groupOfGroups", [
        intDesc("a"),
        groupDesc("inner", [intDesc("b"), groupDesc("innerMost", [stringDesc()])]),
        listDesc("intList", intDesc("element")),
    ])
    value = {"a": 2, "inner": {"b": 3, "innerMost": {"string": "otherString"}}, "intList": [3, 4]}
    graph = Graph("test")
    node = graph.addNewNode("DynamicNode")
    attribute = node.ins.duplicateAttribute(SimpleNamespace(desc=attributeDesc))
    attribute.value = value
    graph.update()

    graphData = graph.serialize()
    serializedAnySet = graphData["graph"][node.name]["inputs"]["ins"]
    children = serializedAnySet["children"] if isinstance(serializedAnySet, dict) else serializedAnySet
    children[0] = legacyFlattenedGroup(children[0])
    assert [item["name"] for item in children[0]["items"]] == ["a", "inner", "b", "innerMost", "string", "intList"]
    graphFile = tmp_path / "legacy_flattened_group.mg"
    graphFile.write_text(json.dumps(graphData), encoding="utf-8")

    loadedNode = loadGraph(str(graphFile)).node(node.name)
    assert not isinstance(loadedNode, CompatibilityNode), loadedNode.issueDetails
    loadedAttribute = loadedNode.ins.childAttribute(attributeDesc.name)
    assert loadedAttribute.asDict() == attribute.asDict()
    assert loadedAttribute.getPrimitiveValue() == value
    assert loadedNode._uid == node._uid


def test_desc_factory_accepts_legacy_non_keyable_serialization():
    """
    Descriptions serialized before the derived keys were omitted, which hold a non-keyable state and an invalidate
    flag at every level, can still be rebuilt.
    """
    def legacyData(name, type, **kwargs):
        return dict(name=name, label=name, description="", type=type, keyable=False, keyType=None, invalidate=True, **kwargs)

    serializedData = legacyData("groupList", "ListAttribute", value=[], elementDesc=legacyData(
        "group", "GroupAttribute", value={}, items=[
            legacyData("string", "StringParam", value="someString"),
            legacyData("choice", "ChoiceParam", value="a", values=["a", "b"], exclusive=True),
            legacyData("stringList", "ListAttribute", value=[], elementDesc=legacyData("string", "StringParam", value="")),
        ]))

    rebuiltDesc = attributeDescriptionFactory(serializedData)
    assert isinstance(rebuiltDesc, desc.ListAttribute)
    assert [(type(item).__name__, item.name) for item in rebuiltDesc.elementDesc.items] == \
        [("StringParam", "string"), ("ChoiceParam", "choice"), ("ListAttribute", "stringList")]
