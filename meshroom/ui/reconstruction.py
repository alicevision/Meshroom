from threading import Thread

from PySide2.QtCore import QObject, Slot, Property, Signal

from meshroom.core import graph
from meshroom.ui import commands


class Reconstruction(QObject):

    def __init__(self, parent=None):
        super(Reconstruction, self).__init__(parent)
        self._graph = graph.Graph("")
        self._undoStack = commands.UndoStack(self)
        self._computeThread = Thread()

    @Slot(str)
    def addNode(self, nodeType):
        self._undoStack.tryAndPush(commands.AddNodeCommand(self._graph, nodeType))

    @Slot(graph.Node)
    def removeNode(self, node):
        self._undoStack.tryAndPush(commands.RemoveNodeCommand(self._graph, node))

    @Slot(graph.Attribute, graph.Attribute)
    def addEdge(self, src, dst):
        self._undoStack.tryAndPush(commands.AddEdgeCommand(self._graph, src, dst))

    @Slot(graph.Edge)
    def removeEdge(self, edge):
        self._undoStack.tryAndPush(commands.RemoveEdgeCommand(self._graph, edge))

    @Slot(graph.Attribute, "QVariant")
    def setAttribute(self, attribute, value):
        self._undoStack.tryAndPush(commands.SetAttributeCommand(self._graph, attribute, value))

    @Slot(graph.Attribute, QJsonValue)
    def appendAttribute(self, attribute, value):
        self._undoStack.tryAndPush(commands.ListAttributeAppendCommand(self._graph, attribute, value.toObject()))

    @Slot(graph.Attribute)
    def removeAttribute(self, attribute):
        self._undoStack.tryAndPush(commands.ListAttributeRemoveCommand(self._graph, attribute))

    @Slot(str)
    def load(self, filepath):
        self._graph.load(filepath)
        self._graph.update()
        self._undoStack.clear()

    @Slot(graph.Node)
    def execute(self, node=None):
        if self.computing:
            return
        nodes = [node] if node else self._graph.getLeaves()
        self._computeThread = Thread(target=self._execute, args=(nodes,))
        self._computeThread.start()

    def _execute(self, nodes):
        self.computingChanged.emit()
        graph.execute(self._graph, nodes)
        self.computingChanged.emit()

    @Slot()
    def stopExecution(self):
        if not self.computing:
            return
        self._graph.stopExecution()
        self._computeThread.join()
        self.computingChanged.emit()

    undoStack = Property(QObject, lambda self: self._undoStack, constant=True)
    graph = Property(graph.Graph, lambda self: self._graph, constant=True)
    nodes = Property(QObject, lambda self: self._graph.nodes, constant=True)
    computingChanged = Signal()
    computing = Property(bool, lambda self: self._computeThread.is_alive(), notify=computingChanged)