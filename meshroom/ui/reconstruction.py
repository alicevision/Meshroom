import json
import logging
import math
import os
from threading import Thread

from PySide2.QtCore import QObject, Slot, Property, Signal, QUrl, QSizeF
from PySide2.QtGui import QMatrix4x4, QMatrix3x3, QQuaternion, QVector3D, QVector2D

import meshroom.core
from meshroom import multiview
from meshroom.common.qt import QObjectListModel
from meshroom.core import Version
from meshroom.core.node import Node, Status, Position
from meshroom.ui.graph import UIGraph
from meshroom.ui.utils import makeProperty


class Message(QObject):
    """ Simple structure wrapping a high-level message. """

    def __init__(self, title, text, detailedText="", parent=None):
        super(Message, self).__init__(parent)
        self._title = title
        self._text = text
        self._detailedText = detailedText

    title = Property(str, lambda self: self._title, constant=True)
    text = Property(str, lambda self: self._text, constant=True)
    detailedText = Property(str, lambda self: self._detailedText, constant=True)


class LiveSfmManager(QObject):
    """
    Manage a live SfM reconstruction by creating augmentation steps in the graph over time,
    based on images progressively added to a watched folder.

    File watching is based on regular polling and not filesystem events to work on network mounts.
    """
    def __init__(self, reconstruction):
        super(LiveSfmManager, self).__init__(reconstruction)
        self.reconstruction = reconstruction
        self._folder = ''
        self.timerId = -1
        self.minImagesPerStep = 4
        self.watchTimerInterval = 1000
        self.allImages = []
        self.cameraInit = None
        self.sfm = None
        self._running = False

    def reset(self):
        self.stop(False)
        self.sfm = None
        self.cameraInit = None

    def setRunning(self, value):
        if self._running == value:
            return
        if self._running:
            self.killTimer(self.timerId)
        else:
            self.timerId = self.startTimer(self.watchTimerInterval)
        self._running = value
        self.runningChanged.emit()

    @Slot(str, int)
    def start(self, folder, minImagesPerStep):
        """
        Start live SfM augmentation.

        Args:
            folder (str): the folder to watch in which images are added over time
            minImagesPerStep (int): minimum number of images in an augmentation step
        """
        # print('[LiveSfmManager] Watching {} for images'.format(folder))
        if not os.path.isdir(folder):
            raise RuntimeError("Invalid folder provided: {}".format(folder))
        self._folder = folder
        self.folderChanged.emit()
        self.cameraInit = self.sfm = None
        self.allImages = self.reconstruction.allImagePaths()
        self.minImagesPerStep = minImagesPerStep
        self.setRunning(True)
        self.update()  # trigger initial update

    @Slot()
    def stop(self, requestCompute=True):
        """ Stop the live SfM reconstruction.

        Request the computation of the last augmentation step if any.
        """
        self.setRunning(False)
        if requestCompute:
            self.computeStep()

    def timerEvent(self, evt):
        self.update()

    def update(self):
        """
        Look for new images in the watched folder and create SfM augmentation step (or modify existing one)
        to include those images to the reconstruction.
        """
        # Get all new images in the watched folder
        imagesInFolder = multiview.findFilesByTypeInFolder(self._folder)
        newImages = set(imagesInFolder).difference(self.allImages)
        for imagePath in newImages:
            # print('[LiveSfmManager] New image file : {}'.format(imagePath))
            if not self.cameraInit:
                # Start graph modification: until 'computeAugmentation' is called, every commands
                # used will be part of this macro
                self.reconstruction.beginModification("SfM Augmentation")
                # Add SfM augmentation step in the graph
                self.cameraInit, self.sfm = self.reconstruction.addSfmAugmentation()
            self.addImageToStep(imagePath)

        # If we have enough images and the graph is not being computed, compute augmentation step
        if len(self.imagesInStep()) >= self.minImagesPerStep and not self.reconstruction.computing:
            self.computeStep()

    def addImageToStep(self, path):
        """ Add an image to the current augmentation step. """
        self.reconstruction.appendAttribute(self.cameraInit.viewpoints, {'path': path})
        self.allImages.append(path)

    def imagePathsInCameraInit(self, node):
        """ Get images in the given CameraInit node. """
        assert node.nodeType == 'CameraInit'
        return [vp.path.value for vp in node.viewpoints.value]

    def imagesInStep(self):
        """ Get images in the current augmentation step. """
        return self.imagePathsInCameraInit(self.cameraInit) if self.cameraInit else []


    @Slot()
    def computeStep(self):
        """ Freeze the current augmentation step and request its computation.
        A new step will be created once another image is added to the watched folder during 'update'.
        """
        if not self.cameraInit:
            return

        # print('[LiveSfmManager] Compute SfM augmentation')
        # Build intrinsics in the main thread
        self.reconstruction.buildIntrinsics(self.cameraInit, [])
        self.cameraInit = None
        sfm = self.sfm
        self.sfm = None
        # Stop graph modification and start sfm computation
        self.reconstruction.endModification()
        self.reconstruction.execute(sfm)

    runningChanged = Signal()
    running = Property(bool, lambda self: self._running, notify=runningChanged)
    folderChanged = Signal()
    folder = Property(str, lambda self: self._folder, notify=folderChanged)


