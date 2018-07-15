#!/usr/bin/env python
# coding:utf-8
import atexit
import datetime
import json
import logging
import os
import re
import shutil
import time
import uuid
from collections import defaultdict

from enum import Enum

import meshroom
from meshroom.common import Signal, Variant, Property, BaseObject, Slot, ListModel, DictModel
from meshroom.core import desc, stats, hashValue
from meshroom.core.attribute import attribute_factory, ListAttribute, GroupAttribute, Attribute
from meshroom.core.exception import UnknownNodeTypeError


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
        self.status = StatusData(node.name, node.nodeType, node.packageName, node.packageVersion)
        self.statistics = stats.Statistics()
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
            self.status.reset()
        else:
            with open(statusFile, 'r') as jsonFile:
                statusData = json.load(jsonFile)
            self.status.fromDict(statusData)
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
        statusFilepathWriting = statusFilepath + '.writing.' + str(uuid.uuid4())
        with open(statusFilepathWriting, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)
        shutil.move(statusFilepathWriting, statusFilepath)

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
        statisticsFilepathWriting = statisticsFilepath + '.writing.' + str(uuid.uuid4())
        with open(statisticsFilepathWriting, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)
        shutil.move(statisticsFilepathWriting, statisticsFilepath)

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


class Node(BaseObject):
    """
    """

    # Regexp handling complex attribute names with recursive understanding of Lists and Groups
    # i.e: a.b, a[0], a[0].b.c[1]
    attributeRE = re.compile(r'\.?(?P<name>\w+)(?:\[(?P<index>\d+)\])?')

    def __init__(self, nodeDesc, parent=None, **kwargs):
        """
        Create a new Node instance based on the given node description.
        Any other keyword argument will be used to initialize this node's attributes.

        Args:
            nodeDesc (desc.Node): the node description for this node
            parent (BaseObject): this Node's parent
            **kwargs: attributes values
        """
        super(Node, self).__init__(parent)
        self.nodeDesc = nodeDesc
        self.packageName = self.nodeDesc.packageName
        self.packageVersion = self.nodeDesc.packageVersion

        self._name = None  # type: str
        self.graph = None  # type: Graph
        self.dirty = True  # whether this node's outputs must be re-evaluated on next Graph update
        self._chunks = ListModel(parent=self)
        self._uids = dict()
        self._cmdVars = {}
        self._size = 0
        self._attributes = DictModel(keyAttrName='name', parent=self)
        self.attributesPerUid = defaultdict(set)
        self._initFromDesc()
        for k, v in kwargs.items():
            self.attribute(k).value = v
        self._updateChunks()

    def __getattr__(self, k):
        try:
            # Throws exception if not in prototype chain
            # return object.__getattribute__(self, k) # doesn't work in python2
            return object.__getattr__(self, k)
        except AttributeError:
            try:
                return self.attribute(k)
            except KeyError:
                raise AttributeError(k)

    def getName(self):
        return self._name


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

    def _initFromDesc(self):
        # Init from class and instance members

        for attrDesc in self.nodeDesc.inputs:
            assert isinstance(attrDesc, meshroom.core.desc.Attribute)
            self._attributes.add(attribute_factory(attrDesc, None, False, self))

        for attrDesc in self.nodeDesc.outputs:
            assert isinstance(attrDesc, meshroom.core.desc.Attribute)
            self._attributes.add(attribute_factory(attrDesc, None, True, self))

        # List attributes per uid
        for attr in self._attributes:
            for uidIndex in attr.attributeDesc.uid:
                self.attributesPerUid[uidIndex].add(attr)

    def _applyExpr(self):
        for attr in self._attributes:
            attr._applyExpr()

    @property
    def nodeType(self):
        return self.nodeDesc.__class__.__name__

    @property
    def depth(self):
        return self.graph.getDepth(self)

    @property
    def minDepth(self):
        return self.graph.getDepth(self, minimal=True)

    def toDict(self):
        attributes = {k: v.getExportValue() for k, v in self._attributes.objects.items() if v.isInput}
        return {
            'nodeType': self.nodeType,
            'packageName': self.packageName,
            'packageVersion': self.packageVersion,
            'attributes': {k: v for k, v in attributes.items() if v is not None},  # filter empty values
        }

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

            if v is not None and v is not '':
                self._cmdVars[attr.attributeDesc.group] = self._cmdVars.get(attr.attributeDesc.group, '') + \
                                                          ' ' + self._cmdVars[name]

        # For updating output attributes invalidation values
        cmdVarsNoCache = self._cmdVars.copy()
        cmdVarsNoCache['cache'] = ''

        # Evaluate output params
        for name, attr in self._attributes.objects.items():
            if attr.isInput:
                continue  # skip inputs
            attr.value = attr.attributeDesc.value.format(**self._cmdVars)
            attr._invalidationValue = attr.attributeDesc.value.format(**cmdVarsNoCache)
            v = attr.getValueStr()

            self._cmdVars[name] = '--{name} {value}'.format(name=name, value=v)
            self._cmdVars[name + 'Value'] = str(v)

            if v is not None and v is not '':
                self._cmdVars[attr.attributeDesc.group] = self._cmdVars.get(attr.attributeDesc.group, '') + \
                                                          ' ' + self._cmdVars[name]

    @property
    def isParallelized(self):
        return bool(self.nodeDesc.parallelization)

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

    @Slot()
    def clearData(self):
        """ Delete this Node internal folder.
        Status will be reset to Status.NONE
        """
        if os.path.exists(self.internalFolder):
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
        """ Update Node's computation task splitting into NodeChunks based on its description """
        self.setSize(self.nodeDesc.size.computeSize(self))
        if self.isParallelized:
            try:
                ranges = self.nodeDesc.parallelization.getRanges(self)
                if len(ranges) != len(self._chunks):
                    self._chunks.setObjectList([NodeChunk(self, range) for range in ranges])
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
            else:
                self._chunks[0].range = desc.Range()

    def updateInternals(self, cacheDir=None):
        """ Update Node's internal parameters and output attributes.

        This method is called when:
         - an input parameter is modified
         - the graph main cache directory is changed

        Args:
            cacheDir (str): (optional) override graph's cache directory with custom path
        """
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
        # Notify internal folder change if needed
        if self.internalFolder != folder:
            self.internalFolderChanged.emit()

    @property
    def internalFolder(self):
        return self.nodeDesc.internalFolder.format(**self._cmdVars)

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

    def getStatus(self):
        return self.status

    def getChunks(self):
        return self._chunks

    @property
    def statusNames(self):
        return [s.status.name for s in self.status]

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
    nodeType = Property(str, nodeType.fget, constant=True)
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


