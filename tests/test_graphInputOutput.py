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
from meshroom.nodes.general.GraphIO import GraphInput, GraphOutput, Input, Output

from .utils import registeredNodeTypes


class Worker(desc.Node):
    inputs = [
        desc.File(name="path", label="Path", description="Input path.", value=""),
        desc.ListAttribute(
            name="files",
            label="Files",
            description="Input files.",
            elementDesc=desc.File(name="file", label="File", description="Input file.", value=""),
        ),
    ]
    outputs = []


# (node type, replacement node type)
GRAPH_IO_TYPES = [("GraphInput", "Input"), ("GraphOutput", "Output")]


@pytest.fixture(autouse=True)
def nodeTypes():
    with registeredNodeTypes([GraphInput, GraphOutput, Input, Output, Worker]):
        yield


def connectExposed(graph, node, attribute):
    """ Expose `attribute` on `node`, as done when connecting them in the Graph Editor. """
    exposed = node.exposeds.duplicateAttribute(attribute)
    if node.isGraphInputNode or node.nodeType == "Input":
        graph.addEdge(exposed, attribute)
    else:
        graph.addEdge(attribute, exposed)
    return exposed


def graphWithExposed(nodeType):
    """ Create a graph with the `nodeType` node exposing the path of a Worker, set to "/value". """
    graph = Graph("")
    node = graph.addNewNode(nodeType)
    worker = graph.addNewNode("Worker")
    exposed = connectExposed(graph, node, worker.path)
    (exposed if nodeType == "GraphInput" else worker.path).value = "/value"
    return graph, node, worker


def assertReplacedNode(node, replacementType, worker):
    """ Check that `node` is a valid `replacementType` node, still connected to `worker` with the same value. """
    assert node.nodeType == replacementType
    assert not node.isCompatibilityNode
    assert node.exposeds.path.value == worker.path.value == "/value"
    edge = (node.exposeds.path, worker.path) if replacementType == "Input" else (worker.path, node.exposeds.path)
    assert edge in [(e.src, e.dst) for e in node.graph.edges.values()]


@pytest.mark.parametrize("nodeClass", [GraphInput, GraphOutput])
def test_graphIONodeCannotBeSubclassed(nodeClass):
    with pytest.raises(TypeError):
        type("CustomNode", (nodeClass,), {})


@pytest.mark.parametrize("nodeType,_", GRAPH_IO_TYPES)
def test_graphHasSingleGraphIONode(nodeType, _):
    graph = Graph("")
    node = graph.addNewNode(nodeType)
    assert graph.findGraphIONode(nodeType) == node

    with pytest.raises(RuntimeError):
        graph.addNewNode(nodeType)

    graph.removeNode(node.name)
    assert graph.findGraphIONode(nodeType) is None
    graph.addNewNode(nodeType)


def test_graphInputDrivesAttributesAndCannotBeDriven():
    graph, node, worker = graphWithExposed("GraphInput")

    graph.findGraphInputAttributes()["path"].value = "/new"
    assert worker.path.value == "/new"

    other = graph.addNewNode("Worker")
    assert not node.exposeds.path.validateIncomingConnection(other.path)
    with pytest.raises(InvalidEdgeError):
        graph.addEdge(other.path, node.exposeds.path)


def test_inputNodeCanBeDrivenByGraphInput():
    graph, node, worker = graphWithExposed("GraphInput")
    inputNode = graph.addNewNode("Input")
    inputAttr = connectExposed(graph, inputNode, graph.addNewNode("Worker").path)

    graph.addEdge(node.exposeds.path, inputAttr)

    assert inputAttr.value == worker.path.value == "/value"
    assert list(graph.findGraphInputAttributes()) == ["path"]


@pytest.mark.parametrize("nodeType,replacementType", GRAPH_IO_TYPES)
def test_duplicateGraphIONodeCreatesReplacementNode(nodeType, replacementType):
    graph, node, worker = graphWithExposed(nodeType)

    duplicates = graph.duplicateNodes([node, worker])

    assert graph.findGraphIONode(nodeType) == node
    assertReplacedNode(duplicates[node][0], replacementType, duplicates[worker][0])
    assert duplicates[node][0].name == f"{replacementType}_1"


