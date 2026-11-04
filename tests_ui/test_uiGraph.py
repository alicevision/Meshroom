#!/usr/bin/env python
# coding:utf-8

from meshroom.nodes.general.InputInt import InputInt

from tests.utils import registeredNodeTypes


def test_setAttributeIsUndoable(uiGraph, undoStack):
    with registeredNodeTypes([InputInt]):
        node = uiGraph.addNewNode("InputInt")
        defaultValue = node.integer.value

        uiGraph.setAttribute(node.integer, defaultValue + 1)
        assert node.integer.value == defaultValue + 1

        undoStack.undo()
        assert node.integer.value == defaultValue

        undoStack.redo()
        assert node.integer.value == defaultValue + 1

        # Undoing the node creation removes it from the graph
        undoStack.undo()
        undoStack.undo()
        assert node.name not in uiGraph.graph.nodes.keys()
