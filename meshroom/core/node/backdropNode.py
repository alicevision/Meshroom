#!/usr/bin/env python

from meshroom.core.attribute import attributeFactory
from meshroom.core.exception import UnknownNodeTypeError
from meshroom.core.node.baseNode import BaseNode


class BackdropNode(BaseNode):
    def __init__(self, nodeType: str, position=None, parent=None, uid=None, **kwargs):
        super().__init__(nodeType, position, parent=parent, uid=uid, **kwargs)

        self._chunksCreated = True

        if not self.nodeDesc:
            raise UnknownNodeTypeError(nodeType)

        self.packageName = self.nodeDesc.packageName

        for attrDesc in self.nodeDesc.internalInputs:
            self._internalAttributes.add(attributeFactory(attrDesc, kwargs.get(attrDesc.name, None),
                                                          isOutput=False, node=self))

    def _isBackdropNode(self) -> bool:
        return True

    def toDict(self):
        internalInputs = {k: v.getSerializedValue() for k, v in self._internalAttributes.objects.items()}

        return {
            'nodeType': self.nodeType,
            'position': self._position,
            'parallelization': {
                'blockSize': 0,
                'size': 0,
                'split': 0
            },
            'uid': self._uid,
            'internalInputs': {k: v for k, v in internalInputs.items() if v is not None},
        }
