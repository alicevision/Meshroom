#!/usr/bin/env python

import copy
import json
import logging
import os
from enum import Enum

from meshroom.common import Property
from meshroom.core import desc, nodeVersion, Version, MrNodeType
from meshroom.core.attribute import attributeFactory, attributeDescriptionFactory, Attribute
from meshroom.core.desc.node import InternalAttributesFactory
from meshroom.core.exception import NodeUpgradeError
from meshroom.core.node.chunk import NodeChunk
from meshroom.core.node.baseNode import BaseNode
from meshroom.core.node.node import Node


class CompatibilityIssue(Enum):
    """
    Enum describing compatibility issues when deserializing a Node.
    """
    UnknownIssue = 0  # unknown issue fallback
    UnknownNodeType = 1  # the node type has no corresponding description class
    VersionConflict = 2  # mismatch between node's description version and serialized node data
    DescriptionConflict = 3  # mismatch between node's description attributes and serialized node data
    UidConflict = 4  # mismatch between computed UIDs and UIDs stored in serialized node data
    PluginIssue = 5  # issue when loading the associated plugin
    DescOnlyNodeType = 6  # the node type is unknown, but its description was found in the .mg file. It cannot be instantiated


class CompatibilityNode(BaseNode):
    """
    Fallback BaseNode subclass to instantiate Nodes having compatibility issues with current type description.
    CompatibilityNode creates an 'empty-shell' exposing the deserialized node as-is,
    with all its inputs and precomputed outputs.
    """
    def __init__(self, nodeType, nodeDict, nodeDescDict=None, position=None, issue=CompatibilityIssue.UnknownIssue, parent=None):
        super().__init__(nodeType, position, parent)

        self.issue = issue
        # Make deepcopies of nodeDict and nodeDescDict to handle CompatibilityNode duplication
        # and be able to change modified inputs (see CompatibilityNode.toDict)
        self.nodeDict = copy.deepcopy(nodeDict)
        self.nodeDescDict = copy.deepcopy(nodeDescDict)
        version = self.nodeDict.get("version")
        if version is None and nodeDescDict:
            version = nodeDescDict.get("version")
        self.version = Version(version) if version else None

        self._inputs = self.nodeDict.get("inputs", {})
        self._internalInputs = self.nodeDict.get("internalInputs", {})
        self.outputs = self.nodeDict.get("outputs", {})
        self._uid = self.nodeDict.get("uid", None)

        # Restore parallelization settings
        self.parallelization = self.nodeDict.get("parallelization", {})
        self.splitCount = self.parallelization.get("split", 1)
        self.setSize(self.parallelization.get("size", 1))

        # Create input attributes
        for attrName, value in self._inputs.items():
            self._addAttribute(attrName, value, isOutput=False)

        # Create outputs attributes
        for attrName, value in self.outputs.items():
            self._addAttribute(attrName, value, isOutput=True)

        # Create internal attributes
        for attrName, value in self._internalInputs.items():
            self._addAttribute(attrName, value, isOutput=False, internalAttr=True)

        if self.nodeDescDict:
            # Add internal flowInputs to internalAttributes
            if "flowInputs" not in self._internalAttributes.keys():
                self._addAttribute("flowInputs", None, isOutput=False, internalAttr=True)
            # Add internal flowOutput to internalAttributes
            if "flowOutput" not in self._internalAttributes.keys():
                self._addAttribute("flowOutput", None, isOutput=True, internalAttr=True)

            # Add any input/output attribute present in the node description but not in the serialized node data
            existingAttrNames = set(self._attributes.keys())
            for attrName in self.nodeDescDict.get("inputs", {}).keys():
                if attrName not in existingAttrNames:
                    self._addAttribute(attrName, None, isOutput=False)
            for attrName in self.nodeDescDict.get("outputs", {}).keys():
                if attrName not in existingAttrNames:
                    self._addAttribute(attrName, None, isOutput=True)

        # Create NodeChunks matching serialized parallelization settings
        self._chunks.setObjectList([
            NodeChunk(self, desc.Range(i, blockSize=self.parallelization.get("blockSize", 0)))
            for i in range(self.splitCount)
        ])

    def _isCompatibilityNode(self):
        return True

    def _updateNodeSize(self):
        # Block the recompute of the node size for compatibility nodes
        pass

    @staticmethod
    def attributeDescFromValue(attrName, value, isOutput):
        """
        Generate an attribute description (desc.Attribute) that best matches 'value'.

        Args:
            attrName (str): the name of the attribute
            value: the value of the attribute
            isOutput (bool): whether the attribute is an output

        Returns:
            desc.Attribute: the generated attribute description
        """
        params = {
            "name": attrName, "label": attrName,
            "description": "Incompatible parameter",
            "value": value, "invalidate": False,
            "commandLineGroup": "incompatible"
        }
        logging.warning(f"Generating attribute description for {attrName} with value {value}")
        if isinstance(value, bool):
            return desc.BoolParam(**params)
        if isinstance(value, int):
            return desc.IntParam(range=None, **params)
        elif isinstance(value, float):
            return desc.FloatParam(range=None, **params)
        elif isinstance(value, str):
            if isOutput or os.path.isabs(value):
                return desc.File(**params)
            elif Attribute.isLinkExpression(value):
                # Do not consider link expression as a valid default desc value.
                # When the link expression is applied and transformed to an actual link,
                # the systems resets the value using `Attribute.resetToDefaultValue` to indicate
                # that this link expression has been handled.
                # If the link expression is stored as the default value, it will never be cleared,
                # leading to unexpected behavior where the link expression on a CompatibilityNode
                # could be evaluated several times and/or incorrectly.
                params["value"] = ""
                return desc.File(**params)
            else:
                return desc.StringParam(**params)
        # Serialized AnySet: its children are self-describing (each one carries its own type), so an empty
        # AnySet description is enough, the AnySet attribute rebuilds its children from the serialized value.
        # Generic inference cannot handle it, as its children may hold values of different types.
        elif CompatibilityNode._isSerializedAnySet(value):
            return desc.AnySet(name=attrName, label=attrName, description="Incompatible parameter",
                               commandLineGroup="incompatible")
        # List/GroupAttribute: recursively build descriptions
        elif isinstance(value, (list, dict)):
            del params["value"]
            del params["invalidate"]
            attrDesc = None
            if isinstance(value, list):
                elt = value[0] if value else ""  # Fallback: empty string value if list is empty
                eltDesc = CompatibilityNode.attributeDescFromValue("element", elt, isOutput)
                attrDesc = desc.ListAttribute(elementDesc=eltDesc, **params)
            elif isinstance(value, dict):
                items = []
                for key, value in value.items():
                    eltDesc = CompatibilityNode.attributeDescFromValue(key, value, isOutput)
                    items.append(eltDesc)
                attrDesc = desc.GroupAttribute(items=items, **params)
            # Override empty default value with
            attrDesc._value = value
            return attrDesc
        # Handle any other type of parameters as Strings
        return desc.StringParam(**params)

    @staticmethod
    def _isSerializedAnySet(value) -> bool:
        """
        Return whether 'value' has the shape of a serialized AnySet, i.e. a dict holding a "children" list
        in which every child is a dict providing at least its "name" and "type".
        """
        if not isinstance(value, dict) or not isinstance(value.get("children"), list):
            return False
        return all(isinstance(child, dict) and "name" in child and "type" in child for child in value["children"])

    @staticmethod
    def attributeDescFromName(refAttributes, name, value, strict=True):
        """
        Try to find a matching attribute description in refAttributes for given attribute
        'name' and 'value'.

        Args:
            refAttributes ([desc.Attribute]): reference Attributes to look for a description
            name (str): attribute's name
            value: attribute's value
            strict: strict test for the match (for instance, regarding a group with some parameter changes)

        Returns:
            desc.Attribute: an attribute description from refAttributes if a match is found, None otherwise.
        """
        # from original node description based on attribute's name
        attrDesc = next((d for d in refAttributes if d.name == name), None)
        if attrDesc is None:
            return None
        # We have found a description, and we still need to
        # check if the value matches the attribute description.
        #
        # If it is a serialized link expression (no proper value to set/evaluate)
        if Attribute.isLinkExpression(value):
            return attrDesc

        # If it is a GroupAttribute, all the attributes within the group should be matched
        # individually so that links can correctly be evaluated.
        if isinstance(attrDesc, desc.GroupAttribute):
            for k, v in value.items():
                if CompatibilityNode.attributeDescFromName(attrDesc.items,
                                                           k, v, strict=True) is None:
                    return None
            return attrDesc

        # If it passes the 'matchDescription' test
        if attrDesc.matchDescription(value, strict):
            return attrDesc

        return None

    @staticmethod
    def attributeDescFromDict(nodeDescDict, name, value, isOutput, strict=True):
        """
        Try to find a matching attribute description in nodeDescDict for given attribute
        'name' and 'value'.

        Args:
            nodeDescDict (dict): node description dictionary containing inputs and outputs
            name (str): attribute's name
            value: attribute's value
            isOutput: whether the attribute is an output
            strict: strict test for the match (for instance, regarding a group with some parameter changes)

        Returns:
            desc.Attribute: an attribute description from nodeDescDict if a match is found, None otherwise.
        """
        refAttrs = nodeDescDict["outputs"] if isOutput else nodeDescDict["inputs"]
        if name not in refAttrs:
            return None
        refAttrs[name]["name"] = name

        if refAttrs[name].get("type") == "AnySet" and value is not None:
            # Add the children attribute descriptions from value to the node description
            refAttrs[name]["items"] = {child["name"]: copy.deepcopy(child) for child in value["children"]}
            # Replace the children list with a dictionary of child values
            value = {child["name"]: child["value"] for child in value["children"] if "value" in child}

        # Recursively replace the 'items' dictionary with a list of items for GroupAttributes/AnySets
        # Define a recursive function to handle nested GroupAttributes/AnySets
        def process_group_items(attr_dict):
            if "items" in attr_dict:
                if isinstance(attr_dict["items"], list):
                    # In case of anySet, the items are stored as a list of dictionaries
                    # Convert list of items to a dictionary with item names as keys
                    attr_dict["items"] = {item["name"]: item for item in attr_dict["items"]}

                for k in attr_dict["items"].keys():
                    attr_dict["items"][k]["name"] = k
                    process_group_items(attr_dict["items"][k])  # Recursively process nested GroupAttributes
                attr_dict["items"] = list(attr_dict["items"].values())  # Keep the original order of items
            if "elementDesc" in attr_dict:
                process_group_items(attr_dict["elementDesc"])  # Recursively process elementDesc
            if "shape" in attr_dict:
                process_group_items(attr_dict["shape"])  # Recursively process shape

        process_group_items(refAttrs[name])

        attrDesc = attributeDescriptionFactory(refAttrs[name])

        # No serialized value to match (e.g. outputs or default-valued inputs in templates): the attribute only
        # exists in the node description, which is used as is
        if value is None:
            return attrDesc

        if Attribute.isLinkExpression(value):
            return attrDesc

        # If it is a GroupAttribute, all the attributes within the group should be matched
        # individually so that links can correctly be evaluated
        if isinstance(attrDesc, desc.GroupAttribute):
            for k, v in value.items():
                if CompatibilityNode.attributeDescFromName(attrDesc.items, k, v, strict) is None:
                    return None
            return attrDesc

        # return the attribute description if the given value passes the 'matchDescription' test
        return attrDesc if attrDesc.matchDescription(value, strict) else None

    def _addAttribute(self, name, val, isOutput, internalAttr=False):
        """
        Add a new attribute on this node.

        Args:
            name (str): the name of the attribute
            val: the attribute's value
            isOutput: whether the attribute is an output
            internalAttr: whether the attribute is internal

        Returns:
            bool: whether the attribute exists in the node description
        """
        attrDesc = None
        if self.nodeDesc:
            if internalAttr:
                refAttrs = self.nodeDesc.internalInputs
            else:
                refAttrs = self.nodeDesc.outputs if isOutput else self.nodeDesc.inputs
            attrDesc = CompatibilityNode.attributeDescFromName(refAttrs, name, val)
        matchDesc = attrDesc is not None
        if attrDesc is None and self.nodeDescDict:
            if internalAttr:
                internalAttrs = InternalAttributesFactory.getInternalAttributes(MrNodeType.BASENODE)
                internalFlowInputs = InternalAttributesFactory.getInternalFlowInputs(MrNodeType.BASENODE)
                internalFlowOutputs = InternalAttributesFactory.getInternalFlowOutputs(MrNodeType.BASENODE)
                refAttrs = internalAttrs + internalFlowInputs + internalFlowOutputs
                attrDesc = CompatibilityNode.attributeDescFromName(refAttrs, name, val)
            else:
                attrDesc = CompatibilityNode.attributeDescFromDict(self.nodeDescDict, name, val, isOutput)
        if attrDesc is None:
            attrDesc = CompatibilityNode.attributeDescFromValue(name, val, isOutput)
        attribute = attributeFactory(attrDesc, val, isOutput, self)
        if internalAttr:
            self._internalAttributes.add(attribute)
        else:
            self._attributes.add(attribute)
        return matchDesc

    @property
    def issueDetails(self):
        if self.issue == CompatibilityIssue.UnknownNodeType:
            return f"Unknown node type: '{self.nodeType}'."
        elif self.issue == CompatibilityIssue.DescOnlyNodeType:
            if "version" not in self.nodeDict:
                return f"Description for node '{self.name}' with node type '{self.nodeType}' only found in .mg."
            version = self.nodeDict["version"]
            return f"Description for node type '{self.nodeType}' version '{version}' only found in .mg."
        elif self.issue == CompatibilityIssue.VersionConflict:
            version = self.nodeDict["version"]
            return f"Node version '{version}' conflicts with current version '{nodeVersion(self.nodeDesc)}'."
        elif self.issue == CompatibilityIssue.DescriptionConflict:
            return "Node attributes do not match node description."
        elif self.issue == CompatibilityIssue.UidConflict:
            return "Node UID differs from the expected one."
        else:
            return "Unknown error."

    @property
    def inputs(self):
        """ Get current node inputs, where links could differ from original serialized node data
        (i.e after node duplication) """
        # if node has not been added to a graph, return serialized node inputs
        if not self.graph:
            return self._inputs
        return {k: v.getSerializedValue() for k, v in self._attributes.objects.items() if v.isInput}

    @property
    def internalInputs(self):
        """ Get current node's internal attributes """
        if not self.graph:
            return self._internalInputs
        return {k: v.getSerializedValue() for k, v in self._internalAttributes.objects.items()}

    def toDict(self):
        """
        Return the original serialized node that generated a compatibility issue.

        Serialized inputs are updated to handle instances that have been duplicated
        and might be connected to different nodes.
        """
        # update inputs to get up-to-date connections
        self.nodeDict.update({"inputs": self.inputs})
        # update position
        self.nodeDict.update({"position": self.position})
        return self.nodeDict

    def getNodeDescription(self):
        # Get the node type, the node version, and the basic information about the io (name, type and default value)
        return {
            'nodeType': self.nodeType,
            'version': self.nodeDict["version"],
            'inputs': {k: v.shortDesc() for k, v in self._attributes.objects.items() if v.isInput},
            'outputs': {k: v.shortDesc() for k, v in self._attributes.objects.items() if v.isOutput}
        }

    @property
    def canUpgrade(self):
        """ Return whether the node can be upgraded.
        This is the case when the underlying node type has a corresponding description. """
        return self.nodeDesc is not None

    def upgrade(self):
        """
        Return a new Node instance based on original node type with common inputs initialized.
        """
        if not self.canUpgrade:
            raise NodeUpgradeError(self.name, "No matching node type")

        # inputs matching current type description
        commonInputs = []
        for attrName, value in self._inputs.items():
            if self.attributeDescFromName(self.nodeDesc.inputs, attrName, value, strict=False):
                # store attributes that could be used during node upgrade
                commonInputs.append(attrName)

        commonInternalAttributes = []
        for attrName, value in self._internalInputs.items():
            if self.attributeDescFromName(self.nodeDesc.internalInputs, attrName, value, strict=False):
                # store internal attributes that could be used during node upgrade
                commonInternalAttributes.append(attrName)

        node = Node(self.nodeType, position=self.position)
        # convert attributes from a list of tuples into a dict
        attrValues = {key: value for (key, value) in self.inputs.items()}
        intAttrValues = {key: value for (key, value) in self.internalInputs.items()}

        # Use upgrade method of the node description itself if available
        try:
            upgradedAttrValues = node.nodeDesc.upgradeAttributeValues(attrValues, self.version)
        except Exception as exc:
            logging.error(f"Error in the upgrade implementation of the node: {self.name}.\n{repr(exc)}")
            upgradedAttrValues = attrValues

        if not isinstance(upgradedAttrValues, dict):
            logging.error(f"Error in the upgrade implementation of the node: {self.name}. The return type is incorrect.")
            upgradedAttrValues = attrValues

        node.upgradeAttributeValues(upgradedAttrValues)

        node.upgradeInternalAttributeValues(intAttrValues)

        return node

    # Override
    def loadOutputAttr(self):
        """ Load output attributes with dynamic values from a values file. """

        if self.nodeDescDict is None or self._uid is None:
            return

        descOutputs = self.nodeDescDict.get("outputs", {})
        dynamicAttrs = [name for name, attrDesc in descOutputs.items()
                        if attrDesc.get("type") and (attrDesc["type"] == "AnySet" or attrDesc.get("value") is None)]

        if not dynamicAttrs:
            return

        valuesFile = self.valuesFile
        if not os.path.exists(valuesFile):
            logging.warning(f"No output attr file: {valuesFile}")
            return

        # Open json file and parse
        with open(valuesFile, "r") as jsonFile:
            data = json.load(jsonFile)

        for name in dynamicAttrs:
            attr = self._attributes.get(name)
            if attr is None:
                continue

            if name not in data:
                logging.warning(f"CompatibilityNode: missing dynamic output value: {self.name}.{name} in valuesFile: {valuesFile}")
                continue

            value = data[name]
            if hasattr(attr, "_populateFromDynamicValue") and attr._populateFromDynamicValue is not None:
                attr._populateFromDynamicValue(value)
            else:
                attr.value = value

    # Override
    def updateStatusFromCache(self):
        """ Update the status from the cache and notify the listeners if the global status has changed. """
        previousStatus = self.getGlobalStatus()
        super().updateStatusFromCache()
        if self.getGlobalStatus() != previousStatus:
            self.globalStatusChanged.emit()
        # Compatibility nodes do not trigger descriptor callbacks, but their validation state must still be notified
        self.hasInvalidAttributeChanged.emit()

    compatibilityIssue = Property(int, lambda self: self.issue.value, constant=True)
    canUpgrade = Property(bool, canUpgrade.fget, constant=True)
    issueDetails = Property(str, issueDetails.fget, constant=True)
