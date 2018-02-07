from __future__ import print_function

import atexit
import collections
import hashlib
import json
import os
import weakref
import shutil
import time
import datetime
import uuid
from collections import defaultdict
from contextlib import contextmanager
from enum import Enum  # available by default in python3. For python2: "pip install enum34"
import logging
import re

from . import stats
from . import desc
import meshroom.core
from meshroom.common import BaseObject, DictModel, Slot, Signal, Property, Variant, ListModel

# Replace default encoder to support Enums
DefaultJSONEncoder = json.JSONEncoder  # store the original one


class MyJSONEncoder(DefaultJSONEncoder):  # declare a new one with Enum support
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.name
        return DefaultJSONEncoder.default(self, obj)  # use the default one for all other types


json.JSONEncoder = MyJSONEncoder  # replace the default implementation with our new one

try:
    unicode = unicode
except NameError:
    # 'unicode' is undefined, must be Python 3
    str = str
    unicode = str
    bytes = bytes
    basestring = (str, bytes)
else:
    # 'unicode' exists, must be Python 2
    str = str
    unicode = unicode
    bytes = str
    basestring = basestring

stringIsLinkRe = re.compile('^\{[A-Za-z]+[A-Za-z0-9_.]*\}$')

def isCollection(v):
    return isinstance(v, collections.Iterable) and not isinstance(v, basestring)

@contextmanager
def GraphModification(graph):
    """
    A Context Manager that can be used to trigger only one Graph update
    for a group of several modifications.
    GraphModifications can be nested.
    """
    if not isinstance(graph, Graph):
        raise ValueError("GraphModification expects a Graph instance")
    # Store update policy for nested usage
    enabled = graph.updateEnabled
    # Disable graph update for nested block
    # (does nothing if already disabled)
    graph.updateEnabled = False
    try:
        yield  # Execute nested block
    except Exception:
        raise
    finally:
        # Restore update policy
        graph.updateEnabled = enabled


def hash(v):
    hashObject = hashlib.sha1(str(v).encode('utf-8'))
    return hashObject.hexdigest()


def attribute_factory(description, value, isOutput, node, root=None, parent=None):
    # type: (desc.Attribute, (), bool, Node, Attribute) -> Attribute
    """
    Create an Attribute based on description type.

    Args:
        description: the Attribute description
        value:  value of the Attribute. Will be set if not None.
        isOutput: whether is Attribute is an output attribute.
        node: node owning the Attribute. Note that the created Attribute is not added to Node's attributes
        root: (optional) parent Attribute (must be ListAttribute or GroupAttribute)
        parent (BaseObject): (optional) the parent BaseObject if any
    """
    if isinstance(description, meshroom.core.desc.GroupAttribute):
        cls = GroupAttribute
    elif isinstance(description, meshroom.core.desc.ListAttribute):
        cls = ListAttribute
    else:
        cls = Attribute
    attr = cls(node, description, isOutput, root, parent)
    if value is not None:
        attr.value = value
    return attr


