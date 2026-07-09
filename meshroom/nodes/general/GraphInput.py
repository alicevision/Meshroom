# -*- coding: utf-8 -*-

__version__ = "1.0"

from meshroom.core import desc


ATTR_TYPES = ["String", "File", "Int", "Float", "Bool"]


class GraphInput(desc.InputNode, desc.InitNode):
    inputs = [
        desc.AnySet(
            name="inputs",
            exposed=True
        )
    ]

    def getParams(self, node):
        serializedAnySet = node.inputs.getSerializedValue()
        serializedChildren = serializedAnySet.get("children") or []
        parameters = [p["name"] for p in serializedChildren]
        return parameters

    def setInputAttribute(self, node, attrName, attrValue):
        attr = node.getAnyAttribute(f"inputs.{attrName}")
        if not attr:
            raise KeyError(f"No GraphInput attribute named {attrName}")
        attr._setValue(attrValue)
