#!/usr/bin/env python
# coding:utf-8

import shlex
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import PropertyMock, patch

import pytest

from meshroom.core import desc
from meshroom.core.plugins.base import NodeDescProvider
from meshroom.core.plugins.env import RezProcessEnv
from meshroom.core.graph import Graph, loadGraph
from meshroom.nodes.general.ComputeMeshroomScene import ComputeMeshroomScene, decodeAttributeName, encodeAttributeName
from meshroom.nodes.general.GraphIO import GraphInput, GraphOutput
from meshroom.nodes.general.InputInt import InputInt
from meshroom.nodes.general.PathJoin import PathJoin

from .nodes.test.OutputNode import OutputNodeTest
from .utils import registeredNodeTypes


class FileProducer(desc.Node):
    """ A node producing a file in its cache folder. """
    inputs = []
    outputs = [
        desc.File(name="output", label="Output", description="Output file.", value="{nodeCacheFolder}/out.txt"),
    ]


class FolderProducer(desc.Node):
    """ A node giving its cache folder as a string. """
    inputs = []
    outputs = [
        desc.StringParam(name="output", label="Output", description="Cache folder.", value="{nodeCacheFolder}"),
    ]


class FileConsumer(desc.Node):
    """ A node reading a file. """
    inputs = [
        desc.File(name="input", label="Input", description="Input file.", value=""),
    ]
    outputs = []


def _saveScene(path):
    """ Save a scene with a GraphInput and a GraphOutput exposing a few attributes. """
    scene = Graph("")
    graphInput = scene.addNewNode("GraphInput")
    graphInput.ins.insertAttribute({"name": "inputFile", "label": "Input File", "type": "File",
                                   "value": "/data/my shots/a.jpg"}, 0)
    graphInput.ins.insertAttribute({"name": "count_", "label": "Count", "type": "IntParam", "value": 3}, 1)
    graphInput.ins.insertAttribute({"name": "size", "label": "Size", "type": "GroupAttribute", "items": [
        {"name": "width", "label": "Width", "type": "IntParam", "value": 1},
        {"name": "height", "label": "Height", "type": "IntParam", "value": 2},
    ]}, 2)
    graphOutput = scene.addNewNode("GraphOutput")
    graphOutput.outs.insertAttribute({"name": "result", "label": "Result", "type": "File", "value": "/out"}, 0)
    scene.save(str(path))
    return graphInput, graphOutput


def test_attributeNameRoundTrip():
    for fullName in ("Node_1.ins.foo", "Node_1.foo_.bar", "Node_1._foo.bar__baz", "Node_1.a_0.b"):
        assert decodeAttributeName(encodeAttributeName(fullName)) == fullName


def test_sceneAttributesAreExposedAndOverridden(tmp_path):
    with registeredNodeTypes([ComputeMeshroomScene, GraphInput, GraphOutput]):
        scenePath = tmp_path / "my scene.mg"
        graphInput, graphOutput = _saveScene(scenePath)

        graph = Graph("")
        graph.save(str(tmp_path / "project.mg"))
        node = graph.addNewNode("ComputeMeshroomScene")
        node.scene.value = str(scenePath)

        # The children of the groups are exposed, in the order of the scene attributes
        exposedInputs = [decodeAttributeName(attr.name) for attr in node.inputs.value]
        assert exposedInputs == [
            f"{graphInput.name}.ins.inputFile",
            f"{graphInput.name}.ins.count_",
            f"{graphInput.name}.ins.size.width",
            f"{graphInput.name}.ins.size.height",
        ]
        assert [decodeAttributeName(attr.name) for attr in node.outputs.value] == [f"{graphOutput.name}.outs.result"]

        def computedValues(path):
            ins = loadGraph(str(path)).node(graphInput.name).ins
            return ins.value.get("inputFile").value, ins.value.get("count_").value

        # The preprocess saves the scene with the modified inputs in the node's folder, which is computed
        node.inputs.value.get(encodeAttributeName(f"{graphInput.name}.ins.inputFile")).value = "/data/other shots/b.jpg"
        node.inputs.value.get(encodeAttributeName(f"{graphInput.name}.ins.count_")).value = 5
        node.nodeDesc.preprocess(node)
        computedScenePath = Path(node.nodeDesc._computedScenePath(node))
        assert computedScenePath != scenePath
        assert computedValues(computedScenePath) == ("/data/other shots/b.jpg", 5)
        args = shlex.split(node.nodeDesc.buildCommandLine(SimpleNamespace(node=node)))
        assert Path(args[1]).name == "meshroom_compute"
        assert Path(args[2]) == computedScenePath

        # The given scene is not modified, unless it is overwritten
        assert computedValues(scenePath) == ("/data/my shots/a.jpg", 3)
        node.overwriteSceneGraph.value = True
        node.nodeDesc.preprocess(node)
        assert computedValues(scenePath) == ("/data/other shots/b.jpg", 5)
        args = shlex.split(node.nodeDesc.buildCommandLine(SimpleNamespace(node=node)))
        assert Path(args[2]) == scenePath


