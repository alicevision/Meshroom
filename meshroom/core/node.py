#!/usr/bin/env python
# coding:utf-8
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
from collections import defaultdict, namedtuple
from enum import Enum

import meshroom
from meshroom.common import Signal, Variant, Property, BaseObject, Slot, ListModel, DictModel
from meshroom.core import desc, stats, hashValue, pyCompatibility, nodeVersion, Version
from meshroom.core.attribute import attributeFactory, ListAttribute, GroupAttribute, Attribute
from meshroom.core.exception import NodeUpgradeError, UnknownNodeTypeError


def getWritingFilepath(filepath):
    return filepath + '.writing.' + str(uuid.uuid4())


def renameWritingToFinalPath(writingFilepath, filepath):
    if platform.system() == 'Windows':
        # On Windows, attempting to remove a file that is in use causes an exception to be raised.
        # So we may need multiple trials, if someone is reading it at the same time.
        for i in range(20):
            try:
                os.remove(filepath)
                # if remove is successful, we can stop the iterations
                break
            except WindowsError:
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


class ExecMode(Enum):
    NONE = 0
    LOCAL = 1
    EXTERN = 2


class StatusData:
    """
    """
    dateTimeFormatting = '%Y-%m-%d %H:%M:%S.%f'

    def __init__(self, nodeName, nodeType, packageName, packageVersion):
        self.status = Status.NONE
        self.execMode = ExecMode.NONE
        self.nodeName = nodeName
        self.nodeType = nodeType
        self.packageName = packageName
        self.packageVersion = packageVersion
        self.graph = ''
        self.commandLine = None
        self.env = None
        self.startDateTime = ""
        self.endDateTime = ""
        self.elapsedTime = 0
        self.hostname = ""
        self.sessionUid = meshroom.core.sessionUid

    def reset(self):
        self.status = Status.NONE
        self.execMode = ExecMode.NONE
        self.graph = ''
        self.commandLine = None
        self.env = None
        self.startDateTime = ""
        self.endDateTime = ""
        self.elapsedTime = 0
        self.hostname = ""
        self.sessionUid = meshroom.core.sessionUid

    def initStartCompute(self):
        import platform
        self.sessionUid = meshroom.core.sessionUid
        self.hostname = platform.node()
        self.startDateTime = datetime.datetime.now().strftime(self.dateTimeFormatting)
        # to get datetime obj: datetime.datetime.strptime(obj, self.dateTimeFormatting)

    def initEndCompute(self):
        self.sessionUid = meshroom.core.sessionUid
        self.endDateTime = datetime.datetime.now().strftime(self.dateTimeFormatting)

    @property
    def elapsedTimeStr(self):
        return str(datetime.timedelta(seconds=self.elapsedTime))

    def toDict(self):
        d = self.__dict__.copy()
        d["elapsedTimeStr"] = self.elapsedTimeStr
        return d

    def fromDict(self, d):
        self.status = getattr(Status, d.get('status', ''), Status.NONE)
        self.execMode = getattr(ExecMode, d.get('execMode', ''), ExecMode.NONE)
        self.nodeName = d.get('nodeName', '')
        self.nodeType = d.get('nodeType', '')
        self.packageName = d.get('packageName', '')
        self.packageVersion = d.get('packageVersion', '')
        self.graph = d.get('graph', '')
        self.commandLine = d.get('commandLine', '')
        self.env = d.get('env', '')
        self.startDateTime = d.get('startDateTime', '')
        self.endDateTime = d.get('endDateTime', '')
        self.elapsedTime = d.get('elapsedTime', 0)
        self.hostname = d.get('hostname', '')
        self.sessionUid = d.get('sessionUid', '')


