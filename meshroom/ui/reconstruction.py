import json
import logging
import math
import os
from collections.abc import Iterable
from multiprocessing.pool import ThreadPool
from threading import Thread

from PySide6.QtCore import QObject, Slot, Property, Signal, QUrl, QSizeF, QPoint
from PySide6.QtGui import QMatrix4x4, QMatrix3x3, QQuaternion, QVector3D, QVector2D

import meshroom.core
import meshroom.common
from meshroom import multiview
from meshroom.common.qt import QObjectListModel
from meshroom.core import Version
from meshroom.core.node import Node, CompatibilityNode, Status, Position, CompatibilityIssue
from meshroom.ui.graph import UIGraph
from meshroom.ui.utils import makeProperty
from meshroom.ui.components.filepath import FilepathHelper


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
        imagesInFolder = multiview.findFilesByTypeInFolder(self._folder).images
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
    undistortedImageParamsChanged = Signal()
    internalChanged = Signal()
    principalPointCorrectedChanged = Signal()
    uvCenterOffsetChanged = Signal()

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
        self._activeNode_PrepareDenseScene = self._reconstruction.activeNodes.get("PrepareDenseScene")
        self._activeNode_ExportAnimatedCamera = self._reconstruction.activeNodes.get("ExportAnimatedCamera")
        self._principalPointCorrected = False
        self.principalPointCorrectedChanged.connect(self.uvCenterOffsetChanged)
        self.sfmParamsChanged.connect(self.uvCenterOffsetChanged)

        # update internally cached variables
        self._updateInitialParams()
        self._updateSfMParams()
        self._updateUndistortedImageParams()

        # trigger internal members updates when reconstruction members changes
        self._reconstruction.cameraInitChanged.connect(self._updateInitialParams)
        self._reconstruction.sfmReportChanged.connect(self._updateSfMParams)
        self._activeNode_PrepareDenseScene.nodeChanged.connect(self._updateUndistortedImageParams)
        self._activeNode_ExportAnimatedCamera.nodeChanged.connect(self._updateUndistortedImageParams)

    def _updateInitialParams(self):
        """ Update internal members depending on CameraInit. """
        if not self._reconstruction.cameraInit:
            self._initialIntrinsics = None
            self._metadata = {}
        else:
            self._initialIntrinsics = self._reconstruction.getIntrinsic(self._viewpoint)
            try:
                # When the viewpoint attribute has already been deleted, metadata.value becomes a PySide property (whereas a string is expected)
                self._metadata = json.loads(self._viewpoint.metadata.value) if isinstance(self._viewpoint.metadata.value, str) and self._viewpoint.metadata.value else None
            except Exception as e:
                logging.warning("Failed to parse Viewpoint metadata: '{}', '{}'".format(str(e), str(self._viewpoint.metadata.value)))
                self._metadata = {}
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

    def _updateUndistortedImageParams(self):
        """ Update internal members depending on PrepareDenseScene or ExportAnimatedCamera. """
        # undistorted image path
        try:
            if self._activeNode_ExportAnimatedCamera.node:
                self._undistortedImagePath = FilepathHelper.resolve(FilepathHelper, self._activeNode_ExportAnimatedCamera.node.outputImages.value, self._viewpoint)
                self._principalPointCorrected = self._activeNode_ExportAnimatedCamera.node.correctPrincipalPoint.value
            elif self._activeNode_PrepareDenseScene.node:
                self._undistortedImagePath = FilepathHelper.resolve(FilepathHelper, self._activeNode_PrepareDenseScene.node.undistorted.value, self._viewpoint)
                self._principalPointCorrected = False
            else:
                self._undistortedImagePath = ''
                self._principalPointCorrected = False
        except Exception as e:
            self._undistortedImagePath = ''
            self._principalPointCorrected = False
            logging.info("Failed to retrieve undistorted images path.")
        self.undistortedImageParamsChanged.emit()
        self.principalPointCorrectedChanged.emit()

    # Get the underlying Viewpoint attribute wrapped by this Viewpoint.
    attribute = Property(QObject, lambda self: self._viewpoint, constant=True)

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
        if self.orientation in (5, 6, 7, 8):
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
        return QVector3D(self._T[0], -self._T[1], -self._T[2])

    @Property(type=QQuaternion, notify=sfmParamsChanged)
    def rotation(self):
        """ Get the camera rotation as a quaternion. """
        if self._R is None:
            return None

        rot = QMatrix3x3([
            self._R[0], -self._R[1], -self._R[2],
            -self._R[3], self._R[4], self._R[5],
            -self._R[6], self._R[7], self._R[8]]
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
            -self._R[3], self._R[4], self._R[5], -self._T[1],
            -self._R[6], self._R[7], self._R[8], -self._T[2],
            0,          0,           0,           1
        )

    @Property(type=QVector3D, notify=sfmParamsChanged)
    def upVector(self):
        """ Get camera up vector. """
        return QVector3D(0.0, 1.0, 0.0)

    @Property(type=QVector2D, notify=uvCenterOffsetChanged)
    def uvCenterOffset(self):
        """ Get UV offset corresponding to the camera principal point. """
        if not self.solvedIntrinsics or self._principalPointCorrected:
            return None
        pp = self.solvedIntrinsics["principalPoint"]
        # compute principal point offset in UV space
        offset = QVector2D(float(pp[0]) / self.imageSize.width(), float(pp[1]) / self.imageSize.height())
        return offset

    @Property(type=float, notify=sfmParamsChanged)
    def fieldOfView(self):
        """ Get camera vertical field of view in degrees. """
        if not self.solvedIntrinsics:
            return None
        focalLength = self.solvedIntrinsics["focalLength"]
        
        #We assume that if the width is less than the weight
        #It's because the image has been rotated and not
        #because the sensor has some unusual shape
        sensorWidth = self.solvedIntrinsics["sensorWidth"]
        sensorHeight = self.solvedIntrinsics["sensorHeight"]
        if self.imageSize.height() > self.imageSize.width():
            sensorWidth, sensorHeight = sensorHeight, sensorWidth

        if self.orientation in (5, 6, 7, 8):
            return 2.0 * math.atan(float(sensorWidth) / (2.0 * float(focalLength))) * 180.0 / math.pi
        else:
            return 2.0 * math.atan(float(sensorHeight) / (2.0 * float(focalLength))) * 180.0 / math.pi
        
    @Property(type=float, notify=sfmParamsChanged)
    def pixelAspectRatio(self):
        """ Get camera pixel aspect ratio. """
        if not self.solvedIntrinsics:
            return 1.0
        
        return float(self.solvedIntrinsics["pixelRatio"])

    @Property(type=QUrl, notify=undistortedImageParamsChanged)
    def undistortedImageSource(self):
        """ Get path to undistorted image source if available. """
        return QUrl.fromLocalFile(self._undistortedImagePath)


