#!/usr/bin/env python
# coding:utf-8

from meshroom.core.graph import Graph
from meshroom.core import pipelineTemplates, Version
from meshroom.core.node import CompatibilityIssue, CompatibilityNode

import json
import meshroom


def test_templateVersions():
    """
    This test checks that there is no compatibility issue with the nodes saved in the template files.
    It fails when an upgrade of a templates is needed. Any template can still be opened even if its
    nodes are not up-to-date, as they will be automatically upgraded.
    """
    meshroom.core.initNodes()
    meshroom.core.initPipelines()

    assert len(pipelineTemplates) >= 1

    for _, path in pipelineTemplates.items():
        with open(path) as jsonFile:
            fileData = json.load(jsonFile)

        graphData = fileData.get(Graph.IO.Keys.Graph, fileData)

        assert isinstance(graphData, dict)

        header = fileData.get(Graph.IO.Keys.Header, {})
        assert header.get("template", False)
        nodesVersions = header.get(Graph.IO.Keys.NodesVersions, {})

        for _, nodeData in graphData.items():
            nodeType = nodeData["nodeType"]
            assert nodeType in meshroom.core.nodesDesc

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

            assert compatibilityIssue is None, "{} in {} for node {}".format(compatibilityIssue, path, nodeType)
