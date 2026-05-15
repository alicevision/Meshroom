#!/usr/bin/env python

import sys
import atexit
import copy
import datetime
import json
import logging
import os
import platform
import re
import shutil
import time
import uuid
from collections import namedtuple, OrderedDict
from enum import Enum, IntEnum, auto
from typing import Callable, Optional, List, Union

import meshroom
from meshroom.common import Signal, Variant, Property, BaseObject, Slot, ListModel, DictModel
from meshroom.core import desc, plugins, stats, hashValue, nodeVersion, Version, MrNodeType
from meshroom.core.attribute import attributeFactory, ListAttribute, GroupAttribute, Attribute
from meshroom.core.exception import NodeUpgradeError, UnknownNodeTypeError
from meshroom.core.mtyping import PathLike


def getWritingFilepath(filepath: str) -> str:
    return filepath + '.writing.' + str(uuid.uuid4())


def renameWritingToFinalPath(writingFilepath: str, filepath: str) -> str:
    if platform.system() == 'Windows':
        # On Windows, attempting to remove a file that is in use causes an exception to be raised.
        # So we may need multiple trials, if someone is reading it at the same time.
        for _ in range(20):
            try:
                os.remove(filepath)
                # If remove is successful, we can stop the iterations
                break
            except OSError:
                pass
    os.rename(writingFilepath, filepath)

class Status(Enum):
    """
    """
    NONE = 0
    SUBMITTED = 1
    RUNNING = 2
    ERROR = 3
    STOPPED = 4
    KILLED = 5
    SUCCESS = 6
    INPUT = 7  # Special status for input nodes


class ExecMode(Enum):
    """
    """
    NONE = auto()
    LOCAL = auto()
    EXTERN = auto()


class ChunkIndex(IntEnum):
    NONE=-3
    PREPROCESS=-2
    POSTPROCESS=-1
    # Standard chunks are indexed from 0


