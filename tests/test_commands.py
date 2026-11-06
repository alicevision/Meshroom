from types import SimpleNamespace

import pytest
from PySide6.QtCore import QMetaObject, QObject

from meshroom.core.graph import Graph
from meshroom.core.node import Status
from meshroom.ui import commands


class _App(QObject):
    """ Parent of the undo stack, collecting its messages in place of MeshroomApp. """
    def __init__(self):
        super().__init__()
        self.messages = []

    def showMessage(self, message, status=None):
        self.messages.append((message, status))


# Separate fixtures: the parent must stay alive, as it owns the stack
@pytest.fixture
def app():
    return _App()


@pytest.fixture
def stack(app):
    return commands.UndoStack(app)


def _setStatus(node, status):
    for chunk in node.getAllChunks():
        chunk._status.status = status
    node._nodeStatus.status = status


def _pushRename(stack, graph, node, name, inTaskManager=()):
    taskManager = SimpleNamespace(contains=lambda n: n in inTaskManager)
    return stack.tryAndPush(commands.RenameNodeCommand(graph, taskManager, node, name))


def test_undo_rename_refused_when_node_has_cache(app, stack):
    """ The undo stack must not move when the rename cannot be reverted, or previous commands would use a wrong name. """
    graph = Graph("")
    stack.tryAndPush(commands.AddNodeCommand(graph, "Ls", None))
    ls = graph.node("Ls")
    assert _pushRename(stack, graph, ls, "Foo") == "Foo"

    _setStatus(ls, Status.SUCCESS)
    # Go through the meta object, as QML does
    assert QMetaObject.invokeMethod(stack, "tryUndo")
    assert stack.index == 2
    assert ls.name == "Foo"
    assert app.messages == [("Cannot undo 'Rename Node Ls to Foo'", "warning")]

    # Once the data is cleared, the whole history can be undone
    _setStatus(ls, Status.NONE)
    stack.tryUndo()
    assert stack.index == 1
    assert ls.name == "Ls"
    stack.tryUndo()
    assert stack.index == 0
    assert not graph.nodes


def test_redo_rename_refused_when_node_has_cache(app, stack):
    graph = Graph("")
    ls = graph.addNewNode("Ls")
    _pushRename(stack, graph, ls, "Foo")
    stack.tryUndo()

    _setStatus(ls, Status.SUCCESS)
    assert QMetaObject.invokeMethod(stack, "tryRedo")
    assert stack.index == 0
    assert ls.name == "Ls"
    assert app.messages == [("Cannot redo 'Rename Node Ls to Foo'", "warning")]


def test_undo_rename_refused_when_node_in_task_manager(app, stack):
    """ The Task Manager references its nodes by name, even if they have no cache (e.g. their UID has changed). """
    graph = Graph("")
    ls = graph.addNewNode("Ls")
    inTaskManager = []
    _pushRename(stack, graph, ls, "Foo", inTaskManager)

    inTaskManager.append(ls)
    stack.tryUndo()
    assert stack.index == 1
    assert ls.name == "Foo"
    assert app.messages == [("Cannot undo 'Rename Node Ls to Foo'", "warning")]


def test_undo_rename_after_node_is_recreated(stack):
    """ Undoing a node removal creates a new Node instance, which the rename command must target. """
    graph = Graph("")
    ls = graph.addNewNode("Ls")
    _pushRename(stack, graph, ls, "Foo")
    stack.tryAndPush(commands.RemoveNodeCommand(graph, ls))
    stack.tryUndo()
    stack.tryUndo()
    assert graph.node("Foo") is None
    assert graph.node("Ls").name == "Ls"
