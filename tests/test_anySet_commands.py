"""Tests for the undo and redo of the AnySet commands."""

import pytest

pytest.importorskip("PySide6.QtGui", exc_type=ImportError)

from meshroom.core.graph import Graph
from meshroom.ui import commands


@pytest.fixture
def graph():
    return Graph("test")


@pytest.fixture
def undoStack():
    return commands.UndoStack()


def edgeNames(graph):
    return sorted((edge.src.fullName, edge.dst.fullName) for edge in graph.edges.values())


def test_add_child_can_be_undone_and_redone(graph, undoStack):
    node = graph.addNewNode("DynamicNode")

    undoStack.tryAndPush(commands.AddAnySetAttributeCommand(graph, node.ins, "IntParam"))
    assert node.ins.int.type == "IntParam"

    undoStack.undo()
    assert node.ins.value.count == 0

    undoStack.redo()
    assert node.ins.int.type == "IntParam"


def test_discarded_add_leaves_no_trace_in_the_history(graph, undoStack):
    node = graph.addNewNode("DynamicNode")
    command = commands.AddAnySetAttributeCommand(graph, node.ins, "IntParam")
    undoStack.tryAndPush(command)

    assert undoStack.discardLastCommand(command)

    assert node.ins.value.count == 0
    assert undoStack.count() == 0


def test_edit_child_can_be_undone_and_keeps_its_edge(graph, undoStack):
    node = graph.addNewNode("DynamicNode")
    srcNode = graph.addNewNode("DynamicNode")
    child = node.ins.insertAttribute(node.ins.getNewAttributeData("StringParam"), 0)
    srcNode.code.connectTo(child)

    undoStack.tryAndPush(commands.EditAnySetAttributeCommand(graph, child, {"name": "renamed", "label": "Renamed"}))
    assert node.ins.renamed.inputLink is srcNode.code

    undoStack.undo()
    assert node.ins.string.inputLink is srcNode.code
    assert node.ins.renamed is None


def test_remove_list_child_can_be_undone_with_the_edges_of_its_elements(graph, undoStack):
    node = graph.addNewNode("DynamicNode")
    srcNode = graph.addNewNode("DynamicNode")
    dstNode = graph.addNewNode("DynamicNode")
    elementDesc = {"name": "string", "label": "String", "type": "StringParam", "value": ""}
    listChild = node.ins.insertAttribute({"name": "list", "label": "List", "type": "ListAttribute", "value": [], "elementDesc": elementDesc}, 0)
    listChild.extend(["a", "b"])
    srcNode.code.connectTo(listChild.at(0))
    listChild.at(1).connectTo(dstNode.code)
    edgesBefore = edgeNames(graph)

    undoStack.tryAndPush(commands.RemoveAnySetAttributeCommand(graph, listChild))
    assert edgeNames(graph) == []

    undoStack.undo()
    assert edgeNames(graph) == edgesBefore


def test_connect_from_anyset_can_be_undone_and_restores_the_previous_link(graph, undoStack):
    node = graph.addNewNode("DynamicNode")
    previousSrcNode = graph.addNewNode("DynamicNode")
    dstNode = graph.addNewNode("DynamicNode")
    previousSrcNode.code.connectTo(dstNode.code)

    undoStack.tryAndPush(commands.ConnectAnySetCommand(graph, src=dstNode.code, anySetAttribute=node.ins, isSource=True))
    assert dstNode.code.inputLink is node.ins.code

    undoStack.undo()
    assert dstNode.code.inputLink is previousSrcNode.code
    assert node.ins.value.count == 0