def test_argumentsAreInTheCommandRunInThePluginEnv(tmp_path):
    rezEnv = RezProcessEnv("/plugin", {}, "mayaPlugin", None)
    with registeredNodeTypes([ComputeMeshroomScene, GraphInput, GraphOutput]), \
            patch.object(NodeDescProvider, "processEnv", new_callable=PropertyMock, return_value=rezEnv), \
            patch.object(RezProcessEnv, "resolveRezSubrequires", return_value=["mayaPackage"]):
        scenePath = tmp_path / "my scene.mg"
        _saveScene(scenePath)
        graph = Graph("")
        node = graph.addNewNode("ComputeMeshroomScene")
        node.scene.value = str(scenePath)
        node.overwriteSceneGraph.value = True

        args = shlex.split(node.nodeDesc.buildCommandLine(SimpleNamespace(node=node)))
        # The meshroom_compute arguments are part of the command run by "rez env", with their quotes kept
        assert args[:4] == ["rez", "env", "mayaPackage", "-c"]
        assert len(args) == 5
        commandArgs = shlex.split(args[4])
        assert commandArgs[0].startswith("PYTHONPATH=$PYTHONPATH")
        assert Path(commandArgs[3]) == scenePath


def test_outputNodesAreNotExposed(tmp_path):
    with registeredNodeTypes([ComputeMeshroomScene, GraphInput, GraphOutput, OutputNodeTest]):
        scenePath = tmp_path / "scene.mg"
        _, graphOutput = _saveScene(scenePath)
        # Output nodes are removed from the computed scene: their attributes cannot be exposed
        scene = loadGraph(str(scenePath))
        scene.addNewNode("OutputNodeTest")
        scene.save(str(scenePath))

        graph = Graph("")
        node = graph.addNewNode("ComputeMeshroomScene")
        node.scene.value = str(scenePath)
        assert [decodeAttributeName(attr.name) for attr in node.outputs.value] == [f"{graphOutput.name}.outs.result"]


def test_graphOutputIsKeptInTemplates(tmp_path):
    with registeredNodeTypes([GraphInput, GraphOutput]):
        scenePath = tmp_path / "scene.mg"
        _saveScene(scenePath)

        graph = Graph("")
        graph.initFromTemplate(str(scenePath))
        assert len(graph.nodesOfType("GraphOutput")) == 1


def test_graphOutputIsNotComputable():
    with registeredNodeTypes([GraphOutput]):
        graph = Graph("")
        assert not graph.addNewNode("GraphOutput").isComputableType


