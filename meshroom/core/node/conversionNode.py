#!/usr/bin/env python

import logging

from meshroom.common import Property
from meshroom.core.attribute import Attribute
from meshroom.core.node.node import Node


class ConversionNode(Node):
    """
    A Node converting the value of its "input" attribute into the type of its "output" attribute.

    The output value is evaluated on-the-fly from the input value (see desc.ConversionNode.convert),
    so the node is never computed and its output is always up-to-date.
    """
    def __init__(self, nodeType, position=None, parent=None, uid=None, **kwargs):
        super().__init__(nodeType, position, parent=parent, uid=uid, **kwargs)
        self.outputAttribute._valueEvaluator = ConversionNode._evaluateOutputValue

    def _isConversionNode(self) -> bool:
        return True

    @staticmethod
    def _evaluateOutputValue(attribute: Attribute):
        return attribute.node.getConvertedValue()

    def getConvertedValue(self):
        """
        Return the converted value of the "input" attribute, or None if it cannot be evaluated
        (dynamic upstream value not computed yet, or conversion error).
        """
        value = self.inputAttribute.value
        if value is None:
            return None
        try:
            return self.nodeDesc.convert(self, value)
        except Exception as exc:
            logging.warning(f"Failed to convert the value '{value}' on node '{self.name}': {exc}")
            return None

    def _onAttributeChanged(self, attr: Attribute):
        super()._onAttributeChanged(attr)
        if not attr.isInput or (self.graph and self.graph.isLoading):
            return
        # Any change on the inputs (connection, upstream value or conversion parameter) may change
        # the converted value: notify the output attribute and the attributes connected to it.
        output = self.outputAttribute
        output.valueChanged.emit()
        if self.graph:
            for edge in self.graph.outEdges(output):
                edge.dst.valueChanged.emit()

    # The attribute holding the value to convert.
    inputAttribute = Property(Attribute, lambda self: self.attribute(self.nodeDesc.inputAttributeName), constant=True)
    # The attribute holding the converted value.
    outputAttribute = Property(Attribute, lambda self: self.attribute(self.nodeDesc.outputAttributeName), constant=True)
