#!/usr/bin/env python

import json
import logging
import os
import re
import shutil
import uuid
from collections import namedtuple
from typing import Callable, Optional, List, Union

import meshroom
from meshroom.common import Signal, Variant, Property, BaseObject, Slot, ListModel, DictModel
from meshroom.core import desc, plugins, hashValue, MrNodeType
from meshroom.core.attribute import ListAttribute, GroupAttribute, Attribute
from meshroom.core.desc.attribute import Attribute as AttributeDescription
from meshroom.core.desc.anySet import AnySet as AnySetDescription
from meshroom.core.node.status import (ChunkIndex, ChunkStatusData, ExecMode,
                                       NodeStatusData, Status, getWritingFilepath,
                                       renameWritingToFinalPath)
from meshroom.core.node.logManager import LogManager
from meshroom.core.node.chunk import NodeChunk


def hasADynamicValue(attribute: AttributeDescription) -> bool:
    return attribute.isDynamicValue or isinstance(attribute, AnySetDescription)


# Simple structure for storing node position
Position = namedtuple("Position", ["x", "y"])
# Initialize default coordinates values to 0
Position.__new__.__defaults__ = (0,) * len(Position._fields)


class BaseNode(BaseObject):
    """
    Base Abstract class for Graph nodes.
    """

    # Regexp handling complex attribute names with recursive understanding of Lists and Groups
    # i.e: a.b, a[0], a[0].b.c[1], a[0][1] (list of lists)
    attributeRE = re.compile(r'\.?(?P<name>\w*)(?:\[(?P<index>\d+)\])?')

    def __init__(self, nodeType: str, position: Position = None, parent: BaseObject = None,
                 uid: str = None, **kwargs):
        """
        Create a new Node instance based on the given node description.
        Any other keyword argument will be used to initialize this node's attributes.

        Args:
            nodeType: name of the node type
            parent: this Node's parent
            **kwargs: attributes values
        """
        super().__init__(parent)
        self._nodeType: str = nodeType
        self.nodeDesc: desc.BaseNode = None
        self.nodeDescProvider: plugins.base.NodeDescProvider = None

        # instantiate node description if nodeType is valid
        if meshroom.core.pluginManager.getNodeDescProvider(nodeType):
            self.nodeDesc = meshroom.core.pluginManager.getNodeDescProvider(nodeType).nodeDescClass()
            self.nodeDescProvider = meshroom.core.pluginManager.getNodeDescProvider(nodeType)

        self.packageName: str = ""
        self._internalFolder: str = ""
        self._sourceCodeFolder: str = self.nodeDesc.sourceCodeFolder if self.nodeDesc else ""
        self._internalFolderExp = "{cache}/{nodeType}/{uid}"

        # temporary unique name for this node
        self._name: str = f"_{nodeType}_{uuid.uuid1()}"
        self.graph = None
        self.dirty: bool = True  # whether this node's outputs must be re-evaluated on next Graph update
        self._chunks: list[NodeChunk] = ListModel(parent=self)
        self._preprocessChunk = None
        if self.hasPreprocessChunk:
            self._preprocessChunk = NodeChunk(self, desc.Range(ChunkIndex.PREPROCESS), parent=self)
            self._preprocessChunk.statusChanged.connect(self.globalStatusChanged)
        self._postprocessChunk = None
        if self.hasPostprocessChunk:
            self._postprocessChunk = NodeChunk(self, desc.Range(ChunkIndex.POSTPROCESS), parent=self)
            self._postprocessChunk.statusChanged.connect(self.globalStatusChanged)
        self._chunksCreated = False  # Only initialize chunks on compute
        self._chunkPlaceholder: list[NodeChunk] = ListModel(parent=self)  # Placeholder chunk for nodes with dynamic ones
        self._uid: str = uid
        self._expVars: dict = {}
        self._size: int = 0
        self._logManager: Optional[LogManager] = None
        self._position: Position = position or Position()
        self._attributes = DictModel(keyAttrName='name', parent=self)
        self._internalAttributes = DictModel(keyAttrName='name', parent=self)
        self.invalidatingAttributes: set = set()
        self._alive: bool = True  # for QML side to know if the node can be used or is going to be deleted
        self._locked: bool = False
        self._duplicates = ListModel(parent=self)  # list of nodes with the same uid
        self._hasDuplicates: bool = False

        self._nodeStatus: NodeStatusData = NodeStatusData(self._name, nodeType, self.packageName,
                                                          self.getMrNodeType())
        self.nodeStatusFileLastModTime = -1

        self.globalStatusChanged.connect(self.updateDuplicatesStatusAndLocked)

        self._staticExpVars = {
            "nodeType": self.nodeType,
            "nodeSourceCodeFolder": self.sourceCodeFolder
        }

    def __getattr__(self, k):
        try:
            # Throws exception if not in prototype chain
            return object.__getattribute__(self, k)
        except AttributeError as err:
            try:
                return self.attribute(k)
            except KeyError:
                raise err

    def getMrNodeType(self):
        # In compatibility mode, we may or may not have access to the nodeDesc and its information
        # about the node type.
        if self.nodeDesc is None:
            return MrNodeType.NONE
        return self.nodeDesc.getMrNodeType()

    def getName(self):
        return self._name

    def getDefaultLabel(self):
        return self.nameToLabel(self._name)

    def getLabel(self) -> str:
        """
        Returns:
            The user-provided label if it exists, the high-level label of this node otherwise
        """
        if self.hasInternalAttribute("label"):
            label = self.internalAttribute("label").value.strip()
            if label:
                return label
        return self.getDefaultLabel()

    def getNodeLogLevel(self) -> str:
        """
        Returns:
            The user-provided log level used for logging on process launched by this node
        """
        if self.hasInternalAttribute("nodeDefaultLogLevel"):
            return self.internalAttribute("nodeDefaultLogLevel").value.strip()
        return "info"

    def getColor(self) -> str:
        """
        Returns:
            The node's color: the user-provided custom color if set, otherwise the descriptor's
            default color (nodeDesc.color), or empty string if neither is defined.
        """
        if self.hasInternalAttribute("color"):
            return self.internalAttribute("color").value.strip()
        return ""

    def getInvalidationMessage(self) -> str:
        """
        Returns:
            The invalidation message on the node if it exists, empty string otherwise
        """
        if self.hasInternalAttribute("invalidation"):
            return self.internalAttribute("invalidation").value
        return ""

    def getComment(self) -> str:
        """
        Returns:
            The comments on the node if they exist, empty string otherwise
        """
        if self.hasInternalAttribute("comment"):
            return self.internalAttribute("comment").value
        return ""

    def getFontSize(self) -> int:
        """
        Returns:
            The font size from the node if it exists, 0 otherwise.
        """
        if self.hasInternalAttribute("fontSize"):
            return self.internalAttribute("fontSize").value
        return 0

    def getFontColor(self) -> str:
        """
        Returns:
            The color of the font from the node if it exists, empty string otherwise.
        """
        if self.hasInternalAttribute("fontColor"):
            return self.internalAttribute("fontColor").value.strip()
        return ""

    def getNodeWidth(self) -> int:
        """
        Returns:
            The width of the node if it has a user-set width, 0 otherwise.
        """
        if self.hasInternalAttribute("nodeWidth"):
            return self.internalAttribute("nodeWidth").value
        return 0

    def getNodeHeight(self) -> int:
        """
        Returns:
            The height of the node if it has a user-set height, 0 otherwise.
        """
        if self.hasInternalAttribute("nodeHeight"):
            return self.internalAttribute("nodeHeight").value
        return 0

    @Slot(str, result=str)
    def nameToLabel(self, name):
        """
        Returns:
            str: the high-level label from the technical node name
        """
        t, idx = name.rsplit("_", 1) if "_" in name else (name, "1")
        return f"{t}{idx if int(idx) > 1 else ''}"

    def getDocumentation(self):
        if not self.nodeDesc:
            return ""
        if self.nodeDesc.documentation:
            return self.nodeDesc.documentation
        else:
            return self.nodeDesc.__doc__

    def getNodeInfo(self):
        if not self.nodeDesc:
            return []
        info = self.nodeDesc.getNodeInfo()
        return [{"key": k, "value": v} for k, v in info.items()]

    def getAnyAttribute(self, name, internal=False):
        attrList = self._internalAttributes if internal else self._attributes
        att = None
        # Complex name indicating a GroupAttribute or ListAttribute
        if '[' in name or '.' in name:
            p = self.attributeRE.findall(name)  # Can produce zero-length matches at delimiter positions
            for n, idx in p:
                if not n and not idx:
                    # Empty tuples ('', '') carry no useful information and are just artifacts of how
                    # findall works with optional groups, and they should be ignored.
                    continue
                elif n:
                    if att is None:
                        # Get root attribute
                        att = attrList.get(n)
                    else:
                        # GroupAttribute, the access should be done through the name
                        if not isinstance(att, GroupAttribute):
                            raise ValueError(f"Cannot access '{n}': {att.fullName} is not a GroupAttribute.")
                        att = att.value.get(n)  # Get child attribute in Group
                if idx:
                    # ListAttribute, the access should be done through the index
                    if not isinstance(att, ListAttribute):
                        raise ValueError(f"Cannot access index '{idx}': {att.fullName} is not a ListAttribute.")
                    att = att.value.at(int(idx))
        else:
            att = attrList.getr(name)
        return att

    @Slot(str, result=Attribute)
    def attribute(self, name):
        return self.getAnyAttribute(name, internal=False)

    @Slot(str, result=Attribute)
    def internalAttribute(self, name):
        return self.getAnyAttribute(name, internal=True)

    def setInternalAttributeValues(self, values):
        # initialize internal attribute values
        for k, v in values.items():
            attr = self.internalAttribute(k)
            attr.value = v

    def getAttributes(self):
        return self._attributes

    def getInternalAttributes(self):
        return self._internalAttributes

    @Slot(str, result=bool)
    def hasAttribute(self, name):
        # Complex name indicating group or list attribute: parse it and get the
        # first output element to check for the attribute's existence
        if "[" in name or "." in name:
            p = self.attributeRE.findall(name)
            return p[0][0] in self._attributes.keys() or p[0][1] in self._attributes.keys()
        return name in self._attributes.keys()

    @Slot(str, result=bool)
    def hasInternalAttribute(self, name):
        if "[" in name or "." in name:
            p = self.attributeRE.findall(name)
            return p[0][0] in self._internalAttributes.keys() or p[0][1] in self._internalAttributes.keys()
        return name in self._internalAttributes.keys()

    def _applyExpr(self):
        for attr in self._attributes:
            attr._applyExpr()
        for attr in self._internalAttributes:
            attr._applyExpr()

    @property
    def nodeType(self):
        return self._nodeType

    @property
    def position(self):
        """ Get node position. """
        return self._position

    @position.setter
    def position(self, value):
        """ Set node position.

        Args:
            value (Position): target position
        """
        if self._position == value:
            return
        self._position = value
        self.positionChanged.emit()

    @property
    def alive(self):
        return self._alive

    @alive.setter
    def alive(self, value):
        if self._alive == value:
            return
        self._alive = value
        self.aliveChanged.emit()

    @property
    def depth(self):
        return self.graph.getDepth(self)

    @property
    def minDepth(self):
        return self.graph.getDepth(self, minimal=True)

    @property
    def valuesFile(self):
        return os.path.join(self.internalFolder, 'values')

    def getInputNodes(self, recursive, dependenciesOnly):
        return self.graph.getInputNodes(self, recursive=recursive,
                                        dependenciesOnly=dependenciesOnly)

    def getOutputNodes(self, recursive, dependenciesOnly):
        return self.graph.getOutputNodes(self, recursive=recursive,
                                         dependenciesOnly=dependenciesOnly)

    def toDict(self):
        pass

    def getNodeDescription(self):
        pass

    def _computeUid(self):
        """ Compute node UID by combining associated attributes' UIDs. """
        # If there is no invalidating attribute, then the computation of the UID should not
        # go through as it will only include the node type
        if not self.invalidatingAttributes:
            return

        # UID is computed by hashing the sorted list of tuple (name, value) of all attributes
        # impacting this UID
        uidAttributes = []
        for attr in self.invalidatingAttributes:
            if not attr.enabled:
                continue  # Disabled params do not contribute to the uid
            dynamicOutputAttr = attr.isLink and attr.inputRootLink.desc.isDynamicValue
            # For dynamic output attributes, the UID does not depend on the attribute value.
            # In particular, when loading a project file, the UIDs are updated first,
            # and the node status and the dynamic output values are not yet loaded,
            # so we should not read the attribute value.
            if not dynamicOutputAttr and not attr.keyable and attr.desc.checkUidIgnoreValue(attr.value):
                continue  # For non-dynamic attributes, check if the value should be ignored
            uidAttributes.append((attr.name, attr.uid()))
        uidAttributes.sort()

        # Adding the node type prevents ending up with two identical UIDs for different node types
        # that have the exact same list of attributes
        uidAttributes.append(self.nodeType)
        self._uid = hashValue(uidAttributes)

    def _computeInternalFolder(self, cacheDir):
        self._internalFolder = self._internalFolderExp.format(
            cache=cacheDir or self.graph.cacheDir,
            nodeType=self.nodeType,
            uid=self._uid)

    def _buildExpVars(self):
        """
        Generate command variables using input attributes and resolved output attributes
        names and values.
        """
        def _buildAttributeExpVars(expVars, name, attr):
            if attr.enabled:
                # xxValue is exposed without quotes to allow to compose expressions
                expVars[name + "Value"] = attr.getValueStr(withQuotes=False)

                if isinstance(attr, GroupAttribute):
                    assert isinstance(attr.value, DictModel)
                    # If the GroupAttribute is not set in a single command line argument,
                    # the sub-attributes may need to be exposed individually
                    for v in attr._value:
                        _buildAttributeExpVars(expVars, v.name, v)

        self._expVars = {
            "uid": self._uid,
            "nodeCacheFolder": self._internalFolder,
            "node": self,
        }

        # Evaluate input params
        for name, attr in self._attributes.objects.items():
            if attr.isOutput:
                continue  # skip outputs
            _buildAttributeExpVars(self._expVars, name, attr)

        # For updating output attributes invalidation values
        expVarsNoCache = self._expVars.copy()
        expVarsNoCache["cache"] = ""

        # Use "self._internalFolder" instead of "self.internalFolder" because we do not want it to
        # be resolved with the {cache} information ("self.internalFolder" resolves
        # "self._internalFolder")
        expVarsNoCache["nodeCacheFolder"] = self._internalFolderExp.format(**expVarsNoCache, **self._staticExpVars)

        # Evaluate output params
        for name, attr in self._attributes.objects.items():
            if attr.isInput:
                continue  # skip inputs

            # Apply expressions for File attributes
            if attr.desc.isExpression:
                defaultValue = ""
                # Do not evaluate expression for disabled attributes
                # (the expression may refer to other attributes that are not defined)
                if attr.enabled:
                    try:
                        # Use the expression template stored when loading from a file (if any),
                        # so that description changes on the node type only affect new nodes.
                        defaultValue = attr._expressionTemplate if attr._expressionTemplate is not None \
                            else attr.getDefaultValue()
                    except AttributeError:
                        # If we load an old scene, the lambda associated to the 'value' could try to
                        # access other params that could not exist yet
                        logging.warning(f'Invalid lambda evaluation for "{self.name}.{attr.name}"')
                    if defaultValue is not None:
                        try:
                            attr.value = defaultValue.format(**self._expVars)
                            attr._invalidationValue = defaultValue.format(**expVarsNoCache)
                        except KeyError as err:
                            logging.warning(f'Invalid expression with missing key on "{self.name}.{attr.name}" with '
                                            f'value "{defaultValue}".\nError: {str(err)}')
                        except ValueError as err:
                            logging.warning(f'Invalid expression value on "{self.name}.{attr.name}" with value '
                                            f'"{defaultValue}".\nError: {str(err)}')

            # xxValue is exposed without quotes to allow to compose expressions
            self._expVars[name + 'Value'] = attr.getValueStr(withQuotes=False)

    def createCmdLineVars(self):
        """
        Generate command variables using input attributes and resolved output attributes
        names and values.
        """
        def _buildAttributeCmdLineVars(cmdLineVars, name, attr):
            if attr.enabled:
                group = attr.desc.commandLineGroup(attr.node) \
                        if callable(attr.desc.commandLineGroup) else attr.desc.commandLineGroup
                if group:
                    # If there is a valid command line "group"
                    v = attr.getValueStr(withQuotes=True)

                    # List elements may give a fully empty string and will not be sent to the command line.
                    # String attributes will return only quotes if it is empty and thus will be send to the command line.
                    # But a List of string containing 1 element,
                    # and this element is an empty string will also return quotes and will be sent to the command line.
                    if v:
                        cmdLineVars[group] = cmdLineVars.get(group, "") + f" --{name} {v}"
                elif isinstance(attr, GroupAttribute):
                    assert isinstance(attr.value, DictModel)
                    # If the GroupAttribute is not set in a single command line argument,
                    # the sub-attributes may need to be exposed individually
                    for v in attr._value:
                        _buildAttributeCmdLineVars(cmdLineVars, v.name, v)

        cmdLineVars = {}

        # Evaluate input params
        for name, attr in self._attributes.objects.items():
            if attr.isOutput:
                continue  # skip outputs
            _buildAttributeCmdLineVars(cmdLineVars, name, attr)

        # Evaluate output params
        for name, attr in self._attributes.objects.items():
            if attr.isInput:
                continue  # skip inputs
            if not attr.desc.commandLineGroup:
                continue  # skip attributes without group

            v = attr.getValueStr(withQuotes=True)

            if not v:
                continue  # skip empty strings

            cmdLineVars[attr.desc.commandLineGroup] = \
                cmdLineVars.get(attr.desc.commandLineGroup, '') + f' --{name} {v}'

        return cmdLineVars

    @property
    def isParallelized(self):
        return bool(self.nodeDesc.parallelization) if meshroom.useMultiChunks else False

    @property
    def cpu(self):
        """ Return the resolved CPU level for this node, by evaluating the descriptor's `cpu`
        attribute with this node instance if it is callable. """
        if self.nodeDesc is None:
            return None
        return self.nodeDesc.resolvedCpu(self)

    @property
    def gpu(self):
        """ Return the resolved GPU level for this node, by evaluating the descriptor's `gpu`
        attribute with this node instance if it is callable. """
        if self.nodeDesc is None:
            return None
        return self.nodeDesc.resolvedGpu(self)

    @property
    def ram(self):
        """ Return the resolved RAM level for this node, by evaluating the descriptor's `ram`
        attribute with this node instance if it is callable. """
        if self.nodeDesc is None:
            return None
        return self.nodeDesc.resolvedRam(self)

    def hasStatus(self, status: Status):
        if self.isInitNode:
            return status == Status.INIT
        if self.isCompatibilityNode:
            # CompatibilityNodes have no chunks but may still have a status
            # Use it instead of defaulting to checking with Status.NONE
            return status == self._nodeStatus.status
        if not self._chunks or not self._chunksCreated:
            return status == Status.NONE
        for chunk in self.getAllChunks():
            if chunk._status.status != status:
                return False
        return True

    def _isComputed(self):
        if not self.isComputableType:
            return True
        return self.hasStatus(Status.SUCCESS)

    def _isComputableType(self):
        """ Return True if this node type is computable, False otherwise.
        A computable node type can be in a context that does not allow computation.
        """
        # Ambiguous case for NONE, which could be used for compatibility nodes if we do not have
        # any information about the node descriptor.
        return self.getMrNodeType() != MrNodeType.INIT and self.getMrNodeType() != MrNodeType.BACKDROP

    def clearData(self):
        """ Delete this Node internal folder.
        Status will be reset to Status.NONE
        """
        # Clear cache
        self._nodeStatus.reset()
        # Reset chunks
        self._resetChunks()
        if self.internalFolder and os.path.exists(self.internalFolder):
            try:
                shutil.rmtree(self.internalFolder)
            except Exception as exc:
                # We could get some "Device or resource busy" on .nfs file while removing the folder
                # on Linux network.
                # On Windows, some output files may be open for visualization and the removal will
                # fail.
                # In both cases, we can ignore it.
                logging.warning(f"Failed to remove internal folder: '{self.internalFolder}'. Error: {exc}.")
            self.updateStatusFromCache()

    @Slot(result=str)
    def getStartDateTime(self):
        """ Return the date (str) of the first running chunk """
        dateTime = [chunk._status.startDateTime for chunk in self.getAllChunks() if chunk._status.status
                    not in (Status.NONE, Status.SUBMITTED) and chunk._status.startDateTime != ""]
        return min(dateTime) if len(dateTime) != 0 else ""

    def isAlreadySubmitted(self):
        if self._chunksCreated:
            return any(c.isAlreadySubmitted() for c in self.getAllChunks())
        else:
            return self._nodeStatus.status in (Status.SUBMITTED, Status.RUNNING)

    def isAlreadySubmittedOrFinished(self):
        if self._chunksCreated:
            return all(c.isAlreadySubmittedOrFinished() for c in self.getAllChunks())
        else:
            return self._nodeStatus.status in (Status.SUBMITTED, Status.RUNNING, Status.SUCCESS)

    @Slot(result=bool)
    def isSubmittedOrRunning(self):
        """
        Return True if all chunks are at least submitted and there is one running chunk,
        False otherwise.
        """
        if not self._chunksCreated:
            return False
        if not self.isAlreadySubmittedOrFinished():
            return False
        for chunk in self.getAllChunks():
            if chunk.isRunning():
                return True
        return False

    @Slot(result=bool)
    def isRunning(self):
        """ Return True if at least one chunk of this Node is running, False otherwise. """
        return any(chunk.isRunning() for chunk in self.getAllChunks())

    @Slot(result=bool)
    def isFinishedOrRunning(self):
        """
        Return True if all chunks of this Node is either finished or running, False
        otherwise.
        """
        allChunks = self.getAllChunks()
        if not allChunks:
            return False
        return all(chunk.isFinishedOrRunning() for chunk in allChunks)

    @Slot(result=bool)
    def isPartiallyFinished(self):
        """ Return True is at least one chunk of this Node is finished, False otherwise. """
        return any(chunk.isFinished() for chunk in self.getAllChunks())

    def isExtern(self):
        """
        Return True if at least one chunk of this Node has an external execution mode,
        False otherwise.

        It is not enough to check whether the first chunk's execution mode is external,
        because computations may have been started locally, interrupted, and restarted externally.
        In that case, if the first chunk has completed locally before the computations were
        interrupted, its execution mode will always be local, even if computations resume
        externally.
        """
        if not self._chunksCreated:
            if self._nodeStatus.execMode == ExecMode.EXTERN:
                return True
            elif self._nodeStatus.execMode == ExecMode.LOCAL and self._nodeStatus.status in (Status.SUBMITTED, Status.RUNNING):
                return meshroom.core.sessionUid != self._nodeStatus.submitterSessionUid
            return False
        return any(chunk.isExtern() for chunk in self.getAllChunks())

    @Slot()
    def clearSubmittedChunks(self):
        """
        Reset all submitted chunks to Status.NONE. This method should be used to clear
        inconsistent status if a computation failed without informing the graph.

        Warnings:
            This must be used with caution. This could lead to inconsistent node status
            if the graph is still being computed.
        """
        chunks: List[Union[BaseNode, NodeChunk]] = self.getAllChunks()
        if not self._chunksCreated:
            chunks.append(self)
        for chunk in chunks:
            if chunk.isAlreadySubmitted():
                chunk.upgradeStatusTo(Status.NONE, ExecMode.NONE)
        self.globalStatusChanged.emit()

    def clearLocallySubmittedChunks(self):
        """ Reset all locally submitted chunks to Status.NONE. """
        chunks: List[Union[BaseNode, NodeChunk]] = self.getAllChunks()
        if not self._chunksCreated:
            chunks.append(self)
        for chunk in chunks:
            if chunk.isAlreadySubmitted() and not chunk.isExtern():
                chunk.upgradeStatusTo(Status.NONE, ExecMode.NONE)
        self.globalStatusChanged.emit()

    def upgradeStatusTo(self, newStatus, execMode=None):
        """ Upgrade node to the given status and save it on disk. """
        if self._preprocessChunk:
            self._preprocessChunk.upgradeStatusTo(newStatus)
        if self._postprocessChunk:
            self._postprocessChunk.upgradeStatusTo(newStatus)
        if self._chunksCreated:
            for chunk in self._chunks:
                chunk.upgradeStatusTo(newStatus)
        else:
            if execMode is not None:
                self._nodeStatus.execMode = execMode
            self._nodeStatus.status = newStatus
            self.upgradeStatusFile()
            chunkPlaceholder = NodeChunk(self, desc.computation.Range(), placeholder=True)
            chunkPlaceholder._status.execMode = self._nodeStatus.execMode
            chunkPlaceholder._status.status = self._nodeStatus.status
            self._chunkPlaceholder.setObjectList([chunkPlaceholder])
            self.chunksChanged.emit()
        self.globalStatusChanged.emit()

    def updateStatisticsFromCache(self):
        for chunk in self.getAllChunks():
            chunk.updateStatisticsFromCache()

    def _resetChunks(self):
        pass

    def createChunksFromCache(self):
        pass

    def _createChunks(self):
        pass

    def evaluateSize(self):
        """
        Evaluate the node size by delegating to the descriptor's resolvedSize classmethod.
        """
        return self.nodeDesc.resolvedSize(self)

    def _updateNodeSize(self):
        self.setSize(self.evaluateSize())

    def _getAttributeChangedCallback(self, attr: Attribute) -> Optional[Callable]:
        """ Get the node descriptor-defined value changed callback associated to `attr` if any. """

        # Callbacks cannot be defined on nested attributes.
        if attr.root is not None:
            return None

        attrCapitalizedName = attr.name[:1].upper() + attr.name[1:]
        callbackName = f"on{attrCapitalizedName}Changed"

        callback = getattr(self.nodeDesc, callbackName, None)
        return callback if callback and callable(callback) else None

    def _onAttributeChanged(self, attr: Attribute):
        """
        When an attribute value has changed, a specific function can be defined in the descriptor
        and be called.

        Args:
            attr: The Attribute that has changed.
        """

        if self.isCompatibilityNode:
            # Compatibility nodes are not meant to be updated.
            return

        if attr.isOutput and not self.isInitNode:
            # Ignore changes on output attributes for non-init nodes
            # as they are updated during the node's computation.
            # And we do not want notifications during the graph processing.
            return

        if not attr.keyable and attr.value is None:
            # Discard dynamic values depending on the graph processing.
            return

        if self.graph and self.graph.isLoading:
            # Do not trigger attribute callbacks during the graph loading.
            return

        callback = self._getAttributeChangedCallback(attr)

        if callback:
            callback(self)

        self.hasInvalidAttributeChanged.emit()

        if self.graph:
            # If we are in a graph, propagate the notification to the connected output attributes
            for edge in self.graph.outEdges(attr):
                edge.dst.valueChanged.emit()

    def onAttributeClicked(self, attr):
        """
        When an attribute is clicked, a specific function can be defined in the descriptor
        and be called.

        Args:
            attr (Attribute): attribute that has been clicked
        """
        paramName = attr.name[:1].upper() + attr.name[1:]
        methodName = f'on{paramName}Clicked'
        if hasattr(self.nodeDesc, methodName):
            m = getattr(self.nodeDesc, methodName)
            if callable(m):
                m(self)

    def updateInternals(self, cacheDir=None):
        """ Update Node's internal parameters and output attributes.

        This method is called when:
         - an input parameter is modified
         - the graph main cache directory is changed

        Args:
            cacheDir (str): (optional) override graph's cache directory with custom path
        """
        if self.nodeDesc:
            self.nodeDesc.update(self)

        for attr in self._attributes:
            attr.updateInternals()

        # Reset chunks splitting
        self._resetChunks()

        # Retrieve current internal folder (if possible)
        try:
            folder = self.internalFolder
        except KeyError:
            folder = ''

        # Update command variables / output attributes
        self._computeUid()
        self._computeInternalFolder(cacheDir)
        self._buildExpVars()
        if self.nodeDesc:
            self.nodeDesc.postUpdate(self)
        # Notify internal folder change if needed
        if self._internalFolder != folder:
            self.internalFolderChanged.emit()

    def updateInternalAttributes(self):
        self.internalAttributesChanged.emit()

    @property
    def internalFolder(self):
        return self._internalFolder

    @property
    def sourceCodeFolder(self):
        return self._sourceCodeFolder

    @property
    def nodeStatusFile(self):
        return os.path.join(self.graph.cacheDir, self.internalFolder, "nodeStatus")

    def shouldMonitorChanges(self):
        """ Check whether we should monitor changes in minimal mode.
        Only chunks that are run externally or local_isolated should be monitored,
        when run locally, status changes are already notified.
        Chunks with an ERROR status may be re-submitted externally and should thus still be monitored
        """
        if self._chunksCreated:
            # Only monitor when chunks are not created (in this case monitor chunk status files instead)
            return False
        return (self.isExtern() and self._nodeStatus.status in (Status.SUBMITTED, Status.RUNNING, Status.ERROR)) or \
               (self.getMrNodeType() == MrNodeType.NODE and self._nodeStatus.status in (Status.SUBMITTED, Status.RUNNING))

    def updateNodeStatusFromCache(self):
        """
        Update node status based on status file content/existence.
        # TODO : integrate nodeStatusFileLastModTime ?
        Returns True if a change on the chunk setup has been detected
        """
        chunksRangeHasChanged = False
        if os.path.exists(self.nodeStatusFile):
            oldChunkSetup = self._nodeStatus.chunksSetup
            self._nodeStatus.loadFromCache(self.nodeStatusFile)
            if self._nodeStatus.chunksSetup != oldChunkSetup:
                chunksRangeHasChanged = True
            self.nodeStatusFileLastModTime = os.path.getmtime(self.nodeStatusFile)
        else:
            # No status file => reset status to Status.None
            self.nodeStatusFileLastModTime = -1
            self._nodeStatus.reset()
        self._nodeStatus.setNodeType(self)
        return chunksRangeHasChanged

    def updateStatusFromCache(self):
        """ Update node status based on status file content/existence. """
        # Update nodeStatus from cache
        chunkChanged = self.updateNodeStatusFromCache()
        # Create chunks from cache if:
        #  - The chunk setup has changed (normal case: nodeStatus was reloaded with new data), OR
        #  - Chunks have not been created yet (recovery: a previous load cycle may have loaded
        #    the nodeStatus without triggering createChunksFromCache, e.g. due to a silent error
        #    in loadFromCache or an extra graph.update() that didn't reset the node's chunk info).
        # In both cases, the nodeStatus must contain valid chunk information (nbChunks > 0).
        if (chunkChanged or not self._chunksCreated) and self._nodeStatus.nbChunks > 0:
            # Update number of chunks
            try:
                self.createChunksFromCache()
            except Exception as e:
                logging.warning(f"Could not create chunks from cache: {e}")
                return

        if self.hasPreprocessChunk:
            if not self._preprocessChunk:
                raise ValueError("No preprocess chunk")
            self._preprocessChunk.updateStatusFromCache()

        if self.hasPostprocessChunk:
            if not self._postprocessChunk:
                raise ValueError("No postprocess chunk")
            self._postprocessChunk.updateStatusFromCache()

        if self._chunksCreated:
            for chunk in self._chunks:
                chunk.updateStatusFromCache()
        else:
            # Restore placeholder chunk if needed
            chunkPlaceholder = NodeChunk(self, desc.computation.Range(), placeholder=True)
            chunkPlaceholder._status.execMode = self._nodeStatus.execMode
            if self._nodeStatus.status in (Status.NONE, Status.SUBMITTED):
                chunkPlaceholder._status.status = self._nodeStatus.status
            elif self._nodeStatus.status in (Status.RUNNING,):
                chunkPlaceholder._status.status = Status.SUBMITTED
            else:
                chunkPlaceholder._status.status = Status.NONE
            self._chunkPlaceholder.setObjectList([chunkPlaceholder])
        self.updateOutputAttr()

    def upgradeStatusFile(self):
        """ Write node status on disk. """
        # Make sure the node has the globalStatus before saving it
        self._nodeStatus.status = self.getGlobalStatus()
        # Ensure chunk info is always in sync with the actual chunks before writing,
        # as _nodeStatus.chunks can be cleared by _resetChunks/loadFromCache and may not
        # have been restored (e.g. after createChunksFromCache which does not call setChunks).
        if self._chunksCreated and self._chunks:
            self._nodeStatus.setChunks(self._chunks)
        data = self._nodeStatus.toDict()
        statusFilepath = self.nodeStatusFile
        folder = os.path.dirname(statusFilepath)
        os.makedirs(folder, exist_ok=True)
        statusFilepathWriting = getWritingFilepath(statusFilepath)
        with open(statusFilepathWriting, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)
        renameWritingToFinalPath(statusFilepathWriting, statusFilepath)

    def setJobId(self, jid, submitterName):
        self._nodeStatus.setJob(jid, submitterName)
        self.upgradeStatusFile()

    def initStatusOnSubmit(self, forceCompute=False):
        """ Prepare chunks status when the node is in a graph that was submitted """
        hasChunkToLaunch = False
        if not self._chunksCreated:
            hasChunkToLaunch = True
            # Clear any stale chunk info from nodeStatus so that:
            # 1. The nodeStatus file written below does NOT contain chunk setup keys.
            # 2. When `meshroom_createChunks` runs on the farm, its call to
            #    `updateStatusFromCache()` will NOT recreate chunks from stale cache,
            #    allowing `node.createChunks()` to evaluate fresh chunk parameters.
            self._nodeStatus.resetChunkInfo()
        for chunk in self.getAllChunks():
            if forceCompute or chunk._status.status != Status.SUCCESS:
                hasChunkToLaunch = True
                chunk._status.setNode(self)
                chunk._status.initExternSubmit()
                chunk.upgradeStatusFile()
        if hasChunkToLaunch:
            self._nodeStatus.setNode(self)
            self._nodeStatus.initExternSubmit()
            self.upgradeStatusFile()
            self.globalStatusChanged.emit()
            if self._nodeStatus.execMode == ExecMode.EXTERN and self._nodeStatus.status in (Status.RUNNING, Status.SUBMITTED):
                chunkPlaceholder = NodeChunk(self, desc.computation.Range(), placeholder=True)
                chunkPlaceholder._status.execMode = self._nodeStatus.execMode
                chunkPlaceholder._status.status = self._nodeStatus.status
                self._chunkPlaceholder.setObjectList([chunkPlaceholder])
                self.chunksChanged.emit()

    def initStatusOnCompute(self, forceCompute=False):
        hasChunkToLaunch = False
        if not self._chunksCreated:
            hasChunkToLaunch = True
            # Same rationale as initStatusOnSubmit: clear stale chunk info
            # so that the nodeStatus file does not contain outdated chunk setup.
            self._nodeStatus.resetChunkInfo()
        for chunk in self.getAllChunks():
            if forceCompute or (chunk._status.status not in (Status.RUNNING, Status.SUCCESS)):
                hasChunkToLaunch = True
                chunk._status.setNode(self)
                chunk._status.initLocalSubmit()
                chunk.upgradeStatusFile()
        if hasChunkToLaunch:
            self._nodeStatus.setNode(self)
            self._nodeStatus.initLocalSubmit()
            self.upgradeStatusFile()
            self.globalStatusChanged.emit()
            if self._nodeStatus.execMode == ExecMode.LOCAL and self._nodeStatus.status in (Status.RUNNING, Status.SUBMITTED):
                chunkPlaceholder = NodeChunk(self, desc.computation.Range(), placeholder=True)
                chunkPlaceholder._status.execMode = self._nodeStatus.execMode
                chunkPlaceholder._status.status = self._nodeStatus.status
                self._chunkPlaceholder.setObjectList([chunkPlaceholder])
                self.chunksChanged.emit()

    def getChunkLogfileName(self, iteration: int):
        if iteration >= 0:
            stem = str(self.chunks[iteration].index)
        elif iteration == ChunkIndex.PREPROCESS:
            stem = "preprocess"
        elif iteration == ChunkIndex.POSTPROCESS:
            stem = "postprocess"
        else:
            stem = "0"
        logFileName = f"{stem}.log"
        return logFileName

    def processIteration(self, iteration):
        self._chunks[iteration].process()

    def preprocess(self, forceCompute=False, inCurrentEnv=False):
        """
        Invoke the pre process command on Client Node to execute before
        we start the processing on the node
        """
        if self.hasPreprocessChunk:
            if not self._preprocessChunk:
                raise RuntimeError("Trying to process preprocess chunk but it doesn't exist")
            self.prepareLogger(ChunkIndex.PREPROCESS)
            self._preprocessChunk.process(forceCompute, inCurrentEnv)
            self.restoreLogger()

    def process(self, forceCompute=False, inCurrentEnv=False):
        for chunk in self._chunks:
            chunk.process(forceCompute, inCurrentEnv)

    def postprocess(self, forceCompute=False, inCurrentEnv=False):
        """
        Invoke the post process command on Client Node to execute after
        the processing on the node is completed
        """
        if self.hasPostprocessChunk:
            if not self._postprocessChunk:
                raise RuntimeError("Trying to process postprocess chunk but it doesn't exist")
            self.prepareLogger(ChunkIndex.POSTPROCESS)
            self._postprocessChunk.process(forceCompute, inCurrentEnv)
            self.restoreLogger()

    def getLogHandlers(self):
        return self._handlers

    def prepareLogger(self, iteration=ChunkIndex.NONE):
        # Get file handler path
        logFileName = self.getChunkLogfileName(iteration)
        logFile = os.path.join(self.internalFolder, logFileName)
        # Setup logger
        rootLogger = logging.getLogger()
        self._logManager = LogManager(rootLogger, logFile)
        self._logManager.clearLogFile()
        self._logManager.start(self.getNodeLogLevel())

    def restoreLogger(self):
        self._logManager.restorePreviousLogger()

    def updateOutputAttr(self):
        if not self.nodeDesc:
            # For DescOnlyNodeType Compatibility Node
            if self.nodeDescDict:
                self.loadOutputAttr()
            return
        if not self.nodeDesc.hasDynamicOutputAttribute:
            return
        # logging.warning(f"updateOutputAttr: {self.name}, status: {self.globalStatus}")
        if Status.SUCCESS in [c._status.status for c in self.getChunks()] or self.isCompatibilityNode:
            self.loadOutputAttr()
        else:
            self.resetOutputAttr()

    def resetOutputAttr(self):
        if not self.nodeDesc.hasDynamicOutputAttribute:
            return
        # logging.warning("resetOutputAttr: {}".format(self.name))
        for output in self.nodeDesc.outputs:
            if output.isDynamicValue:
                if self.hasAttribute(output.name):
                    self.attribute(output.name).value = None
                else:
                    logging.warning(f"resetOutputAttr: Missing dynamic output attribute: {self.name}.{output.name}")

    def loadOutputAttr(self):
        """ Load output attributes with dynamic values from a values.json file.
        """
        # This does not apply to non dynamic output
        if not self.nodeDesc.hasDynamicOutputAttribute:
            return

        # Check existence of values.json file
        valuesFile = self.valuesFile
        if not os.path.exists(valuesFile):
            logging.warning(f"No output attr file: {valuesFile}")
            return

        # Open json file and parse
        with open(valuesFile) as jsonFile:
            data = json.load(jsonFile)

        # Loop over all output attributes in the node description
        for output in self.nodeDesc.outputs:
            # Only consider dynamic values
            if hasADynamicValue(output):
                if self.hasAttribute(output.name) and output.name in data:
                    attr = self.attribute(output.name)

                    # Use _populateFromDynamicValue for compatible classes
                    # (E.g. for ListAttributes) to properly
                    # create QObject children on the main thread
                    if hasattr(attr, '_populateFromDynamicValue') and attr._populateFromDynamicValue is not None:
                        attr._populateFromDynamicValue(data[output.name])
                    else:
                        attr.value = data[output.name]
                else:
                    if not self.hasAttribute(output.name):
                        logging.warning(f"loadOutputAttr: Missing dynamic output attribute. Node={self.name}, "
                                        f"Attribute={output.name}")
                    if output.name not in data:
                        logging.warning(f"loadOutputAttr: Missing dynamic output value in file. Node={self.name}, "
                                        f"Attribute={output.name}, File={valuesFile}, Data keys={data.keys()}")

    def saveOutputAttr(self):
        """ Save output attributes with dynamic values into a values.json file.
        """
        if not self.nodeDesc.hasDynamicOutputAttribute:
            return

        data = {}
        for output in self.nodeDesc.outputs:
            if hasADynamicValue(output):
                if self.hasAttribute(output.name):
                    # Store the primitive value and not the value itself
                    data[output.name] = self.attribute(output.name).getPrimitiveValue()
                else:
                    logging.warning(f"saveOutputAttr: Missing dynamic output attribute: {self.name}.{output.name}")

        valuesFile = self.valuesFile
        # logging.warning("save output attr: {}, value: {}".format(self.name, valuesFile))
        valuesFilepathWriting = getWritingFilepath(valuesFile)
        with open(valuesFilepathWriting, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)
        renameWritingToFinalPath(valuesFilepathWriting, valuesFile)

    def endSequence(self):
        pass

    def stopComputation(self):
        """ Stop the computation of this node. """
        if self.hasPreprocessChunk:
            if not self._preprocessChunk:
                logging.warning("No preprocess chunk to stop")
            self._preprocessChunk.stopProcess()
        if self.hasPostprocessChunk:
            if not self._postprocessChunk:
                logging.warning("No postprocess chunk to stop")
            self._postprocessChunk.stopProcess()
        if self._chunks:
            for chunk in self._chunks.values():
                chunk.stopProcess()
        else:
            # Ensure that we are up-to-date
            self.updateNodeStatusFromCache()
            # The only status possible here is submitted
            if self._nodeStatus.status is Status.SUBMITTED:
                self.upgradeStatusTo(Status.NONE)

    def getGlobalStatus(self):
        """
        Get node global status based on the status of its chunks.

        Returns:
            Status: the node global status
        """
        anyOf = (Status.ERROR, Status.STOPPED, Status.KILLED,
                 Status.RUNNING, Status.SUBMITTED)
        allOf = (Status.SUCCESS,)

        if self.isInitNode:
            return Status.INIT
        if not self._chunksCreated:
            # If the preprocess chunk failed we might not reach the chunk creation part
            if self.hasPreprocessChunk and self._preprocessChunk._status.status in anyOf:
                return self._preprocessChunk._status.status
            # Get status from nodeStatus
            return self._nodeStatus.status
        allChunks = self.getAllChunks()
        if not allChunks:
            return Status.NONE

        chunksStatus = [chunk._status.status for chunk in allChunks]
        if len(chunksStatus) == 1:
            return chunksStatus[0]

        for status in anyOf:
            if any(s == status for s in chunksStatus):
                return status
        for status in allOf:
            if all(s == status for s in chunksStatus):
                return status

        return Status.NONE

    @Slot(result=ChunkStatusData)
    def getFusedStatus(self):
        allChunks = self.getAllChunks()
        if not allChunks:
            return ChunkStatusData()
        fusedStatus = ChunkStatusData()
        fusedStatus.fromDict(allChunks[0]._status.toDict())
        for chunk in allChunks[1:]:
            fusedStatus.merge(chunk._status)
        fusedStatus.status = self.getGlobalStatus()
        return fusedStatus

    @Slot(result=ChunkStatusData)
    def getRecursiveFusedStatus(self):
        fusedStatus = self.getFusedStatus()
        nodes = self.getInputNodes(recursive=True, dependenciesOnly=True)
        for node in nodes:
            fusedStatus.merge(node.fusedStatus)
        return fusedStatus

    def _isCompatibilityNode(self):
        return False

    def _isInitNode(self):
        return isinstance(self.nodeDesc, desc.InitNode)

    def _isInputNode(self):
        return isinstance(self.nodeDesc, desc.InputNode)

    def _isIONode(self) -> bool:
        return isinstance(self.nodeDesc, desc.IONode)

    def _isBackdropNode(self) -> bool:
        return False

    @property
    def globalExecMode(self):
        if not self._chunksCreated:
            return self._nodeStatus.execMode.name
        allChunks = self.getAllChunks()
        if len(allChunks):
            return allChunks[0].getExecModeName()
        else:
            return ExecMode.NONE.name

    def _getJobName(self):
        execMode = self._nodeStatus.execMode
        if execMode == ExecMode.LOCAL:
            return "LOCAL"
        elif execMode == ExecMode.EXTERN:
            return self._nodeStatus.jobName
        else:
            return "NONE"

    def getChunks(self) -> List[NodeChunk]:
        return self._chunks

    def getAllChunks(self) -> List[NodeChunk]:
        chunks = []
        if self.hasPreprocessChunk:
            chunks.append(self._preprocessChunk)
        chunks.extend([c for c in self._chunks])
        if self.hasPostprocessChunk:
            chunks.append(self._postprocessChunk)
        return chunks

    def getSize(self):
        return self._size

    def setSize(self, value):
        if self._size == value:
            return
        self._size = value
        self.sizeChanged.emit()

    def __repr__(self):
        return self.name

    def getLocked(self):
        return self._locked

    def setLocked(self, lock):
        if self._locked == lock:
            return
        self._locked = lock
        self.lockedChanged.emit()

    @Slot()
    def updateDuplicatesStatusAndLocked(self):
        """ Update status of duplicate nodes without any latency and update locked. """
        if self.isMainNode():
            for node in self._duplicates:
                node.updateStatusFromCache()

            self.updateLocked()

    def updateLocked(self):
        currentStatus = self.getGlobalStatus()

        lockedStatus = (Status.RUNNING, Status.SUBMITTED)

        # Unlock required nodes if the current node changes to Error, Stopped or None
        # Warning: we must handle some specific cases for global start/stop
        if self._locked and currentStatus in (Status.ERROR, Status.STOPPED, Status.NONE):
            self.setLocked(False)
            inputNodes = self.getInputNodes(recursive=True, dependenciesOnly=True)

            for node in inputNodes:
                if node.getGlobalStatus() == Status.RUNNING:
                    # Return without unlocking if at least one input node is running
                    # Example: using Cancel Computation on a submitted node
                    return
            for node in inputNodes:
                node.setLocked(False)
            return

        # Avoid useless travel through nodes
        # For instance: when loading a scene with successful nodes
        if not self._locked and currentStatus == Status.SUCCESS:
            return

        if currentStatus == Status.SUCCESS:
            # At this moment, the node is necessarily locked because of previous if statement
            inputNodes = self.getInputNodes(recursive=True, dependenciesOnly=True)
            outputNodes = self.getOutputNodes(recursive=True, dependenciesOnly=True)
            stayLocked = None

            # Check if at least one dependentNode is submitted or currently running
            for node in outputNodes:
                if node.getGlobalStatus() in lockedStatus and node.isMainNode():
                    stayLocked = True
                    break
            if not stayLocked:
                self.setLocked(False)
                # Unlock every input node
                for node in inputNodes:
                    node.setLocked(False)
            return
        elif currentStatus in lockedStatus and self.isMainNode():
            self.setLocked(True)
            inputNodes = self.getInputNodes(recursive=True, dependenciesOnly=True)
            for node in inputNodes:
                node.setLocked(True)
            return

        self.setLocked(False)

    def updateDuplicates(self, nodesPerUid):
        """ Update the list of duplicate nodes (sharing the same UID). """
        if not nodesPerUid or not self._uid:
            if len(self._duplicates) > 0:
                self._duplicates.clear()
                self._hasDuplicates = False
                self.hasDuplicatesChanged.emit()
            return

        newList = [node for node in nodesPerUid.get(self._uid) if node != self]

        # If number of elements in both lists are identical,
        # we must check if their content is the same
        if len(newList) == len(self._duplicates):
            newListName = {node.name for node in newList}
            oldListName = {node.name for node in self._duplicates.values()}

            # If strict equality between both sets,
            # there is no need to set the new list
            if newListName == oldListName:
                return

        # Set the newList
        self._duplicates.setObjectList(newList)
        # Emit a specific signal 'hasDuplicates' to avoid extra binding
        # re-evaluation when the number of duplicates has changed
        if bool(len(newList)) != self._hasDuplicates:
            self._hasDuplicates = bool(len(newList))
            self.hasDuplicatesChanged.emit()

    def initFromThisSession(self) -> bool:
        """ Check if the node was submitted from the current session """
        allChunks = self.getAllChunks()
        if not self._chunksCreated or not allChunks:
            return meshroom.core.sessionUid == self._nodeStatus.submitterSessionUid
        for chunk in allChunks:
            # Technically the check on chunk._status.computeSessionUid is useless
            if meshroom.core.sessionUid not in (chunk._status.computeSessionUid, self._nodeStatus.submitterSessionUid):
                return False
        return True

    def isMainNode(self) -> bool:
        """ In case of a node with duplicates, we check that the node is the one driving the computation. """
        allChunks = self.getAllChunks()
        if len(allChunks) == 0:
            return True
        firstChunk = allChunks[0]
        if not firstChunk.statusNodeName:
            # If nothing is declared, anyone could become the main (if there are duplicates).
            return True
        return firstChunk.statusNodeName == self.name

    @Slot(result=bool)
    def canBeStopped(self) -> bool:
        """
        Return True if this node can be stopped, False otherwise. A node can be stopped if:
        - it has the "RUNNING" status (it is currently being computed)
        - it is executed locally and started from this Meshroom session OR it is executed externally on a render farm
          (and is thus associated to a job name). A node that is executed externally but without an associated job is
          likely a node that was started from another Meshroom instance, and thus cannot be stopped from this one.
        """
        if not self.isComputableType:
            return False
        if self.isCompatibilityNode:
            return False
        # Only locked nodes running in local with the same
        # computeSessionUid as the Meshroom instance can be stopped
        return (
            self.getGlobalStatus() == Status.RUNNING and self.isMainNode() and
            (
                (self.globalExecMode == ExecMode.LOCAL.name and self.initFromThisSession()) or
                (self.globalExecMode == ExecMode.EXTERN.name and self._nodeStatus.jobName != "UNKNOWN")
            )
        )

    @Slot(result=bool)
    def canBeCanceled(self) -> bool:
        """
        Return True if this node can be canceled, False otherwise. A node can be canceled if:
        - it has the "SUBMITTED" status (it is not running yet, but is expected to be in the near future)
        - it is executed locally and started from this Meshroom session OR it is executed externally on a render farm
          (and is thus associated to a job name). A node that is executed externally but without an associated job is
          likely a node that was started from another Meshroom instance, and thus cannot be canceled from this one.
        """
        if not self.isComputableType:
            return False
        if self.isCompatibilityNode:
            return False
        # Only locked nodes submitted in local with the same
        # computeSessionUid as the Meshroom instance can be canceled
        return (
            self.getGlobalStatus() == Status.SUBMITTED and self.isMainNode() and
            (
                (self.globalExecMode == ExecMode.LOCAL.name and self.initFromThisSession()) or
                (self.globalExecMode == ExecMode.EXTERN.name and self._nodeStatus.jobName != "UNKNOWN")
            )
        )

    def hasImageOutputAttribute(self) -> bool:
        """
        Return True if at least one attribute has the 'image' semantic (and can thus be loaded in
        the 2D Viewer), False otherwise.
        """
        for attr in self._attributes:
            if not attr.enabled or not attr.isOutput:
                continue
            if attr.desc.semantic == "image":
                return True
        return False

    def hasSequenceOutputAttribute(self) -> bool:
        """
        Return True if at least one attribute has the 'sequence' semantic (and can thus be loaded in
        the 2D Viewer), False otherwise.
        """
        for attr in self._attributes:
            if not attr.enabled or not attr.isOutput:
                continue
            if attr.desc.semantic in ("sequence", "imageList"):
                return True
        return False

    def has3DOutputAttribute(self):
        """
        Return True if at least one attribute is a File that can be loaded in the 3D Viewer,
        False otherwise. Init nodes have no computed outputs, so their inputs are considered too.
        """
        return next((attr for attr in self._attributes
                     if attr.enabled and (attr.isOutput or self.isInitNode) and attr.is3dDisplayable), None) is not None

    def hasTextOutputAttribute(self) -> bool:
        """
        Return True if at least one attribute is a text file that can be loaded in the Text Viewer,
        False otherwise.
        """
        return next((attr for attr in self._attributes if attr.enabled and attr.isOutput and attr.isTextDisplayable), None) is not None

    def _hasInvalidAttribute(self):
        for attribute in self._attributes:
            if len(attribute.errorMessages) > 0:
                return True
        return False

    def _hasDisplayableShape(self):
        """
        Return True if at least one attribute is a ShapeAttribute, a ShapeListAttribute or a shape File.
        Note: These attributes can be loaded in the ShapeViewer / ShapeEditor.
        False otherwise.
        """
        return next((attr for attr in self._attributes if attr.hasDisplayableShape or
                     attr.desc.semantic == "shapeFile"), None) is not None

    def _hasDisplayableSurveyPoint(self):
        """
        Return True if at least one attribute can provide a SurveyPoint display in Viewer3D.
        False otherwise.
        """
        for attr in self._attributes:
            if attr.type == "SurveyPoint":
                return True
            if attr.type == "ShapeList" and attr.desc.elementDesc.__class__.__name__ == "SurveyPoint":
                return True
        return False


    nodeNameChanged = Signal()
    name = Property(str, getName, notify=nodeNameChanged)
    defaultLabel = Property(str, getDefaultLabel, constant=True)
    nodeType = Property(str, nodeType.fget, constant=True)
    documentation = Property(str, getDocumentation, constant=True)
    nodeInfo = Property(Variant, getNodeInfo, constant=True)
    nodeVersionType = Property(int, lambda self: int(self.nodeDesc.nodeVersionType) if self.nodeDesc else int(desc.NodeVersionType.UNKNOWN), constant=True)
    nodeStatusChanged = Signal()
    nodeStatus = Property(Variant, lambda self: self._nodeStatus, notify=nodeStatusChanged)
    nodeStatusNodeName = Property(str, lambda self: self._nodeStatus.nodeName, notify=nodeStatusChanged)
    positionChanged = Signal()
    position = Property(Variant, position.fget, position.fset, notify=positionChanged)
    x = Property(float, lambda self: self._position.x, notify=positionChanged)
    y = Property(float, lambda self: self._position.y, notify=positionChanged)
    attributes = Property(BaseObject, getAttributes, constant=True)
    internalAttributes = Property(BaseObject, getInternalAttributes, constant=True)
    internalAttributesChanged = Signal()
    label = Property(str, getLabel, notify=internalAttributesChanged)
    color = Property(str, getColor, notify=internalAttributesChanged)
    invalidation = Property(str, getInvalidationMessage, notify=internalAttributesChanged)
    comment = Property(str, getComment, notify=internalAttributesChanged)
    fontSize = Property(int, getFontSize, notify=internalAttributesChanged)
    fontColor = Property(str, getFontColor, notify=internalAttributesChanged)
    nodeWidth = Property(int, getNodeWidth, notify=internalAttributesChanged)
    nodeHeight = Property(int, getNodeHeight, notify=internalAttributesChanged)
    internalFolderChanged = Signal()
    internalFolder = Property(str, internalFolder.fget, notify=internalFolderChanged)
    valuesFile = Property(str, valuesFile.fget, notify=internalFolderChanged)
    depthChanged = Signal()
    depth = Property(int, depth.fget, notify=depthChanged)
    minDepth = Property(int, minDepth.fget, notify=depthChanged)
    chunksCreatedChanged = Signal()
    chunksCreated = Property(bool, lambda self: self._chunksCreated, notify=chunksCreatedChanged)
    chunksChanged = Signal()
    chunks = Property(Variant, getChunks, notify=chunksChanged)
    allChunks = Property(Variant, getAllChunks, notify=chunksChanged)
    hasPreprocessChunk = Property(bool, lambda self: self.nodeDesc.hasPreprocess if self.nodeDesc else False, notify=chunksChanged)
    preprocessChunk = Property(Variant, lambda self: self._preprocessChunk, notify=chunksChanged)
    hasPostprocessChunk = Property(bool, lambda self: self.nodeDesc.hasPostprocess if self.nodeDesc else False, notify=chunksChanged)
    postprocessChunk = Property(Variant, lambda self: self._postprocessChunk, notify=chunksChanged)
    chunkPlaceholder = Property(Variant, lambda self: self._chunkPlaceholder, notify=chunksChanged)
    nbParallelizationBlocks = Property(int, lambda self: len(self._chunks) if self._chunksCreated else 0, notify=chunksChanged)
    sizeChanged = Signal()
    size = Property(int, getSize, notify=sizeChanged)
    globalStatusChanged = Signal()
    globalStatus = Property(str, lambda self: self.getGlobalStatus().name, notify=globalStatusChanged)
    fusedStatus = Property(ChunkStatusData, getFusedStatus, notify=globalStatusChanged)
    elapsedTime = Property(float, lambda self: self.getFusedStatus().elapsedTime, notify=globalStatusChanged)
    recursiveElapsedTime = Property(float, lambda self: self.getRecursiveFusedStatus().elapsedTime,
                                    notify=globalStatusChanged)
    isCompatibilityNode = Property(bool, lambda self: self._isCompatibilityNode(), constant=True)
    isInitNode = Property(bool, lambda self: self._isInitNode(), constant=True)
    isInputNode = Property(bool, lambda self: self._isInputNode(), constant=True)
    isIONode = Property(bool, lambda self: self._isIONode(), constant=True)
    isBackdropNode = Property(bool, lambda self: self._isBackdropNode(), constant=True)

    globalExecMode = Property(str, globalExecMode.fget, notify=globalStatusChanged)
    jobName = Property(str, lambda self: self._getJobName(), notify=globalStatusChanged)
    isExternal = Property(bool, isExtern, notify=globalStatusChanged)
    isComputed = Property(bool, _isComputed, notify=globalStatusChanged)
    isComputableType = Property(bool, _isComputableType, notify=globalStatusChanged)
    aliveChanged = Signal()
    alive = Property(bool, alive.fget, alive.fset, notify=aliveChanged)
    lockedChanged = Signal()
    locked = Property(bool, getLocked, setLocked, notify=lockedChanged)
    duplicates = Property(Variant, lambda self: self._duplicates, constant=True)
    hasDuplicatesChanged = Signal()
    hasDuplicates = Property(bool, lambda self: self._hasDuplicates, notify=hasDuplicatesChanged)

    outputAttrChanged = Signal()
    hasImageOutput = Property(bool, hasImageOutputAttribute, notify=outputAttrChanged)
    hasSequenceOutput = Property(bool, hasSequenceOutputAttribute, notify=outputAttrChanged)
    has3DOutput = Property(bool, has3DOutputAttribute, notify=outputAttrChanged)
    hasTextOutput = Property(bool, hasTextOutputAttribute, notify=outputAttrChanged)
    # Whether the node contains a ShapeAttribute, a ShapeListAttribute or a shape File.
    hasDisplayableShape = Property(bool, _hasDisplayableShape, constant=True)
    # Whether the node contains a SurveyPoint attribute or a SurveyPoint shape list for Viewer3D.
    hasDisplayableSurveyPoint = Property(bool, _hasDisplayableSurveyPoint, constant=True)

    hasInvalidAttributeChanged = Signal()
    hasInvalidAttribute = Property(bool, _hasInvalidAttribute, notify=hasInvalidAttributeChanged)