class ViewpointWrapper(QObject):
    """
    ViewpointWrapper is a high-level object that wraps an input image in the context of a Reconstruction.
    It exposes the attributes of the image and its corresponding camera when reconstructed.
    """

    initialParamsChanged = Signal()
    sfmParamsChanged = Signal()
    denseSceneParamsChanged = Signal()
    internalChanged = Signal()

    def __init__(self, viewpointAttribute, reconstruction):
        """
        Viewpoint constructor

        Args:
            viewpointAttribute (GroupAttribute): viewpoint attribute
            reconstruction (Reconstruction): owner reconstruction of this Viewpoint
        """
        super(ViewpointWrapper, self).__init__(parent=reconstruction)
        self._viewpoint = viewpointAttribute
        self._reconstruction = reconstruction

        # CameraInit
        self._initialIntrinsics = None
        # StructureFromMotion
        self._T = None  # translation
        self._R = None  # rotation
        self._solvedIntrinsics = {}
        self._reconstructed = False
        # PrepareDenseScene
        self._undistortedImagePath = ''

        # update internally cached variables
        self._updateInitialParams()
        self._updateSfMParams()
        self._updateDenseSceneParams()

        # trigger internal members updates when reconstruction members changes
        self._reconstruction.cameraInitChanged.connect(self._updateInitialParams)
        self._reconstruction.sfmReportChanged.connect(self._updateSfMParams)
        self._reconstruction.prepareDenseSceneChanged.connect(self._updateDenseSceneParams)

    def _updateInitialParams(self):
        """ Update internal members depending on CameraInit. """
        if not self._reconstruction.cameraInit:
            self.initialIntrinsics = None
            self._metadata = {}
        else:
            self._initialIntrinsics = self._reconstruction.getIntrinsic(self._viewpoint)
            self._metadata = json.loads(self._viewpoint.metadata.value) if self._viewpoint.metadata.value else None
            if not self._metadata:
                self._metadata = {}
        self.initialParamsChanged.emit()

    def _updateSfMParams(self):
        """ Update internal members depending on StructureFromMotion. """
        if not self._reconstruction.sfm:
            self._T = None
            self._R = None
            self._solvedIntrinsics = {}
            self._reconstructed = False
        else:
            self._solvedIntrinsics = self._reconstruction.getSolvedIntrinsics(self._viewpoint)
            self._R, self._T = self._reconstruction.getPoseRT(self._viewpoint)
            self._reconstructed = self._R is not None
        self.sfmParamsChanged.emit()

    def _updateDenseSceneParams(self):
        """ Update internal members depending on PrepareDenseScene. """
        # undistorted image path
        if not self._reconstruction.prepareDenseScene:
            self._undistortedImagePath = ''
        else:
            filename = "{}.{}".format(self._viewpoint.viewId.value, self._reconstruction.prepareDenseScene.outputFileType.value)
            self._undistortedImagePath = os.path.join(self._reconstruction.prepareDenseScene.output.value, filename)
        self.denseSceneParamsChanged.emit()

    @Property(type=QObject, constant=True)
    def attribute(self):
        """ Get the underlying Viewpoint attribute wrapped by this Viewpoint. """
        return self._viewpoint

    @Property(type="QVariant", notify=initialParamsChanged)
    def initialIntrinsics(self):
        """ Get viewpoint's initial intrinsics. """
        return self._initialIntrinsics

    @Property(type="QVariant", notify=initialParamsChanged)
    def metadata(self):
        """ Get image metadata. """
        return self._metadata

    @Property(type=QSizeF, notify=initialParamsChanged)
    def imageSize(self):
        """ Get image size (width as the largest dimension). """
        if not self._initialIntrinsics:
            return QSizeF(0, 0)
        return QSizeF(self._initialIntrinsics.width.value, self._initialIntrinsics.height.value)

    @Property(type=int, notify=initialParamsChanged)
    def orientation(self):
        """ Get image orientation based on its metadata. """
        return int(self.metadata.get("Orientation", 1))

    @Property(type=QSizeF, notify=initialParamsChanged)
    def orientedImageSize(self):
        """ Get image size taking into account its orientation. """
        if self.orientation in (6, 8):
            return QSizeF(self.imageSize.height(), self.imageSize.width())
        else:
            return self.imageSize

    @Property(type=bool, notify=sfmParamsChanged)
    def isReconstructed(self):
        """ Return whether this viewpoint corresponds to a reconstructed camera. """
        return self._reconstructed

    @Property(type="QVariant", notify=sfmParamsChanged)
    def solvedIntrinsics(self):
        return self._solvedIntrinsics

    @Property(type=QVector3D, notify=sfmParamsChanged)
    def translation(self):
        """ Get the camera translation as a 3D vector. """
        if self._T is None:
            return None
        return QVector3D(*self._T)

    @Property(type=QQuaternion, notify=sfmParamsChanged)
    def rotation(self):
        """ Get the camera rotation as a quaternion. """
        if self._R is None:
            return None

        rot = QMatrix3x3([
            self._R[0], -self._R[1], -self._R[2],
            self._R[3], -self._R[4], -self._R[5],
            self._R[6], -self._R[7], -self._R[8]]
        )

        return QQuaternion.fromRotationMatrix(rot)

    @Property(type=QMatrix4x4, notify=sfmParamsChanged)
    def pose(self):
        """ Get the camera pose of 'viewpoint' as a 4x4 matrix. """
        if self._R is None or self._T is None:
            return None

        # convert transform matrix for Qt
        return QMatrix4x4(
            self._R[0], -self._R[1], -self._R[2], self._T[0],
            self._R[3], -self._R[4], -self._R[5], self._T[1],
            self._R[6], -self._R[7], -self._R[8], self._T[2],
            0,          0,           0,           1
        )

    @Property(type=QVector3D, notify=sfmParamsChanged)
    def upVector(self):
        """ Get camera up vector according to its orientation. """
        if self.orientation == 6:
            return QVector3D(-1.0, 0.0, 0.0)
        elif self.orientation == 8:
            return QVector3D(1.0, 0.0, 0.0)
        else:
            return QVector3D(0.0, 1.0, 0.0)

    @Property(type=QVector2D, notify=sfmParamsChanged)
    def uvCenterOffset(self):
        """ Get UV offset corresponding to the camera principal point. """
        if not self.solvedIntrinsics:
            return None
        pp = self.solvedIntrinsics["principalPoint"]
        # compute principal point offset in UV space
        uvPP = QVector2D(float(pp[0]) / self.imageSize.width(), float(pp[1]) / self.imageSize.height())
        # convert to offset
        offset = uvPP - QVector2D(0.5, 0.5)
        # apply orientation to principal point correction
        if self.orientation == 6:
            offset = QVector2D(-offset.y(), offset.x())
        elif self.orientation == 8:
            offset = QVector2D(offset.y(), -offset.x())
        return offset

    @Property(type=float, notify=sfmParamsChanged)
    def fieldOfView(self):
        """ Get camera vertical field of view in degrees. """
        if not self.solvedIntrinsics:
            return None
        pxFocalLength = float(self.solvedIntrinsics["pxFocalLength"])
        return 2.0 * math.atan(self.orientedImageSize.height() / (2.0 * pxFocalLength)) * 180 / math.pi

    @Property(type=QUrl, notify=denseSceneParamsChanged)
    def undistortedImageSource(self):
        """ Get path to undistorted image source if available. """
        return QUrl.fromLocalFile(self._undistortedImagePath)


