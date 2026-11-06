#!/usr/bin/env python
# coding:utf-8

import re
import shlex
from pathlib import Path
from types import SimpleNamespace

import pytest

from meshroom.core import desc
from meshroom.core.graph import Graph, loadGraph
from meshroom.nodes.general.ComputeMeshroomScene import ComputeMeshroomScene, decodeAttributeName, encodeAttributeName
from meshroom.nodes.general.GraphIO import GraphInput, GraphOutput
from meshroom.nodes.general.InputInt import InputInt

from .nodes.test.OutputNode import OutputNodeTest
from .utils import registeredNodeTypes


# Same expression as meshroom_batch to parse the --paramOverrides arguments
_PARAM_OVERRIDE_RE = re.compile(r'(\w+)([:.])(\w[\w.]*)=(.*)')


class FileProducer(desc.Node):
    """ A node producing a file in its cache folder. """
    inputs = []
    outputs = [
        desc.File(name="output", label="Output", description="Output file.", value="{nodeCacheFolder}/out.txt"),
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

        # Without any change, no input is overridden, and the given scene is not overwritten either
        args = shlex.split(node.nodeDesc.buildCommandLine(SimpleNamespace(node=node)))
        assert "--paramOverrides" not in args
        assert Path(args[args.index("--save") + 1]) != scenePath

        node.inputs.value.get(encodeAttributeName(f"{graphInput.name}.ins.inputFile")).value = "/data/other shots/b.jpg"
        node.inputs.value.get(encodeAttributeName(f"{graphInput.name}.ins.count_")).value = 5
        cmd = node.nodeDesc.buildCommandLine(SimpleNamespace(node=node))
        args = shlex.split(cmd)

        # The given scene is not overwritten with the overrides (paths are compared as Paths, as File values use "/")
        assert Path(args[args.index("-p") + 1]) == scenePath
        assert Path(args[args.index("--save") + 1]) != scenePath

        # Each modified input is overridden and resolves to the scene attribute, as in meshroom_batch
        scene = loadGraph(str(scenePath))
        overrides = args[args.index("--paramOverrides") + 1:]
        overrides = overrides[:next((i for i, arg in enumerate(overrides) if arg.startswith("--")), len(overrides))]
        values = {}
        for override in overrides:
            nodeName, separator, param, value = _PARAM_OVERRIDE_RE.match(override).groups()
            assert separator == "."
            attribute = scene.findNode(nodeName).attribute(param)
            assert attribute is not None
            values[attribute.fullName] = value

        assert values == {
            f"{graphInput.name}.ins.inputFile": "/data/other shots/b.jpg",
            f"{graphInput.name}.ins.count_": "5",
        }


def test_outputNodesAreNotExposed(tmp_path):
    with registeredNodeTypes([ComputeMeshroomScene, GraphInput, GraphOutput, OutputNodeTest]):
        scenePath = tmp_path / "scene.mg"
        _, graphOutput = _saveScene(scenePath)
        # Output nodes are removed from the scene computed by meshroom_batch: their attributes cannot be exposed
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

        # Simulate meshroom_batch saving the scene in the node's folder before computing it
        computedScenePath = Path(node.nodeDesc._computedScenePath(node))
        computedScenePath.parent.mkdir(parents=True)
        loadGraph(str(scenePath)).save(str(computedScenePath))
        node.nodeDesc._updateOutputs(node)

        # The exposed output points to the cache of the computed scene, not to the one of the given scene
        outputPath = Path(list(node.outputs.value)[0].value)
        assert outputPath.name == "out.txt"
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
            node.nodeDesc.buildCommandLine(SimpleNamespace(node=node))


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