class ChunkIndexEnum(BaseObject):
    """
    Wrapper class to expose ChunkIndex enum to QML.
    
    Usage in QML:
        import Node 1.0
        
        if (chunkIndex === ChunkIndexEnum.PREPROCESS) {
            // Handle preprocess case
        }
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    NONE = Property(int, lambda self: int(ChunkIndex.NONE), constant=True)
    PREPROCESS = Property(int, lambda self: int(ChunkIndex.PREPROCESS), constant=True)
    POSTPROCESS = Property(int, lambda self: int(ChunkIndex.POSTPROCESS), constant=True)


# Simple structure for storing chunk information
NodeChunkSetup = namedtuple("NodeChunks", ["blockSize", "fullSize", "nbBlocks"])

class NodeStatusData(BaseObject):
    __slots__ = ("nodeName", "nodeType", "status", "execMode", "packageName", "mrNodeType",
                 "submitterSessionUid", "chunksBlockSize", "chunksFullSize", "chunksNbBlocks", "jobInfo")

    def __init__(self, nodeName='', nodeType='', packageName='',
                 mrNodeType: MrNodeType = MrNodeType.NONE, parent: BaseObject = None):
        super().__init__(parent)
        self.nodeName: str = nodeName
        self.nodeType: str = nodeType
        self.packageName: str = packageName
        self.mrNodeType: str = mrNodeType

        # Session UID where the node was submitted
        self.submitterSessionUid: Optional[str] = None

        self.reset()

    def reset(self):
        self.resetChunkInfo()
        self.resetDynamicValues()

    def resetChunkInfo(self):
        self.chunksSetup: NodeChunkSetup = None

    def resetDynamicValues(self):
        self.status: Status = Status.NONE
        self.execMode: ExecMode = ExecMode.NONE
        self.jobInfo: dict = {}

    def setNodeType(self, node):
        """
        Set the node type and package information from the given node.
        We do not set the name in this method as it may vary if there are duplicates.
        """
        self.nodeType = node.nodeType
        self.packageName = node.packageName
        self.mrNodeType = node.getMrNodeType()

    def setNode(self, node):
        """ Set the node information from one node instance. """
        self.nodeName = node.name
        self.setNodeType(node)

    def setJob(self, jid, submitterName):
        """ Set Job information on the node. """
        self.jobInfo = {
            "jid": str(jid),
            "submitterName": str(submitterName),
        }

    @property
    def jobName(self):
        if self.jobInfo:
            return f"{self.jobInfo['submitterName']}<{self.jobInfo['jid']}>"
        else:
            return "UNKNOWN"

    def initExternSubmit(self):
        """
        When submitting a node, we reset the status information to ensure that we do not keep
        outdated information.
        """
        self.resetDynamicValues()
        self.submitterSessionUid = meshroom.core.sessionUid
        self.status = Status.SUBMITTED
        self.execMode = ExecMode.EXTERN

    def initLocalSubmit(self):
        """
        When submitting a node, we reset the status information to ensure that we do not keep
        outdated information.
        """
        self.resetDynamicValues()
        self.submitterSessionUid = meshroom.core.sessionUid
        self.status = Status.SUBMITTED
        self.execMode = ExecMode.LOCAL

    def toDict(self):
        keys = list(self.__slots__) or []
        d = {key:getattr(self, key, 0) for key in keys}
        for _k, _v in d.items():
            if isinstance(_v, Enum):
                d[_k] = _v.name
        if self.chunksSetup and self.chunksSetup.nbBlocks > 0:
            d["chunksBlockSize"] = self.chunksSetup.blockSize
            d["chunksFullSize"] = self.chunksSetup.fullSize
            d["chunksNbBlocks"] = self.chunksSetup.nbBlocks
        else:
            # Ensure we do not write chunk keys with zero/invalid values,
            # as they would create a poisoned NodeChunkSetup(0,0,0) on reload
            d.pop("chunksBlockSize", None)
            d.pop("chunksFullSize", None)
            d.pop("chunksNbBlocks", None)
        return d

    def fromDict(self, d):
        self.reset()
        if "mrNodeType" in d:
            self.mrNodeType = MrNodeType[d.pop("mrNodeType")]
        if "chunksBlockSize" in d and "chunksFullSize" in d and "chunksNbBlocks" in d:
            blockSize = int(d.pop("chunksBlockSize") or 0)
            fullSize = int(d.pop("chunksFullSize") or 0)
            nbBlocks = int(d.pop("chunksNbBlocks") or 0)
            if nbBlocks > 0:
                self.chunksSetup = NodeChunkSetup(blockSize, fullSize, nbBlocks)
        if "status" in d:
            self.status: Status = Status[d.pop("status")]
        if "execMode" in d:
            self.execMode = ExecMode[d.pop("execMode")]
        for _key, _value in d.items():
            if _key in self.__slots__:
                setattr(self, _key, _value)

    def loadFromCache(self, statusFile):
        self.reset()
        try:
            with open(statusFile) as jsonFile:
                statusData = json.load(jsonFile)
            self.fromDict(statusData)
        except Exception as e:
            logging.warning(f"(loadFromCache) {self.nodeName}: Error while loading status file {statusFile}: {e}")
            self.reset()

    @property
    def nbChunks(self):
        nbBlocks = self.chunksSetup.nbBlocks if self.chunksSetup else -1
        return nbBlocks

    @property
    def fullSize(self):
        fullSize = self.chunksSetup.fullSize if self.chunksSetup else -1
        return fullSize

    def getChunkRanges(self):
        if not self.chunksSetup:
            return []
        ranges = []
        for i in range(self.chunksSetup.nbBlocks):
            ranges.append(desc.Range(
                iteration=i,
                blockSize=self.chunksSetup.blockSize,
                fullSize=self.chunksSetup.fullSize,
                nbBlocks=self.chunksSetup.nbBlocks
            ))
        return ranges

    def setChunks(self, chunks):
        blockSize, fullSize, nbBlocks = 1, 1, 1
        for c in chunks:
            r = c.range
            blockSize, fullSize, nbBlocks = r.blockSize, r.fullSize, r.nbBlocks
            break
        self.chunksSetup = NodeChunkSetup(blockSize, fullSize, nbBlocks)


class ChunkStatusData(BaseObject):
    """
    """
    dateTimeFormatting = '%Y-%m-%d %H:%M:%S.%f'

    __slots__ = (
        "nodeName", "mrNodeType", "computeSessionUid", "execMode", "status",
        "commandLine", "startDateTime", "endDateTime", "elapsedTime", "hostname"
    )

    def __init__(self, nodeName='', mrNodeType: MrNodeType = MrNodeType.NONE, parent: BaseObject = None):
        super().__init__(parent)
        self.nodeName: str = nodeName
        self.mrNodeType = mrNodeType
        self.computeSessionUid: Optional[str] = None    # Session where computation is done
        self.execMode: ExecMode = ExecMode.NONE
        self.resetDynamicValues()

    def resetDynamicValues(self):
        self.status: Status = Status.NONE
        self.commandLine: str = ""
        self._startTime: Optional[datetime.datetime] = None
        self.startDateTime: str = ""
        self.endDateTime: str = ""
        self.elapsedTime: float = 0.0
        self.hostname: str = ""

    def checkStatus(self, statusName):
        return self.status == Status[statusName]

    def setNode(self, node):
        """ Set the node information from one node instance. """
        self.nodeName = node.name
        self.mrNodeType = node.getMrNodeType()

    def merge(self, other):
        self.startDateTime = min(self.startDateTime, other.startDateTime)
        self.endDateTime = max(self.endDateTime, other.endDateTime)
        self.elapsedTime += other.elapsedTime

    def reset(self):
        self.nodeName: str = ""
        self.mrNodeType: MrNodeType = MrNodeType.NONE
        self.execMode: ExecMode = ExecMode.NONE
        self.resetDynamicValues()

    def initStartCompute(self):
        import platform
        self.computeSessionUid = meshroom.core.sessionUid
        self.hostname = platform.node()
        self._startTime = time.time()
        self.startDateTime = datetime.datetime.now().strftime(self.dateTimeFormatting)
        # to get datetime obj: datetime.datetime.strptime(obj, self.dateTimeFormatting)
        self.status = Status.RUNNING
        # Note: We do not modify the "execMode" here, as it is set in the init*Submit methods.
        #       When we compute (from renderfarm or isolated environment),
        #       we do not want to modify the execMode set from the submit.

    def initIsolatedCompute(self):
        """
        When submitting a node, we reset the status information to ensure that we do not keep
        outdated information.
        """
        self.resetDynamicValues()
        self.initStartCompute()
        assert self.mrNodeType == MrNodeType.NODE
        self.computeSessionUid = None

    def initExternSubmit(self):
        """
        When submitting a node, we reset the status information to ensure that we do not keep
        outdated information.
        """
        self.resetDynamicValues()
        self.computeSessionUid = None
        self.status = Status.SUBMITTED
        self.execMode = ExecMode.EXTERN

    def initLocalSubmit(self):
        """
        When submitting a node, we reset the status information to ensure that we do not keep
        outdated information.
        """
        self.resetDynamicValues()
        self.computeSessionUid = None
        self.status = Status.SUBMITTED
        self.execMode = ExecMode.LOCAL

    def initEndCompute(self):
        self.computeSessionUid = meshroom.core.sessionUid
        self.endDateTime = datetime.datetime.now().strftime(self.dateTimeFormatting)
        if self._startTime != None:
            self.elapsedTime = time.time() - self._startTime

    @property
    def elapsedTimeStr(self):
        return str(datetime.timedelta(seconds=self.elapsedTime))

    def toDict(self):
        keys = list(self.__slots__) or []
        d = {key:getattr(self, key) for key in keys}
        for _k, _v in d.items():
            if isinstance(_v, Enum):
                d[_k] = _v.name
        return d

    def fromDict(self, d):
        self.reset()
        if "status" in d:
            self.status: Status = Status[d.pop("status")]
        if "execMode" in d:
            self.execMode = ExecMode[d.pop("execMode")]
        if "mrNodeType" in d:
            self.mrNodeType = MrNodeType[d.pop("mrNodeType")]
        for _key, _value in d.items():
            if _key in self.__slots__:
                setattr(self, _key, _value)


class LogManager:
    dateTimeFormatting = '%H:%M:%S'

    def __init__(self, logger, logFile):
        self.logger: logging.Logger = logger
        self.logFile: PathLike = logFile
        self._previousHandlers: List[logging.Handler] = []
        self._previousLevel: int = 0

    class Formatter(logging.Formatter):
        def format(self, record):
            # Make level name lower case
            record.levelname = record.levelname.lower()
            return logging.Formatter.format(self, record)

    def configureLogger(self):
        self._previousLevel = self.logger.level
        self._previousHandlers = []
        for handler in self.logger.handlers[:]:
            self._previousHandlers.append(handler)
            self.logger.removeHandler(handler)
        handler = logging.FileHandler(self.logFile)
        formatter = self.Formatter('[%(asctime)s.%(msecs)03d][%(levelname)s] %(message)s',
                                   self.dateTimeFormatting)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def restorePreviousLogger(self):
        for h in self.logger.handlers[:]:
            self.logger.removeHandler(h)
        for h in self._previousHandlers:
            self.logger.addHandler(h)
        self.logger.setLevel(self._previousLevel)

    def clearLogFile(self):
        open(self.logFile, 'w').close()

    def start(self, level):
        # Make sure the log file exists
        if not os.path.exists(self.logFile):
            self.clearLogFile()
        self.configureLogger()
        self.logger.propagate = False
        self.logger.setLevel(self.textToLevel(level))
        self.progressBar = False

    def end(self):
        for handler in self.logger.handlers[:]:
            # Stops the file being locked
            handler.close()

    def makeProgressBar(self, end, message=''):
        assert end > 0
        assert not self.progressBar

        self.progressEnd = end
        self.currentProgressTics = 0
        self.progressBar = True

        with open(self.logFile, 'a') as f:
            if message:
                f.write(message+'\n')
            f.write('0%   10   20   30   40   50   60   70   80   90   100%\n')
            f.write('|----|----|----|----|----|----|----|----|----|----|\n\n')

            f.close()

        with open(self.logFile, "r") as f:
            content = f.read()
            self.progressBarPosition = content.rfind('\n')

    def updateProgressBar(self, value):
        assert self.progressBar
        assert value <= self.progressEnd

        tics = round((value/self.progressEnd)*51)

        with open(self.logFile, "r+") as f:
            text = f.read()
            for i in range(tics-self.currentProgressTics):
                text = text[:self.progressBarPosition]+'*'+text[self.progressBarPosition:]
            f.seek(0)
            f.write(text)

        self.currentProgressTics = tics

    def completeProgressBar(self):
        assert self.progressBar

        self.progressBar = False

    @staticmethod
    def textToLevel(text):
        text = text.lower()
        if text in ["critical", "fatal"]:
            return logging.CRITICAL
        elif text == "error":
            return logging.ERROR
        elif text == "warning":
            return logging.WARNING
        elif text == "info":
            return logging.INFO
        elif text == "debug":
            return logging.DEBUG
        elif text == "trace":
            return logging.TRACE
        else:
            return logging.NOTSET


runningProcesses: dict[str, "NodeChunk"] = {}


@atexit.register
def clearProcessesStatus():
    for k, v in runningProcesses.items():
        v.upgradeStatusTo(Status.KILLED)


class NodeChunk(BaseObject):
    def __init__(self, node, range, placeholder=False, parent=None):
        super().__init__(parent)
        self.__uid = uuid.uuid1()
        self.node: Node = node
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


# Simple structure for storing node position
Position = namedtuple("Position", ["x", "y"])
# Initialize default coordinates values to 0
Position.__new__.__defaults__ = (0,) * len(Position._fields)


class BaseNode(BaseObject):
    """
    Base Abstract class for Graph nodes.
    """

    # Regexp handling complex attribute names with recursive understanding of Lists and Groups
    # i.e: a.b, a[0], a[0].b.c[1]
    attributeRE = re.compile(r'\.?(?P<name>\w+)(?:\[(?P<index>\d+)\])?')

    def __init__(self, nodeType: str, position: Position = None, parent: BaseObject = None,
                 uid: str = None, **kwargs):
        """
        Create a new Node instance based on the given node description.
        Any other keyword argument will be used to initialize this node's attributes.

        Args:
            nodeType: name of the node type
            parent: this Node's parent
            **kwargs: attributes values
        """
        super().__init__(parent)
        self._nodeType: str = nodeType
        self.nodeDesc: desc.BaseNode = None
        self.nodePlugin: plugins.Plugin = None

        # instantiate node description if nodeType is valid
        if meshroom.core.pluginManager.getRegisteredNodePlugin(nodeType):
            self.nodeDesc = meshroom.core.pluginManager.getRegisteredNodePlugin(nodeType).nodeDescriptor()
            self.nodePlugin = meshroom.core.pluginManager.getRegisteredNodePlugin(nodeType)

        self.packageName: str = ""
        self._internalFolder: str = ""
        self._sourceCodeFolder: str = self.nodeDesc.sourceCodeFolder if self.nodeDesc else ""
        self._internalFolderExp = "{cache}/{nodeType}/{uid}"

        # temporary unique name for this node
        self._name: str = f"_{nodeType}_{uuid.uuid1()}"
        self.graph = None
        self.dirty: bool = True  # whether this node's outputs must be re-evaluated on next Graph update
        self._chunks: list[NodeChunk] = ListModel(parent=self)
        self._preprocessChunk = None
        if self.nodeDesc and self.nodeDesc.hasPreprocess:
            self._preprocessChunk = NodeChunk(self, desc.Range(ChunkIndex.PREPROCESS), parent=self)
            self._preprocessChunk.statusChanged.connect(self.globalStatusChanged)
        self._postprocessChunk = None
        if self.nodeDesc and self.nodeDesc.hasPostprocess:
            self._postprocessChunk = NodeChunk(self, desc.Range(ChunkIndex.POSTPROCESS), parent=self)
            self._postprocessChunk.statusChanged.connect(self.globalStatusChanged)
        self._chunksCreated = False  # Only initialize chunks on compute
        self._chunkPlaceholder: list[NodeChunk] = ListModel(parent=self)  # Placeholder chunk for nodes with dynamic ones
        self._uid: str = uid
        self._expVars: dict = {}
        self._size: int = 0
        self._logManager: Optional[LogManager] = None
        self._position: Position = position or Position()
        self._attributes = DictModel(keyAttrName='name', parent=self)
        self._internalAttributes = DictModel(keyAttrName='name', parent=self)
        self.invalidatingAttributes: set = set()
        self._alive: bool = True  # for QML side to know if the node can be used or is going to be deleted
        self._locked: bool = False
        self._duplicates = ListModel(parent=self)  # list of nodes with the same uid
        self._hasDuplicates: bool = False

        self._nodeStatus: NodeStatusData = NodeStatusData(self._name, nodeType, self.packageName,
                                                          self.getMrNodeType())
        self.nodeStatusFileLastModTime = -1

        self.globalStatusChanged.connect(self.updateDuplicatesStatusAndLocked)

        self._staticExpVars = {
            "nodeType": self.nodeType,
            "nodeSourceCodeFolder": self.sourceCodeFolder
        }

    def __getattr__(self, k):
        try:
            # Throws exception if not in prototype chain
            return object.__getattribute__(self, k)
        except AttributeError as err:
            try:
                return self.attribute(k)
            except KeyError:
                raise err

    def getMrNodeType(self):
        # In compatibility mode, we may or may not have access to the nodeDesc and its information
        # about the node type.
        if self.nodeDesc is None:
            return MrNodeType.NONE
        return self.nodeDesc.getMrNodeType()

    def getName(self):
        return self._name

    def getDefaultLabel(self):
        return self.nameToLabel(self._name)

    def getLabel(self) -> str:
        """
        Returns:
            The user-provided label if it exists, the high-level label of this node otherwise
        """
        if self.hasInternalAttribute("label"):
            label = self.internalAttribute("label").value.strip()
            if label:
                return label
        return self.getDefaultLabel()

    def getNodeLogLevel(self) -> str:
        """
        Returns:
            The user-provided log level used for logging on process launched by this node
        """
        if self.hasInternalAttribute("nodeDefaultLogLevel"):
            return self.internalAttribute("nodeDefaultLogLevel").value.strip()
        return "info"

    def getColor(self) -> str:
        """
        Returns:
            The node's color: the user-provided custom color if set, otherwise the descriptor's
            default color (nodeDesc.color), or empty string if neither is defined.
        """
        if self.hasInternalAttribute("color"):
            return self.internalAttribute("color").value.strip()
        return ""

    def getInvalidationMessage(self) -> str:
        """
        Returns:
            The invalidation message on the node if it exists, empty string otherwise
        """
        if self.hasInternalAttribute("invalidation"):
            return self.internalAttribute("invalidation").value
        return ""

    def getComment(self) -> str:
        """
        Returns:
            The comments on the node if they exist, empty string otherwise
        """
        if self.hasInternalAttribute("comment"):
            return self.internalAttribute("comment").value
        return ""

    def getFontSize(self) -> int:
        """
        Returns:
            The font size from the node if it exists, 0 otherwise.
        """
        if self.hasInternalAttribute("fontSize"):
            return self.internalAttribute("fontSize").value
        return 0

    def getFontColor(self) -> str:
        """
        Returns:
            The color of the font from the node if it exists, empty string otherwise.
        """
        if self.hasInternalAttribute("fontColor"):
            return self.internalAttribute("fontColor").value.strip()
        return ""

    def getNodeWidth(self) -> int:
        """
        Returns:
            The width of the node if it has a user-set width, 0 otherwise.
        """
        if self.hasInternalAttribute("nodeWidth"):
            return self.internalAttribute("nodeWidth").value
        return 0

    def getNodeHeight(self) -> int:
        """
        Returns:
            The height of the node if it has a user-set height, 0 otherwise.
        """
        if self.hasInternalAttribute("nodeHeight"):
            return self.internalAttribute("nodeHeight").value
        return 0


    @Slot(str, result=str)
    def nameToLabel(self, name):
        """
        Returns:
            str: the high-level label from the technical node name
        """
        t, idx = name.rsplit("_", 1) if "_" in name else (name, "1")
        return f"{t}{idx if int(idx) > 1 else ''}"

    def getDocumentation(self):
        if not self.nodeDesc:
            return ""
        if self.nodeDesc.documentation:
            return self.nodeDesc.documentation
        else:
            return self.nodeDesc.__doc__

    def getNodeInfo(self):
        if not self.nodeDesc:
            return []
        info = OrderedDict([
            ("module", self.nodeDesc.__module__),
            ("modulePath", self.nodeDesc.plugin.path),
        ])
        # > Info from the plugin module
        plugin_module = sys.modules.get(self.nodeDesc.__module__)
        if getattr(plugin_module, "__author__", None):
            info["author"] = plugin_module.__author__
        if getattr(plugin_module, "__license__", None):
            info["license"] = plugin_module.__license__
        if getattr(plugin_module, "__version__", None):
            info["version"] = plugin_module.__version__
        # > Overrides at the node-level
        if getattr(self.nodeDesc, "author", None):
            info["author"] = self.nodeDesc.author
        if getattr(self.nodeDesc, "version", None):
            info["version"] = self.nodeDesc.version
        # > Additional node information stored in a __nodeInfo__ parameter
        additionalNodeInfo = getattr(self.nodeDesc, "__nodeInfo__", None)
        if additionalNodeInfo:
            for key, value in additionalNodeInfo:
                info[key] = value
        return [{"key": k, "value": v} for k, v in info.items()]

    @Slot(str, result=Attribute)
    def attribute(self, name):
        att = None
        # Complex name indicating group or list attribute
        if '[' in name or '.' in name:
            p = self.attributeRE.findall(name)

            for n, idx in p:
                # first step: get root attribute
                if att is None:
                    att = self._attributes.get(n)
                else:
                    # get child Attribute in Group
                    assert isinstance(att, GroupAttribute)
                    att = att.value.get(n)
                if idx != '':
                    # get child Attribute in List
                    assert isinstance(att, ListAttribute)
                    att = att.value.at(int(idx))
        else:
            att = self._attributes.getr(name)
        return att

    @Slot(str, result=Attribute)
    def internalAttribute(self, name):
        # No group or list attributes for internal attributes
        # The internal attribute itself can be returned directly
        return self._internalAttributes.get(name)

    def setInternalAttributeValues(self, values):
        # initialize internal attribute values
        for k, v in values.items():
            attr = self.internalAttribute(k)
            attr.value = v

    def getAttributes(self):
        return self._attributes

    def getInternalAttributes(self):
        return self._internalAttributes

    @Slot(str, result=bool)
    def hasAttribute(self, name):
        # Complex name indicating group or list attribute: parse it and get the
        # first output element to check for the attribute's existence
        if "[" in name or "." in name:
            p = self.attributeRE.findall(name)
            return p[0][0] in self._attributes.keys() or p[0][1] in self._attributes.keys()
        return name in self._attributes.keys()

    @Slot(str, result=bool)
    def hasInternalAttribute(self, name):
        return name in self._internalAttributes.keys()

    def _applyExpr(self):
        for attr in self._attributes:
            attr._applyExpr()

    @property
    def nodeType(self):
        return self._nodeType

    @property
    def position(self):
        """ Get node position. """
        return self._position

    @position.setter
    def position(self, value):
        """ Set node position.

        Args:
            value (Position): target position
        """
        if self._position == value:
            return
        self._position = value
        self.positionChanged.emit()

    @property
    def alive(self):
        return self._alive

    @alive.setter
    def alive(self, value):
        if self._alive == value:
            return
        self._alive = value
        self.aliveChanged.emit()

    @property
    def depth(self):
        return self.graph.getDepth(self)

    @property
    def minDepth(self):
        return self.graph.getDepth(self, minimal=True)

    @property
    def valuesFile(self):
        return os.path.join(self.internalFolder, 'values')

    def getInputNodes(self, recursive, dependenciesOnly):
        return self.graph.getInputNodes(self, recursive=recursive,
                                        dependenciesOnly=dependenciesOnly)

    def getOutputNodes(self, recursive, dependenciesOnly):
        return self.graph.getOutputNodes(self, recursive=recursive,
                                         dependenciesOnly=dependenciesOnly)

    def toDict(self):
        pass

    def _computeUid(self):
        """ Compute node UID by combining associated attributes' UIDs. """
        # If there is no invalidating attribute, then the computation of the UID should not
        # go through as it will only include the node type
        if not self.invalidatingAttributes:
            return

        # UID is computed by hashing the sorted list of tuple (name, value) of all attributes
        # impacting this UID
        uidAttributes = []
        for attr in self.invalidatingAttributes:
            if not attr.enabled:
                continue  # Disabled params do not contribute to the uid
            dynamicOutputAttr = attr.isLink and attr.inputRootLink.desc.isDynamicValue
            # For dynamic output attributes, the UID does not depend on the attribute value.
            # In particular, when loading a project file, the UIDs are updated first,
            # and the node status and the dynamic output values are not yet loaded,
            # so we should not read the attribute value.
            if not dynamicOutputAttr and not attr.keyable and attr.value == attr.desc.uidIgnoreValue:
                continue  # For non-dynamic attributes, check if the value should be ignored
            uidAttributes.append((attr.name, attr.uid()))
        uidAttributes.sort()

        # Adding the node type prevents ending up with two identical UIDs for different node types
        # that have the exact same list of attributes
        uidAttributes.append(self.nodeType)
        self._uid = hashValue(uidAttributes)

    def _computeInternalFolder(self, cacheDir):
        self._internalFolder = self._internalFolderExp.format(
            cache=cacheDir or self.graph.cacheDir,
            nodeType=self.nodeType,
            uid=self._uid)

    def _buildExpVars(self):
        """
        Generate command variables using input attributes and resolved output attributes
        names and values.
        """
        def _buildAttributeExpVars(expVars, name, attr):
            if attr.enabled:
                # xxValue is exposed without quotes to allow to compose expressions
                expVars[name + "Value"] = attr.getValueStr(withQuotes=False)

                if isinstance(attr, GroupAttribute):
                    assert isinstance(attr.value, DictModel)
                    # If the GroupAttribute is not set in a single command line argument,
                    # the sub-attributes may need to be exposed individually
                    for v in attr._value:
                        _buildAttributeExpVars(expVars, v.name, v)

        self._expVars = {
            "uid": self._uid,
            "nodeCacheFolder": self._internalFolder,
            "node": self,
        }

        # Evaluate input params
        for name, attr in self._attributes.objects.items():
            if attr.isOutput:
                continue  # skip outputs
            _buildAttributeExpVars(self._expVars, name, attr)

        # For updating output attributes invalidation values
        expVarsNoCache = self._expVars.copy()
        expVarsNoCache["cache"] = ""

        # Use "self._internalFolder" instead of "self.internalFolder" because we do not want it to
        # be resolved with the {cache} information ("self.internalFolder" resolves
        # "self._internalFolder")
        expVarsNoCache["nodeCacheFolder"] = self._internalFolderExp.format(**expVarsNoCache, **self._staticExpVars)

        # Evaluate output params
        for name, attr in self._attributes.objects.items():
            if attr.isInput:
                continue  # skip inputs

            # Apply expressions for File attributes
            if attr.desc.isExpression:
                defaultValue = ""
                # Do not evaluate expression for disabled attributes
                # (the expression may refer to other attributes that are not defined)
                if attr.enabled:
                    try:
                        defaultValue = attr.getDefaultValue()
                    except AttributeError:
                        # If we load an old scene, the lambda associated to the 'value' could try to
                        # access other params that could not exist yet
                        logging.warning(f'Invalid lambda evaluation for "{self.name}.{attr.name}"')
                    if defaultValue is not None:
                        try:
                            attr.value = defaultValue.format(**self._expVars)
                            attr._invalidationValue = defaultValue.format(**expVarsNoCache)
                        except KeyError as err:
                            logging.warning(f'Invalid expression with missing key on "{self.name}.{attr.name}" with '
                                            f'value "{defaultValue}".\nError: {str(err)}')
                        except ValueError as err:
                            logging.warning(f'Invalid expression value on "{self.name}.{attr.name}" with value '
                                            f'"{defaultValue}".\nError: {str(err)}')

            # xxValue is exposed without quotes to allow to compose expressions
            self._expVars[name + 'Value'] = attr.getValueStr(withQuotes=False)


    def createCmdLineVars(self):
        """
        Generate command variables using input attributes and resolved output attributes
        names and values.
        """
        def _buildAttributeCmdLineVars(cmdLineVars, name, attr):
            if attr.enabled:
                group = attr.desc.commandLineGroup(attr.node) \
                        if callable(attr.desc.commandLineGroup) else attr.desc.commandLineGroup
                if group:
                    # If there is a valid command line "group"
                    v = attr.getValueStr(withQuotes=True)

                    # List elements may give a fully empty string and will not be sent to the command line.
                    # String attributes will return only quotes if it is empty and thus will be send to the command line.
                    # But a List of string containing 1 element,
                    # and this element is an empty string will also return quotes and will be sent to the command line.
                    if v:
                        cmdLineVars[group] = cmdLineVars.get(group, "") + f" --{name} {v}"
                elif isinstance(attr, GroupAttribute):
                    assert isinstance(attr.value, DictModel)
                    # If the GroupAttribute is not set in a single command line argument,
                    # the sub-attributes may need to be exposed individually
                    for v in attr._value:
                        _buildAttributeCmdLineVars(cmdLineVars, v.name, v)

        cmdLineVars = {}

        # Evaluate input params
        for name, attr in self._attributes.objects.items():
            if attr.isOutput:
                continue  # skip outputs
            _buildAttributeCmdLineVars(cmdLineVars, name, attr)

        # Evaluate output params
        for name, attr in self._attributes.objects.items():
            if attr.isInput:
                continue  # skip inputs
            if not attr.desc.commandLineGroup:
                continue  # skip attributes without group

            v = attr.getValueStr(withQuotes=True)

            if not v:
                continue  # skip empty strings

            cmdLineVars[attr.desc.commandLineGroup] = \
                cmdLineVars.get(attr.desc.commandLineGroup, '') + f' --{name} {v}'

        return cmdLineVars

    @property
    def isParallelized(self):
        return bool(self.nodeDesc.parallelization) if meshroom.useMultiChunks else False

    @property
    def cpu(self):
        """ Return the resolved CPU level for this node, by evaluating the descriptor's `cpu`
        attribute with this node instance if it is callable. """
        if self.nodeDesc is None:
            return None
        return self.nodeDesc.resolvedCpu(self)

    @property
    def gpu(self):
        """ Return the resolved GPU level for this node, by evaluating the descriptor's `gpu`
        attribute with this node instance if it is callable. """
        if self.nodeDesc is None:
            return None
        return self.nodeDesc.resolvedGpu(self)

    @property
    def ram(self):
        """ Return the resolved RAM level for this node, by evaluating the descriptor's `ram`
        attribute with this node instance if it is callable. """
        if self.nodeDesc is None:
            return None
        return self.nodeDesc.resolvedRam(self)

    def hasStatus(self, status: Status):
        if self.isInputNode:
            return status == Status.INPUT
        if not self._chunks or not self._chunksCreated:
            return status == Status.NONE
        for chunk in self.getAllChunks():
            if chunk._status.status != status:
                return False
        return True

    def _isComputed(self):
        if not self.isComputableType:
            return True
        return self.hasStatus(Status.SUCCESS)

    def _isComputableType(self):
        """ Return True if this node type is computable, False otherwise.
        A computable node type can be in a context that does not allow computation.
        """
        # Ambiguous case for NONE, which could be used for compatibility nodes if we do not have
        # any information about the node descriptor.
        return self.getMrNodeType() != MrNodeType.INPUT and self.getMrNodeType() != MrNodeType.BACKDROP

    def clearData(self):
        """ Delete this Node internal folder.
        Status will be reset to Status.NONE
        """
        # Clear cache
        self._nodeStatus.reset()
        # Reset chunks
        self._resetChunks()
        if self.internalFolder and os.path.exists(self.internalFolder):
            try:
                shutil.rmtree(self.internalFolder)
            except Exception as exc:
                # We could get some "Device or resource busy" on .nfs file while removing the folder
                # on Linux network.
                # On Windows, some output files may be open for visualization and the removal will
                # fail.
                # In both cases, we can ignore it.
                logging.warning(f"Failed to remove internal folder: '{self.internalFolder}'. Error: {exc}.")
            self.updateStatusFromCache()

    @Slot(result=str)
    def getStartDateTime(self):
        """ Return the date (str) of the first running chunk """
        dateTime = [chunk._status.startDateTime for chunk in self.getAllChunks() if chunk._status.status
                    not in (Status.NONE, Status.SUBMITTED) and chunk._status.startDateTime != ""]
        return min(dateTime) if len(dateTime) != 0 else ""

    def isAlreadySubmitted(self):
        if self._chunksCreated:
            return any(c.isAlreadySubmitted() for c in self.getAllChunks())
        else:
            return self._nodeStatus.status in (Status.SUBMITTED, Status.RUNNING)

    def isAlreadySubmittedOrFinished(self):
        if self._chunksCreated:
            return all(c.isAlreadySubmittedOrFinished() for c in self.getAllChunks())
        else:
            return self._nodeStatus.status in (Status.SUBMITTED, Status.RUNNING, Status.SUCCESS)

    @Slot(result=bool)
    def isSubmittedOrRunning(self):
        """
        Return True if all chunks are at least submitted and there is one running chunk,
        False otherwise.
        """
        if not self._chunksCreated:
            return False
        if not self.isAlreadySubmittedOrFinished():
            return False
        for chunk in self.getAllChunks():
            if chunk.isRunning():
                return True
        return False

    @Slot(result=bool)
    def isRunning(self):
        """ Return True if at least one chunk of this Node is running, False otherwise. """
        return any(chunk.isRunning() for chunk in self.getAllChunks())

    @Slot(result=bool)
    def isFinishedOrRunning(self):
        """
        Return True if all chunks of this Node is either finished or running, False
        otherwise.
        """
        allChunks = self.getAllChunks()
        if not allChunks:
            return False
        return all(chunk.isFinishedOrRunning() for chunk in allChunks)

    @Slot(result=bool)
    def isPartiallyFinished(self):
        """ Return True is at least one chunk of this Node is finished, False otherwise. """
        return any(chunk.isFinished() for chunk in self.getAllChunks())

    def isExtern(self):
        """
        Return True if at least one chunk of this Node has an external execution mode,
        False otherwise.

        It is not enough to check whether the first chunk's execution mode is external,
        because computations may have been started locally, interrupted, and restarted externally.
        In that case, if the first chunk has completed locally before the computations were
        interrupted, its execution mode will always be local, even if computations resume
        externally.
        """
        if not self._chunksCreated:
            if self._nodeStatus.execMode == ExecMode.EXTERN:
                return True
            elif self._nodeStatus.execMode == ExecMode.LOCAL and self._nodeStatus.status in (Status.SUBMITTED, Status.RUNNING):
                return meshroom.core.sessionUid != self._nodeStatus.submitterSessionUid
            return False
        return any(chunk.isExtern() for chunk in self.getAllChunks())

    @Slot()
    def clearSubmittedChunks(self):
        """
        Reset all submitted chunks to Status.NONE. This method should be used to clear
        inconsistent status if a computation failed without informing the graph.

        Warnings:
            This must be used with caution. This could lead to inconsistent node status
            if the graph is still being computed.
        """
        chunks: List[Union[BaseNode, NodeChunk]] = self.getAllChunks()
        if not self._chunksCreated:
            chunks.append(self)
        for chunk in chunks:
            if chunk.isAlreadySubmitted():
                chunk.upgradeStatusTo(Status.NONE, ExecMode.NONE)
        self.globalStatusChanged.emit()

    def clearLocallySubmittedChunks(self):
        """ Reset all locally submitted chunks to Status.NONE. """
        chunks: List[Union[BaseNode, NodeChunk]] = self.getAllChunks()
        if not self._chunksCreated:
            chunks.append(self)
        for chunk in chunks:
            if chunk.isAlreadySubmitted() and not chunk.isExtern():
                chunk.upgradeStatusTo(Status.NONE, ExecMode.NONE)
        self.globalStatusChanged.emit()

    def upgradeStatusTo(self, newStatus, execMode=None):
        """ Upgrade node to the given status and save it on disk. """
        if self._preprocessChunk:
            self._preprocessChunk.upgradeStatusTo(newStatus)
        if self._postprocessChunk:
            self._postprocessChunk.upgradeStatusTo(newStatus)
        if self._chunksCreated:
            for chunk in self._chunks:
                chunk.upgradeStatusTo(newStatus)
        else:
            if execMode is not None:
                self._nodeStatus.execMode = execMode
            self._nodeStatus.status = newStatus
            self.upgradeStatusFile()
            chunkPlaceholder = NodeChunk(self, desc.computation.Range(), placeholder=True)
            chunkPlaceholder._status.execMode = self._nodeStatus.execMode
            chunkPlaceholder._status.status = self._nodeStatus.status
            self._chunkPlaceholder.setObjectList([chunkPlaceholder])
            self.chunksChanged.emit()
        self.globalStatusChanged.emit()

    def updateStatisticsFromCache(self):
        for chunk in self.getAllChunks():
            chunk.updateStatisticsFromCache()

    def _resetChunks(self):
        pass

    def createChunksFromCache(self):
        pass

    def _createChunks(self):
        pass

    def evaluateSize(self):
        """
        Evaluate the node size by delegating to the descriptor's resolvedSize classmethod.
        """
        return self.nodeDesc.resolvedSize(self)

    def _updateNodeSize(self):
        self.setSize(self.evaluateSize())

    def _getAttributeChangedCallback(self, attr: Attribute) -> Optional[Callable]:
        """ Get the node descriptor-defined value changed callback associated to `attr` if any. """

        # Callbacks cannot be defined on nested attributes.
        if attr.root is not None:
            return None

        attrCapitalizedName = attr.name[:1].upper() + attr.name[1:]
        callbackName = f"on{attrCapitalizedName}Changed"

        callback = getattr(self.nodeDesc, callbackName, None)
        return callback if callback and callable(callback) else None

    def _onAttributeChanged(self, attr: Attribute):
        """
        When an attribute value has changed, a specific function can be defined in the descriptor
        and be called.

        Args:
            attr: The Attribute that has changed.
        """

        if self.isCompatibilityNode:
            # Compatibility nodes are not meant to be updated.
            return

        if attr.isOutput and not self.isInputNode:
            # Ignore changes on output attributes for non-input nodes
            # as they are updated during the node's computation.
            # And we do not want notifications during the graph processing.
            return

        if not attr.keyable and attr.value is None:
            # Discard dynamic values depending on the graph processing.
            return

        if self.graph and self.graph.isLoading:
            # Do not trigger attribute callbacks during the graph loading.
            return

        callback = self._getAttributeChangedCallback(attr)

        if callback:
            callback(self)

        self.hasInvalidAttributeChanged.emit()

        if self.graph:
            # If we are in a graph, propagate the notification to the connected output attributes
            for edge in self.graph.outEdges(attr):
                edge.dst.valueChanged.emit()

    def onAttributeClicked(self, attr):
        """
        When an attribute is clicked, a specific function can be defined in the descriptor
        and be called.

        Args:
            attr (Attribute): attribute that has been clicked
        """
        paramName = attr.name[:1].upper() + attr.name[1:]
        methodName = f'on{paramName}Clicked'
        if hasattr(self.nodeDesc, methodName):
            m = getattr(self.nodeDesc, methodName)
            if callable(m):
                m(self)

    def updateInternals(self, cacheDir=None):
        """ Update Node's internal parameters and output attributes.

        This method is called when:
         - an input parameter is modified
         - the graph main cache directory is changed

        Args:
            cacheDir (str): (optional) override graph's cache directory with custom path
        """
        if self.nodeDesc:
            self.nodeDesc.update(self)

        for attr in self._attributes:
            attr.updateInternals()

        # Reset chunks splitting
        self._resetChunks()

        # Retrieve current internal folder (if possible)
        try:
            folder = self.internalFolder
        except KeyError:
            folder = ''

        # Update command variables / output attributes
        self._computeUid()
        self._computeInternalFolder(cacheDir)
        self._buildExpVars()
        if self.nodeDesc:
            self.nodeDesc.postUpdate(self)
        # Notify internal folder change if needed
        if self._internalFolder != folder:
            self.internalFolderChanged.emit()

    def updateInternalAttributes(self):
        self.internalAttributesChanged.emit()

    @property
    def internalFolder(self):
        return self._internalFolder

    @property
    def sourceCodeFolder(self):
        return self._sourceCodeFolder

    @property
    def nodeStatusFile(self):
        return os.path.join(self.graph.cacheDir, self.internalFolder, "nodeStatus")

    def shouldMonitorChanges(self):
        """ Check whether we should monitor changes in minimal mode.
        Only chunks that are run externally or local_isolated should be monitored,
        when run locally, status changes are already notified.
        Chunks with an ERROR status may be re-submitted externally and should thus still be monitored
        """
        if self._chunksCreated:
            # Only monitor when chunks are not created (in this case monitor chunk status files instead)
            return False
        return (self.isExtern() and self._nodeStatus.status in (Status.SUBMITTED, Status.RUNNING, Status.ERROR)) or \
               (self.getMrNodeType() == MrNodeType.NODE and self._nodeStatus.status in (Status.SUBMITTED, Status.RUNNING))

    def updateNodeStatusFromCache(self):
        """
        Update node status based on status file content/existence.
        # TODO : integrate nodeStatusFileLastModTime ?
        Returns True if a change on the chunk setup has been detected
        """
        chunksRangeHasChanged = False
        if os.path.exists(self.nodeStatusFile):
            oldChunkSetup = self._nodeStatus.chunksSetup
            self._nodeStatus.loadFromCache(self.nodeStatusFile)
            if self._nodeStatus.chunksSetup != oldChunkSetup:
                chunksRangeHasChanged = True
            self.nodeStatusFileLastModTime = os.path.getmtime(self.nodeStatusFile)
        else:
            # No status file => reset status to Status.None
            self.nodeStatusFileLastModTime = -1
            self._nodeStatus.reset()
        self._nodeStatus.setNodeType(self)
        return chunksRangeHasChanged

    def updateStatusFromCache(self):
        """ Update node status based on status file content/existence. """
        # Update nodeStatus from cache
        chunkChanged = self.updateNodeStatusFromCache()
        # Create chunks from cache if:
        #  - The chunk setup has changed (normal case: nodeStatus was reloaded with new data), OR
        #  - Chunks have not been created yet (recovery: a previous load cycle may have loaded
        #    the nodeStatus without triggering createChunksFromCache, e.g. due to a silent error
        #    in loadFromCache or an extra graph.update() that didn't reset the node's chunk info).
        # In both cases, the nodeStatus must contain valid chunk information (nbChunks > 0).
        if (chunkChanged or not self._chunksCreated) and self._nodeStatus.nbChunks > 0:
            # Update number of chunks
            try:
                self.createChunksFromCache()
            except Exception as e:
                logging.warning(f"Could not create chunks from cache: {e}")
                return
        s = self.globalStatus
        if self.nodeDesc.hasPreprocess:
            if not self._preprocessChunk:
                raise ValueError("No preprocess chunk")
            self._preprocessChunk.updateStatusFromCache()
        if self.nodeDesc.hasPostprocess:
            if not self._postprocessChunk:
                raise ValueError("No postprocess chunk")
            self._postprocessChunk.updateStatusFromCache()
        if self._chunksCreated:
            for chunk in self._chunks:
                chunk.updateStatusFromCache()
        else:
            # Restore placeholder chunk if needed
            chunkPlaceholder = NodeChunk(self, desc.computation.Range(), placeholder=True)
            chunkPlaceholder._status.execMode = self._nodeStatus.execMode
            if self._nodeStatus.status in (Status.NONE, Status.SUBMITTED):
                chunkPlaceholder._status.status = self._nodeStatus.status
            elif self._nodeStatus.status in (Status.RUNNING,):
                chunkPlaceholder._status.status = Status.SUBMITTED
            else:
                chunkPlaceholder._status.status = Status.NONE
            self._chunkPlaceholder.setObjectList([chunkPlaceholder])
        # logging.debug(f"updateStatusFromCache: {self.name}, status: {s} => {self.globalStatus}")
        self.updateOutputAttr()

    def upgradeStatusFile(self):
        """ Write node status on disk. """
        # Make sure the node has the globalStatus before saving it
        self._nodeStatus.status = self.getGlobalStatus()
        # Ensure chunk info is always in sync with the actual chunks before writing,
        # as _nodeStatus.chunks can be cleared by _resetChunks/loadFromCache and may not
        # have been restored (e.g. after createChunksFromCache which does not call setChunks).
        if self._chunksCreated and self._chunks:
            self._nodeStatus.setChunks(self._chunks)
        data = self._nodeStatus.toDict()
        statusFilepath = self.nodeStatusFile
        folder = os.path.dirname(statusFilepath)
        os.makedirs(folder, exist_ok=True)
        statusFilepathWriting = getWritingFilepath(statusFilepath)
        with open(statusFilepathWriting, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)
        renameWritingToFinalPath(statusFilepathWriting, statusFilepath)

    def setJobId(self, jid, submitterName):
        self._nodeStatus.setJob(jid, submitterName)
        self.upgradeStatusFile()

    def initStatusOnSubmit(self, forceCompute=False):
        """ Prepare chunks status when the node is in a graph that was submitted """
        hasChunkToLaunch = False
        if not self._chunksCreated:
            hasChunkToLaunch = True
            # Clear any stale chunk info from nodeStatus so that:
            # 1. The nodeStatus file written below does NOT contain chunk setup keys.
            # 2. When `meshroom_createChunks` runs on the farm, its call to
            #    `updateStatusFromCache()` will NOT recreate chunks from stale cache,
            #    allowing `node.createChunks()` to evaluate fresh chunk parameters.
            self._nodeStatus.resetChunkInfo()
        for chunk in self.getAllChunks():
            if forceCompute or chunk._status.status != Status.SUCCESS:
                hasChunkToLaunch = True
                chunk._status.setNode(self)
                chunk._status.initExternSubmit()
                chunk.upgradeStatusFile()
        if hasChunkToLaunch:
            self._nodeStatus.setNode(self)
            self._nodeStatus.initExternSubmit()
            self.upgradeStatusFile()
            self.globalStatusChanged.emit()
            if self._nodeStatus.execMode == ExecMode.EXTERN and self._nodeStatus.status in (Status.RUNNING, Status.SUBMITTED):
                chunkPlaceholder = NodeChunk(self, desc.computation.Range(), placeholder=True)
                chunkPlaceholder._status.execMode = self._nodeStatus.execMode
                chunkPlaceholder._status.status = self._nodeStatus.status
                self._chunkPlaceholder.setObjectList([chunkPlaceholder])
                self.chunksChanged.emit()

    def initStatusOnCompute(self, forceCompute=False):
        hasChunkToLaunch = False
        if not self._chunksCreated:
            hasChunkToLaunch = True
            # Same rationale as initStatusOnSubmit: clear stale chunk info
            # so that the nodeStatus file does not contain outdated chunk setup.
            self._nodeStatus.resetChunkInfo()
        for chunk in self.getAllChunks():
            if forceCompute or (chunk._status.status not in (Status.RUNNING, Status.SUCCESS)):
                hasChunkToLaunch = True
                chunk._status.setNode(self)
                chunk._status.initLocalSubmit()
                chunk.upgradeStatusFile()
        if hasChunkToLaunch:
            self._nodeStatus.setNode(self)
            self._nodeStatus.initLocalSubmit()
            self.upgradeStatusFile()
            self.globalStatusChanged.emit()
            if self._nodeStatus.execMode == ExecMode.LOCAL and self._nodeStatus.status in (Status.RUNNING, Status.SUBMITTED):
                chunkPlaceholder = NodeChunk(self, desc.computation.Range(), placeholder=True)
                chunkPlaceholder._status.execMode = self._nodeStatus.execMode
                chunkPlaceholder._status.status = self._nodeStatus.status
                self._chunkPlaceholder.setObjectList([chunkPlaceholder])
                self.chunksChanged.emit()
    
    def getChunkLogfileName(self, iteration: int):
        if iteration >= 0:
            stem = str(self.chunks[iteration].index)
        elif iteration == ChunkIndex.PREPROCESS:
            stem = "preprocess"
        elif iteration == ChunkIndex.POSTPROCESS:
            stem = "postprocess"
        else:
            stem = "0"
        logFileName = f"{stem}.log"
        return logFileName

    def processIteration(self, iteration):
        self._chunks[iteration].process()

    def preprocess(self, forceCompute=False, inCurrentEnv=False):
        """
        Invoke the pre process command on Client Node to execute before
        we start the processing on the node
        """
        if self.nodeDesc.hasPreprocess:
            if not self._preprocessChunk:
                raise RuntimeError("Trying to process preprocess chunk but it doesn't exist")
            self.prepareLogger(ChunkIndex.PREPROCESS)
            self._preprocessChunk.process(forceCompute, inCurrentEnv)
            self.restoreLogger()

    def process(self, forceCompute=False, inCurrentEnv=False):
        for chunk in self._chunks:
            chunk.process(forceCompute, inCurrentEnv)

    def postprocess(self, forceCompute=False, inCurrentEnv=False):
        """
        Invoke the post process command on Client Node to execute after 
        the processing on the node is completed
        """
        if self.nodeDesc.hasPostprocess:
            if not self._postprocessChunk:
                raise RuntimeError("Trying to process postprocess chunk but it doesn't exist")
            self.prepareLogger(ChunkIndex.POSTPROCESS)
            self._postprocessChunk.process(forceCompute, inCurrentEnv)
            self.restoreLogger()

    def getLogHandlers(self):
        return self._handlers

    def prepareLogger(self, iteration=ChunkIndex.NONE):
        # Get file handler path
        logFileName = self.getChunkLogfileName(iteration)
        logFile = os.path.join(self.internalFolder, logFileName)
        # Setup logger
        rootLogger = logging.getLogger()
        self._logManager = LogManager(rootLogger, logFile)
        self._logManager.clearLogFile()
        self._logManager.start(self.getNodeLogLevel())

    def restoreLogger(self):
        self._logManager.restorePreviousLogger()

    def updateOutputAttr(self):
        if not self.nodeDesc:
            return
        if not self.nodeDesc.hasDynamicOutputAttribute:
            return
        # logging.warning(f"updateOutputAttr: {self.name}, status: {self.globalStatus}")
        if Status.SUCCESS in [c._status.status for c in self.getChunks()]:
            self.loadOutputAttr()
        else:
            self.resetOutputAttr()

    def resetOutputAttr(self):
        if not self.nodeDesc.hasDynamicOutputAttribute:
            return
        # logging.warning("resetOutputAttr: {}".format(self.name))
        for output in self.nodeDesc.outputs:
            if output.isDynamicValue:
                if self.hasAttribute(output.name):
                    self.attribute(output.name).value = None
                else:
                    logging.warning(f"resetOutputAttr: Missing dynamic output attribute: {self.name}.{output.name}")

    def loadOutputAttr(self):
        """ Load output attributes with dynamic values from a values.json file.
        """

        # This does not apply to non dynamic output
        if not self.nodeDesc.hasDynamicOutputAttribute:
            return

        # Check existence of values.json file
        valuesFile = self.valuesFile
        if not os.path.exists(valuesFile):
            logging.warning(f"No output attr file: {valuesFile}")
            return

        # Open json file and parse
        with open(valuesFile) as jsonFile:
            data = json.load(jsonFile)

        # loop over all output attributes in the node description
        for output in self.nodeDesc.outputs:
            # Only consider dynamic values
            if output.isDynamicValue:
                if self.hasAttribute(output.name) and output.name in data:
                    attr = self.attribute(output.name)

                    # Use _populateFromDynamicValue for compatible classes
                    # (E.g. for ListAttributes) to properly
                    # create QObject children on the main thread
                    if hasattr(attr, '_populateFromDynamicValue'):
                        attr._populateFromDynamicValue(data[output.name])
                    else:
                        attr.value = data[output.name]
                else:
                    if not self.hasAttribute(output.name):
                        logging.warning(f"loadOutputAttr: Missing dynamic output attribute. Node={self.name}, "
                                        f"Attribute={output.name}")
                    if output.name not in data:
                        logging.warning(f"loadOutputAttr: Missing dynamic output value in file. Node={self.name}, "
                                        f"Attribute={output.name}, File={valuesFile}, Data keys={data.keys()}")

    def saveOutputAttr(self):
        """ Save output attributes with dynamic values into a values.json file.
        """
        if not self.nodeDesc.hasDynamicOutputAttribute:
            return
        data = {}
        for output in self.nodeDesc.outputs:
            if output.isDynamicValue:
                if self.hasAttribute(output.name):
                    # Store the primitive value and not the value itself
                    data[output.name] = self.attribute(output.name).getPrimitiveValue()
                else:
                    logging.warning(f"saveOutputAttr: Missing dynamic output attribute: {self.name}.{output.name}")

        valuesFile = self.valuesFile
        # logging.warning("save output attr: {}, value: {}".format(self.name, valuesFile))
        valuesFilepathWriting = getWritingFilepath(valuesFile)
        with open(valuesFilepathWriting, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)
        renameWritingToFinalPath(valuesFilepathWriting, valuesFile)

    def endSequence(self):
        pass

    def stopComputation(self):
        """ Stop the computation of this node. """
        if self.nodeDesc.hasPreprocess:
            if not self._preprocessChunk:
                logging.warning("No preprocess chunk to stop")
            self._preprocessChunk.stopProcess()
        if self.nodeDesc.hasPostprocess:
            if not self._postprocessChunk:
                logging.warning("No postprocess chunk to stop")
            self._postprocessChunk.stopProcess()
        if self._chunks:
            for chunk in self._chunks.values():
                chunk.stopProcess()
        else:
            # Ensure that we are up-to-date
            self.updateNodeStatusFromCache()
            # The only status possible here is submitted
            if self._nodeStatus.status is Status.SUBMITTED:
                self.upgradeStatusTo(Status.NONE)

    def getGlobalStatus(self):
        """
        Get node global status based on the status of its chunks.

        Returns:
            Status: the node global status
        """
        anyOf = (Status.ERROR, Status.STOPPED, Status.KILLED,
                 Status.RUNNING, Status.SUBMITTED)
        allOf = (Status.SUCCESS,)
        
        if self.isInputNode:
            return Status.INPUT
        if not self._chunksCreated:
            # If the preprocess chunk failed we might not reach the chunk creation part
            if self.nodeDesc.hasPreprocess and self._preprocessChunk._status.status in anyOf:
                return self._preprocessChunk._status.status
            # Get status from nodeStatus
            return self._nodeStatus.status
        allChunks = self.getAllChunks()
        if not allChunks:
            return Status.NONE

        chunksStatus = [chunk._status.status for chunk in allChunks]
        if len(chunksStatus) == 1:
            return chunksStatus[0]

        for status in anyOf:
            if any(s == status for s in chunksStatus):
                return status
        for status in allOf:
            if all(s == status for s in chunksStatus):
                return status

        return Status.NONE

    @Slot(result=ChunkStatusData)
    def getFusedStatus(self):
        allChunks = self.getAllChunks()
        if not allChunks:
            return ChunkStatusData()
        fusedStatus = ChunkStatusData()
        fusedStatus.fromDict(allChunks[0]._status.toDict())
        for chunk in allChunks[1:]:
            fusedStatus.merge(chunk._status)
        fusedStatus.status = self.getGlobalStatus()
        return fusedStatus

    @Slot(result=ChunkStatusData)
    def getRecursiveFusedStatus(self):
        fusedStatus = self.getFusedStatus()
        nodes = self.getInputNodes(recursive=True, dependenciesOnly=True)
        for node in nodes:
            fusedStatus.merge(node.fusedStatus)
        return fusedStatus

    def _isCompatibilityNode(self):
        return False

    def _isInputNode(self):
        return isinstance(self.nodeDesc, desc.InputNode)

    def _isInitNode(self):
        return isinstance(self.nodeDesc, desc.InitNode)

    def _isBackdropNode(self) -> bool:
        return False

    @property
    def globalExecMode(self):
        if not self._chunksCreated:
            return self._nodeStatus.execMode.name
        allChunks = self.getAllChunks()
        if len(allChunks):
            return allChunks[0].getExecModeName()
        else:
            return ExecMode.NONE

    def _getJobName(self):
        execMode = self._nodeStatus.execMode
        if execMode == ExecMode.LOCAL:
            return "LOCAL"
        elif execMode == ExecMode.EXTERN:
            return self._nodeStatus.jobName
        else:
            return "NONE"

    def getChunks(self) -> list[NodeChunk]:
        return self._chunks

    def getAllChunks(self) -> list[NodeChunk]:
        chunks = []
        if self.nodeDesc.hasPreprocess:
            chunks.append(self._preprocessChunk)
        chunks.extend([c for c in self._chunks])
        if self.nodeDesc.hasPostprocess:
            chunks.append(self._postprocessChunk)
        return chunks

    def getSize(self):
        return self._size

    def setSize(self, value):
        if self._size == value:
            return
        self._size = value
        self.sizeChanged.emit()

    def __repr__(self):
        return self.name

    def getLocked(self):
        return self._locked

    def setLocked(self, lock):
        if self._locked == lock:
            return
        self._locked = lock
        self.lockedChanged.emit()

    @Slot()
    def updateDuplicatesStatusAndLocked(self):
        """ Update status of duplicate nodes without any latency and update locked. """
        if self.isMainNode():
            for node in self._duplicates:
                node.updateStatusFromCache()

            self.updateLocked()

    def updateLocked(self):
        currentStatus = self.getGlobalStatus()

        lockedStatus = (Status.RUNNING, Status.SUBMITTED)

        # Unlock required nodes if the current node changes to Error, Stopped or None
        # Warning: we must handle some specific cases for global start/stop
        if self._locked and currentStatus in (Status.ERROR, Status.STOPPED, Status.NONE):
            self.setLocked(False)
            inputNodes = self.getInputNodes(recursive=True, dependenciesOnly=True)

            for node in inputNodes:
                if node.getGlobalStatus() == Status.RUNNING:
                    # Return without unlocking if at least one input node is running
                    # Example: using Cancel Computation on a submitted node
                    return
            for node in inputNodes:
                node.setLocked(False)
            return

        # Avoid useless travel through nodes
        # For instance: when loading a scene with successful nodes
        if not self._locked and currentStatus == Status.SUCCESS:
            return

        if currentStatus == Status.SUCCESS:
            # At this moment, the node is necessarily locked because of previous if statement
            inputNodes = self.getInputNodes(recursive=True, dependenciesOnly=True)
            outputNodes = self.getOutputNodes(recursive=True, dependenciesOnly=True)
            stayLocked = None

            # Check if at least one dependentNode is submitted or currently running
            for node in outputNodes:
                if node.getGlobalStatus() in lockedStatus and node.isMainNode():
                    stayLocked = True
                    break
            if not stayLocked:
                self.setLocked(False)
                # Unlock every input node
                for node in inputNodes:
                    node.setLocked(False)
            return
        elif currentStatus in lockedStatus and self.isMainNode():
            self.setLocked(True)
            inputNodes = self.getInputNodes(recursive=True, dependenciesOnly=True)
            for node in inputNodes:
                node.setLocked(True)
            return

        self.setLocked(False)

    def updateDuplicates(self, nodesPerUid):
        """ Update the list of duplicate nodes (sharing the same UID). """
        if not nodesPerUid or not self._uid:
            if len(self._duplicates) > 0:
                self._duplicates.clear()
                self._hasDuplicates = False
                self.hasDuplicatesChanged.emit()
            return

        newList = [node for node in nodesPerUid.get(self._uid) if node != self]

        # If number of elements in both lists are identical,
        # we must check if their content is the same
        if len(newList) == len(self._duplicates):
            newListName = {node.name for node in newList}
            oldListName = {node.name for node in self._duplicates.values()}

            # If strict equality between both sets,
            # there is no need to set the new list
            if newListName == oldListName:
                return

        # Set the newList
        self._duplicates.setObjectList(newList)
        # Emit a specific signal 'hasDuplicates' to avoid extra binding
        # re-evaluation when the number of duplicates has changed
        if bool(len(newList)) != self._hasDuplicates:
            self._hasDuplicates = bool(len(newList))
            self.hasDuplicatesChanged.emit()

    def initFromThisSession(self) -> bool:
        """ Check if the node was submitted from the current session """
        allChunks = self.getAllChunks()
        if not self._chunksCreated or not allChunks:
            return meshroom.core.sessionUid == self._nodeStatus.submitterSessionUid
        for chunk in allChunks:
            # Technically the check on chunk._status.computeSessionUid is useless
            if meshroom.core.sessionUid not in (chunk._status.computeSessionUid, self._nodeStatus.submitterSessionUid):
                return False
        return True

    def isMainNode(self) -> bool:
        """ In case of a node with duplicates, we check that the node is the one driving the computation. """
        allChunks = self.getAllChunks()
        if len(allChunks) == 0:
            return True
        firstChunk = allChunks[0]
        if not firstChunk.statusNodeName:
            # If nothing is declared, anyone could become the main (if there are duplicates).
            return True
        return firstChunk.statusNodeName == self.name

    @Slot(result=bool)
    def canBeStopped(self) -> bool:
        """
        Return True if this node can be stopped, False otherwise. A node can be stopped if:
        - it has the "RUNNING" status (it is currently being computed)
        - it is executed locally and started from this Meshroom session OR it is executed externally on a render farm
          (and is thus associated to a job name). A node that is executed externally but without an associated job is
          likely a node that was started from another Meshroom instance, and thus cannot be stopped from this one.
        """
        if not self.isComputableType:
            return False
        if self.isCompatibilityNode:
            return False
        # Only locked nodes running in local with the same
        # computeSessionUid as the Meshroom instance can be stopped
        return (self.getGlobalStatus() == Status.RUNNING and self.isMainNode() and
                (
                    (self.globalExecMode == ExecMode.LOCAL.name and self.initFromThisSession())
                    or
                    (self.globalExecMode == ExecMode.EXTERN.name and self._nodeStatus.jobName != "UNKNOWN")
                )
        )

    @Slot(result=bool)
    def canBeCanceled(self) -> bool:
        """
        Return True if this node can be canceled, False otherwise. A node can be canceled if:
        - it has the "SUBMITTED" status (it is not running yet, but is expected to be in the near future)
        - it is executed locally and started from this Meshroom session OR it is executed externally on a render farm
          (and is thus associated to a job name). A node that is executed externally but without an associated job is
          likely a node that was started from another Meshroom instance, and thus cannot be canceled from this one.
        """
        if not self.isComputableType:
            return False
        if self.isCompatibilityNode:
            return False
        # Only locked nodes submitted in local with the same
        # computeSessionUid as the Meshroom instance can be canceled
        return (self.getGlobalStatus() == Status.SUBMITTED and self.isMainNode() and
                (
                    (self.globalExecMode == ExecMode.LOCAL.name and self.initFromThisSession())
                    or
                    (self.globalExecMode == ExecMode.EXTERN.name and self._nodeStatus.jobName != "UNKNOWN")
                )
        )

    def hasImageOutputAttribute(self) -> bool:
        """
        Return True if at least one attribute has the 'image' semantic (and can thus be loaded in
        the 2D Viewer), False otherwise.
        """
        for attr in self._attributes:
            if not attr.enabled or not attr.isOutput:
                continue
            if attr.desc.semantic == "image":
                return True
        return False

    def hasSequenceOutputAttribute(self) -> bool:
        """
        Return True if at least one attribute has the 'sequence' semantic (and can thus be loaded in
        the 2D Viewer), False otherwise.
        """
        for attr in self._attributes:
            if not attr.enabled or not attr.isOutput:
                continue
            if attr.desc.semantic in ("sequence", "imageList"):
                return True
        return False

    def has3DOutputAttribute(self):
        """
        Return True if at least one attribute is a File that can be loaded in the 3D Viewer,
        False otherwise.
        """
        return next((attr for attr in self._attributes if attr.enabled and attr.isOutput and attr.is3dDisplayable), None) is not None

    def hasTextOutputAttribute(self) -> bool:
        """
        Return True if at least one attribute is a text file that can be loaded in the Text Viewer,
        False otherwise.
        """
        return next((attr for attr in self._attributes if attr.enabled and attr.isOutput and attr.isTextDisplayable), None) is not None

    def _hasInvalidAttribute(self):
        for attribute in self._attributes:
            if len(attribute.errorMessages) > 0:
                return True
        return False

    def _hasDisplayableShape(self):
        """
        Return True if at least one attribute is a ShapeAttribute, a ShapeListAttribute or a shape File.
        Note: These attributes can be loaded in the ShapeViewer / ShapeEditor.
        False otherwise.
        """
        return next((attr for attr in self._attributes if attr.hasDisplayableShape or
                     attr.desc.semantic == "shapeFile"), None) is not None


    nodeNameChanged = Signal()
    name = Property(str, getName, notify=nodeNameChanged)
    defaultLabel = Property(str, getDefaultLabel, constant=True)
    nodeType = Property(str, nodeType.fget, constant=True)
    documentation = Property(str, getDocumentation, constant=True)
    nodeInfo = Property(Variant, getNodeInfo, constant=True)
    nodeStatusChanged = Signal()
    nodeStatus = Property(Variant, lambda self: self._nodeStatus, notify=nodeStatusChanged)
    nodeStatusNodeName = Property(str, lambda self: self._nodeStatus.nodeName, notify=nodeStatusChanged)
    positionChanged = Signal()
    position = Property(Variant, position.fget, position.fset, notify=positionChanged)
    x = Property(float, lambda self: self._position.x, notify=positionChanged)
    y = Property(float, lambda self: self._position.y, notify=positionChanged)
    attributes = Property(BaseObject, getAttributes, constant=True)
    internalAttributes = Property(BaseObject, getInternalAttributes, constant=True)
    internalAttributesChanged = Signal()
    label = Property(str, getLabel, notify=internalAttributesChanged)
    color = Property(str, getColor, notify=internalAttributesChanged)
    invalidation = Property(str, getInvalidationMessage, notify=internalAttributesChanged)
    comment = Property(str, getComment, notify=internalAttributesChanged)
    fontSize = Property(int, getFontSize, notify=internalAttributesChanged)
    fontColor = Property(str, getFontColor, notify=internalAttributesChanged)
    nodeWidth = Property(int, getNodeWidth, notify=internalAttributesChanged)
    nodeHeight = Property(int, getNodeHeight, notify=internalAttributesChanged)
    internalFolderChanged = Signal()
    internalFolder = Property(str, internalFolder.fget, notify=internalFolderChanged)
    valuesFile = Property(str, valuesFile.fget, notify=internalFolderChanged)
    depthChanged = Signal()
    depth = Property(int, depth.fget, notify=depthChanged)
    minDepth = Property(int, minDepth.fget, notify=depthChanged)
    chunksCreatedChanged = Signal()
    chunksCreated = Property(bool, lambda self: self._chunksCreated, notify=chunksCreatedChanged)
    chunksChanged = Signal()
    chunks = Property(Variant, getChunks, notify=chunksChanged)
    allChunks = Property(Variant, getAllChunks, notify=chunksChanged)
    hasPreprocessChunk = Property(bool, lambda self: self.nodeDesc.hasPreprocess, notify=chunksChanged)
    preprocessChunk = Property(Variant, lambda self: self._preprocessChunk, notify=chunksChanged)
    hasPostprocessChunk = Property(bool, lambda self: self.nodeDesc.hasPostprocess, notify=chunksChanged)
    postprocessChunk = Property(Variant, lambda self: self._postprocessChunk, notify=chunksChanged)
    chunkPlaceholder = Property(Variant, lambda self: self._chunkPlaceholder, notify=chunksChanged)
    nbParallelizationBlocks = Property(int, lambda self: len(self._chunks) if self._chunksCreated else 0, notify=chunksChanged)
    sizeChanged = Signal()
    size = Property(int, getSize, notify=sizeChanged)
    globalStatusChanged = Signal()
    globalStatus = Property(str, lambda self: self.getGlobalStatus().name, notify=globalStatusChanged)
    fusedStatus = Property(ChunkStatusData, getFusedStatus, notify=globalStatusChanged)
    elapsedTime = Property(float, lambda self: self.getFusedStatus().elapsedTime, notify=globalStatusChanged)
    recursiveElapsedTime = Property(float, lambda self: self.getRecursiveFusedStatus().elapsedTime,
                                    notify=globalStatusChanged)
    isCompatibilityNode = Property(bool, lambda self: self._isCompatibilityNode(), constant=True)
    isInputNode = Property(bool, lambda self: self._isInputNode(), constant=True)
    isInitNode = Property(bool, lambda self: self._isInitNode(), constant=True)
    isBackdropNode = Property(bool, lambda self: self._isBackdropNode(), constant=True)

    globalExecMode = Property(str, globalExecMode.fget, notify=globalStatusChanged)
    jobName = Property(str, lambda self: self._getJobName(), notify=globalStatusChanged)
    isExternal = Property(bool, isExtern, notify=globalStatusChanged)
    isComputed = Property(bool, _isComputed, notify=globalStatusChanged)
    isComputableType = Property(bool, _isComputableType, notify=globalStatusChanged)
    aliveChanged = Signal()
    alive = Property(bool, alive.fget, alive.fset, notify=aliveChanged)
    lockedChanged = Signal()
    locked = Property(bool, getLocked, setLocked, notify=lockedChanged)
    duplicates = Property(Variant, lambda self: self._duplicates, constant=True)
    hasDuplicatesChanged = Signal()
    hasDuplicates = Property(bool, lambda self: self._hasDuplicates, notify=hasDuplicatesChanged)

    outputAttrChanged = Signal()
    hasImageOutput = Property(bool, hasImageOutputAttribute, notify=outputAttrChanged)
    hasSequenceOutput = Property(bool, hasSequenceOutputAttribute, notify=outputAttrChanged)
    has3DOutput = Property(bool, has3DOutputAttribute, notify=outputAttrChanged)
    hasTextOutput = Property(bool, hasTextOutputAttribute, notify=outputAttrChanged)
    # Whether the node contains a ShapeAttribute, a ShapeListAttribute or a shape File.
    hasDisplayableShape = Property(bool, _hasDisplayableShape, constant=True)

    hasInvalidAttributeChanged = Signal()
    hasInvalidAttribute = Property(bool, _hasInvalidAttribute, notify=hasInvalidAttributeChanged)