@pytest.mark.parametrize("nodeType,replacementType", GRAPH_IO_TYPES)
def test_importGraphIONodeCreatesReplacementNodeIfGraphHasOne(nodeType, replacementType, tmp_path):
    importedPath = str(tmp_path / "imported.mg")
    graphWithExposed(nodeType)[0].save(importedPath)

    # Imported as is in a graph that does not have one
    graph = Graph("")
    graph.importGraphContentFromFile(importedPath)
    assert graph.findGraphIONode(nodeType) is not None

    graph = Graph("")
    existingNode = graph.addNewNode(nodeType)
    nodes = {node.nodeType: node for node in graph.importGraphContentFromFile(importedPath)}

    assert graph.findGraphIONode(nodeType) == existingNode
    assertReplacedNode(nodes[replacementType], replacementType, nodes["Worker"])
    assert nodes[replacementType].name == f"{replacementType}_1"


@pytest.mark.parametrize("nodeType,replacementType", GRAPH_IO_TYPES)
def test_loadGraphWithSeveralGraphIONodesKeepsFirstOne(nodeType, replacementType, tmp_path):
    graph, node, worker = graphWithExposed(nodeType)
    graphPath = str(tmp_path / "graph.mg")
    graph.save(graphPath)

    # Add a copy of the node and of the Worker connected to it in the saved file
    with open(graphPath) as f:
        graphData = json.load(f)
    nodes = graphData["graph"]
    nodes[f"{nodeType}_2"] = json.loads(json.dumps(nodes[node.name]).replace(worker.name, "Worker_2"))
    nodes["Worker_2"] = json.loads(json.dumps(nodes[worker.name]).replace(node.name, f"{nodeType}_2"))
    with open(graphPath, "w") as f:
        json.dump(graphData, f)

    loaded = loadGraph(graphPath)

    assert loaded.findGraphIONode(nodeType) == loaded.node(node.name)
    assertReplacedNode(loaded.node(f"{nodeType}_2"), replacementType, loaded.node("Worker_2"))


def test_graphIONodesAreKeptInTemplates(tmp_path):
    graph, _, worker = graphWithExposed("GraphInput")
    graphOutputNode = graph.addNewNode("GraphOutput")
    connectExposed(graph, graphOutputNode, worker.path)
    templatePath = str(tmp_path / "template.mg")
    graph.save(templatePath, template=True)

    loaded = Graph("")
    loaded.initFromTemplate(templatePath)

    assert loaded.findGraphInputAttributes()["path"].value == "/value"
    assert loaded.findGraphOutputNode().exposeds.path.inputLink == loaded.node(worker.name).path


def test_graphOutputExport(tmp_path):
    graph = Graph("")
    worker = graph.addNewNode("Worker")
    node = graph.addNewNode("GraphOutput")
    connectExposed(graph, node, worker.path)
    connectExposed(graph, node, worker.files)
    worker.path.value = "/value"
    worker.files.extend(["/first", "/second"])
    expected = {"path": "/value", "files": ["/first", "/second"]}

    # Nothing is exported without output folder or file
    node.nodeDesc.process(node)
    assert not list(tmp_path.iterdir())

    node.outputFolder.value = str(tmp_path / "folder")
    node.nodeDesc.process(node)
    assert json.loads((tmp_path / "folder" / "outputs.json").read_text()) == expected

    # The output file has priority over the folder
    node.outputFile.value = str(tmp_path / "custom" / "file.json")
    node.nodeDesc.process(node)
    assert json.loads((tmp_path / "custom" / "file.json").read_text()) == expected


def test_meshroomBatchSetsGraphInputAndExportsGraphOutput(tmp_path):
    # The scene only uses standard nodes, as meshroom_batch runs in another process
    scene = Graph("")
    textDesc = {"name": "text", "label": "Text", "type": "StringParam", "value": "default"}
    graphInput = scene.addNewNode("GraphInput").exposeds.insertAttribute(textDesc, 0)
    graphOutput = scene.addNewNode("GraphOutput").exposeds.insertAttribute(textDesc, 0)
    scene.addEdge(graphInput, graphOutput)
    scene.save(str(tmp_path / "scene.mg"))

    outputFolder = tmp_path / "exported"
    batch = [sys.executable, os.path.join(_MESHROOM_ROOT, "bin", "meshroom_batch"),
             "-p", str(tmp_path / "scene.mg"), "--save", str(tmp_path / "computed.mg"), "--compute", "yes"]
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(_MESHROOM_ROOT), os.environ.get("PYTHONPATH", "")])}

    subprocess.run(batch + ["-gi", "text=value", "-go", str(outputFolder)], check=True, env=env)
    assert json.loads((outputFolder / "outputs.json").read_text()) == {"text": "value"}

    # An unknown graph input is an error
    result = subprocess.run(batch + ["-gi", "unknown=value"], capture_output=True, text=True, env=env)
    assert result.returncode != 0
    assert "unknown" in result.stderr
