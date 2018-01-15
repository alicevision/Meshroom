import logging
import os
from threading import Thread

from PySide2.QtCore import QObject, Slot, Property, Signal

from meshroom import multiview
from meshroom.common.qt import QObjectListModel
from meshroom.core import graph
from meshroom.ui.graph import UIGraph


class Reconstruction(UIGraph):
    """
    Specialization of a UIGraph designed to manage a 3D reconstruction.
    """

    imageExtensions = ('.jpg', '.jpeg', '.tif', '.tiff', '.png', '.exr')

    def __init__(self, graphFilepath='', parent=None):
        super(Reconstruction, self).__init__(graphFilepath, parent)
        self._buildIntrinsicsThread = None
        self._buildingIntrinsics = False
        self._cameraInit = None
        self._cameraInits = QObjectListModel(parent=self)
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
        self.updateCameraInits()
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
        self._graph.nodes.countChanged.connect(self.updateCameraInits)

    @staticmethod
    def runAsync(func, args=(), kwargs=None):
        thread = Thread(target=func, args=args, kwargs=kwargs)
        thread.start()
        return thread

    def getViewpoints(self):
        """ Return the Viewpoints model. """
        # TODO: handle multiple Viewpoints models
        return self._cameraInit.viewpoints.value if self._cameraInit else None

    def updateCameraInits(self):
        cameraInits = self._graph.nodesByType("CameraInit", sortedByIndex=True)
        if set(self._cameraInits.objectList()) == set(cameraInits):
            return
        self._cameraInits.setObjectList(cameraInits)
        self.setCameraInit(cameraInits[0] if cameraInits else None)

    def setCameraInit(self, cameraInit):
        """ Set the internal CameraInit node. """
        # TODO: handle multiple CameraInit nodes
        if self._cameraInit == cameraInit:
            return
        self._cameraInit = cameraInit
        self.cameraInitChanged.emit()

    def getCameraInitIndex(self):
        if not self._cameraInit:
            return -1
        return self._cameraInits.indexOf(self._cameraInit)

    def setCameraInitIndex(self, idx):
        self.setCameraInit(self._cameraInits[idx])

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

    @Slot(QObject, graph.Node)
    def handleFilesDrop(self, drop, cameraInit):
        """ Handle drop events aiming to add images to the Reconstruction.
        Fetching urls from dropEvent is generally expensive in QML/JS (bug ?).
        This method allows to reduce process time by doing it on Python side.
        """
        self.importImages(self.getImageFilesFromDrop(drop), cameraInit)

    @staticmethod
    def isImageFile(filepath):
        """ Return whether filepath is a path to an image file supported by Meshroom. """
        return os.path.splitext(filepath)[1].lower() in Reconstruction.imageExtensions

    @staticmethod
    def getImageFilesFromDrop(drop):
        urls = drop.property("urls")
        # Build the list of images paths
        images = []
        for url in urls:
            localFile = url.toLocalFile()
            if os.path.isdir(localFile):  # get folder content
                files = [os.path.join(localFile, f) for f in os.listdir(localFile)]
            else:
                files = [localFile]
            images.extend([f for f in files if Reconstruction.isImageFile(f)])
        return images

    def importImages(self, images, cameraInit):
        """ Add the given list of images to the Reconstruction. """
        # Start the process of updating views and intrinsics
        self._buildIntrinsicsThread = self.runAsync(self.buildIntrinsics, args=(cameraInit, images,))

    def buildIntrinsics(self, cameraInit, additionalViews):
        """
        Build up-to-date intrinsics and views based on already loaded + additional images.
        Does not modify the graph, can be called outside the main thread.
        Emits intrinsicBuilt(views, intrinsics) when done.
        """
        try:
            self.setBuildingIntrinsics(True)
            # Retrieve the list of updated viewpoints and intrinsics
            views, intrinsics = cameraInit.nodeDesc.buildIntrinsics(cameraInit, additionalViews)
            self.intrinsicsBuilt.emit(cameraInit, views, intrinsics)
            return views, intrinsics
        except Exception:
            import traceback
            logging.error("Error while building intrinsics : {}".format(traceback.format_exc()))
        finally:
            self.setBuildingIntrinsics(False)

    def onIntrinsicsAvailable(self, cameraInit, views, intrinsics):
        """ Update CameraInit with given views and intrinsics. """
        with self.groupedGraphModification("Add Images"):
            self.setAttribute(cameraInit.viewpoints, views)
            self.setAttribute(cameraInit.intrinsics, intrinsics)
        self.setCameraInit(cameraInit)

    def setBuildingIntrinsics(self, value):
        if self._buildingIntrinsics == value:
            return
        self._buildingIntrinsics = value
        self.buildingIntrinsicsChanged.emit()

    cameraInitChanged = Signal()
    cameraInit = Property(QObject, lambda self: self._cameraInit, notify=cameraInitChanged)
    cameraInitIndex = Property(int, getCameraInitIndex, setCameraInitIndex, notify=cameraInitChanged)
    viewpoints = Property(QObject, getViewpoints, notify=cameraInitChanged)
    cameraInits = Property(QObject, lambda self: self._cameraInits, constant=True)
    intrinsicsBuilt = Signal(QObject, list, list)
    buildingIntrinsicsChanged = Signal()
    buildingIntrinsics = Property(bool, lambda self: self._buildingIntrinsics, notify=buildingIntrinsicsChanged)
    meshFileChanged = Signal()
    meshFile = Property(str, lambda self: self._meshFile, notify=meshFileChanged)