class Node(BaseNode):
    """
    A standard Graph node based on a node type.
    """
    def __init__(self, nodeType, position=None, parent=None, uid=None, **kwargs):
        super().__init__(nodeType, position, parent=parent, uid=uid, **kwargs)

        if not self.nodeDesc:
            raise UnknownNodeTypeError(nodeType)

        self.packageName = self.nodeDesc.packageName

        for attrDesc in self.nodeDesc.inputs:
            self._attributes.add(attributeFactory(attrDesc, kwargs.get(attrDesc.name, None),
                                                  isOutput=False, node=self))

        for attrDesc in self.nodeDesc.outputs:
            self._attributes.add(attributeFactory(attrDesc, kwargs.get(attrDesc.name, None),
                                                  isOutput=True, node=self))

        for attrDesc in self.nodeDesc.internalInputs:
            self._internalAttributes.add(attributeFactory(attrDesc, kwargs.get(attrDesc.name, None),
                                                          isOutput=False, node=self))

        # Declare events for specific output attributes
        for attr in self._attributes:
            if attr.isOutput and attr.desc.semantic == "image":
                attr.enabledChanged.connect(self.outputAttrChanged)
            if attr.isOutput:
                attr.expressionApplied.connect(self.outputAttrChanged)

        # List attributes per UID
        for attr in self._attributes:
            if attr.isInput and attr.invalidate:
                self.invalidatingAttributes.add(attr)

        # Add internal attributes with a UID to the list
        for attr in self._internalAttributes:
            if attr.invalidate:
                self.invalidatingAttributes.add(attr)

    def setAttributeValues(self, values):
        # initialize attribute values
        for k, v in values.items():
            if not self.hasAttribute(k):
                # skip missing attributes
                continue
            attr = self.attribute(k)
            attr.value = v

    def upgradeAttributeValues(self, values):
        # initialize attribute values
        for k, v in values.items():
            if not self.hasAttribute(k):
                # skip missing attributes
                continue
            attr = self.attribute(k)
            try:
                attr.upgradeValue(v)
            except ValueError:
                pass

    def setInternalAttributeValues(self, values):
        # initialize internal attribute values
        for k, v in values.items():
            if not self.hasInternalAttribute(k):
                # skip missing attributes
                continue
            attr = self.internalAttribute(k)
            attr.value = v

    def upgradeInternalAttributeValues(self, values):
        # initialize internal attibute values
        for k, v in values.items():
            if not self.hasInternalAttribute(k):
                # skip missing atributes
                continue
            attr = self.internalAttribute(k)
            try:
                attr.upgradeValue(v)
            except ValueError:
                pass

    def toDict(self):
        inputs = {k: v.getSerializedValue() for k, v in self._attributes.objects.items() if v.isInput}
        internalInputs = {k: v.getSerializedValue() for k, v in self._internalAttributes.objects.items()}
        outputs = ({k: v.getSerializedValue() for k, v in self._attributes.objects.items()
                    if v.isOutput and not v.desc.isDynamicValue})

        return {
            'nodeType': self.nodeType,
            'position': self._position,
            'parallelization': {
                'blockSize': self.nodeDesc.parallelization.blockSize if self.isParallelized else 0,
                'size': self.size,
                'split': self.nbParallelizationBlocks
            },
            'uid': self._uid,
            'inputs': {k: v for k, v in inputs.items() if v is not None},  # filter empty values
            'internalInputs': {k: v for k, v in internalInputs.items() if v is not None},
            'outputs': outputs,
        }

    def _resetChunks(self):
        """ Set chunks on the node.
        # TODO : Maybe do not delete chunks if we will recreate them as before ?
        """
        if not self.isComputableType:
            self._chunksCreated = True
            return
        for chunk in self._chunks:
            chunk.statusChanged.disconnect(self.globalStatusChanged)
        # Empty list
        self._chunks.setObjectList([])
        self._chunkPlaceholder.setObjectList([])
        # Reset node status to ensure getGlobalStatus() returns NONE during the reset.
        # This prevents updateLocked() from using a stale status (e.g. SUCCESS or SUBMITTED)
        # which could cause the node to be incorrectly locked.
        self._nodeStatus.status = Status.NONE
        # Clear stale chunk setup from nodeStatus so that updateStatusFromCache()
        # correctly detects when chunks need to be recreated from cache.
        # Without this, the stale _nodeStatus.chunks value would match the
        # freshly loaded value, causing chunkChanged to be False and skipping
        # createChunksFromCache() — leaving _chunksCreated = False.
        self._nodeStatus.resetChunkInfo()
        # Recreate list with reset values (1 chunk or the static size)
        if not self.isParallelized:
            self._chunks.setObjectList([NodeChunk(self, desc.Range())])
            self._chunks[0].statusChanged.connect(self.globalStatusChanged)
            self._chunksCreated = True
        elif isinstance(self.nodeDesc.size, desc.computation.StaticNodeSize):
            self._updateNodeSize()
            self._chunks.setObjectList([NodeChunk(self, desc.Range())])
            self._chunks[0].statusChanged.connect(self.globalStatusChanged)
            self._chunksCreated = True
            try:
                ranges = self.nodeDesc.parallelization.getRanges(self)
                self._chunks.setObjectList([NodeChunk(self, range) for range in ranges])
                for c in self._chunks:
                    c.statusChanged.connect(self.globalStatusChanged)
                logging.debug(f"Created {len(self._chunks)} chunks for node: {self.name}")
            except RuntimeError:
                # TODO: set node internal status to error
                logging.warning(f"Invalid Parallelization on node {self._name}")
                self._chunks.clear()
                self._chunksCreated = False
        else:
            self._chunksCreated = False
            self.setSize(0)
            self._chunkPlaceholder.setObjectList([NodeChunk(self, desc.computation.Range(), placeholder=True)])

        # Create chunks when possible
        self.chunksCreatedChanged.emit()
        self.chunksChanged.emit()
        self.globalStatusChanged.emit()

    def __createChunks(self, ranges):
        if self.isParallelized:
            try:
                if len(ranges) != len(self._chunks):
                    self._chunks.setObjectList([NodeChunk(self, range) for range in ranges])
                    for c in self._chunks:
                        c.statusChanged.connect(self.globalStatusChanged)
                    logging.debug(f"Created {len(self._chunks)} chunks for node: {self.name}")
                else:
                    for chunk, range in zip(self._chunks, ranges):
                        chunk.range = range
            except RuntimeError:
                # TODO: set node internal status to error
                logging.warning(f"Invalid Parallelization on node {self._name}")
                self._chunks.clear()
        else:
            if len(self._chunks) != 1:
                self._chunks.setObjectList([NodeChunk(self, desc.Range())])
                self._chunks[0].statusChanged.connect(self.globalStatusChanged)
            else:
                self._chunks[0].range = desc.Range()
        self._chunksCreated = True
        # Update node status
        # TODO: update all chunks status?
        # TODO: update node status?
        # Emit signals for UI updates
        self.chunksChanged.emit()
        self.chunksCreatedChanged.emit()

    def createChunksFromCache(self):
        """ Create chunks when a node cache exists. """
        try:
            # Get size from cache
            size = self._nodeStatus.fullSize
            self.setSize(size)
            ranges = self._nodeStatus.getChunkRanges()
            self.__createChunks(ranges)
        except Exception as e:
            logging.error(f"Failed to create chunks for {self.name}")
            self._chunks.clear()
            self._chunksCreated = False
            raise e

    def createChunks(self):
        """ Create chunks when computation is about to start. """
        if self._chunksCreated:
            return
        if self.isInputNode:
            self._chunksCreated = True
            self.chunksChanged.emit()
            return
        # Grab current chunk information
        logging.debug(f"Creating chunks for node: {self.name}")
        try:
            size = self.evaluateSize()
            self.setSize(size)
            ranges = self.nodeDesc.parallelization.getRanges(self)
            self.__createChunks(ranges)
        except Exception as e:
            logging.error(f"Failed to create chunks for {self.name}: {e}")
            self._chunks.clear()
            self._chunksCreated = False
            raise e
        # Update status
        self._nodeStatus.setChunks(self._chunks)
        self.upgradeStatusFile()