class LogManager:
    dateTimeFormatting = '%H:%M:%S'

    def __init__(self, chunk):
        self.chunk = chunk
        self.logger = logging.getLogger(chunk.node.getName())

    class Formatter(logging.Formatter):
        def format(self, record):
            # Make level name lower case
            record.levelname = record.levelname.lower()
            return logging.Formatter.format(self, record)

    def configureLogger(self):
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        handler = logging.FileHandler(self.chunk.logFile)
        formatter = self.Formatter('[%(asctime)s.%(msecs)03d][%(levelname)s] %(message)s', self.dateTimeFormatting)
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def start(self, level):
        # Clear log file
        open(self.chunk.logFile, 'w').close()
        
        self.configureLogger()
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
        
        with open(self.chunk.logFile, 'a') as f:
            if message:
                f.write(message+'\n')
            f.write('0%   10   20   30   40   50   60   70   80   90   100%\n')
            f.write('|----|----|----|----|----|----|----|----|----|----|\n\n')
            
            f.close()
            
        with open(self.chunk.logFile, 'r') as f:
            content = f.read()
            self.progressBarPosition = content.rfind('\n')
            
            f.close()

    def updateProgressBar(self, value):
        assert self.progressBar
        assert value <= self.progressEnd

        tics = round((value/self.progressEnd)*51)

        with open(self.chunk.logFile, 'r+') as f:
            text = f.read()
            for i in range(tics-self.currentProgressTics):
                text = text[:self.progressBarPosition]+'*'+text[self.progressBarPosition:]
            f.seek(0)
            f.write(text)
            f.close()

        self.currentProgressTics = tics

    def completeProgressBar(self):
        assert self.progressBar

        self.progressBar = False

    def textToLevel(self, text):
        if text == 'critical': return logging.CRITICAL
        elif text == 'error': return logging.ERROR
        elif text == 'warning': return logging.WARNING
        elif text == 'info': return logging.INFO
        elif text == 'debug': return logging.DEBUG
        else: return logging.NOTSET


runningProcesses = {}


@atexit.register
def clearProcessesStatus():
    global runningProcesses
    for k, v in runningProcesses.items():
        v.upgradeStatusTo(Status.KILLED)