class Attribute(BaseObject):
    """
    """

    def __init__(self, node, attributeDesc, isOutput, root=None, parent=None):
        """
        Attribute constructor

        Args:
            node (Node): the Node hosting this Attribute
            attributeDesc (desc.Attribute): the description of this Attribute
            isOutput (bool): whether this Attribute is an output of the Node
            root (Attribute): (optional) the root Attribute (List or Group) containing this one
            parent (BaseObject): (optional) the parent BaseObject
        """
        super(Attribute, self).__init__(parent)
        self._name = attributeDesc.name
        self._root = None if root is None else weakref.ref(root)
        self._node = weakref.ref(node)
        self.attributeDesc = attributeDesc
        self._isOutput = isOutput
        self._value = attributeDesc.value
        self._label = attributeDesc.label

        # invalidation value for output attributes
        self._invalidationValue = ""

    @property
    def node(self):
        return self._node()

    @property
    def root(self):
        return self._root() if self._root else None

    def absoluteName(self):
        return '{}.{}.{}'.format(self.node.graph.name, self.node.name, self._name)

    def fullName(self):
        """ Name inside the Graph: nodeName.name """
        if isinstance(self.root, ListAttribute):
            return '{}[{}]'.format(self.root.fullName(), self.root.index(self))
        elif isinstance(self.root, GroupAttribute):
            return '{}.{}'.format(self.root.fullName(), self._name)
        return '{}.{}'.format(self.node.name, self._name)

    def getName(self):
        """ Attribute name """
        return self._name

    def getType(self):
        return self.attributeDesc.__class__.__name__

    def getLabel(self):
        return self._label

    def _get_value(self):
        return self.getLinkParam().value if self.isLink else self._value

    def _set_value(self, value):
        if self._value == value:
            return

        if isinstance(value, Attribute) or (isinstance(value, basestring) and stringIsLinkRe.match(value)):
            # if we set a link to another attribute
            self._value = value
        else:
            # if we set a new value, we use the attribute descriptor validator to check the validity of the value
            # and apply some conversion if needed
            convertedValue = self.desc.validateValue(value)
            self._value = convertedValue
        # Request graph update when input parameter value is set
        # and parent node belongs to a graph
        # Output attributes value are set internally during the update process,
        # which is why we don't trigger any update in this case
        # TODO: update only the nodes impacted by this change
        # TODO: only update the graph if this attribute participates to a UID
        if self.isInput:
            self.requestGraphUpdate()
        self.valueChanged.emit()

    def requestGraphUpdate(self):
        if self.node.graph and self.attributeDesc.uid:
            self.node.graph.markNodesDirty(self.node)

    @property
    def isOutput(self):
        return self._isOutput

    @property
    def isInput(self):
        return not self._isOutput

    def uid(self, uidIndex=-1):
        """
        """
        # 'uidIndex' should be in 'self.desc.uid' but in the case of linked attribute
        # it will not be the case (so we cannot have an assert).
        if self.isOutput:
            # only dependent on the hash of its value without the cache folder
            return hash(self._invalidationValue)
        if self.isLink:
            return self.getLinkParam().uid(uidIndex)
        if isinstance(self._value, (list, tuple, set,)):
            # hash of sorted values hashed
            return hash([hash(v) for v in sorted(self._value)])
        return hash(self._value)

    @property
    def isLink(self):
        """ Whether the attribute is a link to another attribute. """
        return self.node.graph and self.isInput and self in self.node.graph.edges.keys()

    def getLinkParam(self):
        return self.node.graph.edge(self).src if self.isLink else None

    def _applyExpr(self):
        """
        For string parameters with an expression (when loaded from file),
        this function convert the expression into a real edge in the graph
        and clear the string value.
        """
        v = self._value
        g = self.node.graph
        if not g:
            return
        if isinstance(v, Attribute):
            g.addEdge(v, self)
            self._value = ""
        elif self.isInput and isinstance(v, basestring) and stringIsLinkRe.match(v):
            # value is a link to another attribute
            link = v[1:-1]
            linkNode, linkAttr = link.split('.')
            g.addEdge(g.node(linkNode).attribute(linkAttr), self)
            self._value = ""

    def getExportValue(self):
        if self.isLink:
            return '{' + self.getLinkParam().fullName() + '}'
        if self.isOutput:
            return self.desc.value
        return self._value

    def getValueStr(self):
        if isinstance(self.attributeDesc, desc.ChoiceParam) and not self.attributeDesc.exclusive:
            assert(isinstance(self.value, collections.Sequence) and not isinstance(self.value, basestring))
            return self.attributeDesc.joinChar.join(self.value)
        if isinstance(self.attributeDesc, (desc.StringParam, desc.File)):
            return '"{}"'.format(self.value)
        return str(self.value)

    def defaultValue(self):
        return self.desc.value

    def _isDefault(self):
        return self._value == self.defaultValue()

    def getPrimitiveValue(self, exportDefault=True):
        return self._value

    name = Property(str, getName, constant=True)
    label = Property(str, getLabel, constant=True)
    type = Property(str, getType, constant=True)
    desc = Property(desc.Attribute, lambda self: self.attributeDesc, constant=True)
    valueChanged = Signal()
    value = Property(Variant, _get_value, _set_value, notify=valueChanged)
    isOutput = Property(bool, isOutput.fget, constant=True)
    isLinkChanged = Signal()
    isLink = Property(bool, isLink.fget, notify=isLinkChanged)
    isDefault = Property(bool, _isDefault, notify=valueChanged)


class ListAttribute(Attribute):

    def __init__(self, node, attributeDesc, isOutput, root=None, parent=None):
        super(ListAttribute, self).__init__(node, attributeDesc, isOutput, root, parent)
        self._value = ListModel(parent=self)

    def __getitem__(self, item):
        return self._value.at(item)

    def __len__(self):
        return len(self._value)

    def _set_value(self, value):
        self._value.clear()
        self.extend(value)
        self.requestGraphUpdate()

    def append(self, value):
        self.extend([value])

    def insert(self, index, value):
        values = value if isinstance(value, list) else [value]
        attrs = [attribute_factory(self.attributeDesc.elementDesc, v, self.isOutput, self.node, self) for v in values]
        self._value.insert(index, attrs)
        self.valueChanged.emit()
        self._applyExpr()
        self.requestGraphUpdate()

    def index(self, item):
        return self._value.indexOf(item)

    def extend(self, values):
        self.insert(len(self._value), values)

    def remove(self, index, count=1):
        if self.node.graph:
            for i in range(index, index + count):
                attr = self[i]
                if attr.isLink:
                    self.node.graph.removeEdge(attr)  # delete edge if the attribute is linked
        self._value.removeAt(index, count)
        self.requestGraphUpdate()
        self.valueChanged.emit()

    def uid(self, uidIndex):
        uids = []
        for value in self._value:
            if uidIndex in value.desc.uid:
                uids.append(value.uid(uidIndex))
        return hash(uids)

    def _applyExpr(self):
        if not self.node.graph:
            return
        for value in self._value:
            value._applyExpr()

    def getExportValue(self):
        return [attr.getExportValue() for attr in self._value]

    def defaultValue(self):
        return []

    def _isDefault(self):
        return len(self._value) == 0

    def getPrimitiveValue(self, exportDefault=True):
        if exportDefault:
            return [attr.getPrimitiveValue(exportDefault=exportDefault) for attr in self._value]
        else:
            return [attr.getPrimitiveValue(exportDefault=exportDefault) for attr in self._value if not attr.isDefault]

    def getValueStr(self):
        return self.attributeDesc.joinChar.join([v.getValueStr() for v in self._value])

    # Override value property setter
    value = Property(Variant, Attribute._get_value, _set_value, notify=Attribute.valueChanged)
    isDefault = Property(bool, _isDefault, notify=Attribute.valueChanged)


