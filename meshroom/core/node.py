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
import types
import uuid
from collections import namedtuple
from enum import Enum
from typing import Callable, Optional

import meshroom
from meshroom.common import Signal, Variant, Property, BaseObject, Slot, ListModel, DictModel
from meshroom.core import desc, stats, hashValue, nodeVersion, Version
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
                # If remove is successful, we can stop the iterations
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
    INPUT = 7  # Special status for input nodes


class ExecMode(Enum):
    NONE = 0
    LOCAL = 1
    EXTERN = 2


class StatusData(BaseObject):
    """
    """
    dateTimeFormatting = '%Y-%m-%d %H:%M:%S.%f'

    def __init__(self, nodeName='', nodeType='', packageName='', packageVersion='', parent=None):
        super(StatusData, self).__init__(parent)
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

    def merge(self, other):
        self.startDateTime = min(self.startDateTime, other.startDateTime)
        self.endDateTime = max(self.endDateTime, other.endDateTime)
        self.elapsedTime += other.elapsedTime

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

        # Skip non data attributes from BaseObject
        d.pop("destroyed", None)
        d.pop("objectNameChanged", None)
        return d

    def fromDict(self, d):
        self.status = d.get('status', Status.NONE)
        if not isinstance(self.status, Status):
            self.status = Status[self.status]
        self.execMode = d.get('execMode', ExecMode.NONE)
        if not isinstance(self.execMode, ExecMode):
            self.execMode = ExecMode[self.execMode]
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
        if text == 'critical':
            return logging.CRITICAL
        elif text == 'error':
            return logging.ERROR
        elif text == 'warning':
            return logging.WARNING
        elif text == 'info':
            return logging.INFO
        elif text == 'debug':
            return logging.DEBUG
        else:
            return logging.NOTSET


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
        self._status = StatusData(node.name, node.nodeType, node.packageName, node.packageVersion)
        self.statistics = stats.Statistics()
        self.statusFileLastModTime = -1
        self._subprocess = None
        # Notify update in filepaths when node's internal folder changes
        self.node.internalFolderChanged.connect(self.nodeFolderChanged)

        self.execModeNameChanged.connect(self.node.globalExecModeChanged)

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
        return self._status.status.name

    @property
    def logger(self):
        return self.logManager.logger

    @property
    def execModeName(self):
        return self._status.execMode.name

    def updateStatusFromCache(self):
        """
        Update node status based on status file content/existence.
        """
        statusFile = self.statusFile
        oldStatus = self._status.status
        # No status file => reset status to Status.None
        if not os.path.exists(statusFile):
            self.statusFileLastModTime = -1
            self._status.reset()
        else:
            try:
                with open(statusFile, 'r') as jsonFile:
                    statusData = json.load(jsonFile)
                self.status.fromDict(statusData)
                self.statusFileLastModTime = os.path.getmtime(statusFile)
            except Exception:
                self.statusFileLastModTime = -1
                self.status.reset()

        if oldStatus != self.status.status:
            self.statusChanged.emit()

    @property
    def statusFile(self):
        if self.range.blockSize == 0:
            return os.path.join(self.node.graph.cacheDir, self.node.internalFolder, "status")
        else:
            return os.path.join(self.node.graph.cacheDir, self.node.internalFolder, str(self.index) + ".status")

    @property
    def statisticsFile(self):
        if self.range.blockSize == 0:
            return os.path.join(self.node.graph.cacheDir, self.node.internalFolder, "statistics")
        else:
            return os.path.join(self.node.graph.cacheDir, self.node.internalFolder, str(self.index) + ".statistics")

    @property
    def logFile(self):
        if self.range.blockSize == 0:
            return os.path.join(self.node.graph.cacheDir, self.node.internalFolder, "log")
        else:
            return os.path.join(self.node.graph.cacheDir, self.node.internalFolder, str(self.index) + ".log")

    def saveStatusFile(self):
        """
        Write node status on disk.
        """
        data = self._status.toDict()
        statusFilepath = self.statusFile
        folder = os.path.dirname(statusFilepath)
        try:
            os.makedirs(folder)
        except Exception:
            pass

        statusFilepathWriting = getWritingFilepath(statusFilepath)
        with open(statusFilepathWriting, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)
        renameWritingToFinalPath(statusFilepathWriting, statusFilepath)

    def upgradeStatusTo(self, newStatus, execMode=None):
        if newStatus.value <= self._status.status.value:
            logging.warning("Downgrade status on node '{}' from {} to {}".
                            format(self.name, self._status.status, newStatus))

        if newStatus == Status.SUBMITTED:
            self._status = StatusData(self.node.name, self.node.nodeType, self.node.packageName, self.node.packageVersion)
        if execMode is not None:
            self._status.execMode = execMode
            self.execModeNameChanged.emit()
        self._status.status = newStatus
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

    def process(self, forceCompute=False):
        if not forceCompute and self._status.status == Status.SUCCESS:
            logging.info("Node chunk already computed: {}".format(self.name))
            return
        global runningProcesses
        runningProcesses[self.name] = self
        self._status.initStartCompute()
        exceptionStatus = None
        startTime = time.time()
        self.upgradeStatusTo(Status.RUNNING)
        self.statThread = stats.StatisticsThread(self)
        self.statThread.start()
        try:
            self.node.nodeDesc.processChunk(self)
        except Exception:
            if self._status.status != Status.STOPPED:
                exceptionStatus = Status.ERROR
            raise
        except (KeyboardInterrupt, SystemError, GeneratorExit):
            exceptionStatus = Status.STOPPED
            raise
        finally:
            self._status.initEndCompute()
            self._status.elapsedTime = time.time() - startTime
            if exceptionStatus is not None:
                self.upgradeStatusTo(exceptionStatus)
            logging.info(" - elapsed time: {}".format(self._status.elapsedTimeStr))
            # Ask and wait for the stats thread to stop
            self.statThread.stopRequest()
            self.statThread.join()
            self.statistics = stats.Statistics()
            del runningProcesses[self.name]

        self.upgradeStatusTo(Status.SUCCESS)

    def stopProcess(self):
        if not self.isExtern():
            if self._status.status == Status.RUNNING:
                self.upgradeStatusTo(Status.STOPPED)
            elif self._status.status == Status.SUBMITTED:
                self.upgradeStatusTo(Status.NONE)
        self.node.nodeDesc.stopProcess(self)

    def isExtern(self):
        return self._status.execMode == ExecMode.EXTERN or (
            self._status.execMode == ExecMode.LOCAL and self._status.sessionUid != meshroom.core.sessionUid)

    statusChanged = Signal()
    status = Property(Variant, lambda self: self._status, notify=statusChanged)
    statusName = Property(str, statusName.fget, notify=statusChanged)
    execModeNameChanged = Signal()
    execModeName = Property(str, execModeName.fget, notify=execModeNameChanged)
    statisticsChanged = Signal()

    nodeFolderChanged = Signal()
    statusFile = Property(str, statusFile.fget, notify=nodeFolderChanged)
    logFile = Property(str, logFile.fget, notify=nodeFolderChanged)
    statisticsFile = Property(str, statisticsFile.fget, notify=nodeFolderChanged)

    nodeName = Property(str, lambda self: self.node.name, constant=True)
    statusNodeName = Property(str, lambda self: self._status.nodeName, constant=True)

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

    def __init__(self, nodeType, position=None, parent=None, uid=None, **kwargs):
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
        self._uid = uid
        self._cmdVars = {}
        self._size = 0
        self._position = position or Position()
        self._attributes = DictModel(keyAttrName='name', parent=self)
        self._internalAttributes = DictModel(keyAttrName='name', parent=self)
        self.invalidatingAttributes = set()
        self._alive = True  # for QML side to know if the node can be used or is going to be deleted
        self._locked = False
        self._duplicates = ListModel(parent=self)  # list of nodes with the same uid
        self._hasDuplicates = False

        self.globalStatusChanged.connect(self.updateDuplicatesStatusAndLocked)

    def __getattr__(self, k):
        try:
            # Throws exception if not in prototype chain
            return object.__getattribute__(self, k)
        except AttributeError as e:
            try:
                return self.attribute(k)
            except KeyError:
                raise e

    def getName(self):
        return self._name

    def getDefaultLabel(self):
        return self.nameToLabel(self._name)

    def getLabel(self):
        """
        Returns:
            str: the user-provided label if it exists, the high-level label of this node otherwise
        """
        if self.hasInternalAttribute("label"):
            label = self.internalAttribute("label").value.strip()
            if label:
                return label
        return self.getDefaultLabel()

    def getColor(self):
        """
        Returns:
            str: the user-provided custom color of the node if it exists, empty string otherwise
        """
        if self.hasInternalAttribute("color"):
            return self.internalAttribute("color").value.strip()
        return ""

    def getInvalidationMessage(self):
        """
        Returns:
            str: the invalidation message on the node if it exists, empty string otherwise
        """
        if self.hasInternalAttribute("invalidation"):
            return self.internalAttribute("invalidation").value
        return ""

    def getComment(self):
        """
        Returns:
            str: the comments on the node if they exist, empty string otherwise
        """
        if self.hasInternalAttribute("comment"):
            return self.internalAttribute("comment").value
        return ""

    @Slot(str, result=str)
    def nameToLabel(self, name):
        """
        Returns:
            str: the high-level label from the technical node name
        """
        t, idx = name.split("_")
        return "{}{}".format(t, idx if int(idx) > 1 else "")

    def getDocumentation(self):
        if not self.nodeDesc:
            return ""
        return self.nodeDesc.documentation

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
        return os.path.join(self.graph.cacheDir, self.internalFolder, 'values')

    def getInputNodes(self, recursive, dependenciesOnly):
        return self.graph.getInputNodes(self, recursive=recursive, dependenciesOnly=dependenciesOnly)

    def getOutputNodes(self, recursive, dependenciesOnly):
        return self.graph.getOutputNodes(self, recursive=recursive, dependenciesOnly=dependenciesOnly)

    def toDict(self):
        pass

    def _computeUid(self):
        """ Compute node UID by combining associated attributes' UIDs. """
        # If there is no invalidating attribute, then the computation of the UID should not go through as
        # it will only include the node type
        if not self.invalidatingAttributes:
            return

        # UID is computed by hashing the sorted list of tuple (name, value) of all attributes impacting this UID
        uidAttributes = []
        for attr in self.invalidatingAttributes:
            if not attr.enabled:
                continue  # Disabled params do not contribute to the uid
            dynamicOutputAttr = attr.isLink and attr.getLinkParam(recursive=True).desc.isDynamicValue
            # For dynamic output attributes, the UID does not depend on the attribute value.
            # In particular, when loading a project file, the UIDs are updated first,
            # and the node status and the dynamic output values are not yet loaded,
            # so we should not read the attribute value.
            if not dynamicOutputAttr and attr.value == attr.uidIgnoreValue:
                continue  # For non-dynamic attributes, check if the value should be ignored
            uidAttributes.append((attr.getName(), attr.uid()))
        uidAttributes.sort()

        # Adding the node type prevents ending up with two identical UIDs for different node types
        # that have the exact same list of attributes
        uidAttributes.append(self.nodeType)
        self._uid = hashValue(uidAttributes)

    def _buildCmdVars(self):
        def _buildAttributeCmdVars(cmdVars, name, attr):
            if attr.enabled:
                group = attr.attributeDesc.group(attr.node) \
                        if isinstance(attr.attributeDesc.group, types.FunctionType) else attr.attributeDesc.group
                if group is not None:
                    # If there is a valid command line "group"
                    v = attr.getValueStr(withQuotes=True)
                    cmdVars[name] = "--{name} {value}".format(name=name, value=v)
                    # xxValue is exposed without quotes to allow to compose expressions
                    cmdVars[name + "Value"] = attr.getValueStr(withQuotes=False)

                    # List elements may give a fully empty string and will not be sent to the command line.
                    # String attributes will return only quotes if it is empty and thus will be send to the command line.
                    # But a List of string containing 1 element,
                    # and this element is an empty string will also return quotes and will be sent to the command line.
                    if v:
                        cmdVars[group] = cmdVars.get(group, "") + " " + cmdVars[name]
                elif isinstance(attr, GroupAttribute):
                    assert isinstance(attr.value, DictModel)
                    # If the GroupAttribute is not set in a single command line argument,
                    # the sub-attributes may need to be exposed individually
                    for v in attr._value:
                        _buildAttributeCmdVars(cmdVars, v.name, v)

        """ Generate command variables using input attributes and resolved output attributes names and values. """
        self._cmdVars["uid"] = self._uid

        # Evaluate input params
        for name, attr in self._attributes.objects.items():
            if attr.isOutput:
                continue  # skip outputs
            _buildAttributeCmdVars(self._cmdVars, name, attr)

        # For updating output attributes invalidation values
        cmdVarsNoCache = self._cmdVars.copy()
        cmdVarsNoCache['cache'] = ''

        # Evaluate output params
        for name, attr in self._attributes.objects.items():
            if attr.isInput:
                continue  # skip inputs

            # Apply expressions for File attributes
            if attr.attributeDesc.isExpression:
                defaultValue = ""
                # Do not evaluate expression for disabled attributes
                # (the expression may refer to other attributes that are not defined)
                if attr.enabled:
                    try:
                        defaultValue = attr.defaultValue()
                    except AttributeError:
                        # If we load an old scene, the lambda associated to the 'value' could try to access other
                        # params that could not exist yet
                        logging.warning('Invalid lambda evaluation for "{nodeName}.{attrName}"'.
                                        format(nodeName=self.name, attrName=attr.name))
                    if defaultValue is not None:
                        try:
                            attr.value = defaultValue.format(**self._cmdVars)
                            attr._invalidationValue = defaultValue.format(**cmdVarsNoCache)
                        except KeyError as e:
                            logging.warning('Invalid expression with missing key on "{nodeName}.{attrName}" with '
                                            'value "{defaultValue}".\nError: {err}'.
                                            format(nodeName=self.name, attrName=attr.name, defaultValue=defaultValue,
                                            err=str(e)))
                        except ValueError as e:
                            logging.warning('Invalid expression value on "{nodeName}.{attrName}" with value '
                                            '"{defaultValue}".\nError: {err}'.
                                            format(nodeName=self.name, attrName=attr.name, defaultValue=defaultValue,
                                            err=str(e)))

            v = attr.getValueStr(withQuotes=True)

            self._cmdVars[name] = '--{name} {value}'.format(name=name, value=v)
            # xxValue is exposed without quotes to allow to compose expressions
            self._cmdVars[name + 'Value'] = attr.getValueStr(withQuotes=False)

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
            return (status == Status.INPUT)
        for chunk in self._chunks:
            if chunk.status.status != status:
                return False
        return True

    def _isComputed(self):
        if not self.isComputable:
            return True
        return self.hasStatus(Status.SUCCESS)

    def _isComputable(self):
        return self.getGlobalStatus() != Status.INPUT

    def clearData(self):
        """ Delete this Node internal folder.
        Status will be reset to Status.NONE
        """
        if self.internalFolder and os.path.exists(self.internalFolder):
            shutil.rmtree(self.internalFolder)
            self.updateStatusFromCache()

    @Slot(result=str)
    def getStartDateTime(self):
        """ Return the date (str) of the first running chunk """
        dateTime = [chunk._status.startDateTime for chunk in self._chunks if chunk._status.status
                    not in (Status.NONE, Status.SUBMITTED) and chunk._status.startDateTime != ""]
        return min(dateTime) if len(dateTime) != 0 else ""

    def isAlreadySubmitted(self):
        for chunk in self._chunks:
            if chunk.isAlreadySubmitted():
                return True
        return False

    def isAlreadySubmittedOrFinished(self):
        for chunk in self._chunks:
            if not chunk.isAlreadySubmittedOrFinished():
                return False
        return True

    @Slot(result=bool)
    def isSubmittedOrRunning(self):
        """ Return True if all chunks are at least submitted and there is one running chunk, False otherwise. """
        if not self.isAlreadySubmittedOrFinished():
            return False
        for chunk in self._chunks:
            if chunk.isRunning():
                return True
        return False

    @Slot(result=bool)
    def isRunning(self):
        """ Return True if at least one chunk of this Node is running, False otherwise. """
        return any(chunk.isRunning() for chunk in self._chunks)

    @Slot(result=bool)
    def isFinishedOrRunning(self):
        """ Return True if all chunks of this Node is either finished or running, False otherwise. """
        return all(chunk.isFinishedOrRunning() for chunk in self._chunks)

    @Slot(result=bool)
    def isPartiallyFinished(self):
        """ Return True is at least one chunk of this Node is finished, False otherwise. """
        return any(chunk.isFinished() for chunk in self._chunks)

    def alreadySubmittedChunks(self):
        return [ch for ch in self._chunks if ch.isAlreadySubmitted()]

    def isExtern(self):
        """ Return True if at least one chunk of this Node has an external execution mode, False otherwise.

        It is not enough to check whether the first chunk's execution mode is external, because computations
        may have been started locally, interrupted, and restarted externally. In that case, if the first
        chunk has completed locally before the computations were interrupted, its execution mode will always
        be local, even if computations resume externally.
        """
        return any(chunk.isExtern() for chunk in self._chunks)

    @Slot()
    def clearSubmittedChunks(self):
        """ Reset all submitted chunks to Status.NONE. This method should be used to clear inconsistent status
        if a computation failed without informing the graph.

        Warnings:
            This must be used with caution. This could lead to inconsistent node status
            if the graph is still being computed.
        """
        for chunk in self._chunks:
            if chunk.isAlreadySubmitted():
                chunk.upgradeStatusTo(Status.NONE, ExecMode.NONE)

    def clearLocallySubmittedChunks(self):
        """ Reset all locally submitted chunks to Status.NONE. """
        for chunk in self._chunks:
            if chunk.isAlreadySubmitted() and not chunk.isExtern():
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

    def _getAttributeChangedCallback(self, attr: Attribute) -> Optional[Callable]:
        """Get the node descriptor-defined value changed callback associated to `attr` if any."""

        # Callbacks cannot be defined on nested attributes.
        if attr.root is not None:
            return None

        attrCapitalizedName = attr.name[:1].upper() + attr.name[1:]
        callbackName = f"on{attrCapitalizedName}Changed"

        callback = getattr(self.nodeDesc, callbackName, None)
        return callback if callback and callable(callback) else None

    def _onAttributeChanged(self, attr: Attribute):
        """
        When an attribute value has changed, a specific function can be defined in the descriptor and be called.

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

        if attr.value is None:
            # Discard dynamic values depending on the graph processing.
            return
        
        if self.graph and self.graph.isLoading:
            # Do not trigger attribute callbacks during the graph loading.
            return

        callback = self._getAttributeChangedCallback(attr)

        if callback:
            callback(self)

        if self.graph:
            # If we are in a graph, propagate the notification to the connected output attributes
            for edge in self.graph.outEdges(attr):
                edge.dst.node._onAttributeChanged(edge.dst)

    def onAttributeClicked(self, attr):
        """ When an attribute is clicked, a specific function can be defined in the descriptor and be called.

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
        self._computeUid()
        self._buildCmdVars()
        if self.nodeDesc:
            self.nodeDesc.postUpdate(self)
        # Notify internal folder change if needed
        if self.internalFolder != folder:
            self.internalFolderChanged.emit()

    def updateInternalAttributes(self):
        self.internalAttributesChanged.emit()

    @property
    def internalFolder(self):
        return self._internalFolder.format(**self._cmdVars)

    def updateStatusFromCache(self):
        """
        Update node status based on status file content/existence.
        """
        s = self.globalStatus
        for chunk in self._chunks:
            chunk.updateStatusFromCache()
        # logging.warning("updateStatusFromCache: {}, status: {} => {}".format(self.name, s, self.globalStatus))
        self.updateOutputAttr()

    def submit(self, forceCompute=False):
        for chunk in self._chunks:
            if forceCompute or chunk.status.status != Status.SUCCESS:
                chunk.upgradeStatusTo(Status.SUBMITTED, ExecMode.EXTERN)

    def beginSequence(self, forceCompute=False):
        for chunk in self._chunks:
            if forceCompute or (chunk.status.status not in (Status.RUNNING, Status.SUCCESS)):
                chunk.upgradeStatusTo(Status.SUBMITTED, ExecMode.LOCAL)

    def processIteration(self, iteration):
        self._chunks[iteration].process()

    def preprocess(self):
        # Invoke the Node Description's pre-process for the Client Node to prepare its processing
        self.nodeDesc.preprocess(self)

    def process(self, forceCompute=False):
        for chunk in self._chunks:
            chunk.process(forceCompute)

    def postprocess(self):
        # Invoke the post process on Client Node to execute after the processing on the node is completed
        self.nodeDesc.postprocess(self)
        self.saveOutputAttr()

    def updateOutputAttr(self):
        if not self.nodeDesc:
            return
        if not self.nodeDesc.hasDynamicOutputAttribute:
            return
        # logging.warning("updateOutputAttr: {}, status: {}".format(self.name, self.globalStatus))
        if self.getGlobalStatus() == Status.SUCCESS:
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
        if not self.nodeDesc.hasDynamicOutputAttribute:
            return
        valuesFile = self.valuesFile
        if not os.path.exists(valuesFile):
            logging.warning("No output attr file: {}".format(valuesFile))
            return

        # logging.warning("load output attr: {}, value: {}".format(self.name, valuesFile))
        with open(valuesFile, 'r') as jsonFile:
            data = json.load(jsonFile)

        # logging.warning(data)
        for output in self.nodeDesc.outputs:
            if output.isDynamicValue:
                if self.hasAttribute(output.name) and output.name in data:
                    self.attribute(output.name).value = data[output.name]
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
                    data[output.name] = self.attribute(output.name).value
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
        for chunk in self._chunks.values():
            chunk.stopProcess()

    def getGlobalStatus(self):
        """
        Get node global status based on the status of its chunks.

        Returns:
            Status: the node global status
        """
        if isinstance(self.nodeDesc, desc.InputNode):
            return Status.INPUT
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

    @Slot(result=StatusData)
    def getFusedStatus(self):
        fusedStatus = StatusData()
        if self._chunks:
            fusedStatus.fromDict(self._chunks[0].status.toDict())
            for chunk in self._chunks[1:]:
                fusedStatus.merge(chunk.status)
        fusedStatus.status = self.getGlobalStatus()
        return fusedStatus

    @Slot(result=StatusData)
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

    @property
    def globalExecMode(self):
        return self._chunks.at(0).execModeName

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
        if self.name == self._chunks.at(0).statusNodeName:
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
                if node.getGlobalStatus() in lockedStatus and node._chunks.at(0).statusNodeName == node.name:
                    stayLocked = True
                    break
            if not stayLocked:
                self.setLocked(False)
                # Unlock every input node
                for node in inputNodes:
                    node.setLocked(False)
            return
        elif currentStatus in lockedStatus and self._chunks.at(0).statusNodeName == self.name:
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
            newListName = set([node.name for node in newList])
            oldListName = set([node.name for node in self._duplicates.values()])

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

    def statusInThisSession(self):
        if not self._chunks:
            return False
        for chunk in self._chunks:
            if chunk.status.sessionUid != meshroom.core.sessionUid:
                return False
        return True

    @Slot(result=bool)
    def canBeStopped(self):
        # Only locked nodes running in local with the same
        # sessionUid as the Meshroom instance can be stopped
        return (self.locked and self.getGlobalStatus() == Status.RUNNING and
                self.globalExecMode == "LOCAL" and self.statusInThisSession())

    @Slot(result=bool)
    def canBeCanceled(self):
        # Only locked nodes submitted in local with the same
        # sessionUid as the Meshroom instance can be canceled
        return (self.locked and self.getGlobalStatus() == Status.SUBMITTED and
                self.globalExecMode == "LOCAL" and self.statusInThisSession())

    def hasImageOutputAttribute(self):
        """
        Return True if at least one attribute has the 'image' semantic (and can thus be loaded in the 2D Viewer),
        False otherwise.
        """
        for attr in self._attributes:
            if attr.enabled and attr.isOutput and attr.desc.semantic == "image":
                return True
        return False

    def hasSequenceOutputAttribute(self):
        """
        Return True if at least one attribute has the 'sequence' semantic (and can thus be loaded in the 2D Viewer),
        False otherwise.
        """
        for attr in self._attributes:
            if attr.enabled and attr.isOutput and (attr.desc.semantic == "sequence" or 
                                                   attr.desc.semantic == "imageList"):
                return True
        return False

    def has3DOutputAttribute(self):
        """
        Return True if at least one attribute is a File that can be loaded in the 3D Viewer, False otherwise.
        """
        # List of supported extensions, taken from Viewer3DSettings
        supportedExts = ['.obj', '.stl', '.fbx', '.gltf', '.abc', '.ply']
        for attr in self._attributes:
            # If the attribute is a File attribute, it is an instance of str and can be iterated over
            hasSupportedExt = isinstance(attr.value, str) and any(ext in attr.value for ext in supportedExts)
            if attr.enabled and attr.isOutput and hasSupportedExt:
                return True
        return False

    name = Property(str, getName, constant=True)
    defaultLabel = Property(str, getDefaultLabel, constant=True)
    nodeType = Property(str, nodeType.fget, constant=True)
    documentation = Property(str, getDocumentation, constant=True)
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
    internalFolderChanged = Signal()
    internalFolder = Property(str, internalFolder.fget, notify=internalFolderChanged)
    valuesFile = Property(str, valuesFile.fget, notify=internalFolderChanged)
    depthChanged = Signal()
    depth = Property(int, depth.fget, notify=depthChanged)
    minDepth = Property(int, minDepth.fget, notify=depthChanged)
    chunksChanged = Signal()
    chunks = Property(Variant, getChunks, notify=chunksChanged)
    sizeChanged = Signal()
    size = Property(int, getSize, notify=sizeChanged)
    globalStatusChanged = Signal()
    globalStatus = Property(str, lambda self: self.getGlobalStatus().name, notify=globalStatusChanged)
    fusedStatus = Property(StatusData, getFusedStatus, notify=globalStatusChanged)
    elapsedTime = Property(float, lambda self: self.getFusedStatus().elapsedTime, notify=globalStatusChanged)
    recursiveElapsedTime = Property(float, lambda self: self.getRecursiveFusedStatus().elapsedTime,
                                    notify=globalStatusChanged)
    # isCompatibilityNode: need lambda to evaluate the virtual function
    isCompatibilityNode = Property(bool, lambda self: self._isCompatibilityNode(), constant=True)
    isInputNode = Property(bool, lambda self: self._isInputNode(), constant=True)

    globalExecModeChanged = Signal()
    globalExecMode = Property(str, globalExecMode.fget, notify=globalExecModeChanged)
    isExternal = Property(bool, isExtern, notify=globalExecModeChanged)
    isComputed = Property(bool, _isComputed, notify=globalStatusChanged)
    isComputable = Property(bool, _isComputable, notify=globalStatusChanged)
    aliveChanged = Signal()
    alive = Property(bool, alive.fget, alive.fset, notify=aliveChanged)
    lockedChanged = Signal()
    locked = Property(bool, getLocked, setLocked, notify=lockedChanged)
    duplicates = Property(Variant, lambda self: self._duplicates, constant=True)
    hasDuplicatesChanged = Signal()
    hasDuplicates = Property(bool, lambda self: self._hasDuplicates, notify=hasDuplicatesChanged)

    outputAttrEnabledChanged = Signal()
    hasImageOutput = Property(bool, hasImageOutputAttribute, notify=outputAttrEnabledChanged)
    hasSequenceOutput = Property(bool, hasSequenceOutputAttribute, notify=outputAttrEnabledChanged)
    has3DOutput = Property(bool, has3DOutputAttribute, notify=outputAttrEnabledChanged)