class NodeChunk(BaseObject):
    def __init__(self, node, range, parent=None):
        super(NodeChunk, self).__init__(parent)
        self.node = node
        self.range = range
        self.logManager = LogManager(self)
        self.status = StatusData(node.name, node.nodeType, node.packageName, node.packageVersion)
        self.statistics = stats.Statistics()
        self.statusFileLastModTime = -1
        self._subprocess = None
        # notify update in filepaths when node's internal folder changes
        self.node.internalFolderChanged.connect(self.nodeFolderChanged)

    @property
    def index(self):
        return self.range.iteration

    @property
    def name(self):
        if self.range.blockSize:
            return "{}({})".format(self.node.name, self.index)
        else:
            return self.node.name

    @property
    def statusName(self):
        return self.status.status.name

    @property
    def logger(self):
        return self.logManager.logger

    @property
    def execModeName(self):
        return self.status.execMode.name

    def updateStatusFromCache(self):
        """
        Update node status based on status file content/existence.
        """
        statusFile = self.statusFile
        oldStatus = self.status.status
        # No status file => reset status to Status.None
        if not os.path.exists(statusFile):
            self.statusFileLastModTime = -1
            self.status.reset()
        else:
            with open(statusFile, 'r') as jsonFile:
                statusData = json.load(jsonFile)
            self.status.fromDict(statusData)
            self.statusFileLastModTime = os.path.getmtime(statusFile)
        if oldStatus != self.status.status:
            self.statusChanged.emit()

    @property
    def statusFile(self):
        if self.range.blockSize == 0:
            return os.path.join(self.node.graph.cacheDir, self.node.internalFolder, 'status')
        else:
            return os.path.join(self.node.graph.cacheDir, self.node.internalFolder, str(self.index) + '.status')

    @property
    def statisticsFile(self):
        if self.range.blockSize == 0:
            return os.path.join(self.node.graph.cacheDir, self.node.internalFolder, 'statistics')
        else:
            return os.path.join(self.node.graph.cacheDir, self.node.internalFolder, str(self.index) + '.statistics')

    @property
    def logFile(self):
        if self.range.blockSize == 0:
            return os.path.join(self.node.graph.cacheDir, self.node.internalFolder, 'log')
        else:
            return os.path.join(self.node.graph.cacheDir, self.node.internalFolder, str(self.index) + '.log')

    def saveStatusFile(self):
        """
        Write node status on disk.
        """
        data = self.status.toDict()
        statusFilepath = self.statusFile
        folder = os.path.dirname(statusFilepath)
        if not os.path.exists(folder):
            os.makedirs(folder)
        statusFilepathWriting = getWritingFilepath(statusFilepath)
        with open(statusFilepathWriting, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)
        renameWritingToFinalPath(statusFilepathWriting, statusFilepath)

    def upgradeStatusTo(self, newStatus, execMode=None):
        if newStatus.value <= self.status.status.value:
            print('WARNING: downgrade status on node "{}" from {} to {}'.format(self.name, self.status.status,
                                                                                newStatus))
        if execMode is not None:
            self.status.execMode = execMode
            self.execModeNameChanged.emit()
        self.status.status = newStatus
        self.saveStatusFile()
        self.statusChanged.emit()

    def updateStatisticsFromCache(self):
        """
        """
        oldTimes = self.statistics.times
        statisticsFile = self.statisticsFile
        if not os.path.exists(statisticsFile):
            return
        with open(statisticsFile, 'r') as jsonFile:
            statisticsData = json.load(jsonFile)
        self.statistics.fromDict(statisticsData)
        if oldTimes != self.statistics.times:
            self.statisticsChanged.emit()

    def saveStatistics(self):
        data = self.statistics.toDict()
        statisticsFilepath = self.statisticsFile
        folder = os.path.dirname(statisticsFilepath)
        if not os.path.exists(folder):
            os.makedirs(folder)
        statisticsFilepathWriting = getWritingFilepath(statisticsFilepath)
        with open(statisticsFilepathWriting, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)
        renameWritingToFinalPath(statisticsFilepathWriting, statisticsFilepath)

    def isAlreadySubmitted(self):
        return self.status.status in (Status.SUBMITTED, Status.RUNNING)

    def process(self, forceCompute=False):
        if not forceCompute and self.status.status == Status.SUCCESS:
            print("Node chunk already computed:", self.name)
            return
        global runningProcesses
        runningProcesses[self.name] = self
        self.status.initStartCompute()
        startTime = time.time()
        self.upgradeStatusTo(Status.RUNNING)
        self.statThread = stats.StatisticsThread(self)
        self.statThread.start()
        try:
            self.node.nodeDesc.processChunk(self)
        except Exception as e:
            self.upgradeStatusTo(Status.ERROR)
            raise
        except (KeyboardInterrupt, SystemError, GeneratorExit) as e:
            self.upgradeStatusTo(Status.STOPPED)
            raise
        finally:
            self.status.initEndCompute()
            self.status.elapsedTime = time.time() - startTime
            print(' - elapsed time:', self.status.elapsedTimeStr)
            # ask and wait for the stats thread to stop
            self.statThread.stopRequest()
            self.statThread.join()
            self.statistics = stats.Statistics()
            del runningProcesses[self.name]

        self.upgradeStatusTo(Status.SUCCESS)

    def stopProcess(self):
        self.node.nodeDesc.stopProcess(self)

    statusChanged = Signal()
    statusName = Property(str, statusName.fget, notify=statusChanged)
    execModeNameChanged = Signal()
    execModeName = Property(str, execModeName.fget, notify=execModeNameChanged)
    statisticsChanged = Signal()

    nodeFolderChanged = Signal()
    statusFile = Property(str, statusFile.fget, notify=nodeFolderChanged)
    logFile = Property(str, logFile.fget, notify=nodeFolderChanged)
    statisticsFile = Property(str, statisticsFile.fget, notify=nodeFolderChanged)


# simple structure for storing node position
Position = namedtuple("Position", ["x", "y"])
# initialize default coordinates values to 0
Position.__new__.__defaults__ = (0,) * len(Position._fields)


