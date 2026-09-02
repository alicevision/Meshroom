import logging
from typing import Any, Optional, Union
from collections.abc import Iterable

import meshroom.core
from meshroom.core import Version, desc
from meshroom.core.desc.anySet import AnySet
from meshroom.core.node import BackdropNode, CompatibilityIssue, CompatibilityNode, Node, Position


def nodeFactory(
    nodeData: dict,
    name: Optional[str] = None,
    inTemplate: bool = False,
    expectedUid: Optional[str] = None,
    nodeDescDict: dict = None,
) -> Union[Node, BackdropNode, CompatibilityNode]:
    """
    Create a node instance by deserializing the given node data.
    If the serialized data matches the corresponding node type description, a Node instance is created.
    If any compatibility issue occurs, a NodeCompatibility instance is created instead.

    Args:
        nodeData: The serialized Node data.
        name: The node's name.
        inTemplate: True if the node is created as part of a graph template.
        expectedUid: The expected UID of the node within the context of a Graph.

    Returns:
        The created Node instance.
    """
    return _NodeCreator(nodeData, name, inTemplate, expectedUid, nodeDescDict).create()


def getNodeConstructor(nodeType: str, position: Optional[Position]=None, **kwargs) -> Union[BackdropNode, Node]:
    constructors = {
        "Backdrop": BackdropNode,
    }
    constructor = constructors.get(nodeType, Node)
    return constructor(nodeType, position=position, **kwargs)


def isCustomAttribute(attribute:Any) -> bool:
    # Check if the given attribute is a AnySet instance or a child of a AnySet

    if isinstance(attribute, AnySet):
        return True
    if hasattr(attribute, 'root') and isinstance(attribute.root, AnySet):
        return True
    return False

