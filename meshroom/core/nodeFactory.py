import logging

import meshroom.core
from meshroom.core import Version, desc
from meshroom.core.node import CompatibilityIssue, CompatibilityNode, Node, Position


def nodeFactory(nodeDict, name=None, template=False, uidConflict=False):
    """
    Create a node instance by deserializing the given node data.
    If the serialized data matches the corresponding node type description, a Node instance is created.
    If any compatibility issue occurs, a NodeCompatibility instance is created instead.

    Args:
        nodeDict (dict): the serialization of the node
        name (str): (optional) the node's name
        template (bool): (optional) true if the node is part of a template, false otherwise
        uidConflict (bool): (optional) true if a UID conflict has been detected externally on that node

    Returns:
        BaseNode: the created node
    """
    nodeType = nodeDict["nodeType"]

    # Retro-compatibility: inputs were previously saved as "attributes"
    if "inputs" not in nodeDict and "attributes" in nodeDict:
        nodeDict["inputs"] = nodeDict["attributes"]
        del nodeDict["attributes"]

    # Get node inputs/outputs
    inputs = nodeDict.get("inputs", {})
    internalInputs = nodeDict.get("internalInputs", {})
    outputs = nodeDict.get("outputs", {})
    version = nodeDict.get("version", None)
    internalFolder = nodeDict.get("internalFolder", None)
    position = Position(*nodeDict.get("position", []))
    uid = nodeDict.get("uid", None)

    compatibilityIssue = None

    nodeDesc = None
    try:
        nodeDesc = meshroom.core.nodesDesc[nodeType]
    except KeyError:
        # Unknown node type
        compatibilityIssue = CompatibilityIssue.UnknownNodeType

    # Unknown node type should take precedence over UID conflict, as it cannot be resolved
    if uidConflict and nodeDesc:
        compatibilityIssue = CompatibilityIssue.UidConflict

    if nodeDesc and not uidConflict:  # if uidConflict, there is no need to look for another compatibility issue
        # Compare serialized node version with current node version
        currentNodeVersion = meshroom.core.nodeVersion(nodeDesc)
        # If both versions are available, check for incompatibility in major version
        if version and currentNodeVersion and Version(version).major != Version(currentNodeVersion).major:
            compatibilityIssue = CompatibilityIssue.VersionConflict
        # In other cases, check attributes compatibility between serialized node and its description
        else:
            # Check that the node has the exact same set of inputs/outputs as its description, except
            # if the node is described in a template file, in which only non-default parameters are saved;
            # do not perform that check for internal attributes because there is no point in
            # raising compatibility issues if their number differs: in that case, it is only useful
            # if some internal attributes do not exist or are invalid
            if not template and (sorted([attr.name for attr in nodeDesc.inputs 
                                         if not isinstance(attr, desc.PushButtonParam)]) != sorted(inputs.keys()) or
                                 sorted([attr.name for attr in nodeDesc.outputs if not attr.isDynamicValue]) !=
                                 sorted(outputs.keys())):
                compatibilityIssue = CompatibilityIssue.DescriptionConflict

            # Check whether there are any internal attributes that are invalidating in the node description: if there
            # are, then check that these internal attributes are part of nodeDict; if they are not, a compatibility
            # issue must be raised to warn the user, as this will automatically change the node's UID
            if not template:
                invalidatingIntInputs = []
                for attr in nodeDesc.internalInputs:
                    if attr.invalidate:
                        invalidatingIntInputs.append(attr.name)
                for attr in invalidatingIntInputs:
                    if attr not in internalInputs.keys():
                        compatibilityIssue = CompatibilityIssue.DescriptionConflict
                        break

            # Verify that all inputs match their descriptions
            for attrName, value in inputs.items():
                if not CompatibilityNode.attributeDescFromName(nodeDesc.inputs, attrName, value):
                    compatibilityIssue = CompatibilityIssue.DescriptionConflict
                    break
            # Verify that all internal inputs match their description
            for attrName, value in internalInputs.items():
                if not CompatibilityNode.attributeDescFromName(nodeDesc.internalInputs, attrName, value):
                    compatibilityIssue = CompatibilityIssue.DescriptionConflict
                    break
            # Verify that all outputs match their descriptions
            for attrName, value in outputs.items():
                if not CompatibilityNode.attributeDescFromName(nodeDesc.outputs, attrName, value):
                    compatibilityIssue = CompatibilityIssue.DescriptionConflict
                    break

    if compatibilityIssue is None:
        node = Node(nodeType, position, uid=uid, **inputs, **internalInputs, **outputs)
    else:
        logging.debug("Compatibility issue detected for node '{}': {}".format(name, compatibilityIssue.name))
        node = CompatibilityNode(nodeType, nodeDict, position, compatibilityIssue)
        # Retro-compatibility: no internal folder saved
        # can't spawn meaningful CompatibilityNode with precomputed outputs
        # => automatically try to perform node upgrade
        if not internalFolder and nodeDesc:
            logging.warning("No serialized output data: performing automatic upgrade on '{}'".format(name))
            node = node.upgrade()
        # If the node comes from a template file and there is a conflict, it should be upgraded anyway unless it is
        # an "unknown node type" conflict (in which case the upgrade would fail)
        elif template and compatibilityIssue is not CompatibilityIssue.UnknownNodeType:
            node = node.upgrade()

    return node