class GroupAttribute(Attribute):

    def __init__(self, node, attributeDesc, isOutput, root=None, parent=None):
        super(GroupAttribute, self).__init__(node, attributeDesc, isOutput, root, parent)
        self._value = DictModel(keyAttrName='name', parent=self)

        subAttributes = []
        for subAttrDesc in self.attributeDesc.groupDesc:
            childAttr = attribute_factory(subAttrDesc, None, self.isOutput, self.node, self)
            subAttributes.append(childAttr)
            childAttr.valueChanged.connect(self.valueChanged)

        self._value.reset(subAttributes)

    def __getattr__(self, key):
        try:
            return super(GroupAttribute, self).__getattr__(key)
        except AttributeError:
            try:
                return self._value.get(key)
            except KeyError:
                raise AttributeError(key)

    def _set_value(self, exportedValue):
        # set individual child attribute values
        for key, value in exportedValue.items():
            self._value.get(key).value = value

    def uid(self, uidIndex):
        uids = []
        for k, v in self._value.items():
            if uidIndex in v.desc.uid:
                uids.append(v.uid(uidIndex))
        return hash(uids)

    def _applyExpr(self):
        for value in self._value:
            value._applyExpr()

    def getExportValue(self):
        return {key: attr.getExportValue() for key, attr in self._value.objects.items()}

    def _isDefault(self):
        return all(v.isDefault for v in self._value)

    def defaultValue(self):
        return {key: attr.defaultValue() for key, attr in self._value.items()}

    def getPrimitiveValue(self, exportDefault=True):
        if exportDefault:
            return {name: attr.getPrimitiveValue(exportDefault=exportDefault) for name, attr in self._value.items()}
        else:
            return {name: attr.getPrimitiveValue(exportDefault=exportDefault) for name, attr in self._value.items() if not attr.isDefault}

    def getValueStr(self):
        return self.attributeDesc.joinChar.join([v.getValueStr() for v in self._value.objects.values()])

    # Override value property
    value = Property(Variant, Attribute._get_value, _set_value, notify=Attribute.valueChanged)
    isDefault = Property(bool, _isDefault, notify=Attribute.valueChanged)


