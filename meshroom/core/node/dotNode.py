#!/usr/bin/env python

from meshroom.core.node.node import Node


class DotNode(Node):
    """
    A Dot node: a pass-through node that forwards the value of its single input to its
    single output, without any computation. It is only used to organize and re-route
    connections in the graph (see desc.DotNode for the node type requirements).
    """
    def __init__(self, nodeType: str, position=None, parent=None, uid=None, **kwargs):
        super().__init__(nodeType, position, parent=parent, uid=uid, **kwargs)

        # A Dot is never computed: consider its chunks as created so that no chunk,
        # cache folder or status file is ever created for it.
        self._chunksCreated = True

        # Forward input link/value changes to the output attribute, so that anything
        # bound to the Dot output (its dynamic type, its value) is notified when the
        # input connection changes, and so that downstream attributes are notified
        # as if the upstream attribute was connected directly.
        inputAttr = self.attribute("input")
        outputAttr = self.attribute("output")
        inputAttr.inputLinksChanged.connect(outputAttr.inputLinksChanged)
        inputAttr.valueChanged.connect(outputAttr.valueChanged)

    def _isDotNode(self) -> bool:
        return True