class Reconstruction(UIGraph):
    """
    Specialization of a UIGraph designed to manage a 3D reconstruction.
    """

    def __init__(self, defaultPipeline='', parent=None):
        super(Reconstruction, self).__init__(parent)

        # initialize member variables for key steps of the 3D reconstruction pipeline

        # - CameraInit
        self._cameraInit = None                            # current CameraInit node
        self._cameraInits = QObjectListModel(parent=self)  # all CameraInit nodes
        self._buildingIntrinsics = False
        self.intrinsicsBuilt.connect(self.onIntrinsicsAvailable)

        self._hdrCameraInit = None

        self.importImagesFailed.connect(self.onImportImagesFailed)

        # - Feature Extraction
        self._featureExtraction = None
        self.cameraInitChanged.connect(self.updateFeatureExtraction)

        # - SfM
        self._sfm = None
        self._views = None
        self._poses = None
        self._solvedIntrinsics = None
        self._selectedViewId = None
        self._selectedViewpoint = None
        self._liveSfmManager = LiveSfmManager(self)

        # - Prepare Dense Scene (undistorted images)
        self._prepareDenseScene = None

        # - Depth Map
        self._depthMap = None
        self.cameraInitChanged.connect(self.updateDepthMapNode)

        # - Texturing
        self._texturing = None

        # - LDR2HDR
        self._ldr2hdr = None
        self.cameraInitChanged.connect(self.updateLdr2hdrNode)

        # react to internal graph changes to update those variables
        self.graphChanged.connect(self.onGraphChanged)

        self.setDefaultPipeline(defaultPipeline)

    def setDefaultPipeline(self, defaultPipeline):
        self._defaultPipeline = defaultPipeline

    @Slot()
    @Slot(str)
    def new(self, pipeline=None):
        p = pipeline if pipeline != None else self._defaultPipeline
        """ Create a new photogrammetry pipeline. """
        if p.lower() == "photogrammetry":
            # default photogrammetry pipeline
            self.setGraph(multiview.photogrammetry())
        elif p.lower() == "hdri":
            # default hdri pipeline
            self.setGraph(multiview.hdri())
        else:
            # use the user-provided default photogrammetry project file
            self.load(p, setupProjectFile=False)

    @Slot(str)
    def load(self, filepath, setupProjectFile=True):
        try:
            super(Reconstruction, self).load(filepath, setupProjectFile)
            # warn about pre-release projects being automatically upgraded
            if Version(self._graph.fileReleaseVersion).major == "0":
                self.warning.emit(Message(
                    "Automatic project upgrade",
                    "This project was created with an older version of Meshroom and has been automatically upgraded.\n"
                    "Data might have been lost in the process.",
                    "Open it with the corresponding version of Meshroom to recover your data."
                ))
        except Exception as e:
            import traceback
            trace = traceback.format_exc()
            self.error.emit(
                Message(
                    "Error while loading {}".format(os.path.basename(filepath)),
                    "An unexpected error has occurred",
                    trace
                )
            )
            logging.error(trace)

    def onGraphChanged(self):
        """ React to the change of the internal graph. """
        self._liveSfmManager.reset()
        self.selectedViewId = "-1"
        self.featureExtraction = None
        self.sfm = None
        self.prepareDenseScene = None
        self.depthMap = None
        self.texturing = None
        self.ldr2hdr = None
        self.hdrCameraInit = None
        self.updateCameraInits()
        if not self._graph:
            return

        self.setSfm(self.lastSfmNode())

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
        self.cameraInit = cameraInits[0] if cameraInits else None

    def getCameraInitIndex(self):
        if not self._cameraInit:
            # No CameraInit node
            return -1
        if not self._cameraInit.graph:
            # The CameraInit node is a temporary one not attached to a graph
            return -1
        return self._cameraInits.indexOf(self._cameraInit)

    def setCameraInitIndex(self, idx):
        camInit = self._cameraInits[idx] if self._cameraInits else None
        self.cameraInit = camInit

    def updateFeatureExtraction(self):
        """ Set the current FeatureExtraction node based on the current CameraInit node. """
        self.featureExtraction = self.lastNodeOfType('FeatureExtraction', self.cameraInit) if self.cameraInit else None

    def updateDepthMapNode(self):
        """ Set the current FeatureExtraction node based on the current CameraInit node. """
        self.depthMap = self.lastNodeOfType('DepthMapFilter', self.cameraInit) if self.cameraInit else None

    def updateLdr2hdrNode(self):
        """ Set the current LDR2HDR node based on the current CameraInit node. """
        self.ldr2hdr = self.lastNodeOfType('LDRToHDR', self.cameraInit) if self.cameraInit else None

    @Slot()
    def setupLDRToHDRCameraInit(self):
        if not self.ldr2hdr:
            self.hdrCameraInit = Node("CameraInit")
            return
        sfmFile = self.ldr2hdr.attribute("outSfMDataFilename").value
        if not sfmFile or not os.path.isfile(sfmFile):
            self.hdrCameraInit = Node("CameraInit")
            return
        nodeDesc = meshroom.core.nodesDesc["CameraInit"]()
        views, intrinsics = nodeDesc.readSfMData(sfmFile)
        tmpCameraInit = Node("CameraInit", viewpoints=views, intrinsics=intrinsics)
        self.hdrCameraInit = tmpCameraInit

    def lastSfmNode(self):
        """ Retrieve the last SfM node from the initial CameraInit node. """
        return self.lastNodeOfType("StructureFromMotion", self._cameraInit, Status.SUCCESS)

    def lastNodeOfType(self, nodeType, startNode, preferredStatus=None):
        """
        Returns the last node of the given type starting from 'startNode'.
        If 'preferredStatus' is specified, the last node with this status will be considered in priority.

        Args:
            nodeType (str): the node type
            startNode (Node): the node to start from
            preferredStatus (Status): (optional) the node status to prioritize

        Returns:
            Node: the node matching the input parameters or None
        """
        if not startNode:
            return None
        nodes = self._graph.nodesFromNode(startNode, nodeType)[0]
        if not nodes:
            return None
        node = nodes[-1]
        if preferredStatus:
            node = next((n for n in reversed(nodes) if n.getGlobalStatus() == preferredStatus), node)
        return node

    def addSfmAugmentation(self, withMVS=False):
        """
        Create a new augmentation step connected to the last SfM node of this Reconstruction and
        return the created CameraInit and SfM nodes.

        If the Reconstruction is not initialized (empty initial CameraInit), this method won't
        create anything and return initial CameraInit and SfM nodes.

        Args:
            withMVS (bool): whether to create the MVS pipeline after the augmentation

        Returns:
            Node, Node: CameraInit, StructureFromMotion
        """
        sfm = self.lastSfmNode()
        if not sfm:
            return None, None

        if len(self._cameraInits) == 1:
            assert self._cameraInit == self._cameraInits[0]
            # Initial CameraInit is empty, use this one
            if len(self._cameraInits[0].viewpoints) == 0:
                return self._cameraInit, sfm

        # enable updates between duplication and layout to get correct depths during layout
        with self.groupedGraphModification("SfM Augmentation", disableUpdates=False):
            # disable graph updates when adding augmentation branch
            with self.groupedGraphModification("Augmentation", disableUpdates=True):
                sfm, mvs = multiview.sfmAugmentation(self, self.lastSfmNode(), withMVS=withMVS)
            first, last = sfm[0], mvs[-1] if mvs else sfm[-1]
            # use graph current bounding box height to spawn the augmentation branch
            bb = self.layout.boundingBox()
            self.layout.autoLayout(first, last, bb[0], bb[3] + self._layout.gridSpacing)

        self.sfmAugmented.emit(first, last)
        return sfm[0], sfm[-1]

    def allImagePaths(self):
        """ Get all image paths in the reconstruction. """
        return [vp.path.value for node in self._cameraInits for vp in node.viewpoints.value]

    def allViewIds(self):
        """ Get all view Ids involved in the reconstruction. """
        return [vp.viewId.value for node in self._cameraInits for vp in node.viewpoints.value]

    @Slot(QObject, Node)
    def handleFilesDrop(self, drop, cameraInit):
        """ Handle drop events aiming to add images to the Reconstruction.
        Fetching urls from dropEvent is generally expensive in QML/JS (bug ?).
        This method allows to reduce process time by doing it on Python side.
        """
        filesByType = self.getFilesByTypeFromDrop(drop)
        if filesByType.images:
            self.importImagesAsync(filesByType.images, cameraInit)
        if filesByType.videos:
            boundingBox = self.layout.boundingBox()
            keyframeNode = self.addNewNode("KeyframeSelection", position=Position(boundingBox[0], boundingBox[1] + boundingBox[3]))
            keyframeNode.mediaPaths.value = filesByType.videos
            if len(filesByType.videos) == 1:
                newVideoNodeMessage = "New node '{}' added for the input video.".format(keyframeNode.getLabel())
            else:
                newVideoNodeMessage = "New node '{}' added for a rig of {} synchronized cameras.".format(keyframeNode.getLabel(), len(filesByType.videos))
            self.info.emit(
                Message(
                    "Video Input",
                    newVideoNodeMessage,
                    "Warning: You need to manually compute the KeyframeSelection node \n"
                    "and then reimport the created images into Meshroom for the reconstruction.\n\n"
                    "If you know the Camera Make/Model, it is highly recommended to declare them in the Node."
                ))

        if filesByType.panoramaInfo:
            if len(filesByType.panoramaInfo) > 1:
                self.error.emit(
                    Message(
                        "Multiple XML files in input",
                        "Ignore the xml Panorama files:\n\n'{}'.".format(',\n'.join(filesByType.panoramaInfo)),
                        "",
                    ))
            else:
                panoramaExternalInfoNodes = self.graph.nodesByType('PanoramaExternalInfo')
                for panoramaInfoFile in filesByType.panoramaInfo:
                    for panoramaInfoNode in panoramaExternalInfoNodes:
                        panoramaInfoNode.attribute('config').value = panoramaInfoFile
                if panoramaExternalInfoNodes:
                    self.info.emit(
                        Message(
                            "Panorama XML",
                            "XML file declared on PanoramaExternalInfo node",
                            "XML file '{}' set on node '{}'".format(','.join(filesByType.panoramaInfo), ','.join([n.getLabel() for n in panoramaExternalInfoNodes])),
                        ))
                else:
                    self.error.emit(
                        Message(
                            "No PanoramaExternalInfo Node",
                            "No PanoramaExternalInfo Node to set the Panorama file:\n'{}'.".format(','.join(filesByType.panoramaInfo)),
                            "",
                        ))

        if not filesByType.images and not filesByType.videos and not filesByType.panoramaInfo:
            if filesByType.other:
                extensions = set([os.path.splitext(url)[1] for url in filesByType.other])
                self.error.emit(
                    Message(
                        "No Recognized Input File",
                        "No recognized input file in the {} dropped files".format(len(filesByType.other)),
                        "Unknown file extensions: " + ', '.join(extensions)
                    )
                )

    @staticmethod
    def getFilesByTypeFromDrop(drop):
        """

        Args:
            drop:

        Returns:
            <images, otherFiles> List of recognized images and list of other files
        """
        urls = drop.property("urls")
        # Build the list of images paths
        filesByType = multiview.FilesByType()
        for url in urls:
            localFile = url.toLocalFile()
            if os.path.isdir(localFile):  # get folder content
                filesByType.extend(multiview.findFilesByTypeInFolder(localFile))
            else:
                filesByType.addFile(localFile)
        return filesByType

    def importImagesFromFolder(self, path, recursive=False):
        """

        Args:
            path: A path to a folder or file or a list of files/folders
            recursive: List files in folders recursively.

        """
        filesByType = multiview.findFilesByTypeInFolder(path, recursive)
        if filesByType.images:
            self.buildIntrinsics(self.cameraInit, filesByType.images)

    def importImagesAsync(self, images, cameraInit):
        """ Add the given list of images to the Reconstruction. """
        # Start the process of updating views and intrinsics
        logging.debug("Import images: " + str(images))
        self.runAsync(self.importImagesSync, args=(images, cameraInit,))

    def importImagesSync(self, images, cameraInit):
        try:
            self.buildIntrinsics(cameraInit, images)
        except Exception as e:
            self.importImagesFailed.emit(str(e))

    @Slot()
    def onImportImagesFailed(self, msg):
        self.error.emit(
            Message(
                "Failed to Import Images",
                "You probably have a corrupted image within the images that you are trying to import.",
                ""  # msg
            )
        )

    def buildIntrinsics(self, cameraInit, additionalViews, rebuild=False):
        """
        Build up-to-date intrinsics and views based on already loaded + additional images.
        Does not modify the graph, can be called outside the main thread.
        Emits intrinsicBuilt(views, intrinsics) when done.

        Args:
            cameraInit (Node): CameraInit node to build the intrinsics for
            additionalViews: list of additional views to add to the CameraInit viewpoints
            rebuild (bool): whether to rebuild already created intrinsics
        """
        views = []
        intrinsics = []

        # Duplicate 'cameraInit' outside the graph.
        #   => allows to compute intrinsics without modifying the node or the graph
        # If cameraInit is None (i.e: SfM augmentation):
        #   * create an uninitialized node
        #   * wait for the result before actually creating new nodes in the graph (see onIntrinsicsAvailable)
        inputs = cameraInit.toDict()["inputs"] if cameraInit else {}
        cameraInitCopy = Node("CameraInit", **inputs)
        if rebuild:
            # if rebuilding all intrinsics, for each Viewpoint:
            for vp in cameraInitCopy.viewpoints.value:
                vp.intrinsicId.resetValue()  # reset intrinsic assignation
                vp.metadata.resetValue()  # and metadata (to clear any previous 'SensorWidth' entries)
            # reset existing intrinsics list
            cameraInitCopy.intrinsics.resetValue()

        try:
            self.setBuildingIntrinsics(True)
            # Retrieve the list of updated viewpoints and intrinsics
            views, intrinsics = cameraInitCopy.nodeDesc.buildIntrinsics(cameraInitCopy, additionalViews)
        except Exception as e:
            logging.error("Error while building intrinsics: {}".format(str(e)))
            raise
        finally:
            # Delete the duplicate
            cameraInitCopy.deleteLater()
            self.setBuildingIntrinsics(False)

        # always emit intrinsicsBuilt signal to inform listeners
        # in other threads that computation is over
        self.intrinsicsBuilt.emit(cameraInit, views, intrinsics, rebuild)

    @Slot(Node)
    def rebuildIntrinsics(self, cameraInit):
        """
        Rebuild intrinsics of 'cameraInit' from scratch.

        Args:
            cameraInit (Node): the CameraInit node
        """
        self.runAsync(self.buildIntrinsics, args=(cameraInit, (), True))

    def onIntrinsicsAvailable(self, cameraInit, views, intrinsics, rebuild=False):
        """ Update CameraInit with given views and intrinsics. """
        augmentSfM = cameraInit is None
        commandTitle = "Add {} Images"

        # SfM augmentation
        if augmentSfM:
            # filter out views already involved in the reconstruction
            allViewIds = self.allViewIds()
            views = [view for view in views if int(view["viewId"]) not in allViewIds]
            commandTitle = "Augment Reconstruction ({} Images)"

        if rebuild:
            commandTitle = "Rebuild '{}' Intrinsics".format(cameraInit.label)

        # No additional views: early return
        if not views:
            return

        commandTitle = commandTitle.format(len(views))
        # allow updates between commands so that node depths
        # are updated after "addSfmAugmentation" (useful for auto layout)
        with self.groupedGraphModification(commandTitle, disableUpdates=False):
            if augmentSfM:
                cameraInit, self.sfm = self.addSfmAugmentation(withMVS=True)
            with self.groupedGraphModification("Set Views and Intrinsics"):
                self.setAttribute(cameraInit.viewpoints, views)
                self.setAttribute(cameraInit.intrinsics, intrinsics)
        self.cameraInit = cameraInit

    def setBuildingIntrinsics(self, value):
        if self._buildingIntrinsics == value:
            return
        self._buildingIntrinsics = value
        self.buildingIntrinsicsChanged.emit()

    cameraInitChanged = Signal()
    cameraInit = makeProperty(QObject, "_cameraInit", cameraInitChanged, resetOnDestroy=True)
    hdrCameraInitChanged = Signal()
    hdrCameraInit = makeProperty(QObject, "_hdrCameraInit", hdrCameraInitChanged, resetOnDestroy=True)
    cameraInitIndex = Property(int, getCameraInitIndex, setCameraInitIndex, notify=cameraInitChanged)
    viewpoints = Property(QObject, getViewpoints, notify=cameraInitChanged)
    cameraInits = Property(QObject, lambda self: self._cameraInits, constant=True)
    importImagesFailed = Signal(str)
    intrinsicsBuilt = Signal(QObject, list, list, bool)
    buildingIntrinsicsChanged = Signal()
    buildingIntrinsics = Property(bool, lambda self: self._buildingIntrinsics, notify=buildingIntrinsicsChanged)
    liveSfmManager = Property(QObject, lambda self: self._liveSfmManager, constant=True)

    @Slot(QObject)
    def setActiveNodeOfType(self, node):
        """ Set node as the active node of its type. """
        if node.nodeType == "StructureFromMotion":
            self.sfm = node
        elif node.nodeType == "FeatureExtraction":
            self.featureExtraction = node
        elif node.nodeType == "CameraInit":
            self.cameraInit = node
        elif node.nodeType == "PrepareDenseScene":
            self.prepareDenseScene = node
        elif node.nodeType in ("DepthMap", "DepthMapFilter"):
            self.depthMap = node

    def updateSfMResults(self):
        """
        Update internal views, poses and solved intrinsics based on the current SfM node.
        """
        if not self._sfm:
            self._views = dict()
            self._poses = dict()
            self._solvedIntrinsics = dict()
        else:
            self._views, self._poses, self._solvedIntrinsics = self._sfm.nodeDesc.getResults(self._sfm)
        self.sfmReportChanged.emit()

    def getSfm(self):
        """ Returns the current SfM node. """
        return self._sfm

    def _unsetSfm(self):
        """ Unset current SfM node. This is shortcut equivalent to _setSfm(None). """
        self._setSfm(None)

    def _setSfm(self, node):
        """ Set current SfM node to 'node' and update views and poses.
        Notes: this should not be called directly, use setSfm instead.
        See Also: setSfm
        """
        self._sfm = node
        # Update sfm results and do so each time
        # the status of the SfM node's only chunk changes
        self.updateSfMResults()
        if self._sfm:
            # when destroyed, directly use '_setSfm' to bypass
            # disconnection step in 'setSfm' (at this point, 'self._sfm' underlying object
            # has been destroyed and can't be evaluated anymore)
            self._sfm.destroyed.connect(self._unsetSfm)
            self._sfm.chunks[0].statusChanged.connect(self.updateSfMResults)
        self.sfmChanged.emit()

    def setSfm(self, node):
        """ Set the current SfM node.
        This node will be used to retrieve sparse reconstruction result like camera poses.
        """
        # disconnect from previous SfM node if any
        if self._sfm:
            self._sfm.chunks[0].statusChanged.disconnect(self.updateSfMResults)
            self._sfm.destroyed.disconnect(self._unsetSfm)
        self._setSfm(node)

        self.texturing = self.lastNodeOfType("Texturing", self._sfm, Status.SUCCESS)
        self.prepareDenseScene = self.lastNodeOfType("PrepareDenseScene", self._sfm, Status.SUCCESS)

    @Slot(QObject, result=bool)
    def isInViews(self, viewpoint):
        if not viewpoint:
            return False
        # keys are strings (faster lookup)
        return str(viewpoint.viewId.value) in self._views

    @Slot(QObject, result=bool)
    def isReconstructed(self, viewpoint):
        if not viewpoint:
            return False
        # fetch up-to-date poseId from sfm result (in case of rigs, poseId might have changed)
        view = self._views.get(str(viewpoint.poseId.value), None)  # keys are strings (faster lookup)
        return view.get('poseId', -1) in self._poses if view else False

    @Slot(QObject, result=bool)
    def hasValidIntrinsic(self, viewpoint):
        # keys are strings (faster lookup)
        allIntrinsicIds = [i.intrinsicId.value for i in self._cameraInit.intrinsics.value]
        return viewpoint.intrinsicId.value in allIntrinsicIds

    @Slot(QObject, result=QObject)
    def getIntrinsic(self, viewpoint):
        """
        Get the intrinsic attribute associated to 'viewpoint' based on its intrinsicId.

        Args:
            viewpoint (Attribute): the Viewpoint to consider.
        Returns:
            Attribute: the Viewpoint's corresponding intrinsic or None if not found.
        """
        if not viewpoint:
            return None
        return next((i for i in self._cameraInit.intrinsics.value if i.intrinsicId.value == viewpoint.intrinsicId.value)
                    , None)

    @Slot(QObject, result=bool)
    def hasMetadata(self, viewpoint):
        # Should be greater than 2 to avoid the particular case of ""
        return len(viewpoint.metadata.value) > 2

    def setSelectedViewId(self, viewId):
        if viewId == self._selectedViewId:
            return
        self._selectedViewId = viewId
        vp = None
        if self.viewpoints:
            vp = next((v for v in self.viewpoints if str(v.viewId.value) == self._selectedViewId), None)
        self.setSelectedViewpoint(vp)
        self.selectedViewIdChanged.emit()

    def setSelectedViewpoint(self, viewpointAttribute):
        if self._selectedViewpoint:
            # Reconstruction has ownership of Viewpoint object - destroy it when not needed anymore
            self._selectedViewpoint.deleteLater()
        self._selectedViewpoint = ViewpointWrapper(viewpointAttribute, self) if viewpointAttribute else None

    def reconstructedCamerasCount(self):
        """ Get the number of reconstructed cameras in the current context. """
        return len([v for v in self.getViewpoints() if self.isReconstructed(v)])

    @Slot(QObject, result="QVariant")
    def getSolvedIntrinsics(self, viewpoint):
        """ Return viewpoint's solved intrinsics if it has been reconstructed, None otherwise.

        Args:
            viewpoint: the viewpoint object to instrinsics for.
        """
        if not viewpoint:
            return None
        return self._solvedIntrinsics.get(str(viewpoint.intrinsicId.value), None)

    def getPoseRT(self, viewpoint):
        """ Get the camera pose as rotation and translation of the given viewpoint.

        Args:
            viewpoint: the viewpoint attribute to consider.
        Returns:
            R, T: the rotation and translation as lists of floats
        """
        if not viewpoint:
            return None, None
        view = self._views.get(str(viewpoint.viewId.value), None)
        if not view:
            return None, None
        pose = self._poses.get(view.get('poseId', -1), None)
        if not pose:
            return None, None

        pose = pose["transform"]
        R = [float(i) for i in pose["rotation"]]
        T = [float(i) for i in pose["center"]]

        return R, T

    selectedViewIdChanged = Signal()
    selectedViewId = Property(str, lambda self: self._selectedViewId, setSelectedViewId, notify=selectedViewIdChanged)
    selectedViewpoint = Property(ViewpointWrapper, lambda self: self._selectedViewpoint, notify=selectedViewIdChanged)

    sfmChanged = Signal()
    sfm = Property(QObject, getSfm, setSfm, notify=sfmChanged)

    featureExtractionChanged = Signal()
    featureExtraction = makeProperty(QObject, "_featureExtraction", featureExtractionChanged, resetOnDestroy=True)

    sfmReportChanged = Signal()
    # convenient property for QML binding re-evaluation when sfm report changes
    sfmReport = Property(bool, lambda self: len(self._poses) > 0, notify=sfmReportChanged)
    sfmAugmented = Signal(Node, Node)

    prepareDenseSceneChanged = Signal()
    prepareDenseScene = makeProperty(QObject, "_prepareDenseScene", notify=prepareDenseSceneChanged, resetOnDestroy=True)

    depthMapChanged = Signal()
    depthMap = makeProperty(QObject, "_depthMap", depthMapChanged, resetOnDestroy=True)

    texturingChanged = Signal()
    texturing = makeProperty(QObject, "_texturing", notify=texturingChanged)

    ldr2hdrChanged = Signal()
    ldr2hdr = makeProperty(QObject, "_ldr2hdr", notify=ldr2hdrChanged, resetOnDestroy=True)

    nbCameras = Property(int, reconstructedCamerasCount, notify=sfmReportChanged)

    # Signals to propagate high-level messages
    error = Signal(Message)
    warning = Signal(Message)
    info = Signal(Message)
