"""
Full serialization of attribute descriptions (type, value, choices, range, children...), to recreate an
attribute of any type from data: e.g. the ports of a subgraph or the children of an AnySet, which can be
groups (a frame range), choices (formats) or lists. Callables (enabled / visible lambdas) are not kept.
"""
import logging

from meshroom.core import desc

_COMMON = ("label", "description", "advanced", "semantic", "exposed")


def describeAttribute(attributeDesc) -> dict:
    """ A JSON-compatible description of an attribute description (see buildAttributeDesc). """
    data = {"type": type(attributeDesc).__name__, "name": attributeDesc.name}
    for key in _COMMON:
        value = getattr(attributeDesc, "_" + key, None)
        if value not in (None, "", False):
            data[key] = value
    if isinstance(attributeDesc, desc.GroupAttribute) and not isinstance(attributeDesc, desc.AnySet):
        data["items"] = [describeAttribute(item) for item in attributeDesc._items]
    elif isinstance(attributeDesc, desc.ListAttribute):
        data["elementDesc"] = describeAttribute(attributeDesc._elementDesc)
    else:
        value = attributeDesc._value
        if not callable(value):
            data["value"] = value
    if isinstance(attributeDesc, desc.ChoiceParam):
        data["values"] = list(attributeDesc._values)
        data["exclusive"] = attributeDesc._exclusive
    if isinstance(attributeDesc, (desc.IntParam, desc.FloatParam)) and attributeDesc._range:
        data["range"] = list(attributeDesc._range)
    return data


def buildAttributeDesc(data: dict, name: str = None, label: str = None):
    """
    An attribute description from describeAttribute data (name / label replaced if given). Unknown types
    or invalid data give a LiveValue (any value), with a warning.
    """
    data = dict(data)
    typeName = data.get("type", "LiveValue")
    attributeClass = getattr(desc, typeName, None)
    name = name or data.get("name")
    kwargs = {key: data[key] for key in _COMMON if key in data}
    if label:
        kwargs["label"] = label
    try:
        if attributeClass is None or not issubclass(attributeClass, desc.Attribute):
            raise ValueError(f"unknown attribute type '{typeName}'")
        if issubclass(attributeClass, desc.GroupAttribute) and not issubclass(attributeClass, desc.AnySet):
            items = [buildAttributeDesc(item) for item in data.get("items", [])]
            return attributeClass(items=items, name=name, **kwargs)
        if issubclass(attributeClass, desc.ListAttribute):
            return attributeClass(elementDesc=buildAttributeDesc(data["elementDesc"]), name=name, **kwargs)
        if issubclass(attributeClass, desc.ChoiceParam):
            kwargs.update(values=data.get("values", []), exclusive=data.get("exclusive", True))
        if issubclass(attributeClass, (desc.IntParam, desc.FloatParam)) and data.get("range"):
            kwargs["range"] = tuple(data["range"])
        if "value" in data:
            kwargs["value"] = data["value"]
        attributeDesc = attributeClass(name=name, **kwargs)
        if issubclass(attributeClass, desc.ChoiceParam) and not attributeDesc._values and attributeDesc._value is None:
            # Choices unknown (saved without them): any text
            attributeDesc._valueType = str
        return attributeDesc
    except Exception as e:
        logging.warning(f"Attribute '{name}' of type '{typeName}' recreated as LiveValue: {e}")
        return desc.LiveValue(name=name, label=kwargs.get("label"), description=kwargs.get("description"))
