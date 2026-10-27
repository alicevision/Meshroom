#!/usr/bin/env python

import logging

from meshroom.core import desc, nodeVersion
from meshroom.core.attribute import attributeFactory
from meshroom.core.exception import UnknownNodeTypeError
from meshroom.core.mixins import Expandable
from meshroom.core.node.status import Status
from meshroom.core.node.chunk import NodeChunk
from meshroom.core.node.baseNode import BaseNode


class Node(BaseNode):
    """
    A standard Graph node based on a node type.
    """
    def __init__(self, nodeType, position=None, parent=None, uid=None, **kwargs):
        super().__init__(nodeType, position, parent=parent, uid=uid, **kwargs)

        if not self.nodeDesc:
            raise UnknownNodeTypeError(nodeType)

        self.packageName = self.nodeDesc.packageName


        for attrDesc in self.nodeDesc.inputs:
            self._attributes.add(attributeFactory(attrDesc, kwargs.get(attrDesc.name, None),
                                                  isOutput=False, node=self))

        for attrDesc in self.nodeDesc.outputs:
            self._attributes.add(attributeFactory(attrDesc, kwargs.get(attrDesc.name, None),
                                                  isOutput=True, node=self))

        for attrDesc in self.nodeDesc.internalInputs:
            self._internalAttributes.add(attributeFactory(attrDesc, kwargs.get(attrDesc.name, None),
                                                          isOutput=False, node=self))

        # Add internal flow input/output attributes to _internalAttributes.
        # Skip any that are already defined by the node itself (in inputs/outputs).
        existingAttrNames = set(self._attributes.keys())
        for attrDesc in self.nodeDesc.internalFlowInputs:
            if attrDesc.name not in existingAttrNames:
                self._internalAttributes.add(attributeFactory(attrDesc, kwargs.get(attrDesc.name, None),
                                                              isOutput=False, node=self))

        for attrDesc in self.nodeDesc.internalFlowOutputs:
            if attrDesc.name not in existingAttrNames:
                self._internalAttributes.add(attributeFactory(attrDesc, kwargs.get(attrDesc.name, None),
                                                              isOutput=True, node=self))

        # Declare events for specific output attributes
        for attr in self._attributes:
            if attr.isOutput and attr.desc.semantic == "image":
                attr.enabledChanged.connect(self.outputAttrChanged)
            if attr.isOutput:
                attr.expressionApplied.connect(self.outputAttrChanged)

        # List attributes per UID
        for attr in self._attributes:
            if attr.isInput and attr.invalidate:
                self.invalidatingAttributes.add(attr)

        # Add internal attributes with a UID to the list
        for attr in self._internalAttributes:
            if attr.invalidate:
                self.invalidatingAttributes.add(attr)

    def setAttributeValues(self, values):
        # initialize attribute values
        for k, v in values.items():
            if not self.hasAttribute(k):
                # skip missing attributes
                continue
            attr = self.attribute(k)
            attr.value = v

    def upgradeAttributeValues(self, values):
        # initialize attribute values
        for k, v in values.items():
            if not self.hasAttribute(k):
                # skip missing attributes
                continue
            attr = self.attribute(k)
            try:
                attr.upgradeValue(v)
            except ValueError:
                pass

    def setInternalAttributeValues(self, values):
        # initialize internal attribute values
        for k, v in values.items():
            if not self.hasInternalAttribute(k):
                # skip missing attributes
                continue
            attr = self.internalAttribute(k)
            attr.value = v

    def upgradeInternalAttributeValues(self, values):
        # initialize internal attibute values
        for k, v in values.items():
            if not self.hasInternalAttribute(k):
                # skip missing atributes
                continue
            attr = self.internalAttribute(k)
            try:
                attr.upgradeValue(v)
            except ValueError:
                pass

    def toDict(self):
        version = nodeVersion(self.nodeDesc)
        inputs = {k: v.getSerializedValue() for k, v in self._attributes.objects.items() if v.isInput}
        # Special case for internal inputs : flowInputs is only serialized if it is not the default value
        internalInputs = {}
        for k, v in self._internalAttributes.objects.items():
            if k == "flowInputs" and v.isDefault and not v.isLink:
                continue
            internalInputs[k] = v.getSerializedValue()
        outputs = ({k: v.getSerializedValue() for k, v in self._attributes.objects.items()
                    if v.isOutput and (not v.desc.isDynamicValue or isinstance(v, Expandable))})

        return {
            'nodeType': self.nodeType,
            'version': version if version is not None else "0.0",
            'position': self._position,
            'parallelization': {
                'blockSize': self.nodeDesc.parallelization.blockSize if self.isParallelized else 0,
                'size': self.size,
                'split': self.nbParallelizationBlocks
            },
            'uid': self._uid,
            'inputs': {k: v for k, v in inputs.items() if v is not None},  # filter empty values
            'internalInputs': {k: v for k, v in internalInputs.items() if v is not None},
            'outputs': outputs
        }

    def getNodeDescription(self):
        # Get the node type, the node version, and the basic information about the io (name, type and default value)
        version = nodeVersion(self.nodeDesc)
        shortDescs = [v.shortDesc() for v in self._attributes.objects.values()]

        return {
            'nodeType': self.nodeType,
            'version': version if version is not None else "0.0",
            'inputs': {k: sd for (k, v), sd in zip(self._attributes.objects.items(), shortDescs) if v.isInput and sd is not None},
            'outputs': {k: sd for (k, v), sd in zip(self._attributes.objects.items(), shortDescs) if v.isOutput and sd is not None}
        }

    def _resetChunks(self):
        """ Set chunks on the node.
        # TODO : Maybe do not delete chunks if we will recreate them as before ?
        """
        if not self.isComputableType:
            self._chunksCreated = True
            return
        for chunk in self._chunks:
            chunk.statusChanged.disconnect(self.globalStatusChanged)
        # Empty list
        self._chunks.setObjectList([])
        self._chunkPlaceholder.setObjectList([])
        # Reset node status to ensure getGlobalStatus() returns NONE during the reset.
        # This prevents updateLocked() from using a stale status (e.g. SUCCESS or SUBMITTED)
        # which could cause the node to be incorrectly locked.
        self._nodeStatus.status = Status.NONE
        # Clear stale chunk setup from nodeStatus so that updateStatusFromCache()
        # correctly detects when chunks need to be recreated from cache.
        # Without this, the stale _nodeStatus.chunks value would match the
        # freshly loaded value, causing chunkChanged to be False and skipping
        # createChunksFromCache() — leaving _chunksCreated = False.
        self._nodeStatus.resetChunkInfo()
        # Recreate list with reset values (1 chunk or the static size)
        if not self.isParallelized:
            self._chunks.setObjectList([NodeChunk(self, desc.Range())])
            self._chunks[0].statusChanged.connect(self.globalStatusChanged)
            self._chunksCreated = True
        elif isinstance(self.nodeDesc.size, desc.computation.StaticNodeSize):
            self._updateNodeSize()
            self._chunks.setObjectList([NodeChunk(self, desc.Range())])
            self._chunks[0].statusChanged.connect(self.globalStatusChanged)
            self._chunksCreated = True
            try:
                ranges = self.nodeDesc.parallelization.getRanges(self)
                self._chunks.setObjectList([NodeChunk(self, range) for range in ranges])
                for c in self._chunks:
                    c.statusChanged.connect(self.globalStatusChanged)
                logging.debug(f"Created {len(self._chunks)} chunks for node: {self.name}")
            except RuntimeError:
                # TODO: set node internal status to error
                logging.warning(f"Invalid Parallelization on node {self._name}")
                self._chunks.clear()
                self._chunksCreated = False
        else:
            self._chunksCreated = False
            self.setSize(0)
            self._chunkPlaceholder.setObjectList([NodeChunk(self, desc.computation.Range(), placeholder=True)])

        # Create chunks when possible
        self.chunksCreatedChanged.emit()
        self.chunksChanged.emit()
        self.globalStatusChanged.emit()

    def __createChunks(self, ranges):
        if self.isParallelized:
            try:
                if len(ranges) != len(self._chunks):
                    self._chunks.setObjectList([NodeChunk(self, range) for range in ranges])
                    for c in self._chunks:
                        c.statusChanged.connect(self.globalStatusChanged)
                    logging.debug(f"Created {len(self._chunks)} chunks for node: {self.name}")
                else:
                    for chunk, range in zip(self._chunks, ranges):
                        chunk.range = range
            except RuntimeError:
                # TODO: set node internal status to error
                logging.warning(f"Invalid Parallelization on node {self._name}")
                self._chunks.clear()
        else:
            if len(self._chunks) != 1:
                self._chunks.setObjectList([NodeChunk(self, desc.Range())])
                self._chunks[0].statusChanged.connect(self.globalStatusChanged)
            else:
                self._chunks[0].range = desc.Range()
        self._chunksCreated = True
        # Update node status
        # TODO: update all chunks status?
        # TODO: update node status?
        # Emit signals for UI updates
        self.chunksChanged.emit()
        self.chunksCreatedChanged.emit()

    def createChunksFromCache(self):
        """ Create chunks when a node cache exists. """
        try:
            # Get size from cache
            size = self._nodeStatus.fullSize
            self.setSize(size)
            ranges = self._nodeStatus.getChunkRanges()
            self.__createChunks(ranges)
        except Exception as e:
            logging.error(f"Failed to create chunks for {self.name}")
            self._chunks.clear()
            self._chunksCreated = False
            raise e

    def createChunks(self):
        """ Create chunks when computation is about to start. """
        if self._chunksCreated:
            return
        if self.isInitNode:
            self._chunksCreated = True
            self.chunksChanged.emit()
            return
        # Grab current chunk information
        logging.debug(f"Creating chunks for node: {self.name}")
        try:
            size = self.evaluateSize()
            self.setSize(size)
            ranges = self.nodeDesc.parallelization.getRanges(self)
            self.__createChunks(ranges)
        except Exception as e:
            logging.error(f"Failed to create chunks for {self.name}: {e}")
            self._chunks.clear()
            self._chunksCreated = False
            raise e
        # Update status
        self._nodeStatus.setChunks(self._chunks)
        self.upgradeStatusFile()
