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


def test_remove_linked_child_undo_keeps_value_from_before_the_link(graph, undoStack):
    node = graph.addNewNode("DynamicNode")
    srcNode = graph.addNewNode("DynamicNode")
    child = node.ins.insertAttribute(node.ins.getNewAttributeData("StringParam"), 0)
    child.value = "hello"
    srcNode.code.connectTo(child)

    undoStack.tryAndPush(commands.RemoveAnySetAttributeCommand(graph, child))
    undoStack.undo()
    assert node.ins.string.inputLink is srcNode.code

    graph.removeEdge(node.ins.string)
    assert node.ins.string.value == "hello"


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
