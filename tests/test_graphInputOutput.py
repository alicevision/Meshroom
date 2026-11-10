#!/usr/bin/env python
# coding:utf-8

import json
import os
import subprocess
import sys

import pytest

from meshroom import _MESHROOM_ROOT
from meshroom.core import desc
from meshroom.core.exception import InvalidEdgeError
from meshroom.core.graph import Graph, loadGraph
from meshroom.nodes.general.AnySetNode import AnySetNode
from meshroom.nodes.general.GraphIO import GraphInput, GraphOutput

from .utils import registeredNodeTypes


class Worker(desc.Node):
    inputs = [
        desc.File(name="path", label="Path", description="Input path.", value=""),
    ]
    outputs = []


# (node type, name of its AnySet, label of the AnySetNode replacing it)
GRAPH_IO_TYPES = [("GraphInput", "ins", "Inputs"), ("GraphOutput", "outs", "Outputs")]


@pytest.fixture(autouse=True)
def nodeTypes():
    with registeredNodeTypes([GraphInput, GraphOutput, AnySetNode, Worker]):
        yield


def graphWithExposed(nodeType, anySetName):
    """ Create a graph with the `nodeType` node exposing the path of a Worker, set to "/value". """
    graph = Graph("")
    node = graph.addNewNode(nodeType)
    worker = graph.addNewNode("Worker")
    exposed = node.attribute(anySetName).duplicateAttribute(worker.path)
    if nodeType == "GraphInput":
        graph.addEdge(exposed, worker.path)
        exposed.value = "/value"
    else:
        graph.addEdge(worker.path, exposed)
        worker.path.value = "/value"
    return graph, node, worker


def assertAnySetNode(node, label, worker):
    """ Check that `node` is an AnySetNode labelled `label`, still connected to `worker` with the same value. """
    assert node.nodeType == "AnySetNode"
    assert node.label == label
    exposed = node.attribute("attributes").path
    assert exposed.value == worker.path.value == "/value"
    edge = (worker.path, exposed) if label == "Outputs" else (exposed, worker.path)
    assert edge in [(e.src, e.dst) for e in node.graph.edges.values()]


@pytest.mark.parametrize("nodeClass", [GraphInput, GraphOutput])
def test_graphIONodeCannotBeSubclassed(nodeClass):
    with pytest.raises(TypeError):
        type("CustomNode", (nodeClass,), {})


@pytest.mark.parametrize("nodeType,_,__", GRAPH_IO_TYPES)
def test_graphHasSingleGraphIONode(nodeType, _, __):
    graph = Graph("")
    node = graph.addNewNode(nodeType)
    assert graph.findGraphIONode(nodeType) == node

    with pytest.raises(RuntimeError):
        graph.addNewNode(nodeType)

    graph.removeNode(node.name)
    assert graph.findGraphIONode(nodeType) is None
    graph.addNewNode(nodeType)


def test_graphInputDrivesAttributesAndCannotBeDriven():
    graph, node, worker = graphWithExposed("GraphInput", "ins")

    graph.findGraphInputAttributes()["path"].value = "/new"
    assert worker.path.value == "/new"

    with pytest.raises(InvalidEdgeError):
        graph.addEdge(graph.addNewNode("Worker").path, node.ins.path)


@pytest.mark.parametrize("nodeType,anySetName,label", GRAPH_IO_TYPES)
def test_convertToAnySetNode(nodeType, anySetName, label):
    graph, node, worker = graphWithExposed(nodeType, anySetName)

    anySetNode = graph.convertToAnySetNode(node)

    assert graph.findGraphIONode(nodeType) is None
    assertAnySetNode(anySetNode, label, worker)


@pytest.mark.parametrize("nodeType,anySetName,label", GRAPH_IO_TYPES)
def test_duplicateGraphIONodeCreatesAnySetNode(nodeType, anySetName, label):
    graph, node, worker = graphWithExposed(nodeType, anySetName)

    duplicates = graph.duplicateNodes([node, worker])

    assert graph.findGraphIONode(nodeType) == node
    assertAnySetNode(duplicates[node][0], label, duplicates[worker][0])


@pytest.mark.parametrize("nodeType,anySetName,label", GRAPH_IO_TYPES)
def test_importGraphIONodeCreatesAnySetNodeIfGraphHasOne(nodeType, anySetName, label, tmp_path):
    importedPath = str(tmp_path / "imported.mg")
    graphWithExposed(nodeType, anySetName)[0].save(importedPath)

    # Imported as is in a graph that does not have one
    graph = Graph("")
    graph.importGraphContentFromFile(importedPath)
    assert graph.findGraphIONode(nodeType) is not None

    graph = Graph("")
    existingNode = graph.addNewNode(nodeType)
    nodes = {node.nodeType: node for node in graph.importGraphContentFromFile(importedPath)}

    assert graph.findGraphIONode(nodeType) == existingNode
    assertAnySetNode(nodes["AnySetNode"], label, nodes["Worker"])


def test_loadGraphWithSeveralGraphInputNodesRemovesTheOtherOnes(tmp_path):
    graph, node, worker = graphWithExposed("GraphInput", "ins")
    graphPath = str(tmp_path / "graph.mg")
    graph.save(graphPath)

    # Add a copy of the node and of the Worker connected to it in the saved file
    with open(graphPath) as f:
        graphData = json.load(f)
    nodes = graphData["graph"]
    nodes["GraphInput_2"] = nodes[node.name]
    nodes["Worker_2"] = json.loads(json.dumps(nodes[worker.name]).replace(node.name, "GraphInput_2"))
    with open(graphPath, "w") as f:
        json.dump(graphData, f)

    loaded = loadGraph(graphPath)

    assert loaded.findGraphInputNode() == loaded.node(node.name)
    assert loaded.node("GraphInput_2") is None
    assert not loaded.node("Worker_2").path.isLink


def test_graphIONodesAreKeptInTemplates(tmp_path):
    graph, _, worker = graphWithExposed("GraphInput", "ins")
    graphOutputNode = graph.addNewNode("GraphOutput")
    graph.addEdge(worker.path, graphOutputNode.outs.duplicateAttribute(worker.path))
    templatePath = str(tmp_path / "template.mg")
    graph.save(templatePath, template=True)

    loaded = Graph("")
    loaded.initFromTemplate(templatePath)

    assert loaded.findGraphInputAttributes()["path"].value == "/value"
    assert loaded.findGraphOutputNode().outs.path.inputLink == loaded.node(worker.name).path


def test_meshroomBatchSetsGraphInput(tmp_path):
    # The scene only uses standard nodes, as meshroom_batch runs in another process
    scene = Graph("")
    textDesc = {"name": "text", "label": "Text", "type": "StringParam", "value": "default"}
    scene.addNewNode("GraphInput").ins.insertAttribute(textDesc, 0)
    scene.save(str(tmp_path / "scene.mg"))

    savedPath = str(tmp_path / "saved.mg")
    batch = [sys.executable, os.path.join(_MESHROOM_ROOT, "bin", "meshroom_batch"),
             "-p", str(tmp_path / "scene.mg"), "--save", savedPath, "--compute", "no"]
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(_MESHROOM_ROOT), os.environ.get("PYTHONPATH", "")])}

    subprocess.run(batch + ["-gi", "text=value"], check=True, env=env)
    assert loadGraph(savedPath).findGraphInputAttributes()["text"].value == "value"

    # An unknown graph input is an error
    result = subprocess.run(batch + ["-gi", "unknown=value"], capture_output=True, text=True, env=env)
    assert result.returncode != 0
    assert "unknown" in result.stderr
