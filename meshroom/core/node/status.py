#!/usr/bin/env python

import datetime
import json
import logging
import os
import platform
import time
import uuid
from collections import namedtuple
from enum import Enum, IntEnum, auto
from typing import Optional

import meshroom
from meshroom.common import Property, BaseObject
from meshroom.core import desc, MrNodeType


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
    INIT = 7  # Special status for init nodes


class ExecMode(Enum):
    """
    """
    NONE = auto()
    LOCAL = auto()
    EXTERN = auto()


class ChunkIndex(IntEnum):
    NONE = -3
    PREPROCESS = -2
    POSTPROCESS = -1
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
        d = {key: getattr(self, key, 0) for key in keys}
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
        if self._startTime is not None:
            self.elapsedTime = time.time() - self._startTime

    @property
    def elapsedTimeStr(self):
        return str(datetime.timedelta(seconds=self.elapsedTime))

    def toDict(self):
        keys = list(self.__slots__) or []
        d = {key: getattr(self, key) for key in keys}
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
