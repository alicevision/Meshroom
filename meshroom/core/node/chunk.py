#!/usr/bin/env python

import atexit
import json
import logging
import os
import uuid
from typing import TYPE_CHECKING, Dict

import meshroom
from meshroom.common import Signal, Variant, Property, BaseObject
from meshroom.core import desc, stats, MrNodeType
from meshroom.core.node.status import ChunkIndex, ChunkStatusData, ExecMode, Status, getWritingFilepath, renameWritingToFinalPath
from meshroom.core.node.logManager import LogManager

if TYPE_CHECKING:
    from meshroom.core.node.node import Node


runningProcesses: Dict[str, "NodeChunk"] = {}


@atexit.register
def clearProcessesStatus():
    for k, v in runningProcesses.items():
        v.upgradeStatusTo(Status.KILLED)


class NodeChunk(BaseObject):
    def __init__(self, node, range, placeholder=False, parent=None):
        super().__init__(parent)
        self.__uid = uuid.uuid1()
        self.node: "Node" = node
        self.range: desc.Range = range
        self.placeholder = placeholder
        self._logManager = None
        self._status: ChunkStatusData = ChunkStatusData(nodeName=node.name, mrNodeType=node.getMrNodeType())
        self.statistics: stats.Statistics = stats.Statistics()
        self.statusFileLastModTime = -1
        self.subprocess = None
        # Notify update in filepaths when node's internal folder changes
        self.node.internalFolderChanged.connect(self.nodeFolderChanged)

    def __repr__(self):
        return f"<NodeChunk {self.name} ({self.getStatusName()}) {self.__uid}>"

    def __del__(self):
        logging.debug(f"NodeChunk: delete chunk {self}")

    @property
    def index(self):
        return self.range.iteration

    @property
    def isPreprocess(self):
        return self.index == ChunkIndex.PREPROCESS

    @property
    def isPostprocess(self):
        return self.index == ChunkIndex.POSTPROCESS

    def getChunkIndexName(self):
        if self.isPreprocess:
            return "preprocess"
        if self.isPostprocess:
            return "postprocess"
        if self.range.blockSize:
            return str(self.index)
        if self.placeholder:
            return "placeholder"
        return str(self.range.iteration)

    @property
    def name(self):
        return f"{self.node.name} ({self.getChunkIndexName()})"

    @property
    def logManager(self):
        if self._logManager is None:
            logger = logging.getLogger(self.node.getName())
            self._logManager = LogManager(logger, self.getLogFile())
        return self._logManager

    def getStatusName(self):
        return self._status.status.name

    @property
    def logger(self):
        return self.logManager.logger

    def getExecModeName(self):
        return self._status.execMode.name

    def shouldMonitorChanges(self):
        """
        Check whether we should monitor changes in minimal mode.
        Only chunks that are run externally or local_isolated should be monitored,
        when run locally, status changes are already notified.
        Chunks with an ERROR status may be re-submitted externally and should thus still be
        monitored.
        """
        return (self.isExtern() and self._status.status in (Status.SUBMITTED, Status.RUNNING, Status.ERROR)) or \
               (self.node.getMrNodeType() == MrNodeType.NODE and self._status.status in (Status.SUBMITTED, Status.RUNNING))

    def updateStatusFromCache(self):
        """
        Update chunk status based on status file content/existence.
        """
        # TODO : If this is a placeholder chunk
        # Then we should not do anything here

        statusFile = self.getStatusFile()
        oldStatus = self._status.status
        # No status file => reset status to Status.None
        if not os.path.exists(statusFile):
            self.statusFileLastModTime = -1
            self._status.reset()
            self._status.setNode(self.node)
        else:
            try:
                with open(statusFile) as jsonFile:
                    statusData = json.load(jsonFile)
                # logging.debug(f"updateStatusFromCache({self.node.name}): From status {self._status.status} to {statusData['status']}")
                self._status.fromDict(statusData)
                self.statusFileLastModTime = os.path.getmtime(statusFile)
            except Exception as exc:
                logging.debug(f"updateStatusFromCache({self.node.name}): Error while loading status file {statusFile}: {exc}")
                self.statusFileLastModTime = -1
                self._status.reset()
                self._status.setNode(self.node)

        if oldStatus != self._status.status:
            self.statusChanged.emit()

    def _getFile(self, fileType: str):
        """
        Return the path for the requested type of file.
        It is expected to be prefixed by the chunk number, but for compatibility purposes, it may not be.
        """
        chunkName = self.getChunkIndexName()
        # Retro-compatibility: ensure we do not lose files computed when single chunks were not prefixed
        # If both the prefixed and not prefixed files exist, the prefixed one should be returned
        if os.path.exists(os.path.join(self.node.internalFolder, fileType)):
            if not os.path.exists(os.path.join(self.node.internalFolder, chunkName + "." + fileType)):
                return os.path.join(self.node.internalFolder, fileType)
        return os.path.join(self.node.internalFolder, chunkName + "." + fileType)

    def getStatusFile(self):
        return self._getFile("status")

    def getStatisticsFile(self):
        return self._getFile("statistics")

    def getLogFile(self):
        return self._getFile("log")

    def saveStatusFile(self):
        """
        Write node status on disk.
        """
        data = self._status.toDict()
        statusFilepath = self.getStatusFile()
        folder = os.path.dirname(statusFilepath)
        os.makedirs(folder, exist_ok=True)

        statusFilepathWriting = getWritingFilepath(statusFilepath)
        with open(statusFilepathWriting, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)
        renameWritingToFinalPath(statusFilepathWriting, statusFilepath)

    def upgradeStatusFile(self):
        """
        Upgrade node status file based on the current status.
        """
        self.saveStatusFile()
        # We want to make sure the nodeStatus is up to date too
        self.node.upgradeStatusFile()
        self.statusChanged.emit()

    def upgradeStatusTo(self, newStatus, execMode=None):
        if newStatus.value < self._status.status.value:
            logging.warning(f"Downgrade status on node '{self.name}' from {self._status.status} to {newStatus}")

        if execMode is not None:
            self._status.execMode = execMode
        self._status.status = newStatus
        self.upgradeStatusFile()

    def updateStatisticsFromCache(self):
        """
        """
        oldTimes = self.statistics.times
        statisticsFile = self.getStatisticsFile()
        if not os.path.exists(statisticsFile):
            return
        with open(statisticsFile) as jsonFile:
            statisticsData = json.load(jsonFile)
        self.statistics.fromDict(statisticsData)
        if oldTimes != self.statistics.times:
            self.statisticsChanged.emit()

    def saveStatistics(self):
        data = self.statistics.toDict()
        statisticsFilepath = self.getStatisticsFile()
        folder = os.path.dirname(statisticsFilepath)
        os.makedirs(folder, exist_ok=True)
        statisticsFilepathWriting = getWritingFilepath(statisticsFilepath)
        with open(statisticsFilepathWriting, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)
        renameWritingToFinalPath(statisticsFilepathWriting, statisticsFilepath)

    def isAlreadySubmitted(self):
        return self._status.status in (Status.SUBMITTED, Status.RUNNING)

    def isAlreadySubmittedOrFinished(self):
        return self._status.status in (Status.SUBMITTED, Status.RUNNING, Status.SUCCESS)

    def isFinishedOrRunning(self):
        return self._status.status in (Status.SUCCESS, Status.RUNNING)

    def isRunning(self):
        return self._status.status == Status.RUNNING

    def isStopped(self):
        return self._status.status == Status.STOPPED

    def isFinished(self):
        return self._status.status == Status.SUCCESS

    def process(self, forceCompute=False, inCurrentEnv=False):
        if not forceCompute and self._status.status == Status.SUCCESS:
            logging.info(f"Node chunk already computed: {self.name}")
            return

        # Start the process environment for nodes running in isolation.
        # This only happens once, when the node has the SUBMITTED status.
        # The sub-process will go through this method again, but the node status will
        # have been set to RUNNING.
        if not inCurrentEnv and self.node.getMrNodeType() == MrNodeType.NODE:
            self._processInIsolatedEnvironment()
            return

        runningProcesses[self.name] = self
        self._status.setNode(self.node)
        self._status.initStartCompute()
        self.upgradeStatusFile()
        executionStatus = None
        self.statThread = stats.StatisticsThread(self)
        self.statThread.start()

        try:
            if self.isPreprocess:
                self.node.nodeDesc.preprocess(self.node)
            elif self.isPostprocess:
                self.node.nodeDesc.postprocess(self.node)
            else:
                self.node.nodeDesc.processChunk(self)
            # NOTE: this assumes saving the output attributes for each chunk
            self.node.saveOutputAttr()
            executionStatus = Status.SUCCESS
        except Exception:
            self.updateStatusFromCache()  # check if the status has been updated by another process
            if self._status.status != Status.STOPPED:
                executionStatus = Status.ERROR
            raise
        except (KeyboardInterrupt, SystemError, GeneratorExit):
            executionStatus = Status.STOPPED
            raise
        finally:
            self._status.setNode(self.node)
            self._status.initEndCompute()
            self.upgradeStatusFile()

            if executionStatus:
                self.upgradeStatusTo(executionStatus)
            logging.info(f"[Process chunk] elapsed time: {self._status.elapsedTimeStr}")
            # Ask and wait for the stats thread to stop
            self.statThread.stopRequest()
            self.statThread.join()
            self.statistics = stats.Statistics()
            del runningProcesses[self.name]

    def _processInIsolatedEnvironment(self):
        """
        Process this node chunk in the isolated environment defined in the environment
        configuration.
        """
        try:
            self._status.setNode(self.node)
            self._status.initIsolatedCompute()
            self.upgradeStatusFile()

            self.node.nodeDesc.processChunkInEnvironment(self)
        except Exception as err:
            # status should be already updated by meshroom_compute
            self.updateStatusFromCache()
            if self._status.status not in (Status.ERROR, Status.STOPPED, Status.KILLED):
                # If meshroom_compute has crashed or been killed, the status may have not been
                # set to ERROR.
                # In this particular case, we enforce it from here.
                self.upgradeStatusTo(Status.ERROR)
            raise err
        # Update the chunk status.
        self.updateStatusFromCache()
        # Update the output attributes, as any chunk may have modified them.
        self.node.updateOutputAttr()

    def stopProcess(self):
        # Ensure that we are up-to-date
        self.updateStatusFromCache()

        if self._status.status != Status.RUNNING:
            # When we stop the process of a node with multiple chunks, the Node function will call
            # the stop function of each chunk.
            # So, the chunk status could be SUBMITTED, RUNNING or ERROR.

            if self._status.status is Status.SUBMITTED:
                self.upgradeStatusTo(Status.NONE)
            elif self._status.status in (Status.ERROR, Status.STOPPED, Status.KILLED,
                                         Status.SUCCESS, Status.NONE):
                # Nothing to do, the computation is already stopped.
                pass
            else:
                logging.debug(f"Cannot stop process: node is not running (status is: {self._status.status}).")
            return

        self.node.nodeDesc.stopProcess(self)

        # Update the status to get latest information before changing it
        self.updateStatusFromCache()
        self.upgradeStatusTo(Status.STOPPED)

    def isExtern(self):
        """
        The computation is managed externally by another instance of Meshroom.
        In the ambiguous case of an isolated environment, it is considered as local as we can stop
        it (if it is run from the current Meshroom instance).
        """
        if self._status.execMode == ExecMode.EXTERN:
            return True
        elif self._status.execMode == ExecMode.LOCAL:
            if self._status.status in (Status.SUBMITTED, Status.RUNNING):
                return meshroom.core.sessionUid not in (self.node._nodeStatus.submitterSessionUid, self._status.computeSessionUid)
            return False
        return False

    statusChanged = Signal()
    status = Property(Variant, lambda self: self._status, notify=statusChanged)
    statusName = Property(str, getStatusName, notify=statusChanged)
    execModeName = Property(str, getExecModeName, notify=statusChanged)
    statisticsChanged = Signal()
    chunkIndexName = Property(str, getChunkIndexName, constant=True)
    chunkIndex = Property(int, lambda self: self.index, constant=True)
    chunkNode = Property(Variant, lambda self: self.node, constant=True)

    nodeFolderChanged = Signal()
    statusFile = Property(str, getStatusFile, notify=nodeFolderChanged)
    logFile = Property(str, getLogFile, notify=nodeFolderChanged)
    statisticsFile = Property(str, getStatisticsFile, notify=nodeFolderChanged)

    nodeName = Property(str, lambda self: self.node.name, constant=True)
    statusNodeName = Property(str, lambda self: self._status.nodeName, notify=statusChanged)

    elapsedTime = Property(float, lambda self: self._status.elapsedTime, notify=statusChanged)