class Node(BaseNode):
    """
    A standard Graph node based on a node type.
    """
    def __init__(self, nodeType, position=None, parent=None, uid=None, **kwargs):
        super(Node, self).__init__(nodeType, position, parent=parent, uid=uid, **kwargs)

        if not self.nodeDesc:
            raise UnknownNodeTypeError(nodeType)

        self.packageName = self.nodeDesc.packageName
        self.packageVersion = self.nodeDesc.packageVersion
        self._internalFolder = self.nodeDesc.internalFolder

        for attrDesc in self.nodeDesc.inputs:
            self._attributes.add(attributeFactory(attrDesc, kwargs.get(attrDesc.name, None), isOutput=False, node=self))

        for attrDesc in self.nodeDesc.outputs:
            self._attributes.add(attributeFactory(attrDesc, kwargs.get(attrDesc.name, None), isOutput=True, node=self))

        for attrDesc in self.nodeDesc.internalInputs:
            self._internalAttributes.add(attributeFactory(attrDesc, kwargs.get(attrDesc.name, None), isOutput=False,
                                                          node=self))

        # Declare events for specific output attributes
        for attr in self._attributes:
            if attr.isOutput and attr.desc.semantic == "image":
                attr.enabledChanged.connect(self.outputAttrEnabledChanged)

        # List attributes per UID
        for attr in self._attributes:
            if attr.isInput and attr.invalidate:
                self.invalidatingAttributes.add(attr)

        # Add internal attributes with a UID to the list
        for attr in self._internalAttributes:
            if attr.invalidate:
                self.invalidatingAttributes.add(attr)

        self.optionalCallOnDescriptor("onNodeCreated")

    def optionalCallOnDescriptor(self, methodName, *args, **kwargs):
        """ Call of optional method defined in the descriptor.
        Available method names are:
         - onNodeCreated
        """
        if hasattr(self.nodeDesc, methodName):
            m = getattr(self.nodeDesc, methodName)
            if callable(m):
                try:
                    m(self, *args, **kwargs)
                except Exception:
                    import traceback
                    # Format error strings with all the provided arguments
                    argsStr = ", ".join(str(arg) for arg in args)
                    kwargsStr = ", ".join(str(key) + "=" + str(value) for key, value in kwargs.items())
                    finalErrStr = argsStr
                    if kwargsStr:
                        if argsStr:
                            finalErrStr += ", "
                        finalErrStr += kwargsStr

                    logging.error("Error on call to '{}' (with args: '{}') for node type {}".
                                  format(methodName, finalErrStr, self.nodeType))
                    logging.error(traceback.format_exc())

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
        inputs = {k: v.getExportValue() for k, v in self._attributes.objects.items() if v.isInput}
        internalInputs = {k: v.getExportValue() for k, v in self._internalAttributes.objects.items()}
        outputs = ({k: v.getExportValue() for k, v in self._attributes.objects.items()
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
            'internalFolder': self._internalFolder,
            'inputs': {k: v for k, v in inputs.items() if v is not None},  # filter empty values
            'internalInputs': {k: v for k, v in internalInputs.items() if v is not None},
            'outputs': outputs,
        }

    def _updateChunks(self):
        """ Update Node's computation task splitting into NodeChunks based on its description """
        if isinstance(self.nodeDesc, desc.InputNode):
            return
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
    UidConflict = 4  # mismatch between computed UIDs and UIDs stored in serialized node data


class CompatibilityNode(BaseNode):
    """
    Fallback BaseNode subclass to instantiate Nodes having compatibility issues with current type description.
    CompatibilityNode creates an 'empty-shell' exposing the deserialized node as-is,
    with all its inputs and precomputed outputs.
    """
    def __init__(self, nodeType, nodeDict, position=None, issue=CompatibilityIssue.UnknownIssue, parent=None):
        super(CompatibilityNode, self).__init__(nodeType, position, parent)

        self.issue = issue
        # Make a deepcopy of nodeDict to handle CompatibilityNode duplication
        # and be able to change modified inputs (see CompatibilityNode.toDict)
        self.nodeDict = copy.deepcopy(nodeDict)
        self.version = Version(self.nodeDict.get("version", None))

        self._inputs = self.nodeDict.get("inputs", {})
        self._internalInputs = self.nodeDict.get("internalInputs", {})
        self.outputs = self.nodeDict.get("outputs", {})
        self._internalFolder = self.nodeDict.get("internalFolder", "")
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
            "group": "incompatible"
        }
        if isinstance(value, bool):
            return desc.BoolParam(**params)
        if isinstance(value, int):
            return desc.IntParam(range=None, **params)
        elif isinstance(value, float):
            return desc.FloatParam(range=None, **params)
        elif isinstance(value, str):
            if isOutput or os.path.isabs(value) or Attribute.isLinkExpression(value):
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
                groupDesc = []
                for key, value in value.items():
                    eltDesc = CompatibilityNode.attributeDescFromValue(key, value, isOutput)
                    groupDesc.append(eltDesc)
                attrDesc = desc.GroupAttribute(groupDesc=groupDesc, **params)
            # Override empty default value with
            attrDesc._value = value
            return attrDesc
        # Handle any other type of parameters as Strings
        return desc.StringParam(**params)

    @staticmethod
    def attributeDescFromName(refAttributes, name, value, strict=True):
        """
        Try to find a matching attribute description in refAttributes for given attribute 'name' and 'value'.

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
            return "Unknown node type: '{}'.".format(self.nodeType)
        elif self.issue == CompatibilityIssue.VersionConflict:
            return "Node version '{}' conflicts with current version '{}'.".format(
                self.nodeDict["version"], nodeVersion(self.nodeDesc)
            )
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
        return {k: v.getExportValue() for k, v in self._attributes.objects.items() if v.isInput}

    @property
    def internalInputs(self):
        """ Get current node's internal attributes """
        if not self.graph:
            return self._internalInputs
        return {k: v.getExportValue() for k, v in self._internalAttributes.objects.items()}

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
        except Exception as e:
            logging.error("Error in the upgrade implementation of the node: {}.\n{}".format(self.name, repr(e)))
            upgradedAttrValues = attrValues

        if not isinstance(upgradedAttrValues, dict):
            logging.error("Error in the upgrade implementation of the node: {}. The return type is incorrect.".
                          format(self.name))
            upgradedAttrValues = attrValues

        node.upgradeAttributeValues(upgradedAttrValues)

        node.upgradeInternalAttributeValues(intAttrValues)

        return node

    compatibilityIssue = Property(int, lambda self: self.issue.value, constant=True)
    canUpgrade = Property(bool, canUpgrade.fget, constant=True)
    issueDetails = Property(str, issueDetails.fget, constant=True)