def test_exposedOutputsAreSetFromTheComputedScene(tmp_path):
    with registeredNodeTypes([ComputeMeshroomScene, GraphOutput, FileProducer]):
        scene = Graph("")
        producer = scene.addNewNode("FileProducer")
        graphOutput = scene.addNewNode("GraphOutput")
        result = graphOutput.outs.insertAttribute({"name": "result", "label": "Result", "type": "File", "value": ""}, 0)
        scene.addEdge(producer.output, result)
        scenePath = tmp_path / "scene" / "scene.mg"
        scenePath.parent.mkdir()
        scene.save(str(scenePath))

        graph = Graph("")
        graph.save(str(tmp_path / "project.mg"))
        node = graph.addNewNode("ComputeMeshroomScene")
        node.scene.value = str(scenePath)

        node.nodeDesc.preprocess(node)
        computedScenePath = Path(node.nodeDesc._computedScenePath(node))
        node.nodeDesc._updateOutputs(node)

        # The exposed output points to the cache of the computed scene, not to the one of the given scene
        outputPath = Path(list(node.outputs.value)[0].value)
        assert outputPath.name == "out.txt"
        assert computedScenePath.parent in outputPath.parents


def test_exposedOutputsAreEvaluatedOnInlineNodes(tmp_path):
    """ Inline nodes are not computed with the scene: the ones read by the GraphOutput are evaluated afterwards. """
    with registeredNodeTypes([ComputeMeshroomScene, GraphOutput, FolderProducer, PathJoin]):
        scene = Graph("")
        producer = scene.addNewNode("FolderProducer")
        pathJoin = scene.addNewNode("PathJoin")
        pathJoin.paths.extend(["", "sub.txt"])
        scene.addEdge(producer.output, pathJoin.paths.at(0))
        graphOutput = scene.addNewNode("GraphOutput")
        result = graphOutput.outs.insertAttribute({"name": "result", "label": "Result", "type": "File", "value": ""}, 0)
        scene.addEdge(pathJoin.outputPath, result)
        scenePath = tmp_path / "scene" / "scene.mg"
        scenePath.parent.mkdir()
        scene.save(str(scenePath))

        graph = Graph("")
        graph.save(str(tmp_path / "project.mg"))
        node = graph.addNewNode("ComputeMeshroomScene")
        node.scene.value = str(scenePath)

        node.nodeDesc.preprocess(node)
        computedScenePath = Path(node.nodeDesc._computedScenePath(node))
        node.nodeDesc._updateOutputs(node)

        outputPath = Path(list(node.outputs.value)[0].value)
        assert outputPath.name == "sub.txt"
        assert computedScenePath.parent in outputPath.parents


def test_edgesFollowTheSceneChanges(tmp_path):
    with registeredNodeTypes([ComputeMeshroomScene, GraphInput, GraphOutput, InputInt, FileConsumer]):
        fullScenePath = tmp_path / "full.mg"
        graphInput, graphOutput = _saveScene(fullScenePath)
        # Same scene without the "count_" input
        partialScene = loadGraph(str(fullScenePath))
        ins = partialScene.node(graphInput.name).ins
        ins.removeAttribute(ins.value.get("count_"))
        partialScenePath = tmp_path / "partial.mg"
        partialScene.save(str(partialScenePath))

        projectPath = tmp_path / "project.mg"
        graph = Graph("")
        graph.save(str(projectPath))
        node = graph.addNewNode("ComputeMeshroomScene")
        node.scene.value = str(fullScenePath)
        inputInt = graph.addNewNode("InputInt")
        consumer = graph.addNewNode("FileConsumer")
        countName = encodeAttributeName(f"{graphInput.name}.ins.count_")
        resultName = encodeAttributeName(f"{graphOutput.name}.outs.result")
        graph.addEdge(inputInt.integer, node.inputs.value.get(countName))
        graph.addEdge(node.outputs.value.get(resultName), consumer.input)

        # The edge of the removed input is removed, the other one is restored on the new attribute
        node.scene.value = str(partialScenePath)
        assert countName not in node.inputs.value.keys()
        resultAttr = node.outputs.value.get(resultName)
        assert [(edge.src, edge.dst) for edge in graph.edges.values()] == [(resultAttr, consumer.input)]

        # No dangling edge: the project is reloaded with the same edge
        graph.save(str(projectPath))
        reloadedGraph = loadGraph(str(projectPath))
        assert [(edge.src.fullName, edge.dst.fullName) for edge in reloadedGraph.edges.values()] == [
            (f"{node.name}.outputs.{resultName}", f"{consumer.name}.input")
        ]

        # Setting the full scene again (e.g. undoing the scene change) restores the removed edge
        node.scene.value = str(fullScenePath)
        assert {(edge.src, edge.dst) for edge in graph.edges.values()} == {
            (inputInt.integer, node.inputs.value.get(countName)),
            (node.outputs.value.get(resultName), consumer.input),
        }

        # The edges of a removed node are forgotten
        node.scene.value = str(partialScenePath)
        graph.removeNode(inputInt.name)
        node.scene.value = str(fullScenePath)
        resultAttr = node.outputs.value.get(resultName)
        assert [(edge.src, edge.dst) for edge in graph.edges.values()] == [(resultAttr, consumer.input)]


