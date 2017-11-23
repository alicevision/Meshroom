import logging
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

        self._buildIntrinsicsThread = None
        self.intrinsicsBuilt.connect(self.onIntrinsicsAvailable)

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
            import traceback
            logging.error("Error during Graph execution: {}".format(traceback.format_exc()))
        finally:
            self.computingChanged.emit()

    @Slot()
    def stopExecution(self):
        if not self.computing:
            return
        self._graph.stopExecution()
        self._computeThread.join()
        self.computingChanged.emit()

    @staticmethod
    def runAsync(func, args=(), kwargs=None):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread

    undoStack = Property(QObject, lambda self: self._undoStack, constant=True)
    graphChanged = Signal()
    graph = Property(graph.Graph, lambda self: self._graph, notify=graphChanged)
    computingChanged = Signal()
    computing = Property(bool, lambda self: self._computeThread.is_alive(), notify=computingChanged)
    filepathChanged = Signal()
    filepath = Property(str, lambda self: self._filepath, notify=filepathChanged)

    @Slot(QObject)
    def handleFilesDrop(self, drop):
        """ Handle drop events aiming to add images to the Reconstruction.
        Fetching urls from dropEvent is generally expensive in QML/JS (bug ?).
        This method allows to reduce process time by doing it on Python side.
        """
        self.importImagesFromUrls(drop.property("urls"))

    @Slot(QObject)
    def importImagesFromUrls(self, urls):
        """ Add the given list of images (as QUrl) to the Reconstruction. """
        # Build the list of images paths
        images = []
        for url in urls:
            localFile = url.toLocalFile()
            if os.path.splitext(localFile)[1].lower() in (".jpg", ".png", ".jpeg"):
                images.append(localFile)
        if not images:
            return
        # Start the process of updating views and intrinsics
        self._buildIntrinsicsThread = self.runAsync(self.buildIntrinsics, args=(images,))

    def buildIntrinsics(self, additionalViews):
        """
        Build up-to-date intrinsics and views based on already loaded + additional images.
        Does not modify the graph, can be called outside the main thread.
        Emits intrinsicBuilt(views, intrinsics) when done.
        """
        try:
            self.buildingIntrinsicsChanged.emit()
            cameraInit = self._graph.findNode("CameraInit")
            # Retrieve the list of updated viewpoints and intrinsics
            views, intrinsics = cameraInit.nodeDesc.buildIntrinsics(cameraInit, additionalViews)
            self.intrinsicsBuilt.emit(views, intrinsics)
            return views, intrinsics
        except Exception as e:
            logging.error("Error while building intrinsics : {}".format(e))
        finally:
            self.buildingIntrinsicsChanged.emit()

    def onIntrinsicsAvailable(self, views, intrinsics):
        """ Update CameraInit with given views and intrinsics. """
        cameraInit = self._graph.findNode("CameraInit")
        with self.groupedGraphModification("Add Images"):
            self.setAttribute(cameraInit.viewpoints, views)
            self.setAttribute(cameraInit.intrinsics, intrinsics)

    intrinsicsBuilt = Signal(list, list)

    buildingIntrinsicsChanged = Signal()
    buildingIntrinsics = Property(bool, lambda self: self._buildIntrinsicsThread and self._buildIntrinsicsThread.isAlive(),
                                  notify=buildingIntrinsicsChanged)
