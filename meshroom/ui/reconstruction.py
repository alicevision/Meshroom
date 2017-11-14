import os
from threading import Thread

from PySide2.QtCore import QObject, Slot, Property, Signal, QJsonValue, QUrl

from meshroom import multiview
from meshroom.core import graph, defaultCacheFolder, cacheFolderName
from meshroom.ui import commands


class Reconstruction(QObject):

    def __init__(self, graphFilepath="", parent=None):
        super(Reconstruction, self).__init__(parent)
        self._graph = None
        self._undoStack = commands.UndoStack(self)
        self._computeThread = Thread()
        self._filepath = graphFilepath
        if self._filepath:
            self.load(self._filepath)
        else:
            self.new()

    @Slot()
    def new(self):
        self.clear()
        self._graph = multiview.photogrammetryPipeline()
        self._graph.cacheDir = defaultCacheFolder
        self._graph.update()
        self.graphChanged.emit()

    def clear(self):
        if self._graph:
            self._graph.clear()
            self._graph.deleteLater()
            self._graph = None
        self.setFilepath("")
        self._undoStack.clear()

    def setFilepath(self, path):
        if self._filepath == path:
            return
        self._filepath = path
        self.filepathChanged.emit()

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
        if value.isArray():
            pyValue = value.toArray().toVariantList()
        else:
            pyValue = None if value.isNull() else value.toObject()
        self._undoStack.tryAndPush(commands.ListAttributeAppendCommand(self._graph, attribute, pyValue))

    @Slot(graph.Attribute)
    def removeAttribute(self, attribute):
        self._undoStack.tryAndPush(commands.ListAttributeRemoveCommand(self._graph, attribute))

    def load(self, filepath):
        self.clear()
        self._graph = graph.Graph("")
        self._graph.load(filepath)
        self.setFilepath(filepath)
        self.graphChanged.emit()

    @Slot(QUrl)
    def loadUrl(self, url):
        self.load(url.toLocalFile())

    @Slot(QUrl)
    def saveAs(self, url):
        self.setFilepath(url.toLocalFile())
        self.save()

    @Slot()
    def save(self):
        self._graph.save(self._filepath)
        self._graph.cacheDir = os.path.join(os.path.dirname(self._filepath), cacheFolderName)
        self._undoStack.setClean()

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
    graphChanged = Signal()
    graph = Property(graph.Graph, lambda self: self._graph, notify=graphChanged)
    computingChanged = Signal()
    computing = Property(bool, lambda self: self._computeThread.is_alive(), notify=computingChanged)
    filepathChanged = Signal()
    filepath = Property(str, lambda self: self._filepath, notify=filepathChanged)
