#!/usr/bin/env python
# coding:utf-8

from meshroom.core import pipelineTemplates, Version
from meshroom.core.node import CompatibilityIssue, CompatibilityNode
from meshroom.core.graphIO import GraphIO

import meshroom

import json

def checkTemplateVersions(path: str) -> bool:
    """ Check whether there is a compatibility issue with the nodes saved in the template provided with "path". """
    meshroom.core.initNodes()

    with open(path) as jsonFile:
        fileData = json.load(jsonFile)

    graphData = fileData.get(GraphIO.Keys.Graph, fileData)
    if not isinstance(graphData, dict):
        return False

    header = fileData.get(GraphIO.Keys.Header, {})
    if not header.get("template", False):
        return False
    nodesVersions = header.get(GraphIO.Keys.NodesVersions, {})

    for _, nodeData in graphData.items():
        nodeType = nodeData["nodeType"]
        if not nodeType in meshroom.core.nodesDesc:
            return False

        nodeDesc = meshroom.core.nodesDesc[nodeType]
        currentNodeVersion = meshroom.core.nodeVersion(nodeDesc)

        inputs = nodeData.get("inputs", {})
        internalInputs = nodeData.get("internalInputs", {})
        version = nodesVersions.get(nodeType, None)

        compatibilityIssue = None

        if version and currentNodeVersion and Version(version).major != Version(currentNodeVersion).major:
            compatibilityIssue = CompatibilityIssue.VersionConflict
        else:
            for attrName, value in inputs.items():
                if not CompatibilityNode.attributeDescFromName(nodeDesc.inputs, attrName, value):
                    compatibilityIssue = CompatibilityIssue.DescriptionConflict
                    break
            for attrName, value in internalInputs.items():
                if not CompatibilityNode.attributeDescFromName(nodeDesc.internalInputs, attrName, value):
                    compatibilityIssue = CompatibilityIssue.DescriptionConflict
                    break

        if compatibilityIssue is not None:
            print("{} in {} for node {}".format(compatibilityIssue, path, nodeType))
            return False

    return True


def checkAllTemplatesVersions() -> bool:
    meshroom.core.initPipelines()

    validVersions = []
    for _, path in pipelineTemplates.items():
        validVersions.append(checkTemplateVersions(path))

    return all(validVersions)