class BaseNode(BaseObject):
    """
    Base Abstract class for Graph nodes.
    """

    # Regexp handling complex attribute names with recursive understanding of Lists and Groups
    # i.e: a.b, a[0], a[0].b.c[1]
    attributeRE = re.compile(r'\.?(?P<name>\w+)(?:\[(?P<index>\d+)\])?')

    def __init__(self, nodeType, position=None, parent=None, **kwargs):
        """
        Create a new Node instance based on the given node description.
        Any other keyword argument will be used to initialize this node's attributes.

        Args:
            nodeDesc (desc.Node): the node description for this node
            parent (BaseObject): this Node's parent
            **kwargs: attributes values
        """
        super(BaseNode, self).__init__(parent)
        self._nodeType = nodeType
        self.nodeDesc = None

        # instantiate node description if nodeType is valid
        if nodeType in meshroom.core.nodesDesc:
            self.nodeDesc = meshroom.core.nodesDesc[nodeType]()

        self.packageName = self.packageVersion = ""
        self._internalFolder = ""

        self._name = None
        self.graph = None
        self.dirty = True  # whether this node's outputs must be re-evaluated on next Graph update
        self._chunks = ListModel(parent=self)
        self._uids = dict()
        self._cmdVars = {}
        self._size = 0
        self._position = position or Position()
        self._attributes = DictModel(keyAttrName='name', parent=self)
        self.attributesPerUid = defaultdict(set)

    def __getattr__(self, k):
        try:
            # Throws exception if not in prototype chain
            # return object.__getattribute__(self, k) # doesn't work in python2
            return object.__getattr__(self, k)
        except AttributeError as e:
            try:
                return self.attribute(k)
            except KeyError:
                raise e

    def getName(self):
        return self._name

    def getLabel(self):
        """
        Returns:
            str: the high-level label of this node
        """
        t, idx = self._name.split("_")
        return "{}{}".format(t, idx if int(idx) > 1 else "")

    @property
    def packageFullName(self):
        return '-'.join([self.packageName, self.packageVersion])

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
            att = self._attributes.get(name)
        return att

    def getAttributes(self):
        return self._attributes

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
    def depth(self):
        return self.graph.getDepth(self)

    @property
    def minDepth(self):
        return self.graph.getDepth(self, minimal=True)

    def toDict(self):
        pass

    def _computeUids(self):
        """ Compute node uids by combining associated attributes' uids. """
        for uidIndex, associatedAttributes in self.attributesPerUid.items():
            # uid is computed by hashing the sorted list of tuple (name, value) of all attributes impacting this uid
            uidAttributes = [(a.getName(), a.uid(uidIndex)) for a in associatedAttributes]
            uidAttributes.sort()
            self._uids[uidIndex] = hashValue(uidAttributes)

    def _buildCmdVars(self):
        """ Generate command variables using input attributes and resolved output attributes names and values. """
        for uidIndex, value in self._uids.items():
            self._cmdVars['uid{}'.format(uidIndex)] = value

        # Evaluate input params
        for name, attr in self._attributes.objects.items():
            if attr.isOutput:
                continue  # skip outputs
            v = attr.getValueStr()

            self._cmdVars[name] = '--{name} {value}'.format(name=name, value=v)
            self._cmdVars[name + 'Value'] = str(v)

            if v:
                self._cmdVars[attr.attributeDesc.group] = self._cmdVars.get(attr.attributeDesc.group, '') + \
                                                          ' ' + self._cmdVars[name]

        # For updating output attributes invalidation values
        cmdVarsNoCache = self._cmdVars.copy()
        cmdVarsNoCache['cache'] = ''

        # Evaluate output params
        for name, attr in self._attributes.objects.items():
            if attr.isInput:
                continue  # skip inputs

            # Only consider File attributes for command output parameters
            if not isinstance(attr.attributeDesc, desc.File):
                continue

            attr.value = attr.attributeDesc.value.format(**self._cmdVars)
            attr._invalidationValue = attr.attributeDesc.value.format(**cmdVarsNoCache)
            v = attr.getValueStr()

            self._cmdVars[name] = '--{name} {value}'.format(name=name, value=v)
            self._cmdVars[name + 'Value'] = str(v)

            if v:
                self._cmdVars[attr.attributeDesc.group] = self._cmdVars.get(attr.attributeDesc.group, '') + \
                                                          ' ' + self._cmdVars[name]

    @property
    def isParallelized(self):
        return bool(self.nodeDesc.parallelization) if meshroom.useMultiChunks else False

    @property
    def nbParallelizationBlocks(self):
        return len(self._chunks)

    def hasStatus(self, status):
        if not self._chunks:
            return False
        for chunk in self._chunks:
            if chunk.status.status != status:
                return False
        return True

    @Slot(result=bool)
    def isComputed(self):
        return self.hasStatus(Status.SUCCESS)

    @Slot()
    def clearData(self):
        """ Delete this Node internal folder.
        Status will be reset to Status.NONE
        """
        if self.internalFolder and os.path.exists(self.internalFolder):
            shutil.rmtree(self.internalFolder)
            self.updateStatusFromCache()

    def isAlreadySubmitted(self):
        for chunk in self._chunks:
            if chunk.isAlreadySubmitted():
                return True
        return False

    def alreadySubmittedChunks(self):
        return [ch for ch in self._chunks if ch.isAlreadySubmitted()]

    @Slot()
    def clearSubmittedChunks(self):
        """ Reset all submitted chunks to Status.NONE. This method should be used to clear inconsistent status
        if a computation failed without informing the graph.

        Warnings:
            This must be used with caution. This could lead to inconsistent node status
            if the graph is still being computed.
        """
        for chunk in self.alreadySubmittedChunks():
            chunk.upgradeStatusTo(Status.NONE, ExecMode.NONE)

    def upgradeStatusTo(self, newStatus):
        """
        Upgrade node to the given status and save it on disk.
        """
        for chunk in self._chunks:
            chunk.upgradeStatusTo(newStatus)

    def updateStatisticsFromCache(self):
        for chunk in self._chunks:
            chunk.updateStatisticsFromCache()

    def _updateChunks(self):
        pass

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
        # Update chunks splitting
        self._updateChunks()
        # Retrieve current internal folder (if possible)
        try:
            folder = self.internalFolder
        except KeyError:
            folder = ''
        # Update command variables / output attributes
        self._cmdVars = {
            'cache': cacheDir or self.graph.cacheDir,
            'nodeType': self.nodeType,
        }
        self._computeUids()
        self._buildCmdVars()
        if self.nodeDesc:
            self.nodeDesc.postUpdate(self)
        # Notify internal folder change if needed
        if self.internalFolder != folder:
            self.internalFolderChanged.emit()

    @property
    def internalFolder(self):
        return self._internalFolder.format(**self._cmdVars)

    def updateStatusFromCache(self):
        """
        Update node status based on status file content/existence.
        """
        for chunk in self._chunks:
            chunk.updateStatusFromCache()

    def submit(self, forceCompute=False):
        for chunk in self._chunks:
            if forceCompute or chunk.status.status != Status.SUCCESS:
                chunk.upgradeStatusTo(Status.SUBMITTED, ExecMode.EXTERN)

    def beginSequence(self, forceCompute=False):
        for chunk in self._chunks:
            if forceCompute or chunk.status.status != Status.SUCCESS:
                chunk.upgradeStatusTo(Status.SUBMITTED, ExecMode.LOCAL)

    def processIteration(self, iteration):
        self._chunks[iteration].process()

    def process(self, forceCompute=False):
        for chunk in self._chunks:
            chunk.process(forceCompute)

    def endSequence(self):
        pass

    def getGlobalStatus(self):
        """
        Get node global status based on the status of its chunks.

        Returns:
            Status: the node global status
        """
        chunksStatus = [chunk.status.status for chunk in self._chunks]

        anyOf = (Status.ERROR, Status.STOPPED, Status.KILLED,
                 Status.RUNNING, Status.SUBMITTED)
        allOf = (Status.SUCCESS,)

        for status in anyOf:
            if any(s == status for s in chunksStatus):
                return status
        for status in allOf:
            if all(s == status for s in chunksStatus):
                return status

        return Status.NONE

    def getChunks(self):
        return self._chunks

    def getSize(self):
        return self._size

    def setSize(self, value):
        if self._size == value:
            return
        self._size = value
        self.sizeChanged.emit()

    def __repr__(self):
        return self.name

    name = Property(str, getName, constant=True)
    label = Property(str, getLabel, constant=True)
    nodeType = Property(str, nodeType.fget, constant=True)
    positionChanged = Signal()
    position = Property(Variant, position.fget, position.fset, notify=positionChanged)
    x = Property(float, lambda self: self._position.x, notify=positionChanged)
    y = Property(float, lambda self: self._position.y, notify=positionChanged)
    attributes = Property(BaseObject, getAttributes, constant=True)
    internalFolderChanged = Signal()
    internalFolder = Property(str, internalFolder.fget, notify=internalFolderChanged)
    depthChanged = Signal()
    depth = Property(int, depth.fget, notify=depthChanged)
    minDepth = Property(int, minDepth.fget, notify=depthChanged)
    chunksChanged = Signal()
    chunks = Property(Variant, getChunks, notify=chunksChanged)
    sizeChanged = Signal()
    size = Property(int, getSize, notify=sizeChanged)
    globalStatusChanged = Signal()
    globalStatus = Property(str, lambda self: self.getGlobalStatus().name, notify=globalStatusChanged)