def parseSfMJsonFile(sfmJsonFile):
    """
    Parse the SfM Json file and return views, poses and intrinsics as three dicts with viewId, poseId and intrinsicId as keys.
    """
    if not os.path.exists(sfmJsonFile):
        return {}, {}, {}

    with open(sfmJsonFile) as jsonFile:
        report = json.load(jsonFile)

    views = dict()
    poses = dict()
    intrinsics = dict()

    for view in report['views']:
        views[view['viewId']] = view

    if "poses" in report:
        for pose in report['poses']:
            poses[pose['poseId']] = pose['pose']

    for intrinsic in report['intrinsics']:
        intrinsics[intrinsic['intrinsicId']] = intrinsic

    return views, poses, intrinsics


class ActiveNode(QObject):
    """
    Hold one active node for a given NodeType.
    """
    def __init__(self, nodeType, parent=None):
        super(ActiveNode, self).__init__(parent)
        self.nodeType = nodeType
        self._node = None

    nodeChanged = Signal()
    node = makeProperty(QObject, "_node", nodeChanged, resetOnDestroy=True)


class Reconstruction(UIGraph):
    """
    Specialization of a UIGraph designed to manage a 3D reconstruction.
    """
    activeNodeCategories = {
        # All nodes generating a sfm scene (3D reconstruction or panorama)
        "sfm": ["StructureFromMotion", "GlobalSfM", "PanoramaEstimation", "SfMTransform",
                "SfMAlignment"],
        # All nodes generating a sfmData file
        "sfmData": ["CameraInit", "DistortionCalibration", "StructureFromMotion", "GlobalSfM",
                    "PanoramaEstimation", "SfMTransfer", "SfMTransform", "SfMAlignment",
                    "ApplyCalibration"],
        # All nodes generating depth map files
        "allDepthMap": ["DepthMap", "DepthMapFilter"],
        # Nodes that can be used to provide features folders to the UI
        "featureProvider": ["FeatureExtraction", "FeatureMatching", "StructureFromMotion"],
        # Nodes that can be used to provide matches folders to the UI
        "matchProvider": ["FeatureMatching", "StructureFromMotion"]
    }

    def __init__(self, undoStack, taskManager, defaultPipeline="", parent=None):
        super(Reconstruction, self).__init__(undoStack, taskManager, parent)

        # initialize member variables for key steps of the 3D reconstruction pipeline
        self._active = False
        self._activeNodes = meshroom.common.DictModel(keyAttrName="nodeType")
        self.initActiveNodes()

        # - CameraInit
        self._cameraInit = None                            # current CameraInit node
        self._cameraInits = QObjectListModel(parent=self)  # all CameraInit nodes
        self._buildingIntrinsics = False
        self.intrinsicsBuilt.connect(self.onIntrinsicsAvailable)

        self.cameraInitChanged.connect(self.onCameraInitChanged)

        self._tempCameraInit = None

        self.importImagesFailed.connect(self.onImportImagesFailed)

        # - SfM
        self._sfm = None
        self._views = None
        self._poses = None
        self._solvedIntrinsics = None
        self._selectedViewId = None
        self._selectedViewpoint = None
        self._pickedViewId = None
        self._liveSfmManager = LiveSfmManager(self)

        self._currentViewPath = ""

        self._workerThreads = ThreadPool(processes=1)

        # react to internal graph changes to update those variables
        self.graphChanged.connect(self.onGraphChanged)

        self.setDefaultPipeline(defaultPipeline)

    def __del__(self):
        self._workerThreads.terminate()
        self._workerThreads.join()

    def setActive(self, active):
        self._active = active

    @Slot()
    def clear(self):
        self.clearActiveNodes()
        super(Reconstruction, self).clear()
        self.setActive(False)

    def setDefaultPipeline(self, defaultPipeline):
        self._defaultPipeline = defaultPipeline

    def setSubmitLabel(self, submitLabel):
        self.submitLabel = submitLabel

    def initActiveNodes(self):
        # Create all possible entries
        for category, _ in self.activeNodeCategories.items():
            self._activeNodes.add(ActiveNode(category, parent=self))
        for nodeType, _ in meshroom.core.nodesDesc.items():
            self._activeNodes.add(ActiveNode(nodeType, parent=self))

    def clearActiveNodes(self):
        for key in self._activeNodes.keys():
            self._activeNodes.get(key).node = None

    def onCameraInitChanged(self):
        if self._cameraInit is None:
            return
        # Update active nodes when CameraInit changes
        nodes = self._graph.dfsOnDiscover(startNodes=[self._cameraInit], reverse=True)[0]
        self.setActiveNodes(nodes)

    @Slot()
    @Slot(str)
    def new(self, pipeline=None):
        """ Create a new pipeline. """
        p = pipeline if pipeline != None else self._defaultPipeline
        # Lower the input and the dictionary keys to make sure that all input types can be found:
        # - correct pipeline name but the case does not match (e.g. panoramaHDR instead of panoramaHdr)
        # - lowercase pipeline name given through the "New Pipeline" menu
        loweredPipelineTemplates = dict((k.lower(), v) for k, v in meshroom.core.pipelineTemplates.items())
        if p.lower() in loweredPipelineTemplates:
            self.load(loweredPipelineTemplates[p.lower()], setupProjectFile=False)
        else:
            # use the user-provided default project file
            self.load(p, setupProjectFile=False)

    @Slot(str, result=bool)
    def load(self, filepath, setupProjectFile=True, publishOutputs=False):
        logging.info(f"Load project file: '{filepath}'")
        try:
            status = super(Reconstruction, self).loadGraph(filepath, setupProjectFile, publishOutputs)
            # warn about pre-release projects being automatically upgraded
            if Version(self._graph.fileReleaseVersion).major == "0":
                self.warning.emit(Message(
                    "Automatic project upgrade",
                    "This project was created with an older version of Meshroom and has been automatically upgraded.\n"
                    "Data might have been lost in the process.",
                    "Open it with the corresponding version of Meshroom to recover your data."
                ))
            self.setActive(True)
            return status
        except FileNotFoundError as e:
            self.error.emit(
                Message(
                    "No Such File",
                    "Error While Loading '{}': No Such File.".format(os.path.basename(filepath)),
                    ""
                )
            )
            logging.error("Error while loading '{}': No Such File.".format(filepath))
            return False
        except Exception as e:
            import traceback
            trace = traceback.format_exc()
            self.error.emit(
                Message(
                    "Error While Loading Project File",
                    "An unexpected error has occurred while loading file: '{}'".format(os.path.basename(filepath)),
                    trace
                )
            )
            logging.error("Error while loading '{}'.".format(filepath))
            logging.error(trace)
            return False

    @Slot(QUrl, result=bool)
    @Slot(QUrl, bool, bool, result=bool)
    def loadUrl(self, url, setupProjectFile=True, publishOutputs=False):
        if isinstance(url, (QUrl)):
            # depending how the QUrl has been initialized,
            # toLocalFile() may return the local path or an empty string
            localFile = url.toLocalFile()
            if not localFile:
                localFile = url.toString()
        else:
            localFile = url
        return self.load(localFile, setupProjectFile, publishOutputs)

    def onGraphChanged(self):
        """ React to the change of the internal graph. """
        self._liveSfmManager.reset()
        self.selectedViewId = "-1"
        self.tempCameraInit = None
        self.updateCameraInits()
        self.resetActiveNodePerCategory()
        self.sfm = self.lastSfmNode()
        if not self._graph:
            return

        # TODO: listen specifically for cameraInit creation/deletion
        self._graph.nodes.countChanged.connect(self.updateCameraInits)

    @Slot(QObject)
    def getViewpoints(self):
        """ Return the Viewpoints model. """
        # TODO: handle multiple Viewpoints models
        if self.tempCameraInit:
            return self.tempCameraInit.viewpoints.value
        elif self._cameraInit:
            return self._cameraInit.viewpoints.value
        else:
            return QObjectListModel(parent=self)

    def updateCameraInits(self):
        cameraInits = self._graph.nodesOfType("CameraInit", sortedByIndex=True)
        if set(self._cameraInits.objectList()) == set(cameraInits):
            return
        self._cameraInits.setObjectList(cameraInits)

        if self.cameraInit is None or self.cameraInit not in cameraInits:
            self.cameraInit = cameraInits[0] if cameraInits else None

        # Manually emit the signal to ensure the active CameraInit index is always up-to-date in the UI
        self.cameraInitChanged.emit()

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
        # Update the active viewpoint accordingly
        if self.viewpoints:
            self.setSelectedViewId(self.viewpoints[0].viewId.value)

    def setCameraInitNode(self, node):
        if self._cameraInit == node:
            return
        self.setCameraInitIndex(self._cameraInits.indexOf(node))

    @Slot()
    def clearTempCameraInit(self):
        self.tempCameraInit = None

    @Slot(QObject, str)
    def setupTempCameraInit(self, node, attrName):
        if not node or not attrName:
            self.tempCameraInit = None
            return
        sfmFile = node.attribute(attrName).value
        if not sfmFile or not os.path.isfile(sfmFile):
            self.tempCameraInit = None
            return
        nodeDesc = meshroom.core.nodesDesc["CameraInit"]()
        views, intrinsics = nodeDesc.readSfMData(sfmFile)
        tmpCameraInit = Node("CameraInit", viewpoints=views, intrinsics=intrinsics)
        tmpCameraInit.locked = True
        self.tempCameraInit = tmpCameraInit
        rootNode = self.graph.dfsOnFinish([node])[0][0]
        if rootNode.nodeType == "CameraInit":
            self.setCameraInitNode(rootNode)

    @Slot(QObject, result=QVector3D)
    def getAutoFisheyeCircle(self, panoramaInit):
        if not panoramaInit or not panoramaInit.isComputed:
            return QVector3D(0.0, 0.0, 0.0)
        if not panoramaInit.attribute("estimateFisheyeCircle").value:
            return QVector3D(0.0, 0.0, 0.0)

        sfmFile = panoramaInit.attribute('outSfMData').value
        if not os.path.exists(sfmFile):
            return QVector3D(0.0, 0.0, 0.0)
        # skip decoding errors to avoid potential exceptions due to non utf-8 characters in images metadata
        with open(sfmFile, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)

        intrinsics = data.get('intrinsics', [])
        if len(intrinsics) == 0:
            return QVector3D(0.0, 0.0, 0.0)
        intrinsic = intrinsics[0]

        res = QVector3D(float(intrinsic.get("fisheyeCircleCenterX", 0.0)) - float(intrinsic.get("width", 0.0)) * 0.5,
                        float(intrinsic.get("fisheyeCircleCenterY", 0.0)) - float(intrinsic.get("height", 0.0)) * 0.5,
                        float(intrinsic.get("fisheyeCircleRadius", 0.0)))
        return res

    def lastSfmNode(self):
        """ Retrieve the last SfM node from the initial CameraInit node. """
        return self.lastNodeOfType(self.activeNodeCategories['sfm'], self._cameraInit, Status.SUCCESS)

    def lastNodeOfType(self, nodeTypes, startNode, preferredStatus=None):
        """
        Returns the last node of the given type starting from 'startNode'.
        If 'preferredStatus' is specified, the last node with this status will be considered in priority.

        Args:
            nodeTypes (str list): the node types
            startNode (Node): the node to start from
            preferredStatus (Status): (optional) the node status to prioritize

        Returns:
            Node: the node matching the input parameters or None
        """
        if not startNode:
            return None
        nodes = self._graph.dfsOnDiscover(startNodes=[startNode], filterTypes=nodeTypes, reverse=True)[0]
        if not nodes:
            return None
        # order the nodes according to their depth in the graph, then according to their name
        nodes.sort(key=lambda n: (n.depth, n.name))
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

    @Slot(result="QVariantList")
    def allImagePaths(self):
        """ Get all image paths in the reconstruction. """
        return [vp.path.value for node in self._cameraInits for vp in node.viewpoints.value]

    def allViewIds(self):
        """ Get all view Ids involved in the reconstruction. """
        return [vp.viewId.value for node in self._cameraInits for vp in node.viewpoints.value]

    @Slot("QVariantMap", result=bool)
    @Slot("QVariantMap", Node, result=bool)
    @Slot("QVariantMap", Node, "QPoint", result=bool)
    def handleFilesUrl(self, filesByType, cameraInit=None, position=None):
        """ Handle drop events aiming to add images to the Reconstruction.
        This method allows to reduce process time by doing it on Python side.

        Args:
            {images, videos, panoramaInfo, meshroomScenes, otherFiles}: Map containing the lists of paths for recognized images, videos, Meshroom scenes and other files.
            Node: cameraInit node used to add new images to it
            QPoint: position to locate the node (usually the mouse position)
        """
        if filesByType["images"]:
            if cameraInit is None:
                if not self._cameraInits:
                    if isinstance(position, QPoint):
                        p = Position(position.x(), position.y())
                    else:
                        p = position
                    cameraInit = self.addNewNode("CameraInit", position=p)
                else:
                    boundingBox = self.layout.boundingBox()
                    if not position:
                        p = Position(boundingBox[0], boundingBox[1] + boundingBox[3])
                    elif isinstance(position, QPoint):
                        p = Position(position.x(), position.y())
                    else:
                        p = position
                    cameraInit = self.addNewNode("CameraInit", position=p)
            self._workerThreads.apply_async(func=self.importImagesSync, args=(filesByType["images"], cameraInit,))
        if filesByType["videos"]:
            if self.nodes:
                boundingBox = self.layout.boundingBox()
                p = Position(boundingBox[0], boundingBox[1] + boundingBox[3])
            else:
                p = position
            keyframeNode = self.addNewNode("KeyframeSelection", position=p)
            keyframeNode.inputPaths.value = filesByType["videos"]
            if len(filesByType["videos"]) == 1:
                newVideoNodeMessage = "New node '{}' added for the input video.".format(keyframeNode.getLabel())
            else:
                newVideoNodeMessage = "New node '{}' added for a rig of {} synchronized cameras.".format(keyframeNode.getLabel(), len(filesByType["videos"]))
            self.info.emit(
                Message(
                    "Video Input",
                    newVideoNodeMessage,
                    "Warning: You need to manually compute the KeyframeSelection node \n"
                    "and then reimport the created images into Meshroom for the reconstruction.\n\n"
                    "If you know the Camera Make/Model, it is highly recommended to declare them in the Node."
                ))

        if filesByType["panoramaInfo"]:
            if len(filesByType["panoramaInfo"]) > 1:
                self.error.emit(
                    Message(
                        "Multiple XML files in input",
                        "Ignore the xml Panorama files:\n\n'{}'.".format(',\n'.join(filesByType["panoramaInfo"])),
                        "",
                    ))
            else:
                panoramaInitNodes = self.graph.nodesOfType('PanoramaInit')
                for panoramaInfoFile in filesByType["panoramaInfo"]:
                    for panoramaInitNode in panoramaInitNodes:
                        panoramaInitNode.attribute('initializeCameras').value = 'File'
                        panoramaInitNode.attribute('config').value = panoramaInfoFile
                if panoramaInitNodes:
                    self.info.emit(
                        Message(
                            "Panorama XML",
                            "XML file declared on PanoramaInit node",
                            "XML file '{}' set on node '{}'".format(','.join(filesByType["panoramaInfo"]), ','.join([n.getLabel() for n in panoramaInitNodes])),
                        ))
                else:
                    self.error.emit(
                        Message(
                            "No PanoramaInit Node",
                            "No PanoramaInit Node to set the Panorama file:\n'{}'.".format(','.join(filesByType["panoramaInfo"])),
                            "",
                        ))

        if filesByType["meshroomScenes"]:
            if len(filesByType["meshroomScenes"]) > 1:
                self.error.emit(
                    Message(
                    "Too Many Meshroom Scenes",
                    "A single Meshroom scene (.mg file) can be imported at once."
                    )
                )
            else:
                return self.loadUrl(filesByType["meshroomScenes"][0])



        if not filesByType["images"] and not filesByType["videos"] and not filesByType["panoramaInfo"] and not filesByType["meshroomScenes"]:
            if filesByType["other"]:
                extensions = set([os.path.splitext(url)[1] for url in filesByType["other"]])
                self.error.emit(
                    Message(
                        "No Recognized Input File",
                        "No recognized input file in the {} dropped files".format(len(filesByType["other"])),
                        "Unknown file extensions: " + ', '.join(extensions)
                    )
                )
        
        # As the boolean is introduced to check if the project is loaded or not, the return value is added to the function.
        # The default value is False, which means the project is not loaded.
        return False

    @Slot("QList<QUrl>", result="QVariantMap")
    def getFilesByTypeFromDrop(self, urls):
        """

        Args:
            urls: list of filepaths

        Returns:
            {images, videos, panoramaInfo, meshroomScenes, otherFiles}: Map containing the lists of paths for recognized images, videos, Meshroom scenes and other files.
        """
        # Build the list of images paths
        filesByType = multiview.FilesByType()
        for url in urls:
            localFile = url.toLocalFile()
            if os.path.isdir(localFile):  # get folder content
                filesByType.extend(multiview.findFilesByTypeInFolder(localFile))
            else:
                filesByType.addFile(localFile)
        return {"images": filesByType.images, "videos": filesByType.videos, "panoramaInfo": filesByType.panoramaInfo, "meshroomScenes": filesByType.meshroomScenes, "other": filesByType.other}

    def importImagesFromFolder(self, path, recursive=False):
        """

        Args:
            path: A path to a folder or file or a list of files/folders
            recursive: List files in folders recursively.

        """
        logging.debug("importImagesFromFolder: " + str(path))
        filesByType = multiview.findFilesByTypeInFolder(path, recursive)
        if not self.cameraInit:
            # Create a CameraInit node if none exists
            self.cameraInit = self.addNewNode("CameraInit")
        if filesByType.images:
            self._workerThreads.apply_async(func=self.importImagesSync, args=(filesByType.images, self.cameraInit,))

    @Slot("QVariant")
    def importImagesUrls(self, imagePaths, recursive=False):
        paths = []
        for imagePath in imagePaths:
            if isinstance(imagePath, (QUrl)):
                p = imagePath.toLocalFile()
                if not p:
                    p = imagePath.toString()
            else:
                p = imagePath
            paths.append(p)
        self.importImagesFromFolder(paths)

    def importImagesSync(self, images, cameraInit):
        """ Add the given list of images to the Reconstruction. """
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
                vp.intrinsicId.resetToDefaultValue()  # reset intrinsic assignation
                vp.metadata.resetToDefaultValue()  # and metadata (to clear any previous 'SensorWidth' entries)
            # reset existing intrinsics list
            cameraInitCopy.intrinsics.resetToDefaultValue()

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
        self._workerThreads.apply_async(func=self.buildIntrinsics, args=(cameraInit, (), True,))

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

    activeNodes = makeProperty(QObject, "_activeNodes", resetOnDestroy=True)
    cameraInitChanged = Signal()
    cameraInit = makeProperty(QObject, "_cameraInit", cameraInitChanged, resetOnDestroy=True)
    tempCameraInitChanged = Signal()
    tempCameraInit = makeProperty(QObject, "_tempCameraInit", tempCameraInitChanged, resetOnDestroy=True)
    cameraInitIndex = Property(int, getCameraInitIndex, setCameraInitIndex, notify=cameraInitChanged)
    viewpoints = Property(QObject, getViewpoints, notify=cameraInitChanged)
    cameraInits = Property(QObject, lambda self: self._cameraInits, constant=True)
    importImagesFailed = Signal(str)
    intrinsicsBuilt = Signal(QObject, list, list, bool)
    buildingIntrinsicsChanged = Signal()
    buildingIntrinsics = Property(bool, lambda self: self._buildingIntrinsics, notify=buildingIntrinsicsChanged)
    liveSfmManager = Property(QObject, lambda self: self._liveSfmManager, constant=True)

    @Slot(QObject)
    def setActiveNode(self, node, categories=True, inputs=True):
        """ Set node as the active node of its type and of its categories.
        Also upgrade related input nodes.
        """
        if categories:
            for category, nodeTypes in self.activeNodeCategories.items():
                if node.nodeType in nodeTypes:
                    self.activeNodes.getr(category).node = node

                    if category == "sfm":
                        self.setSfm(node)

        if node.nodeType == "CameraInit":
            # if the active node is a CameraInit node, update the camera init index
            self.setCameraInitNode(node)
        elif inputs:
            # Update the input node to ensure that it is part of the dependency of the new active node.
            # Retrieve all nodes that are input nodes of the new active node
            inputNodes = node.getInputNodes(recursive=True, dependenciesOnly=True)
            inputCameraInitNodes = [n for n in inputNodes if n.nodeType == "CameraInit"]
            # if the current camera init node is not the same as the camera init node of the active node
            if inputCameraInitNodes and self.cameraInit not in inputCameraInitNodes:
                # set the camera init node of the active node as the current camera init node
                # if multiple camera init, select one arbitrarily (the one with more viewpoints)
                inputCameraInitNodes.sort(key=lambda n: len(n.viewpoints.value), reverse=True)
                cameraInitNode = inputCameraInitNodes[0]
                self.setCameraInitNode(cameraInitNode)

        # Set the new active node (if it is not an unknown type)
        unknownType = isinstance(node, CompatibilityNode) and node.issue == CompatibilityIssue.UnknownNodeType
        if not unknownType:
            self.activeNodes.get(node.nodeType).node = node

    @Slot(QObject)
    def setActiveNodes(self, nodes):
        """ Set node as the active node of its type. """
        for node in nodes:
            if node is None:
                continue
            self.setActiveNode(node, categories=False, inputs=False)

    def resetActiveNodePerCategory(self):
        # Setup the active node per category only once, on the last one
        nodesByCategory = {}
        for category, nodeTypes in self.activeNodeCategories.items():
            node = self.lastNodeOfType(nodeTypes, self._cameraInit, Status.SUCCESS)
            self.activeNodes.get(category).node = node

    def updateSfMResults(self):
        """
        Update internal views, poses and solved intrinsics based on the current SfM node.
        """
        if not self._sfm or ('outputViewsAndPoses' not in self._sfm.getAttributes().keys()):
            self._views = dict()
            self._poses = dict()
            self._solvedIntrinsics = dict()
        else:
            self._views, self._poses, self._solvedIntrinsics = parseSfMJsonFile(self._sfm.outputViewsAndPoses.value)
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
        if not self._views:
            return False
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
        self.setPickedViewId(viewId)
        vp = None
        if self.viewpoints:
            vp = next((v for v in self.viewpoints if str(v.viewId.value) == self._selectedViewId), None)
        self._setSelectedViewpoint(vp)
        self.selectedViewIdChanged.emit()

    def _setSelectedViewpoint(self, viewpointAttribute):
        if self._selectedViewpoint:
            # Reconstruction has ownership of Viewpoint object - destroy it when not needed anymore
            self._selectedViewpoint.deleteLater()
        self._selectedViewpoint = ViewpointWrapper(viewpointAttribute, self) if viewpointAttribute else None
        self.selectedViewpointChanged.emit()

    def setPickedViewId(self, viewId):
        if viewId == self._pickedViewId:
            return
        self._pickedViewId = viewId
        self.pickedViewIdChanged.emit()

    @Slot(str)
    def updateSelectedViewpoint(self, viewId):
        """ Update the currently set viewpoint if the provided view ID corresponds to one. """
        vp = None
        if self.viewpoints:
            vp = next((v for v in self.viewpoints if str(v.viewId.value) == viewId), None)
        self._setSelectedViewpoint(vp)

    def reconstructedCamerasCount(self):
        """ Get the number of reconstructed cameras in the current context. """
        viewpoints = self.getViewpoints()
        # Check that the object is iterable to avoid error with undefined Qt Property
        if not isinstance(viewpoints, Iterable):
            return 0
        return len([v for v in viewpoints if self.isReconstructed(v)])

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

    def setCurrentViewPath(self, path):
        if self._currentViewPath == path:
            return
        self._currentViewPath = path
        self.currentViewPathChanged.emit()

    selectedViewIdChanged = Signal()
    selectedViewId = Property(str, lambda self: self._selectedViewId, setSelectedViewId, notify=selectedViewIdChanged)
    selectedViewpointChanged = Signal()
    selectedViewpoint = Property(ViewpointWrapper, lambda self: self._selectedViewpoint, notify=selectedViewpointChanged)
    pickedViewIdChanged = Signal()
    pickedViewId = Property(str, lambda self: self._pickedViewId, setPickedViewId, notify=pickedViewIdChanged)

    sfmChanged = Signal()
    sfm = Property(QObject, getSfm, setSfm, notify=sfmChanged)

    sfmReportChanged = Signal()
    # convenient property for QML binding re-evaluation when sfm report changes
    sfmReport = Property(bool, lambda self: len(self._poses) > 0, notify=sfmReportChanged)
    sfmAugmented = Signal(Node, Node)

    nbCameras = Property(int, reconstructedCamerasCount, notify=sfmReportChanged)

    # Provides the path of the image that is currently displayed
    # This is an alternative to "selectedViewpoint.attribute.path.value" for images that are displayed
    # but not part of the list of viewpoints of a CameraInit node (i.e. "sequence" node outputs)
    currentViewPathChanged = Signal()
    currentViewPath = Property(str, lambda self: self._currentViewPath, setCurrentViewPath, notify=currentViewPathChanged)

    # Whether the Reconstruction object has been set ("new" has been called) or not ("new" has never
    # been called or "clear" has been called)
    activeChanged = Signal()
    active = Property(bool, lambda self: self._active, setActive, notify=activeChanged)

    # Signals to propagate high-level messages
    error = Signal(Message)
    warning = Signal(Message)
    info = Signal(Message)