class BackdropNode(BaseNode):
    def __init__(self, nodeType: str, position=None, parent=None, uid=None, **kwargs):
        super().__init__(nodeType, position, parent=parent, uid=uid, **kwargs)

        self._chunksCreated = True

        if not self.nodeDesc:
            raise UnknownNodeTypeError(nodeType)

        self.packageName = self.nodeDesc.packageName

        for attrDesc in self.nodeDesc.internalInputs:
            self._internalAttributes.add(attributeFactory(attrDesc, kwargs.get(attrDesc.name, None),
                                                          isOutput=False, node=self))

    def _isBackdropNode(self) -> bool:
        return True

    def toDict(self):
        internalInputs = {k: v.getSerializedValue() for k, v in self._internalAttributes.objects.items()}

        return {
            'nodeType': self.nodeType,
            'position': self._position,
            'parallelization': {
                'blockSize': 0,
                'size': 0,
                'split': 0
            },
            'uid': self._uid,
            'internalInputs': {k: v for k, v in internalInputs.items() if v is not None},
        }


class CompatibilityIssue(Enum):
    """
    Enum describing compatibility issues when deserializing a Node.
    """
    UnknownIssue = 0  # unknown issue fallback
    UnknownNodeType = 1  # the node type has no corresponding description class
    VersionConflict = 2  # mismatch between node's description version and serialized node data
    DescriptionConflict = 3  # mismatch between node's description attributes and serialized node data
    UidConflict = 4  # mismatch between computed UIDs and UIDs stored in serialized node data
    PluginIssue = 5  # issue when loading the associated plugin


