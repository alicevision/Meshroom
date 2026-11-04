#!/usr/bin/env python
# coding:utf-8

from meshroom.core.graph import loadGraph
from meshroom.nodes.general.ComputeMeshroomScene import ComputeMeshroomScene, encodeAttributeName
from meshroom.nodes.general.GraphIO import GraphInput, GraphOutput
from meshroom.nodes.general.InputInt import InputInt

from tests.test_computeMeshroomScene import _saveScene
from tests.utils import registeredNodeTypes


def test_undoingASceneChangeRestoresTheInputValues(uiGraph, undoStack, tmp_path):
    with registeredNodeTypes([ComputeMeshroomScene, GraphInput, GraphOutput]):
        scenePath = tmp_path / "scene.mg"
        otherScenePath = tmp_path / "other.mg"
        graphInput, _ = _saveScene(scenePath)
        _saveScene(otherScenePath)
        countName = encodeAttributeName(f"{graphInput.name}.exposeds.count_")

        node = uiGraph.addNewNode("ComputeMeshroomScene")
        uiGraph.setAttribute(node.scene, str(scenePath))
        uiGraph.setAttribute(node.inputs.value.get(countName), 5)

        # The other scene starts from its own values
        uiGraph.setAttribute(node.scene, str(otherScenePath))
        assert node.inputs.value.get(countName).value == 3

        undoStack.undo()
        assert node.scene.value == str(scenePath)
        assert node.inputs.value.get(countName).value == 5

        undoStack.redo()
        assert node.inputs.value.get(countName).value == 3

        # Undoing the scene change, then the value change
        undoStack.undo()
        undoStack.undo()
        assert node.inputs.value.get(countName).value == 3


def test_undoingUseOnlyGraphIONodesRestoresTheHiddenInputValues(uiGraph, undoStack, tmp_path):
    with registeredNodeTypes([ComputeMeshroomScene, GraphInput, GraphOutput, InputInt]):
        scenePath = tmp_path / "scene.mg"
        _saveScene(scenePath)
        scene = loadGraph(str(scenePath))
        inputInt = scene.addNewNode("InputInt")
        scene.save(str(scenePath))
        integerName = encodeAttributeName(f"{inputInt.name}.integer")

        node = uiGraph.addNewNode("ComputeMeshroomScene")
        uiGraph.setAttribute(node.scene, str(scenePath))
        uiGraph.setAttribute(node.inputs.value.get(integerName), 7)

        uiGraph.setAttribute(node.useOnlyGraphIONodes, True)
        assert integerName not in node.inputs.value.keys()

        undoStack.undo()
        assert node.inputs.value.get(integerName).value == 7