def test_unreadableSceneFailsTheCompute(tmp_path):
    with registeredNodeTypes([ComputeMeshroomScene]):
        graph = Graph("")
        node = graph.addNewNode("ComputeMeshroomScene")
        node.scene.value = str(tmp_path / "missing.mg")
        with pytest.raises(RuntimeError, match="missing.mg"):
            node.nodeDesc.preprocess(node)


def test_inputValuesAreKeptWhenUsingOnlyGraphIONodes(tmp_path):
    with registeredNodeTypes([ComputeMeshroomScene, GraphInput, GraphOutput, InputInt]):
        scenePath = tmp_path / "scene.mg"
        graphInput, _ = _saveScene(scenePath)
        scene = loadGraph(str(scenePath))
        inputInt = scene.addNewNode("InputInt")
        scene.save(str(scenePath))

        graph = Graph("")
        node = graph.addNewNode("ComputeMeshroomScene")
        node.scene.value = str(scenePath)
        countName = encodeAttributeName(f"{graphInput.name}.ins.count_")
        integerName = encodeAttributeName(f"{inputInt.name}.integer")
        node.inputs.value.get(countName).value = 5
        node.inputs.value.get(integerName).value = 7

        # The attributes of the other input nodes are hidden, the values of the GraphInput ones are kept
        node.useOnlyGraphIONodes.value = True
        assert integerName not in node.inputs.value.keys()
        assert node.inputs.value.get(countName).value == 5

        # The hidden attributes come back with their values
        node.useOnlyGraphIONodes.value = False
        assert node.inputs.value.get(countName).value == 5
        assert node.inputs.value.get(integerName).value == 7

        # Another scene starts from its own values
        otherScenePath = tmp_path / "other.mg"
        _saveScene(otherScenePath)
        node.scene.value = str(otherScenePath)
        assert node.inputs.value.get(countName).value == 3

        # Setting the first scene again (e.g. undoing the scene change) restores the values set on its inputs
        node.scene.value = str(scenePath)
        assert node.inputs.value.get(countName).value == 5
        assert node.inputs.value.get(integerName).value == 7


def test_inputValuesAreRestoredAfterReloadAndSceneChange(tmp_path):
    with registeredNodeTypes([ComputeMeshroomScene, GraphInput, GraphOutput]):
        scenePath = tmp_path / "scene.mg"
        graphInput, _ = _saveScene(scenePath)
        otherScenePath = tmp_path / "other.mg"
        _saveScene(otherScenePath)
        countName = encodeAttributeName(f"{graphInput.name}.ins.count_")

        projectPath = tmp_path / "project.mg"
        graph = Graph("")
        graph.save(str(projectPath))
        node = graph.addNewNode("ComputeMeshroomScene")
        node.scene.value = str(scenePath)
        node.inputs.value.get(countName).value = 5
        graph.save(str(projectPath))

        # The exposed scene is saved with the project: its values are remembered on the first scene change after a reload
        node = loadGraph(str(projectPath)).node(node.name)
        node.scene.value = str(otherScenePath)
        node.scene.value = str(scenePath)
        assert node.inputs.value.get(countName).value == 5
