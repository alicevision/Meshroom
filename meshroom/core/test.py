#!/usr/bin/env python

from meshroom.core import unregisterNodeType, pipelineTemplates, Version
from meshroom.core.node import CompatibilityIssue, CompatibilityNode
from meshroom.core.graphIO import GraphIO

import meshroom

import json

def checkTemplateVersions(path: str, nodesAlreadyLoaded: bool = False) -> bool:
    """ Check whether there is a compatibility issue with the nodes saved in the template provided with "path". """
    if not nodesAlreadyLoaded:
        meshroom.core.initNodes()

    with open(path) as jsonFile:
        fileData = json.load(jsonFile)

    try:
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
                print(f"{compatibilityIssue} in {path} for node {nodeType}")
                return False

        return True

    finally:
        if not nodesAlreadyLoaded:
            nodeTypes = [nodeType for _, nodeType in meshroom.core.nodesDesc.items()]
            for nodeType in nodeTypes:
                unregisterNodeType(nodeType)


def checkAllTemplatesVersions() -> bool:
    meshroom.core.initNodes()
    meshroom.core.initPipelines()

    validVersions = []
    for _, path in pipelineTemplates.items():
        validVersions.append(checkTemplateVersions(path, nodesAlreadyLoaded=True))

    return all(validVersions)
