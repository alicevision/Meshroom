import logging
import os
from threading import Thread

from PySide2.QtCore import QObject, Slot, Property, Signal

from meshroom import multiview
from meshroom.core import graph
from meshroom.ui.graph import UIGraph


class Reconstruction(UIGraph):
    """
    Specialization of a UIGraph designed to manage a 3D reconstruction.
    """
    def __init__(self, graphFilepath='', parent=None):
        super(Reconstruction, self).__init__(graphFilepath, parent)
        self._buildIntrinsicsThread = None
        self._cameraInit = None
        self._endChunk = None
        self._meshFile = ''
        self.intrinsicsBuilt.connect(self.onIntrinsicsAvailable)
        self.graphChanged.connect(self.onGraphChanged)
        if graphFilepath:
            self.onGraphChanged()
        else:
            self.new()

    @Slot()
    def new(self):
        """ Create a new photogrammetry pipeline. """
        self.setGraph(multiview.photogrammetryPipeline())

    def onGraphChanged(self):
        """ React to the change of the internal graph. """
        self._endChunk = None
        self.setMeshFile('')
        self.updateCameraInit()
        if not self._graph:
            return

        try:
            endNode = self._graph.findNode("Texturing")
            self._endChunk = endNode.getChunks()[0]  # type: graph.NodeChunk
            endNode.outputMesh.valueChanged.connect(self.updateMeshFile)
            self._endChunk.statusChanged.connect(self.updateMeshFile)
            self.updateMeshFile()
        except KeyError:
            self._endChunk = None
        # TODO: listen specifically for cameraInit creation/deletion
        self._graph.nodes.countChanged.connect(self.updateCameraInit)

    @staticmethod
    def runAsync(func, args=(), kwargs=None):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread

    def getViewpoints(self):
        """ Return the Viewpoints model. """
        # TODO: handle multiple Viewpoints models
        return self._cameraInit.viewpoints.value if self._cameraInit else None

    def updateCameraInit(self):
        """ Update internal CameraInit node (Viewpoints model owner) based on graph content. """
        # TODO: handle multiple CameraInit nodes
        if self._cameraInit in self._graph.nodes:
            return
        cameraInits = self._graph.findNodeCandidates("CameraInit")
        self.setCameraInit(cameraInits[0] if cameraInits else None)

    def setCameraInit(self, cameraInit):
        """ Set the internal CameraInit node. """
        # TODO: handle multiple CameraInit nodes
        if self._cameraInit == cameraInit:
            return
        self._cameraInit = cameraInit
        self.viewpointsChanged.emit()

    def updateMeshFile(self):
        if self._endChunk and self._endChunk.status.status == graph.Status.SUCCESS:
            self.setMeshFile(self._endChunk.node.outputMesh.value)
        else:
            self.setMeshFile('')

    def setMeshFile(self, mf):
        if self._meshFile == mf:
            return
        self._meshFile = mf
        self.meshFileChanged.emit()

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
            # Retrieve the list of updated viewpoints and intrinsics
            views, intrinsics = self._cameraInit.nodeDesc.buildIntrinsics(self._cameraInit, additionalViews)
            self.intrinsicsBuilt.emit(views, intrinsics)
            return views, intrinsics
        except Exception as e:
            logging.error("Error while building intrinsics : {}".format(e))
        finally:
            self.buildingIntrinsicsChanged.emit()

    def onIntrinsicsAvailable(self, views, intrinsics):
        """ Update CameraInit with given views and intrinsics. """
        with self.groupedGraphModification("Add Images"):
            self.setAttribute(self._cameraInit.viewpoints, views)
            self.setAttribute(self._cameraInit.intrinsics, intrinsics)

    def isBuildingIntrinsics(self):
        """ Whether intrinsics are being built """
        return self._buildIntrinsicsThread and self._buildIntrinsicsThread.isAlive()

    viewpointsChanged = Signal()
    viewpoints = Property(QObject, getViewpoints, notify=viewpointsChanged)
    intrinsicsBuilt = Signal(list, list)
    buildingIntrinsicsChanged = Signal()
    buildingIntrinsics = Property(bool, isBuildingIntrinsics, notify=buildingIntrinsicsChanged)
    meshFileChanged = Signal()
    meshFile = Property(str, lambda self: self._meshFile, notify=meshFileChanged)