class Node(BaseNode):
    """
    A standard Graph node based on a node type.
    """
    def __init__(self, nodeType, position=None, parent=None, **kwargs):
        super(Node, self).__init__(nodeType, position, parent, **kwargs)

        if not self.nodeDesc:
            raise UnknownNodeTypeError(nodeType)

        self.packageName = self.nodeDesc.packageName
        self.packageVersion = self.nodeDesc.packageVersion
        self._internalFolder = self.nodeDesc.internalFolder

        for attrDesc in self.nodeDesc.inputs:
            self._attributes.add(attributeFactory(attrDesc, None, False, self))

        for attrDesc in self.nodeDesc.outputs:
            self._attributes.add(attributeFactory(attrDesc, None, True, self))

        # List attributes per uid
        for attr in self._attributes:
            for uidIndex in attr.attributeDesc.uid:
                self.attributesPerUid[uidIndex].add(attr)

        # initialize attribute values
        for k, v in kwargs.items():
            attr = self.attribute(k)
            if attr.isInput:
                self.attribute(k).value = v

    def toDict(self):
        inputs = {k: v.getExportValue() for k, v in self._attributes.objects.items() if v.isInput}
        outputs = ({k: v.getExportValue() for k, v in self._attributes.objects.items() if v.isOutput})

        return {
            'nodeType': self.nodeType,
            'position': self._position,
            'parallelization': {
                'blockSize': self.nodeDesc.parallelization.blockSize if self.isParallelized else 0,
                'size': self.size,
                'split': self.nbParallelizationBlocks
            },
            'uids': self._uids,
            'internalFolder': self._internalFolder,
            'inputs': {k: v for k, v in inputs.items() if v is not None},  # filter empty values
            'outputs': outputs,
        }

    def _updateChunks(self):
        """ Update Node's computation task splitting into NodeChunks based on its description """
        self.setSize(self.nodeDesc.size.computeSize(self))
        if self.isParallelized:
            try:
                ranges = self.nodeDesc.parallelization.getRanges(self)
                if len(ranges) != len(self._chunks):
                    self._chunks.setObjectList([NodeChunk(self, range) for range in ranges])
                    for c in self._chunks:
                        c.statusChanged.connect(self.globalStatusChanged)
                else:
                    for chunk, range in zip(self._chunks, ranges):
                        chunk.range = range
            except RuntimeError:
                # TODO: set node internal status to error
                logging.warning("Invalid Parallelization on node {}".format(self._name))
                self._chunks.clear()
        else:
            if len(self._chunks) != 1:
                self._chunks.setObjectList([NodeChunk(self, desc.Range())])
                self._chunks[0].statusChanged.connect(self.globalStatusChanged)
            else:
                self._chunks[0].range = desc.Range()