class _NodeCreator:

    def __init__(
        self,
        nodeData: dict,
        name: Optional[str] = None,
        inTemplate: bool = False,
        expectedUid: Optional[str] = None,
        nodeDescDict: dict = None,
    ):
        self.nodeData = nodeData
        self.name = name
        self.inTemplate = inTemplate
        self.expectedUid = expectedUid

        self._normalizeNodeData()

        self.nodeType = self.nodeData["nodeType"]
        self.inputs = self.nodeData.get("inputs", {})
        self.internalInputs = self.nodeData.get("internalInputs", {})
        self.outputs = self.nodeData.get("outputs", {})
        self.version = self.nodeData.get("version", None)
        self.position = Position(*self.nodeData.get("position", []))
        self.uid = self.nodeData.get("uid", None)
        self.nodeDescDict = nodeDescDict
        self.nodeDesc = None
        if meshroom.core.pluginManager.isNodeDescRegistered(self.nodeType):
            self.nodeDesc = meshroom.core.pluginManager.getNodeDescProvider(self.nodeType).nodeDescClass

    def create(self) -> Union[Node, BackdropNode, CompatibilityNode]:
        compatibilityIssue = self._checkCompatibilityIssues()
        if compatibilityIssue:
            node = self._createCompatibilityNode(compatibilityIssue)
            node = self._tryUpgradeCompatibilityNode(node)
        else:
            node = self._createNode()
        return node

    def _normalizeNodeData(self):
        """Consistency fixes for backward compatibility with older serialized data."""
        # Inputs were previously saved as "attributes".
        if "inputs" not in self.nodeData and "attributes" in self.nodeData:
            self.nodeData["inputs"] = self.nodeData["attributes"]
            del self.nodeData["attributes"]

    def _checkCompatibilityIssues(self) -> Optional[CompatibilityIssue]:
        if self.nodeDesc is None:
            if meshroom.core.pluginManager.getPluginFromNodeDesc(self.nodeType) is not None:
                return CompatibilityIssue.PluginIssue
            if self.nodeDescDict is not None:
                return CompatibilityIssue.DescOnlyNodeType
            return CompatibilityIssue.UnknownNodeType

        if not self._checkUidCompatibility():
            return CompatibilityIssue.UidConflict

        if not self._checkVersionCompatibility():
            return CompatibilityIssue.VersionConflict

        if not self._checkDescriptionCompatibility():
            return CompatibilityIssue.DescriptionConflict

        return None

    def _checkUidCompatibility(self) -> bool:
        return self.expectedUid is None or self.expectedUid == self.uid

    def _checkVersionCompatibility(self) -> bool:
        # Special case: a node with a version set to None indicates
        # that it has been created from the current version of the node type.
        nodeCreatedFromCurrentVersion = self.version is None
        if nodeCreatedFromCurrentVersion:
            return True
        nodeTypeCurrentVersion = meshroom.core.nodeVersion(self.nodeDesc)
        # If the node type has not current version information, assume compatibility.
        if nodeTypeCurrentVersion is None:
            return True
        return Version(self.version).major == Version(nodeTypeCurrentVersion).major

    def _checkDescriptionCompatibility(self) -> bool:
        # Only perform strict attribute name matching for non-template graphs,
        # since only non-default-value input attributes are serialized in templates.
        if not self.inTemplate:
            if not self._checkAttributesNamesMatchDescription():
                return False

        return self._checkAttributesAreCompatibleWithDescription()

    def _checkAttributesNamesMatchDescription(self) -> bool:
        return (
            self._checkInputAttributesNames()
            and self._checkOutputAttributesNames()
            and self._checkInternalAttributesNames()
        )

    def _checkAttributesAreCompatibleWithDescription(self) -> bool:

        inputAnySet = [attribute.name for attribute in self.nodeDesc.inputs if isCustomAttribute(attribute)]
        outputAnySet = [attribute.name for attribute in self.nodeDesc.outputs if isCustomAttribute(attribute)]
        staticInputs = {k: v for k, v in self.inputs.items() if not k in inputAnySet }
        staticOutputs = {k: v for k, v in self.outputs.items() if not k in outputAnySet }

        # Combine regular internal attributes with internal flow inputs for compatibility checking,
        # as internal flow inputs (when connected) appear in the 'internalInputs' section of the file.
        allInternalDescriptions = list(self.nodeDesc.internalInputs) + list(self.nodeDesc.internalFlowInputs)
        return (
            self._checkAttributesCompatibility(self.nodeDesc.inputs, staticInputs)
            and self._checkAttributesCompatibility(allInternalDescriptions, self.internalInputs)
            and self._checkAttributesCompatibility(self.nodeDesc.outputs, staticOutputs)
        )

    def _checkInputAttributesNames(self) -> bool:
        def serializedInput(attr: desc.Attribute) -> bool:
            """ Filter that excludes not-serialized desc input attributes. """
            if isinstance(attr, desc.PushButtonParam):
                # PushButtonParam are not serialized has they do not hold a value.
                return False
            if isinstance(attr, desc.Flow):
                # Flow inputs are only serialized when connected (as link expressions).
                # They are optional in the serialized data, so they are handled separately.
                return False
            return True

        def optionalInput(attr: desc.Attribute) -> bool:
            """ Return True if the attribute may optionally be serialized (present or absent in file). """
            return isinstance(attr, desc.Flow)

        refAttributes = filter(serializedInput, self.nodeDesc.inputs)
        # User-defined Flow inputs in nodeDesc.inputs are optional in the 'inputs' section.
        # Internal flow inputs (internalFlowInputs) now go in 'internalInputs', not 'inputs'.
        optionalFlowAttrs = list(filter(optionalInput, self.nodeDesc.inputs))
        return self._checkAttributesNamesMatchWithOptional(refAttributes, self.inputs, optionalFlowAttrs)

    def _checkOutputAttributesNames(self) -> bool:
        def serializedOutput(attr: desc.Attribute) -> bool:
            """ Filter that excludes not-serialized desc output attributes. """
            if attr.isDynamicValue:
                # Dynamic outputs values are not serialized with the node,
                # as their value is written in the computed output data.
                return False
            if isinstance(attr, desc.Flow):
                # Flow outputs hold no data and are never serialized.
                return False
            return True

        refAttributes = filter(serializedOutput, self.nodeDesc.outputs)
        return self._checkAttributesNamesStrictlyMatch(refAttributes, self.outputs)

    def _checkInternalAttributesNames(self) -> bool:
        # Required: all invalidating internal attributes must be present.
        invalidatingDescAttributes = [attr.name for attr in self.nodeDesc.internalInputs if attr.invalidate]
        if not all(attr in self.internalInputs.keys() for attr in invalidatingDescAttributes):
            return False
        # Optional: internal Flow attributes may optionally appear in internalInputs
        # (as link expressions when connected).
        allInternalDescriptions = list(self.nodeDesc.internalInputs) + list(self.nodeDesc.internalFlowInputs)
        allowedNames = {attr.name for attr in allInternalDescriptions}
        return all(k in allowedNames for k in self.internalInputs.keys())

    def _checkAttributesNamesStrictlyMatch(
        self, descAttributes: Iterable[desc.Attribute], attributesDict: dict[str, Any]
    ) -> bool:
        refNames = sorted([attr.name for attr in descAttributes])
        attrNames = sorted(attributesDict.keys())
        return refNames == attrNames

    def _checkAttributesNamesMatchWithOptional(self,
                                               requiredDescAttributes: Iterable[desc.Attribute],
                                               attributesDict: dict[str, Any],
                                               optionalDescAttributes: Iterable[desc.Attribute]) -> bool:
        """
        Check that attribute names in 'attributesDict' match the expected description,
        where 'requiredDescAttributes' must all be present and 'optionalDescAttributes'
        may optionally be present.

        Args:
            requiredDescAttributes: Desc attributes that must be serialized.
            attributesDict: The serialized attribute dict to check against.
            optionalDescAttributes: Desc attributes that may or may not be serialized.

        Returns:
            True if all required attributes are present and no unknown attributes exist.
        """
        requiredNames = set(attr.name for attr in requiredDescAttributes)
        optionalNames = set(attr.name for attr in optionalDescAttributes)
        allowedNames = requiredNames | optionalNames
        attrNames = set(attributesDict.keys())

        # All required attributes must be present in the serialized data (subset check).
        if not requiredNames <= attrNames:
            return False
        # All serialized attribute names must be either required or optional (no unknown attrs).
        if not attrNames <= allowedNames:
            return False

        return True

    def _checkAttributesCompatibility(
        self, descAttributes: list[desc.Attribute], attributesDict: dict[str, Any]
    ) -> bool:
        return all(
            CompatibilityNode.attributeDescFromName(descAttributes, attrName, value) is not None
            for attrName, value in attributesDict.items()
        )

    def _createNode(self) -> Union[BackdropNode, Node]:
        logging.info(f"Creating node '{self.name}'")
        # TODO: user inputs/outputs may conflicts with internal names (like logLevel, position, uid)
        # The line below can cause UI issues but at least prevent crashes
        internalInputs = {k: v for k, v in self.internalInputs.items() if k not in self.inputs.keys()}
        return getNodeConstructor(
            self.nodeType,
            position=self.position,
            uid=self.uid,
            **self.inputs,
            **internalInputs,
            **self.outputs,
        )

    def _createCompatibilityNode(self, compatibilityIssue) -> CompatibilityNode:
        logging.warning(f"Compatibility issue detected for node '{self.name}': {compatibilityIssue.name}")
        return CompatibilityNode(
            self.nodeType, self.nodeData, nodeDescDict=self.nodeDescDict, position=self.position, issue=compatibilityIssue
        )

    def _tryUpgradeCompatibilityNode(self, node: CompatibilityNode) -> Union[Node, CompatibilityNode]:
        """Handle possible upgrades of CompatibilityNodes, when no computed data is associated to the Node."""
        if node.issue == CompatibilityIssue.UnknownNodeType or node.issue == CompatibilityIssue.DescOnlyNodeType:
            return node

        # Nodes in templates are not meant to hold computation data.
        if self.inTemplate:
            logging.warning(f"Compatibility issue in template: performing automatic upgrade on '{self.name}'")
            return node.upgrade()

        # Backward compatibility: "uid" was not serialized.
        if not self.uid:
            logging.warning(f"No serialized output data: performing automatic upgrade on '{self.name}'")
            return node.upgrade()

        return node