class CompatibilityNode(BaseNode):
    """
    Fallback BaseNode subclass to instantiate Nodes having compatibility issues with current type description.
    CompatibilityNode creates an 'empty-shell' exposing the deserialized node as-is,
    with all its inputs and precomputed outputs.
    """
    def __init__(self, nodeType, nodeDict, position=None, issue=CompatibilityIssue.UnknownIssue, parent=None):
        super().__init__(nodeType, position, parent)

        self.issue = issue
        # Make a deepcopy of nodeDict to handle CompatibilityNode duplication
        # and be able to change modified inputs (see CompatibilityNode.toDict)
        self.nodeDict = copy.deepcopy(nodeDict)
        version = self.nodeDict.get("version")
        self.version = Version(version) if version else None

        self._inputs = self.nodeDict.get("inputs", {})
        self._internalInputs = self.nodeDict.get("internalInputs", {})
        self.outputs = self.nodeDict.get("outputs", {})
        self._uid = self.nodeDict.get("uid", None)

        # Restore parallelization settings
        self.parallelization = self.nodeDict.get("parallelization", {})
        self.splitCount = self.parallelization.get("split", 1)
        self.setSize(self.parallelization.get("size", 1))

        # Create input attributes
        for attrName, value in self._inputs.items():
            self._addAttribute(attrName, value, isOutput=False)

        # Create outputs attributes
        for attrName, value in self.outputs.items():
            self._addAttribute(attrName, value, isOutput=True)

        # Create internal attributes
        for attrName, value in self._internalInputs.items():
            self._addAttribute(attrName, value, isOutput=False, internalAttr=True)

        # Create NodeChunks matching serialized parallelization settings
        self._chunks.setObjectList([
            NodeChunk(self, desc.Range(i, blockSize=self.parallelization.get("blockSize", 0)))
            for i in range(self.splitCount)
        ])

    def _isCompatibilityNode(self):
        return True

    def _updateNodeSize(self):
        # Block the recompute of the node size for compatibility nodes
        pass

    @staticmethod
    def attributeDescFromValue(attrName, value, isOutput):
        """
        Generate an attribute description (desc.Attribute) that best matches 'value'.

        Args:
            attrName (str): the name of the attribute
            value: the value of the attribute
            isOutput (bool): whether the attribute is an output

        Returns:
            desc.Attribute: the generated attribute description
        """
        params = {
            "name": attrName, "label": attrName,
            "description": "Incompatible parameter",
            "value": value, "invalidate": False,
            "commandLineGroup": "incompatible"
        }
        if isinstance(value, bool):
            return desc.BoolParam(**params)
        if isinstance(value, int):
            return desc.IntParam(range=None, **params)
        elif isinstance(value, float):
            return desc.FloatParam(range=None, **params)
        elif isinstance(value, str):
            if isOutput or os.path.isabs(value):
                return desc.File(**params)
            elif Attribute.isLinkExpression(value):
                # Do not consider link expression as a valid default desc value.
                # When the link expression is applied and transformed to an actual link,
                # the systems resets the value using `Attribute.resetToDefaultValue` to indicate
                # that this link expression has been handled.
                # If the link expression is stored as the default value, it will never be cleared,
                # leading to unexpected behavior where the link expression on a CompatibilityNode
                # could be evaluated several times and/or incorrectly.
                params["value"] = ""
                return desc.File(**params)
            else:
                return desc.StringParam(**params)
        # List/GroupAttribute: recursively build descriptions
        elif isinstance(value, (list, dict)):
            del params["value"]
            del params["invalidate"]
            attrDesc = None
            if isinstance(value, list):
                elt = value[0] if value else ""  # Fallback: empty string value if list is empty
                eltDesc = CompatibilityNode.attributeDescFromValue("element", elt, isOutput)
                attrDesc = desc.ListAttribute(elementDesc=eltDesc, **params)
            elif isinstance(value, dict):
                items = []
                for key, value in value.items():
                    eltDesc = CompatibilityNode.attributeDescFromValue(key, value, isOutput)
                    items.append(eltDesc)
                attrDesc = desc.GroupAttribute(items=items, **params)
            # Override empty default value with
            attrDesc._value = value
            return attrDesc
        # Handle any other type of parameters as Strings
        return desc.StringParam(**params)

    @staticmethod
    def attributeDescFromName(refAttributes, name, value, strict=True):
        """
        Try to find a matching attribute description in refAttributes for given attribute
        'name' and 'value'.

        Args:
            refAttributes ([desc.Attribute]): reference Attributes to look for a description
            name (str): attribute's name
            value: attribute's value
            strict: strict test for the match (for instance, regarding a group with some parameter changes)

        Returns:
            desc.Attribute: an attribute description from refAttributes if a match is found, None otherwise.
        """
        # from original node description based on attribute's name
        attrDesc = next((d for d in refAttributes if d.name == name), None)
        if attrDesc is None:
            return None
        # We have found a description, and we still need to
        # check if the value matches the attribute description.
        #
        # If it is a serialized link expression (no proper value to set/evaluate)
        if Attribute.isLinkExpression(value):
            return attrDesc

        # If it is a GroupAttribute, all the attributes within the group should be matched
        # individually so that links can correctly be evaluated.
        if isinstance(attrDesc, desc.GroupAttribute):
            for k, v in value.items():
                if CompatibilityNode.attributeDescFromName(attrDesc.items,
                                                           k, v, strict=True) is None:
                    return None
            return attrDesc

        # If it passes the 'matchDescription' test
        if attrDesc.matchDescription(value, strict):
            return attrDesc

        return None

    def _addAttribute(self, name, val, isOutput, internalAttr=False):
        """
        Add a new attribute on this node.

        Args:
            name (str): the name of the attribute
            val: the attribute's value
            isOutput: whether the attribute is an output
            internalAttr: whether the attribute is internal

        Returns:
            bool: whether the attribute exists in the node description
        """
        attrDesc = None
        if self.nodeDesc:
            if internalAttr:
                refAttrs = self.nodeDesc.internalInputs
            else:
                refAttrs = self.nodeDesc.outputs if isOutput else self.nodeDesc.inputs
            attrDesc = CompatibilityNode.attributeDescFromName(refAttrs, name, val)
        matchDesc = attrDesc is not None
        if attrDesc is None:
            attrDesc = CompatibilityNode.attributeDescFromValue(name, val, isOutput)
        attribute = attributeFactory(attrDesc, val, isOutput, self)
        if internalAttr:
            self._internalAttributes.add(attribute)
        else:
            self._attributes.add(attribute)
        return matchDesc

    @property
    def issueDetails(self):
        if self.issue == CompatibilityIssue.UnknownNodeType:
            return f"Unknown node type: '{self.nodeType}'."
        elif self.issue == CompatibilityIssue.VersionConflict:
            version = self.nodeDict["version"]
            return f"Node version '{version}' conflicts with current version '{nodeVersion(self.nodeDesc)}'."
        elif self.issue == CompatibilityIssue.DescriptionConflict:
            return "Node attributes do not match node description."
        elif self.issue == CompatibilityIssue.UidConflict:
            return "Node UID differs from the expected one."
        else:
            return "Unknown error."

    @property
    def inputs(self):
        """ Get current node inputs, where links could differ from original serialized node data
        (i.e after node duplication) """
        # if node has not been added to a graph, return serialized node inputs
        if not self.graph:
            return self._inputs
        return {k: v.getSerializedValue() for k, v in self._attributes.objects.items() if v.isInput}

    @property
    def internalInputs(self):
        """ Get current node's internal attributes """
        if not self.graph:
            return self._internalInputs
        return {k: v.getSerializedValue() for k, v in self._internalAttributes.objects.items()}

    def toDict(self):
        """
        Return the original serialized node that generated a compatibility issue.

        Serialized inputs are updated to handle instances that have been duplicated
        and might be connected to different nodes.
        """
        # update inputs to get up-to-date connections
        self.nodeDict.update({"inputs": self.inputs})
        # update position
        self.nodeDict.update({"position": self.position})
        return self.nodeDict

    @property
    def canUpgrade(self):
        """ Return whether the node can be upgraded.
        This is the case when the underlying node type has a corresponding description. """
        return self.nodeDesc is not None

    def upgrade(self):
        """
        Return a new Node instance based on original node type with common inputs initialized.
        """
        if not self.canUpgrade:
            raise NodeUpgradeError(self.name, "No matching node type")

        # inputs matching current type description
        commonInputs = []
        for attrName, value in self._inputs.items():
            if self.attributeDescFromName(self.nodeDesc.inputs, attrName, value, strict=False):
                # store attributes that could be used during node upgrade
                commonInputs.append(attrName)

        commonInternalAttributes = []
        for attrName, value in self._internalInputs.items():
            if self.attributeDescFromName(self.nodeDesc.internalInputs, attrName, value, strict=False):
                # store internal attributes that could be used during node upgrade
                commonInternalAttributes.append(attrName)

        node = Node(self.nodeType, position=self.position)
        # convert attributes from a list of tuples into a dict
        attrValues = {key: value for (key, value) in self.inputs.items()}
        intAttrValues = {key: value for (key, value) in self.internalInputs.items()}

        # Use upgrade method of the node description itself if available
        try:
            upgradedAttrValues = node.nodeDesc.upgradeAttributeValues(attrValues, self.version)
        except Exception as exc:
            logging.error(f"Error in the upgrade implementation of the node: {self.name}.\n{repr(exc)}")
            upgradedAttrValues = attrValues

        if not isinstance(upgradedAttrValues, dict):
            logging.error(f"Error in the upgrade implementation of the node: {self.name}. The return type is incorrect.")
            upgradedAttrValues = attrValues

        node.upgradeAttributeValues(upgradedAttrValues)

        node.upgradeInternalAttributeValues(intAttrValues)

        return node

    compatibilityIssue = Property(int, lambda self: self.issue.value, constant=True)
    canUpgrade = Property(bool, canUpgrade.fget, constant=True)
    issueDetails = Property(str, issueDetails.fget, constant=True)