class CompatibilityIssue(Enum):
    """
    Enum describing compatibility issues when deserializing a Node.
    """
    UnknownIssue = 0  # unknown issue fallback
    UnknownNodeType = 1  # the node type has no corresponding description class
    VersionConflict = 2  # mismatch between node's description version and serialized node data
    DescriptionConflict = 3  # mismatch between node's description attributes and serialized node data
    UidConflict = 4  # mismatch between computed uids and uids stored in serialized node data


class CompatibilityNode(BaseNode):
    """
    Fallback BaseNode subclass to instantiate Nodes having compatibility issues with current type description.
    CompatibilityNode creates an 'empty-shell' exposing the deserialized node as-is,
    with all its inputs and precomputed outputs.
    """
    def __init__(self, nodeType, nodeDict, position=None, issue=CompatibilityIssue.UnknownIssue, parent=None):
        super(CompatibilityNode, self).__init__(nodeType, position, parent)

        self.issue = issue
        # make a deepcopy of nodeDict to handle CompatibilityNode duplication
        # and be able to change modified inputs (see CompatibilityNode.toDict)
        self.nodeDict = copy.deepcopy(nodeDict)

        self._inputs = nodeDict.get("inputs", {})
        self.outputs = nodeDict.get("outputs", {})
        self._internalFolder = self.nodeDict.get("internalFolder", "")
        self._uids = self.nodeDict.get("uids", {})

        # restore parallelization settings
        self.parallelization = self.nodeDict.get("parallelization", {})
        self.splitCount = self.parallelization.get("split", 1)
        self.setSize(self.parallelization.get("size", 1))

        # create input attributes
        for attrName, value in self._inputs.items():
            self._addAttribute(attrName, value, False)

        # create outputs attributes
        for attrName, value in self.outputs.items():
            self._addAttribute(attrName, value, True)

        # create NodeChunks matching serialized parallelization settings
        self._chunks.setObjectList([
            NodeChunk(self, desc.Range(i, blockSize=self.parallelization.get("blockSize", 0)))
            for i in range(self.splitCount)
        ])

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
            "value": value, "uid": (),
            "group": "incompatible"
        }
        if isinstance(value, bool):
            return desc.BoolParam(**params)
        if isinstance(value, int):
            return desc.IntParam(range=None, **params)
        elif isinstance(value, float):
            return desc.FloatParam(range=None, **params)
        elif isinstance(value, pyCompatibility.basestring):
            if isOutput or os.path.isabs(value) or Attribute.isLinkExpression(value):
                return desc.File(**params)
            else:
                return desc.StringParam(**params)
        # List/GroupAttribute: recursively build descriptions
        elif isinstance(value, (list, dict)):
            del params["value"]
            del params["uid"]
            attrDesc = None
            if isinstance(value, list):
                elt = value[0] if value else ""  # fallback: empty string value if list is empty
                eltDesc = CompatibilityNode.attributeDescFromValue("element", elt, isOutput)
                attrDesc = desc.ListAttribute(elementDesc=eltDesc, **params)
            elif isinstance(value, dict):
                groupDesc = []
                for key, value in value.items():
                    eltDesc = CompatibilityNode.attributeDescFromValue(key, value, isOutput)
                    groupDesc.append(eltDesc)
                attrDesc = desc.GroupAttribute(groupDesc=groupDesc, **params)
            # override empty default value with
            attrDesc._value = value
            return attrDesc
        # handle any other type of parameters as Strings
        return desc.StringParam(**params)

    @staticmethod
    def attributeDescFromName(refAttributes, name, value, conform=False):
        """
        Try to find a matching attribute description in refAttributes for given attribute 'name' and 'value'.

        Args:
            refAttributes ([desc.Attribute]): reference Attributes to look for a description
            name (str): attribute's name
            value: attribute's value

        Returns:
            desc.Attribute: an attribute description from refAttributes if a match is found, None otherwise.
        """
        # from original node description based on attribute's name
        attrDesc = next((d for d in refAttributes if d.name == name), None)
        # consider this value matches description:
        #  - if it's a serialized link expression (no proper value to set/evaluate)
        #  - or if it passes the 'matchDescription' test
        if attrDesc and (Attribute.isLinkExpression(value) or attrDesc.matchDescription(value, conform)):
            return attrDesc

        return None

    def _addAttribute(self, name, val, isOutput):
        """
        Add a new attribute on this node.

        Args:
            name (str): the name of the attribute
            val: the attribute's value
            isOutput: whether the attribute is an output

        Returns:
            bool: whether the attribute exists in the node description
        """
        attrDesc = None
        if self.nodeDesc:
            refAttrs = self.nodeDesc.outputs if isOutput else self.nodeDesc.inputs
            attrDesc = CompatibilityNode.attributeDescFromName(refAttrs, name, val)
        matchDesc = attrDesc is not None
        if not matchDesc:
            attrDesc = CompatibilityNode.attributeDescFromValue(name, val, isOutput)
        attribute = attributeFactory(attrDesc, val, isOutput, self)
        self._attributes.add(attribute)
        return matchDesc

    @property
    def issueDetails(self):
        if self.issue == CompatibilityIssue.UnknownNodeType:
            return "Unknown node type: {}.".format(self.nodeType)
        elif self.issue == CompatibilityIssue.VersionConflict:
            return "Node version '{}' conflicts with current version '{}'.".format(
                self.nodeDict["version"], nodeVersion(self.nodeDesc)
            )
        elif self.issue == CompatibilityIssue.DescriptionConflict:
            return "Node attributes don't match node description."
        else:
            return "Unknown error."

    @property
    def inputs(self):
        """ Get current node inputs, where links could differ from original serialized node data
        (i.e after node duplication) """
        # if node has not been added to a graph, return serialized node inputs
        if not self.graph:
            return self._inputs
        return {k: v.getExportValue() for k, v in self._attributes.objects.items() if v.isInput}

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
            raise NodeUpgradeError(self.name, "no matching node type")
        # TODO: use upgrade method of node description if available

        # inputs matching current type description
        commonInputs = []
        for attrName, value in self._inputs.items():
            if self.attributeDescFromName(self.nodeDesc.inputs, attrName, value, conform=True):
                # store attributes that could be used during node upgrade
                commonInputs.append(attrName)

        return Node(self.nodeType, position=self.position,
                    **{key: value for key, value in self.inputs.items() if key in commonInputs})

    compatibilityIssue = Property(int, lambda self: self.issue.value, constant=True)
    canUpgrade = Property(bool, canUpgrade.fget, constant=True)
    issueDetails = Property(str, issueDetails.fget, constant=True)