def node_factory(nodeType, skipInvalidAttributes=False, **attributes):
    """
    Create a new Node of type NodeType and initialize its attributes with given kwargs.

    Args:
        nodeType (str): name of the node description class
        skipInvalidAttributes (bool): whether to skip attributes not defined in
                                      or incompatible with nodeType's description.
        attributes (): serialized nodes attributes

    Raises:
        UnknownNodeTypeError if nodeType is unknown
    """
    try:
        nodeDesc = meshroom.core.nodesDesc[nodeType]()
    except KeyError:
        # unknown node type
        raise UnknownNodeTypeError(nodeType)

    if skipInvalidAttributes:
        # compare given attributes with the ones from node desc
        descAttrNames = set([attr.name for attr in nodeDesc.inputs])
        attrNames = set([name for name in attributes.keys()])
        invalidAttributes = list(attrNames.difference(descAttrNames))
        commonAttributes = list(attrNames.intersection(descAttrNames))
        # compare value types for common attributes
        for attr in [attr for attr in nodeDesc.inputs if attr.name in commonAttributes]:
            try:
                attr.validateValue(attributes[attr.name])
            except:
                invalidAttributes.append(attr.name)

        if invalidAttributes and skipInvalidAttributes:
            # filter out invalid attributes
            logging.info("Skipping invalid attributes initialization for {}: {}".format(nodeType, invalidAttributes))
            for attr in invalidAttributes:
                del attributes[attr]

    return Node(nodeDesc, **attributes)