class Edge(BaseObject):

    def __init__(self, src, dst, parent=None):
        super(Edge, self).__init__(parent)
        self._src = weakref.ref(src)
        self._dst = weakref.ref(dst)
        self._repr = "<Edge> {} -> {}".format(self._src(), self._dst())

    @property
    def src(self):
        return self._src()

    @property
    def dst(self):
        return self._dst()

    src = Property(Attribute, src.fget, constant=True)
    dst = Property(Attribute, dst.fget, constant=True)


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
    for k, v in runningProcesses.iteritems():
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

    def __init__(self, nodeType, parent=None, **kwargs):
        """
        Create a new Node instance based of the given node type name (name of a desc.Node subclass).
        Any other keyword argument will be used to initialize this node's attributes.

        Args:
            nodeType: the node type name
            parent (BaseObject): this Node's parent
            **kwargs: attributes values
        """
        super(Node, self).__init__(parent)
        self.nodeDesc = meshroom.core.nodesDesc[nodeType]()
        self.packageName = self.nodeDesc.packageName
        self.packageVersion = self.nodeDesc.packageVersion

        self._name = None  # type: str
        self.graph = None  # type: Graph
        self.dirty = True  # whether this node's outputs must be re-evaluated on next Graph update
        self._chunks = ListModel(parent=self)
        self._cmdVars = {}
        self._size = 0
        self._attributes = DictModel(keyAttrName='name', parent=self)
        self.attributesPerUid = defaultdict(set)
        self._initFromDesc()
        for k, v in kwargs.items():
            self.attribute(k).value = v


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
        with GraphModification(self.graph):
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

    def _buildCmdVars(self, cmdVars):
        for uidIndex, associatedAttributes in self.attributesPerUid.items():
            assAttr = [(a.getName(), a.uid(uidIndex)) for a in associatedAttributes]
            assAttr.sort()
            cmdVars['uid{}'.format(uidIndex)] = hash(tuple([b for a, b in assAttr]))

        # Evaluate input params
        for name, attr in self._attributes.objects.items():
            if attr.isOutput:
                continue  # skip outputs
            v = attr.getValueStr()

            cmdVars[name] = '--{name} {value}'.format(name=name, value=v)
            cmdVars[name + 'Value'] = str(v)

            if v is not None and v is not '':
                cmdVars[attr.attributeDesc.group] = cmdVars.get(attr.attributeDesc.group, '') + \
                                                          ' ' + cmdVars[name]

        # For updating output attributes invalidation values
        cmdVarsNoCache = cmdVars.copy()
        cmdVarsNoCache['cache'] = ''

        # Evaluate output params
        for name, attr in self._attributes.objects.items():
            if attr.isInput:
                continue  # skip inputs
            attr.value = attr.attributeDesc.value.format(
                **cmdVars)
            attr._invalidationValue = attr.attributeDesc.value.format(
                **cmdVarsNoCache)
            v = attr.getValueStr()

            cmdVars[name] = '--{name} {value}'.format(name=name, value=v)
            cmdVars[name + 'Value'] = str(v)

            if v is not None and v is not '':
                cmdVars[attr.attributeDesc.group] = cmdVars.get(attr.attributeDesc.group, '') + \
                                                          ' ' + cmdVars[name]

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

    def updateInternals(self):
        """ Update Node's internal parameters and output attributes.

        This method is called when:
         - an input parameter is modified
         - the graph main cache directory is changed
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
            'cache': self.graph.cacheDir,
            'nodeType': self.nodeType,
        }
        self._buildCmdVars(self._cmdVars)
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


WHITE = 0
GRAY = 1
BLACK = 2


class Visitor(object):
    """
    Base class for Graph Visitors that does nothing.
    Sub-classes can override any method to implement specific algorithms.
    """

    # def initializeVertex(self, s, g):
    #     '''is invoked on every vertex of the graph before the start of the graph search.'''
    #     pass
    # def startVertex(self, s, g):
    #     '''is invoked on the source vertex once before the start of the search.'''
    #     pass

    def discoverVertex(self, u, g):
        """ Is invoked when a vertex is encountered for the first time. """
        pass

    def examineEdge(self, e, g):
        """ Is invoked on every out-edge of each vertex after it is discovered."""
        pass

    def treeEdge(self, e, g):
        """ Is invoked on each edge as it becomes a member of the edges that form the search tree.
        If you wish to record predecessors, do so at this event point. """
        pass

    def backEdge(self, e, g):
        """ Is invoked on the back edges in the graph. """
        pass

    def forwardOrCrossEdge(self, e, g):
        """ Is invoked on forward or cross edges in the graph.
        In an undirected graph this method is never called."""
        pass

    def finishEdge(self, e, g):
        """ Is invoked on the non-tree edges in the graph
        as well as on each tree edge after its target vertex is finished. """
        pass

    def finishVertex(self, u, g):
        """ Is invoked on a vertex after all of its out edges have been added to the search tree and all of the
        adjacent vertices have been discovered (but before their out-edges have been examined). """
        pass


def changeTopology(func):
    """
    Graph methods modifying the graph topology (add/remove edges or nodes)
    must be decorated with 'changeTopology' for update mechanism to work as intended.
    """
    def decorator(self, *args, **kwargs):
        assert isinstance(self, Graph)
        # call method
        result = func(self, *args, **kwargs)
        # mark graph dirty
        self.dirtyTopology = True
        # request graph update
        self.update()
        return result
    return decorator


class Graph(BaseObject):
    """
    _________________      _________________      _________________
    |               |      |               |      |               |
    |     Node A    |      |     Node B    |      |     Node C    |
    |               | edge |               | edge |               |
    |input    output|>---->|input    output|>---->|input    output|
    |_______________|      |_______________|      |_______________|

    Data structures:

        nodes = {'A': <nodeA>, 'B': <nodeB>, 'C': <nodeC>}
        edges = {B.input: A.output, C.input: B.output,}

    """

    def __init__(self, name, parent=None):
        super(Graph, self).__init__(parent)
        self.name = name
        self._updateEnabled = True
        self._updateRequested = False
        self.dirtyTopology = False
        self._nodesMinMaxDepths = {}
        self._nodes = DictModel(keyAttrName='name', parent=self)
        self._edges = DictModel(keyAttrName='dst', parent=self)  # use dst attribute as unique key since it can only have one input connection
        self._cacheDir = meshroom.core.defaultCacheFolder
        self._filepath = ''

    def clear(self):
        self._nodes.clear()
        self._edges.clear()

    @Slot(str)
    def load(self, filepath):
        self.clear()
        with open(filepath) as jsonFile:
            graphData = json.load(jsonFile)
        if not isinstance(graphData, dict):
            raise RuntimeError('loadGraph error: Graph is not a dict. File: {}'.format(filepath))

        with GraphModification(self):
            # iterate over nodes sorted by suffix index in their names
            for nodeName, nodeData in sorted(graphData.items(), key=lambda x: self.getNodeIndexFromName(x[0])):
                if not isinstance(nodeData, dict):
                    raise RuntimeError('loadGraph error: Node is not a dict. File: {}'.format(filepath))
                n = Node(nodeData['nodeType'], **nodeData['attributes'])
                # Add node to the graph with raw attributes values
                self._addNode(n, nodeName)

        # Update filepath related members
        self._setFilepath(filepath)

        # Create graph edges by resolving attributes expressions
        self._applyExpr()

    @property
    def updateEnabled(self):
        return self._updateEnabled

    @updateEnabled.setter
    def updateEnabled(self, enabled):
        self._updateEnabled = enabled
        if enabled and self._updateRequested:
            # Trigger an update if requested while disabled
            self.update()
            self._updateRequested = False

    @changeTopology
    def _addNode(self, node, uniqueName):
        """
        Internal method to add the given node to this Graph, with the given name (must be unique).
        Attribute expressions are not resolved.
        """
        if node.graph is not None and node.graph != self:
            raise RuntimeError(
                'Node "{}" cannot be part of the Graph "{}", as it is already part of the other graph "{}".'.format(
                    node.nodeType, self.name, node.graph.name))

        assert uniqueName not in self._nodes.keys()
        node._name = uniqueName
        node.graph = self
        self._nodes.add(node)

    def addNode(self, node, uniqueName=None):
        """
        Add the given node to this Graph with an optional unique name,
        and resolve attributes expressions.
        """
        self._addNode(node, uniqueName if uniqueName else self._createUniqueNodeName(node.nodeType))
        # Resolve attribute expressions
        node._applyExpr()
        return node

    def outEdges(self, attribute):
        """ Return the list of edges starting from the given attribute """
        # type: (Attribute,) -> [Edge]
        return [edge for edge in self.edges if edge.src == attribute]

    def nodeInEdges(self, node):
        # type: (Node) -> [Edge]
        """ Return the list of edges arriving to this node """
        return [edge for edge in self.edges if edge.dst.node == node]

    def nodeOutEdges(self, node):
        # type: (Node) -> [Edge]
        """ Return the list of edges starting from this node """
        return [edge for edge in self.edges if edge.src.node == node]

    @changeTopology
    def removeNode(self, nodeName):
        """
        Remove the node identified by 'nodeName' from the graph
        and return in and out edges removed by this operation in two dicts {dstAttr.fullName(), srcAttr.fullName()}
        """
        node = self.node(nodeName)
        inEdges = {}
        outEdges = {}

        # Remove all edges arriving to and starting from this node
        with GraphModification(self):
            for edge in self.nodeOutEdges(node):
                self.removeEdge(edge.dst)
                outEdges[edge.dst.fullName()] = edge.src.fullName()
            for edge in self.nodeInEdges(node):
                self.removeEdge(edge.dst)
                inEdges[edge.dst.fullName()] = edge.src.fullName()

            self._nodes.remove(node)
            self.update()

        return inEdges, outEdges

    def addNewNode(self, nodeType, name=None, **kwargs):
        """
        Create and add a new node to the graph.

        Args:
            nodeType (str): the node type name.
            name (str): if specified, the desired name for this node. If not unique, will be prefixed (_N).
            **kwargs: keyword arguments to initialize node's attributes

        Returns:
             The newly created node.
        """
        if name and name in self._nodes.keys():
            name = self._createUniqueNodeName(name)
        n = self.addNode(Node(nodeType=nodeType, **kwargs), uniqueName=name)
        n.updateInternals()
        return n

    def _createUniqueNodeName(self, inputName):
        i = 1
        while i:
            newName = "{name}_{index}".format(name=inputName, index=i)
            if newName not in self._nodes.objects:
                return newName
            i += 1

    def node(self, nodeName):
        return self._nodes.get(nodeName)

    @Slot(str, result=Attribute)
    def attribute(self, fullName):
        # type: (str) -> Attribute
        """
        Return the attribute identified by the unique name 'fullName'.
        """
        node, attribute = fullName.split('.', 1)
        return self.node(node).attribute(attribute)

    @staticmethod
    def getNodeIndexFromName(name):
        """ Nodes are created with a suffix index; returns this index by parsing node name.

        Args:
            name (str): the node name
        Returns:
             int: the index retrieved from node name (-1 if not found)
        """
        try:
            return int(name.split('_')[-1])
        except:
            return -1

    @staticmethod
    def sortNodesByIndex(nodes):
        """
        Sort the given list of Nodes using the suffix index in their names.
        [NodeName_1, NodeName_0] => [NodeName_0, NodeName_1]

        Args:
            nodes (list[Node]): the list of Nodes to sort
        Returns:
            list[Node]: the sorted list of Nodes based on their index
        """
        return sorted(nodes, key=lambda x: Graph.getNodeIndexFromName(x.name))

    def nodesByType(self, nodeType, sortedByIndex=True):
        """
        Returns all Nodes of the given nodeType.

        Args:
            nodeType (str): the node type name to consider.
            sortedByIndex (bool): whether to sort the nodes by their index (see Graph.sortNodesByIndex)
        Returns:
            list[Node]: the list of nodes matching the given nodeType.
        """
        nodes = [n for n in self._nodes.values() if n.nodeType == nodeType]
        return self.sortNodesByIndex(nodes) if sortedByIndex else nodes

    def findNodeCandidates(self, nodeNameExpr):
        pattern = re.compile(nodeNameExpr)
        return [v for k, v in self._nodes.objects.items() if pattern.match(k)]

    def findNode(self, nodeExpr):
        candidates = self.findNodeCandidates('^' + nodeExpr)
        if not candidates:
            raise KeyError('No node candidate for "{}"'.format(nodeExpr))
        elif len(candidates) > 1:
            raise KeyError('Multiple node candidates for "{}": {}'.format(nodeExpr, str([c.name for c in candidates])))
        return candidates[0]

    def findNodes(self, nodesExpr):
        return [self.findNode(nodeName) for nodeName in nodesExpr]

    def edge(self, dstAttributeName):
        return self._edges.get(dstAttributeName)

    def getLeaves(self):
        nodesWithOutput = set([edge.src.node for edge in self.edges])
        return set(self._nodes) - nodesWithOutput

    @changeTopology
    def addEdge(self, srcAttr, dstAttr):
        assert isinstance(srcAttr, Attribute)
        assert isinstance(dstAttr, Attribute)
        if srcAttr.node.graph != self or dstAttr.node.graph != self:
            raise RuntimeError('The attributes of the edge should be part of a common graph.')
        if dstAttr in self.edges.keys():
            raise RuntimeError('Destination attribute "{}" is already connected.'.format(dstAttr.fullName()))
        edge = Edge(srcAttr, dstAttr)
        self.edges.add(edge)
        self.markNodesDirty(dstAttr.node)
        dstAttr.valueChanged.emit()
        dstAttr.isLinkChanged.emit()
        return edge

    def addEdges(self, *edges):
        with GraphModification(self):
            for edge in edges:
                self.addEdge(*edge)

    @changeTopology
    def removeEdge(self, dstAttr):
        if dstAttr not in self.edges.keys():
            raise RuntimeError('Attribute "{}" is not connected'.format(dstAttr.fullName()))
        self.edges.pop(dstAttr)
        self.markNodesDirty(dstAttr.node)
        dstAttr.valueChanged.emit()
        dstAttr.isLinkChanged.emit()

    def getDepth(self, node, minimal=False):
        """ Return node's depth in this Graph.
        By default, returns the maximal depth of the node unless minimal is set to True.

        Args:
            node (Node): the node to consider.
            minimal (bool): whether to return the minimal depth instead of the maximal one (default).
        Returns:
            int: the node's depth in this Graph.
        """
        assert node.graph == self
        assert not self.dirtyTopology
        minDepth, maxDepth = self._nodesMinMaxDepths[node]
        return minDepth if minimal else maxDepth

    def getInputEdges(self, node):
        return set([edge for edge in self.edges if edge.dst.node is node])

    def _getInputEdgesPerNode(self):
        nodeEdges = defaultdict(set)

        for edge in self.edges:
            nodeEdges[edge.dst.node].add(edge.src.node)

        return nodeEdges

    def _getOutputEdgesPerNode(self):
        nodeEdges = defaultdict(set)

        for edge in self.edges:
            nodeEdges[edge.src.node].add(edge.dst.node)

        return nodeEdges

    def dfs(self, visitor, startNodes=None, longestPathFirst=False, reverse=False):
        # Default direction: from node to root
        # Reverse direction: from node to leaves
        nodeChildren = self._getOutputEdgesPerNode() if reverse else self._getInputEdgesPerNode()
        # Initialize color map
        colors = {}
        for u in self._nodes:
            colors[u] = WHITE

        nodes = startNodes or self.getLeaves()

        if longestPathFirst:
            # Graph topology must be known and node depths up-to-date
            assert not self.dirtyTopology
            nodes = sorted(nodes, key=lambda item: item.depth)

        for node in nodes:
            self.dfsVisit(node, visitor, colors, nodeChildren, longestPathFirst)

    def dfsVisit(self, u, visitor, colors, nodeChildren, longestPathFirst):
        colors[u] = GRAY
        visitor.discoverVertex(u, self)
        # d_time[u] = time = time + 1
        children = nodeChildren[u]
        if longestPathFirst:
            assert not self.dirtyTopology
            children = sorted(children, reverse=True, key=lambda item: self._nodesMinMaxDepths[item][1])
        for v in children:
            visitor.examineEdge((u, v), self)
            if colors[v] == WHITE:
                visitor.treeEdge((u, v), self)
                # (u,v) is a tree edge
                self.dfsVisit(v, visitor, colors, nodeChildren, longestPathFirst)  # TODO: avoid recursion
            elif colors[v] == GRAY:
                visitor.backEdge((u, v), self)
                pass  # (u,v) is a back edge
            elif colors[v] == BLACK:
                visitor.forwardOrCrossEdge((u, v), self)
                pass  # (u,v) is a cross or forward edge
            visitor.finishEdge((u, v), self)
        colors[u] = BLACK
        visitor.finishVertex(u, self)

    def dfsOnFinish(self, startNodes=None):
        """
        :param startNodes: list of starting nodes. Use all leaves if empty.
        :return: visited nodes and edges. The order is defined by the visit and finishVertex event.
        """
        nodes = []
        edges = []
        visitor = Visitor()
        visitor.finishVertex = lambda vertex, graph: nodes.append(vertex)
        visitor.finishEdge = lambda edge, graph: edges.append(edge)
        self.dfs(visitor=visitor, startNodes=startNodes)
        return nodes, edges

    def dfsToProcess(self, startNodes=None):
        """
        :param startNodes: list of starting nodes. Use all leaves if empty.
        :return: visited nodes and edges that are not already computed (node.status != SUCCESS).
                 The order is defined by the visit and finishVertex event.
        """
        nodes = []
        edges = []
        visitor = Visitor()

        def finishVertex(vertex, graph):
            chunksToProcess = []
            for chunk in vertex.chunks:
                if chunk.status.status is Status.SUBMITTED:
                    logging.warning('Node "{}" is already submitted.'.format(chunk.name))
                if chunk.status.status is Status.RUNNING:
                    logging.warning('Node "{}" is already running.'.format(chunk.name))
                if chunk.status.status is not Status.SUCCESS:
                    chunksToProcess.append(chunk)
            if chunksToProcess:
                nodes.append(vertex)  # We could collect specific chunks

        def finishEdge(edge, graph):
            if edge[0].hasStatus(Status.SUCCESS) or edge[1].hasStatus(Status.SUCCESS):
                return
            else:
                edges.append(edge)

        visitor.finishVertex = finishVertex
        visitor.finishEdge = finishEdge
        self.dfs(visitor=visitor, startNodes=startNodes)
        return nodes, edges

    def minMaxDepthPerNode(self, startNodes=None):
        """
        Compute the min and max depth for each node.

        Args:
            startNodes: list of starting nodes. Use all leaves if empty.

        Returns:
            dict: {node: (minDepth, maxDepth)}
        """
        depthPerNode = {}
        for node in self.nodes:
            depthPerNode[node] = (0, 0)

        visitor = Visitor()

        def finishEdge(edge, graph):
            u, v = edge
            du = depthPerNode[u]
            dv = depthPerNode[v]
            if du[0] == 0:
                # if not initialized, set the depth of the first child
                depthMin = dv[0] + 1
            else:
                depthMin = min(du[0], dv[0] + 1)
            depthPerNode[u] = (depthMin, max(du[1], dv[1] + 1))

        visitor.finishEdge = finishEdge
        self.dfs(visitor=visitor, startNodes=startNodes)
        return depthPerNode

    def dfsMaxEdgeLength(self, startNodes=None):
        """
        :param startNodes: list of starting nodes. Use all leaves if empty.
        :return:
        """
        nodesStack = []
        edgesScore = defaultdict(lambda: 0)
        visitor = Visitor()

        def finishEdge(edge, graph):
            u, v = edge
            for i, n in enumerate(reversed(nodesStack)):
                index = i + 1
                if index > edgesScore[(n, v)]:
                    edgesScore[(n, v)] = index

        def finishVertex(vertex, graph):
            v = nodesStack.pop()
            assert v == vertex

        visitor.discoverVertex = lambda vertex, graph: nodesStack.append(vertex)
        visitor.finishVertex = finishVertex
        visitor.finishEdge = finishEdge
        self.dfs(visitor=visitor, startNodes=startNodes, longestPathFirst=True)
        return edgesScore

    def flowEdges(self, startNodes=None):
        """
        Return as few edges as possible, such that if there is a directed path from one vertex to another in the
        original graph, there is also such a path in the reduction.

        :param startNodes:
        :return: the remaining edges after a transitive reduction of the graph.
        """
        flowEdges = []
        edgesScore = self.dfsMaxEdgeLength(startNodes)

        for link, score in edgesScore.items():
            assert score != 0
            if score == 1:
                flowEdges.append(link)
        return flowEdges

    def nodesFromNode(self, startNode, filterType=None):
        """
        Return the node chain from startNode to the graph leaves.

        Args:
            startNode (Node): the node to start the visit from.
            filterType (str): (optional) only return the nodes of the given type
                              (does not stop the visit, this is a post-process only)
        Returns:
            The list of nodes from startNode to the graph leaves following edges.
        """
        nodes = []
        edges = []
        visitor = Visitor()

        def discoverVertex(vertex, graph):
            if not filterType or vertex.nodeType == filterType:
                nodes.append(vertex)

        visitor.discoverVertex = discoverVertex
        visitor.examineEdge = lambda edge, graph: edges.append(edge)
        self.dfs(visitor=visitor, startNodes=[startNode], reverse=True)
        return nodes, edges

    def _applyExpr(self):
        with GraphModification(self):
            for node in self._nodes:
                node._applyExpr()

    def toDict(self):
        return {k: node.toDict() for k, node in self._nodes.objects.items()}

    @Slot(result=str)
    def asString(self):
        return str(self.toDict())

    def save(self, filepath=None):
        data = self.toDict()
        path = filepath or self._filepath
        if not path:
            raise ValueError("filepath must be specified for unsaved files.")

        with open(path, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)

        if path != self._filepath:
            self._setFilepath(path)

    def _setFilepath(self, filepath):
        """
        Set the internal filepath of this Graph.
        This method should not be used directly from outside, use save/load instead.
        Args:
            filepath: the graph file path
        """
        assert os.path.isfile(filepath)

        if self._filepath == filepath:
            return
        self._filepath = filepath
        # For now:
        #  * cache folder is located next to the graph file
        #  * graph name if the basename of the graph file
        self.name = os.path.splitext(os.path.basename(filepath))[0]
        self.cacheDir = os.path.join(os.path.abspath(os.path.dirname(filepath)), meshroom.core.cacheFolderName)
        self.filepathChanged.emit()

    def updateInternals(self, startNodes=None, force=False):
        nodes, edges = self.dfsOnFinish(startNodes=startNodes)
        for node in nodes:
            if node.dirty or force:
                node.updateInternals()

    def updateStatusFromCache(self, force=False):
        for node in self._nodes:
            if node.dirty or force:
                node.updateStatusFromCache()

    def updateStatisticsFromCache(self):
        for node in self._nodes:
            node.updateStatisticsFromCache()

    def update(self):
        if not self._updateEnabled:
            # To do the update once for multiple changes
            self._updateRequested = True
            return

        # Graph topology has changed
        if self.dirtyTopology:
            # Update nodes depths cache
            self._nodesMinMaxDepths = self.minMaxDepthPerNode()
            self.dirtyTopology = False

        self.updateInternals()
        if os.path.exists(self._cacheDir):
            self.updateStatusFromCache()
        for node in self.nodes:
            node.dirty = False

        self.updated.emit()

    def markNodesDirty(self, fromNode):
        """
        Mark all nodes following 'fromNode' as dirty, and request a graph update.
        All nodes marked as dirty will get their outputs to be re-evaluated
        during the next graph update.

        Args:
            fromNode (Node): the node to start the invalidation from

        See Also:
            Graph.update, Graph.updateInternals, Graph.updateStatusFromCache
        """
        nodes, edges = self.nodesFromNode(fromNode)
        for node in nodes:
            node.dirty = True
        self.update()

    def stopExecution(self):
        """ Request graph execution to be stopped by terminating running chunks"""
        for chunk in self.iterChunksByStatus(Status.RUNNING):
            chunk.stopProcess()

    def clearSubmittedNodes(self):
        """ Reset the status of already submitted nodes to Status.NONE """
        for node in self.nodes:
            node.clearSubmittedChunks()

    def iterChunksByStatus(self, status):
        """ Iterate over NodeChunks with the given status """
        for node in self.nodes:
            for chunk in node.chunks:
                if chunk.status.status == status:
                    yield chunk

    def getChunksByStatus(self, status):
        """ Return the list of NodeChunks with the given status """
        chunks = []
        for node in self.nodes:
            chunks += [chunk for chunk in node.chunks if chunk.status.status == status]
        return chunks

    def getChunks(self, nodes=None):
        """ Returns the list of NodeChunks for the given list of nodes (for all nodes if nodes is None) """
        chunks = []
        for node in nodes or self.nodes:
            chunks += [chunk for chunk in node.chunks]
        return chunks

    def getOrderedChunks(self):
        """ Get chunks as visited by dfsOnFinish.

        Returns:
            list of NodeChunks: the ordered list of NodeChunks
        """
        return self.getChunks(self.dfsOnFinish()[0])

    @property
    def nodes(self):
        return self._nodes

    @property
    def edges(self):
        return self._edges

    @property
    def cacheDir(self):
        return self._cacheDir

    @cacheDir.setter
    def cacheDir(self, value):
        if self._cacheDir == value:
            return
        self._cacheDir = value
        self.updateInternals(force=True)
        self.updateStatusFromCache(force=True)
        self.cacheDirChanged.emit()

    nodes = Property(BaseObject, nodes.fget, constant=True)
    edges = Property(BaseObject, edges.fget, constant=True)
    filepathChanged = Signal()
    filepath = Property(str, lambda self: self._filepath, notify=filepathChanged)
    cacheDirChanged = Signal()
    cacheDir = Property(str, cacheDir.fget, cacheDir.fset, notify=cacheDirChanged)
    updated = Signal()


def loadGraph(filepath):
    """
    """
    graph = Graph("")
    graph.load(filepath)
    return graph


def getAlreadySubmittedChunks(nodes):
    out = []
    for node in nodes:
        for chunk in node.chunks:
            if chunk.isAlreadySubmitted():
                out.append(chunk)
    return out


def execute(graph, toNodes=None, forceCompute=False, forceStatus=False):
    """
    """
    if forceCompute:
        nodes, edges = graph.dfsOnFinish(startNodes=toNodes)
    else:
        nodes, edges = graph.dfsToProcess(startNodes=toNodes)
        chunksInConflict = getAlreadySubmittedChunks(nodes)

        if chunksInConflict:
            chunksStatus = set([chunk.status.status.name for chunk in chunksInConflict])
            chunksName = [node.name for node in chunksInConflict]
            msg = 'WARNING: Some nodes are already submitted with status: {}\nNodes: {}'.format(
                  ', '.join(chunksStatus),
                  ', '.join(chunksName)
                  )
            if forceStatus:
                print(msg)
            else:
                raise RuntimeError(msg)

    print('Nodes to execute: ', str([n.name for n in nodes]))

    for node in nodes:
        node.beginSequence(forceCompute)

    for n, node in enumerate(nodes):
        try:
            multiChunks = len(node.chunks) > 1
            for c, chunk in enumerate(node.chunks):
                if multiChunks:
                    print('\n[{node}/{nbNodes}]({chunk}/{nbChunks}) {nodeName}'.format(
                        node=n+1, nbNodes=len(nodes),
                        chunk=c+1, nbChunks=len(node.chunks), nodeName=node.nodeType))
                else:
                    print('\n[{node}/{nbNodes}] {nodeName}'.format(
                        node=n + 1, nbNodes=len(nodes), nodeName=node.nodeType))
                chunk.process(forceCompute)
        except Exception as e:
            logging.error("Error on node computation: {}".format(e))
            graph.clearSubmittedNodes()
            raise

    for node in nodes:
        node.endSequence()


def submitGraph(graph, submitter, toNodes=None):
    nodesToProcess, edgesToProcess = graph.dfsToProcess(startNodes=toNodes)
    flowEdges = graph.flowEdges(startNodes=toNodes)
    edgesToProcess = set(edgesToProcess).intersection(flowEdges)

    if not nodesToProcess:
        logging.warning('Nothing to compute')
        return

    logging.info("Nodes to process: {}".format(edgesToProcess))
    logging.info("Edges to process: {}".format(edgesToProcess))

    sub = meshroom.core.submitters.get(submitter, None)
    if sub is None:
        raise RuntimeError("Unknown Submitter : " + submitter)

    try:
        res = sub.submit(nodesToProcess, edgesToProcess, graph.filepath)
        if res:
            for node in nodesToProcess:
                node.submit()  # update node status
    except Exception as e:
        logging.error("Error on submit : {}".format(e))


def submit(graphFile, submitter, toNode=None):
    """
    Submit the given graph via the given submitter.
    """
    graph = loadGraph(graphFile)
    toNodes = graph.findNodes([toNode]) if toNode else None
    submitGraph(graph, submitter, toNodes)

