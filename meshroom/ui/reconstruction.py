import logging
import os
from threading import Thread

from PySide2.QtCore import QObject, Slot, Property, Signal

from meshroom import multiview
from meshroom.common.qt import QObjectListModel
from meshroom.core import Version
from meshroom.core.node import Node, Status
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
        imagesInFolder = multiview.findImageFiles(self._folder)
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


class Reconstruction(UIGraph):
    """
    Specialization of a UIGraph designed to manage a 3D reconstruction.
    """

    def __init__(self, graphFilepath='', parent=None):
        super(Reconstruction, self).__init__(graphFilepath, parent)

        # initialize member variables for key steps of the 3D reconstruction pipeline

        # - CameraInit
        self._cameraInit = None                            # current CameraInit node
        self._cameraInits = QObjectListModel(parent=self)  # all CameraInit nodes
        self._buildingIntrinsics = False
        self.intrinsicsBuilt.connect(self.onIntrinsicsAvailable)

        self.importImagesFailed.connect(self.onImportImagesFailed)

        # - Feature Extraction
        self._featureExtraction = None
        self.cameraInitChanged.connect(self.updateFeatureExtraction)

        # - SfM
        self._sfm = None
        self._views = None
        self._poses = None
        self._selectedViewId = None
        self._liveSfmManager = LiveSfmManager(self)

        # - Texturing
        self._texturing = None

        # react to internal graph changes to update those variables
        self.graphChanged.connect(self.onGraphChanged)

        if graphFilepath:
            self.onGraphChanged()
        else:
            self.new()

    @Slot()
    def new(self):
        """ Create a new photogrammetry pipeline. """
        self.setGraph(multiview.photogrammetry())

    def load(self, filepath):
        try:
            super(Reconstruction, self).load(filepath)
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
        self.featureExtraction = None
        self.sfm = None
        self.texturing = None
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
            return -1
        return self._cameraInits.indexOf(self._cameraInit)

    def setCameraInitIndex(self, idx):
        camInit = self._cameraInits[idx] if self._cameraInits else None
        self.cameraInit = camInit

    def updateFeatureExtraction(self):
        """ Set the current FeatureExtraction node based on the current CameraInit node. """
        self.featureExtraction = self.lastNodeOfType('FeatureExtraction', self.cameraInit) if self.cameraInit else None

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
        images, urls = self.getImageFilesFromDrop(drop)
        if not images:
            extensions = set([os.path.splitext(url)[1] for url in urls])
            self.error.emit(
                Message(
                    "No Recognized Image",
                    "No recognized image file in the {} dropped files".format(len(urls)),
                    "File extensions: " + ', '.join(extensions)
                )
            )
            return
        self.importImages(images, cameraInit)

    @staticmethod
    def getImageFilesFromDrop(drop):
        """

        Args:
            drop:

        Returns:
            <images, otherFiles> List of recognized images and list of other files
        """
        urls = drop.property("urls")
        # Build the list of images paths
        images = []
        otherFiles = []
        for url in urls:
            localFile = url.toLocalFile()
            if os.path.isdir(localFile):  # get folder content
                images.extend(multiview.findImageFiles(localFile))
            elif multiview.isImageFile(localFile):
                images.append(localFile)
            else:
                otherFiles.append(localFile)
        return images, otherFiles

    def importImages(self, images, cameraInit):
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
    cameraInitIndex = Property(int, getCameraInitIndex, setCameraInitIndex, notify=cameraInitChanged)
    viewpoints = Property(QObject, getViewpoints, notify=cameraInitChanged)
    cameraInits = Property(QObject, lambda self: self._cameraInits, constant=True)
    importImagesFailed = Signal(str)
    intrinsicsBuilt = Signal(QObject, list, list, bool)
    buildingIntrinsicsChanged = Signal()
    buildingIntrinsics = Property(bool, lambda self: self._buildingIntrinsics, notify=buildingIntrinsicsChanged)
    liveSfmManager = Property(QObject, lambda self: self._liveSfmManager, constant=True)

    def updateViewsAndPoses(self):
        """
        Update internal views and poses based on the current SfM node.
        """
        if not self._sfm:
            self._views = dict()
            self._poses = dict()
        else:
            self._views, self._poses = self._sfm.nodeDesc.getViewsAndPoses(self._sfm)
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
        # Update views and poses and do so each time
        # the status of the SfM node's only chunk changes
        self.updateViewsAndPoses()
        if self._sfm:
            # when destroyed, directly use '_setSfm' to bypass
            # disconnection step in 'setSfm' (at this point, 'self._sfm' underlying object
            # has been destroyed and can't be evaluated anymore)
            self._sfm.destroyed.connect(self._unsetSfm)
            self._sfm.chunks[0].statusChanged.connect(self.updateViewsAndPoses)
        self.sfmChanged.emit()

    def setSfm(self, node):
        """ Set the current SfM node.
        This node will be used to retrieve sparse reconstruction result like camera poses.
        """
        # disconnect from previous SfM node if any
        if self._sfm:
            self._sfm.chunks[0].statusChanged.disconnect(self.updateViewsAndPoses)
            self._sfm.destroyed.disconnect(self._unsetSfm)
        self._setSfm(node)

        self.texturing = self.lastNodeOfType("Texturing", self._sfm, Status.SUCCESS)

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
        self.selectedViewIdChanged.emit()

    def reconstructedCamerasCount(self):
        """ Get the number of reconstructed cameras in the current context. """
        return len([v for v in self.getViewpoints() if self.isReconstructed(v)])


    selectedViewIdChanged = Signal()
    selectedViewId = Property(str, lambda self: self._selectedViewId, setSelectedViewId, notify=selectedViewIdChanged)

    sfmChanged = Signal()
    sfm = Property(QObject, getSfm, setSfm, notify=sfmChanged)

    featureExtractionChanged = Signal()
    featureExtraction = makeProperty(QObject, "_featureExtraction", featureExtractionChanged, resetOnDestroy=True)

    sfmReportChanged = Signal()
    # convenient property for QML binding re-evaluation when sfm report changes
    sfmReport = Property(bool, lambda self: len(self._poses) > 0, notify=sfmReportChanged)
    sfmAugmented = Signal(Node, Node)
    texturingChanged = Signal()
    texturing = makeProperty(QObject, "_texturing", notify=texturingChanged)

    nbCameras = Property(int, reconstructedCamerasCount, notify=sfmReportChanged)

    # Signals to propagate high-level messages
    error = Signal(Message)
    warning = Signal(Message)
    info = Signal(Message)
