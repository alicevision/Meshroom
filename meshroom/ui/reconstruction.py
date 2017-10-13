from PySide2.QtCore import QObject, Slot, Property, Signal

from meshroom.core import graph
from meshroom.ui import commands


class Reconstruction(QObject):

    def __init__(self, parent=None):
        super(Reconstruction, self).__init__(parent)
        self._graph = graph.Graph("")
        self._undoStack = commands.UndoStack(self)

    @Slot(str)
    def addNode(self, nodeType):
        self._undoStack.tryAndPush(commands.AddNodeCommand(self._graph, nodeType))

    @Slot(graph.Node)
    def removeNode(self, node):
        self._undoStack.tryAndPush(commands.RemoveNodeCommand(self._graph, node))

    @Slot(graph.Attribute, "QVariant")
    def setAttribute(self, attribute, value):
        self._undoStack.tryAndPush(commands.SetAttributeCommand(self._graph, attribute, value))

    @Slot(str)
    def load(self, filepath):
        self._graph.load(filepath)

    undoStack = Property(QObject, lambda self: self._undoStack, constant=True)
    graph = Property(graph.Graph, lambda self: self._graph, constant=True)
    nodes = Property(QObject, lambda self: self._graph.nodes, constant=True)
