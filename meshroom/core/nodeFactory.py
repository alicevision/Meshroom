import logging
from typing import Any, Iterable, Optional, Union

import meshroom.core
from meshroom.core import Version, desc
from meshroom.core.node import CompatibilityIssue, CompatibilityNode, Node, Position


def nodeFactory(
    nodeData: dict,
    name: Optional[str] = None,
    inTemplate: bool = False,
    expectedUid: Optional[str] = None,
) -> Union[Node, CompatibilityNode]:
    """
    Create a node instance by deserializing the given node data.
    If the serialized data matches the corresponding node type description, a Node instance is created.
    If any compatibility issue occurs, a NodeCompatibility instance is created instead.

    Args:
        nodeDict: The serialized Node data.
        name: (optional) The node's name.
        inTemplate: (optional) True if the node is created as part of a graph template.
        expectedUid: (optional) The expected UID of the node within the context of a Graph.

    Returns:
        The created Node instance.
    """
    return _NodeCreator(nodeData, name, inTemplate, expectedUid).create()


class _NodeCreator:

    def __init__(
        self,
        nodeData: dict,
        name: Optional[str] = None,
        inTemplate: bool = False,
        expectedUid: Optional[str] = None,
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
        self.internalFolder = self.nodeData.get("internalFolder")
        self.position = Position(*self.nodeData.get("position", []))
        self.uid = self.nodeData.get("uid", None)
        self.nodeDesc = meshroom.core.nodesDesc.get(self.nodeType, None)

    def create(self) -> Union[Node, CompatibilityNode]:
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
        nodeTypeCurrentVersion = meshroom.core.nodeVersion(self.nodeDesc, "0.0")
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
        return (
            self._checkAttributesCompatibility(self.nodeDesc.inputs, self.inputs)
            and self._checkAttributesCompatibility(self.nodeDesc.internalInputs, self.internalInputs)
            and self._checkAttributesCompatibility(self.nodeDesc.outputs, self.outputs)
        )

    def _checkInputAttributesNames(self) -> bool:
        def serializedInput(attr: desc.Attribute) -> bool:
            """Filter that excludes not-serialized desc input attributes."""
            if isinstance(attr, desc.PushButtonParam):
                # PushButtonParam are not serialized has they do not hold a value.
                return False
            return True

        refAttributes = filter(serializedInput, self.nodeDesc.inputs)
        return self._checkAttributesNamesStrictlyMatch(refAttributes, self.inputs)

    def _checkOutputAttributesNames(self) -> bool:
        def serializedOutput(attr: desc.Attribute) -> bool:
            """Filter that excludes not-serialized desc output attributes."""
            if attr.isDynamicValue:
                # Dynamic outputs values are not serialized with the node,
                # as their value is written in the computed output data.
                return False
            return True

        refAttributes = filter(serializedOutput, self.nodeDesc.outputs)
        return self._checkAttributesNamesStrictlyMatch(refAttributes, self.outputs)

    def _checkInternalAttributesNames(self) -> bool:
        invalidatingDescAttributes = [attr.name for attr in self.nodeDesc.internalInputs if attr.invalidate]
        return all(attr in self.internalInputs.keys() for attr in invalidatingDescAttributes)

    def _checkAttributesNamesStrictlyMatch(
        self, descAttributes: Iterable[desc.Attribute], attributesDict: dict[str, Any]
    ) -> bool:
        refNames = sorted([attr.name for attr in descAttributes])
        attrNames = sorted(attributesDict.keys())
        return refNames == attrNames

    def _checkAttributesCompatibility(
        self, descAttributes: list[desc.Attribute], attributesDict: dict[str, Any]
    ) -> bool:
        return all(
            CompatibilityNode.attributeDescFromName(descAttributes, attrName, value) is not None
            for attrName, value in attributesDict.items()
        )

    def _createNode(self) -> Node:
        logging.info(f"Creating node '{self.name}'")
        return Node(
            self.nodeType,
            position=self.position,
            uid=self.uid,
            **self.inputs,
            **self.internalInputs,
            **self.outputs,
        )

    def _createCompatibilityNode(self, compatibilityIssue) -> CompatibilityNode:
        logging.warning(f"Compatibility issue detected for node '{self.name}': {compatibilityIssue.name}")
        return CompatibilityNode(
            self.nodeType, self.nodeData, position=self.position, issue=compatibilityIssue
        )

    def _tryUpgradeCompatibilityNode(self, node: CompatibilityNode) -> Union[Node, CompatibilityNode]:
        """Handle possible upgrades of CompatibilityNodes, when no computed data is associated to the Node."""
        if node.issue == CompatibilityIssue.UnknownNodeType:
            return node
        
        # Nodes in templates are not meant to hold computation data.
        if self.inTemplate:
            logging.warning(f"Compatibility issue in template: performing automatic upgrade on '{self.name}'")
            return node.upgrade()

        # Backward compatibility: "internalFolder" was not serialized.
        if not self.internalFolder:
            logging.warning(f"No serialized output data: performing automatic upgrade on '{self.name}'")

        return node
