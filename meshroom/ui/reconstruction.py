from PySide2 import QtCore

from meshroom.processGraph import graph
from meshroom.ui import commands


class Reconstruction(QtCore.QObject):

    def __init__(self, parent=None):
        super(Reconstruction, self).__init__(parent)
        self._graph = graph.Graph("")
        self._undoStack = commands.UndoStack(self)

    @QtCore.Slot(str)
    def addNode(self, nodeType):
        self._undoStack.tryAndPush(commands.AddNodeCommand(self._graph, nodeType))

    @QtCore.Slot(graph.Node)
    def removeNode(self, node):
        self._undoStack.tryAndPush(commands.RemoveNodeCommand(self._graph, node))

    @QtCore.Slot(graph.Attribute, "QVariant")
    def setAttribute(self, attribute, value):
        self._undoStack.tryAndPush(commands.SetAttributeCommand(self._graph, attribute, value))

    @QtCore.Slot(str)
    def load(self, filepath):
        self._graph.load(filepath)

    undoStack = QtCore.Property(QtCore.QObject, lambda self: self._undoStack, constant=True)
    graph = QtCore.Property(QtCore.QObject, lambda self: self._graph, constant=True)
    nodes = QtCore.Property(QtCore.QObject, lambda self: self._graph.nodes, constant=True)