def nodeFactory(nodeDict, name=None):
    """
    Create a node instance by deserializing the given node data.
    If the serialized data matches the corresponding node type description, a Node instance is created.
    If any compatibility issue occurs, a NodeCompatibility instance is created instead.

    Args:
        nodeDict (dict): the serialization of the node
        name (str): (optional) the node's name

    Returns:
        BaseNode: the created node
    """
    nodeType = nodeDict["nodeType"]

    # retro-compatibility: inputs were previously saved as "attributes"
    if "inputs" not in nodeDict and "attributes" in nodeDict:
        nodeDict["inputs"] = nodeDict["attributes"]
        del nodeDict["attributes"]

    # get node inputs/outputs
    inputs = nodeDict.get("inputs", {})
    outputs = nodeDict.get("outputs", {})
    version = nodeDict.get("version", None)
    internalFolder = nodeDict.get("internalFolder", None)
    position = Position(*nodeDict.get("position", []))

    compatibilityIssue = None

    nodeDesc = None
    try:
        nodeDesc = meshroom.core.nodesDesc[nodeType]
    except KeyError:
        # unknown node type
        compatibilityIssue = CompatibilityIssue.UnknownNodeType

    if nodeDesc:
        # compare serialized node version with current node version
        currentNodeVersion = meshroom.core.nodeVersion(nodeDesc)
        # if both versions are available, check for incompatibility in major version
        if version and currentNodeVersion and Version(version).major != Version(currentNodeVersion).major:
            compatibilityIssue = CompatibilityIssue.VersionConflict
        # in other cases, check attributes compatibility between serialized node and its description
        else:
            # check that the node has the exact same set of inputs/outputs as its description
            if sorted([attr.name for attr in nodeDesc.inputs]) != sorted(inputs.keys()) or \
                    sorted([attr.name for attr in nodeDesc.outputs]) != sorted(outputs.keys()):
                compatibilityIssue = CompatibilityIssue.DescriptionConflict
            # verify that all inputs match their descriptions
            for attrName, value in inputs.items():
                if not CompatibilityNode.attributeDescFromName(nodeDesc.inputs, attrName, value):
                    compatibilityIssue = CompatibilityIssue.DescriptionConflict
                    break
            # verify that all outputs match their descriptions
            for attrName, value in outputs.items():
                if not CompatibilityNode.attributeDescFromName(nodeDesc.outputs, attrName, value):
                    compatibilityIssue = CompatibilityIssue.DescriptionConflict
                    break

    if compatibilityIssue is None:
        node = Node(nodeType, position, **inputs)
    else:
        logging.warning("Compatibility issue detected for node '{}': {}".format(name, compatibilityIssue.name))
        node = CompatibilityNode(nodeType, nodeDict, position, compatibilityIssue)
        # retro-compatibility: no internal folder saved
        # can't spawn meaningful CompatibilityNode with precomputed outputs
        # => automatically try to perform node upgrade
        if not internalFolder and nodeDesc:
            logging.warning("No serialized output data: performing automatic upgrade on '{}'".format(name))
            node = node.upgrade()

    return node
