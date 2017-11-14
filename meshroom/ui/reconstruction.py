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

    def push(self, command):
        """ Try and push the given command to the undo stack.

        Args:
            command (commands.UndoCommand): the command to push
        """
        self._undoStack.tryAndPush(command)

    def groupedGraphModification(self, title):
        """ Get a GroupedGraphModification for this Reconstruction.

        Args:
            title (str): the title of the macro command

        Returns:
            GroupedGraphModification: the instantiated context manager
        """
        return commands.GroupedGraphModification(self._graph, self._undoStack, title)

    @Slot(str)
    def addNode(self, nodeType):
        self.push(commands.AddNodeCommand(self._graph, nodeType))

    @Slot(graph.Node)
    def removeNode(self, node):
        self.push(commands.RemoveNodeCommand(self._graph, node))

    @Slot(graph.Attribute, graph.Attribute)
    def addEdge(self, src, dst):
        if isinstance(dst, graph.ListAttribute):
            with self.groupedGraphModification("Insert and Add Edge on {}".format(dst.fullName())):
                self.appendAttribute(dst)
                self.push(commands.AddEdgeCommand(self._graph, src, dst[-1]))
        else:
            self.push(commands.AddEdgeCommand(self._graph, src, dst))

    @Slot(graph.Edge)
    def removeEdge(self, edge):
        if isinstance(edge.dst.root, graph.ListAttribute):
            with self.groupedGraphModification("Remove Edge and Delete {}".format(edge.dst.fullName())):
                self.push(commands.RemoveEdgeCommand(self._graph, edge))
                self.removeAttribute(edge.dst)
        else:
            self.push(commands.RemoveEdgeCommand(self._graph, edge))

    @Slot(graph.Attribute, "QVariant")
    def setAttribute(self, attribute, value):
        self.push(commands.SetAttributeCommand(self._graph, attribute, value))

    @Slot(graph.Attribute, QJsonValue)
    def appendAttribute(self, attribute, value=QJsonValue()):
        if value.isArray():
            pyValue = value.toArray().toVariantList()
        else:
            pyValue = None if value.isNull() else value.toObject()
        self.push(commands.ListAttributeAppendCommand(self._graph, attribute, pyValue))

    @Slot(graph.Attribute)
    def removeAttribute(self, attribute):
        self.push(commands.ListAttributeRemoveCommand(self._graph, attribute))

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
        try:
            graph.execute(self._graph, nodes)
        except Exception as e:
            logging.error("Error during Graph execution {}".format(e))
        finally:
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
