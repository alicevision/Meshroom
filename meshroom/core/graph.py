from __future__ import print_function

import atexit
import collections
import hashlib
import json
import os
import psutil
import re
import shutil
import time
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

stringIsLinkRe = re.compile('^\{.+\}$')

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
    # Store update policy
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


def attribute_factory(description, value, isOutput, node, parent=None):
    # type: (desc.Attribute, (), bool, Node, Attribute) -> Attribute
    """
    Create an Attribute based on description type.

    Args:
        description: the Attribute description
        value:  value of the Attribute. Will be set if not None.
        isOutput: whether is Attribute is an output attribute.
        node: node owning the Attribute. Note that the created Attribute is not added to Node's attributes
        parent: (optional) parent Attribute (must be ListAttribute or GroupAttribute)
    """
    if isinstance(description, meshroom.core.desc.GroupAttribute):
        cls = GroupAttribute
    elif isinstance(description, meshroom.core.desc.ListAttribute):
        cls = ListAttribute
    else:
        cls = Attribute
    attr = cls(node, description, isOutput, parent=parent)
    if value is not None:
        attr.value = value
    return attr


class Attribute(BaseObject):
    """
    """

    def __init__(self, node, attributeDesc, isOutput, parent=None):
        super(Attribute, self).__init__(parent)
        self._name = attributeDesc.name
        self.node = node  # type: Node
        self.attributeDesc = attributeDesc
        self._isOutput = isOutput
        self._value = attributeDesc.value
        self._label = attributeDesc.label

        # invalidation value for output attributes
        self._invalidationValue = ""

    def absoluteName(self):
        return '{}.{}.{}'.format(self.node.graph.name, self.node.name, self._name)

    def fullName(self):
        """ Name inside the Graph: nodeName.name """
        if isinstance(self.parent(), ListAttribute):
            return '{}[{}]'.format(self.parent().fullName(), self.parent().index(self))
        elif isinstance(self.parent(), GroupAttribute):
            return '{}.{}'.format(self.parent().fullName(), self._name)
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
        if self.node.graph and self.isInput:
            self.node.graph.update()
        self.valueChanged.emit()

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
        return self.isInput and self in self.node.graph.edges.keys()

    def getLinkParam(self):
        return self.node.graph.edge(self).src if self.isLink else None

    def _applyExpr(self):
        """
        For string parameters with an expression (when loaded from file),
        this function convert the expression into a real edge in the graph
        and clear the string value.
        """
        v = self._value
        if isinstance(v, Attribute):
            g = self.node.graph
            g.addEdge(v, self)
            self._value = ""
        elif isinstance(v, basestring) and len(v) > 2 and v[0] == '{' and v[-1] == '}':
            # value is a link to another attribute
            g = self.node.graph
            link = v[1:-1]
            linkNode, linkAttr = link.split('.')
            g.addEdge(g.node(linkNode).attribute(linkAttr), self)
            self._value = ""

    def getExportValue(self):
        return '{' + self.getLinkParam().fullName() + '}' if self.isLink else self._value

    name = Property(str, getName, constant=True)
    label = Property(str, getLabel, constant=True)
    type = Property(str, getType, constant=True)
    desc = Property(desc.Attribute, lambda self: self.attributeDesc, constant=True)
    valueChanged = Signal()
    value = Property(Variant, _get_value, _set_value, notify=valueChanged)
    isOutput = Property(bool, isOutput.fget, constant=True)
    isLinkChanged = Signal()
    isLink = Property(bool, isLink.fget, notify=isLinkChanged)


class ListAttribute(Attribute):

    def __init__(self, node, attributeDesc, isOutput, parent=None):
        super(ListAttribute, self).__init__(node, attributeDesc, isOutput, parent)
        self._value = ListModel(parent=self)

    def __getitem__(self, item):
        return self._value.at(item)

    def __len__(self):
        return len(self._value)

    def _set_value(self, value):
        self._value.clear()
        self.extend(value)

    def append(self, value):
        self.extend([value])

    def insert(self, value, index):
        attr = attribute_factory(self.attributeDesc.elementDesc, value, self.isOutput, self.node, self)
        self._value.insert(index, [attr])

    def index(self, item):
        return self._value.indexOf(item)

    def extend(self, values):
        childAttributes = []
        for value in values:
            attr = attribute_factory(self.attributeDesc.elementDesc, value, self.isOutput, self.node, parent=self)
            childAttributes.append(attr)
        self._value.extend(childAttributes)

    def remove(self, index):
        self._value.removeAt(index)

    def uid(self, uidIndex):
        uids = []
        for value in self._value:
            if uidIndex in value.desc.uid:
                uids.append(value.uid(uidIndex))
        return hash(uids)

    def _applyExpr(self):
        for value in self._value:
            value._applyExpr()

    def getExportValue(self):
        return [attr.getExportValue() for attr in self._value]

    # Override value property setter
    value = Property(Variant, Attribute._get_value, _set_value, notify=Attribute.valueChanged)


class GroupAttribute(Attribute):

    def __init__(self, node, attributeDesc, isOutput, parent=None):
        super(GroupAttribute, self).__init__(node, attributeDesc, isOutput, parent)
        self._value = DictModel(keyAttrName='name', parent=self)

        subAttributes = []
        for subAttrDesc in self.attributeDesc.groupDesc:
            childAttr = attribute_factory(subAttrDesc, None, self.isOutput, self.node, parent=self)
            subAttributes.append(childAttr)

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
        for value in self._value:
            if uidIndex in value.desc.uid:
                uids.append(value.uid(uidIndex))
        return hash(uids)

    def _applyExpr(self):
        for value in self._value:
            value._applyExpr()

    def getExportValue(self):
        return {key: attr.getExportValue() for key, attr in self._value.objects.items()}

    # Override value property
    value = Property(Variant, Attribute._get_value, _set_value, notify=Attribute.valueChanged)


class Edge(BaseObject):

    def __init__(self, src, dst, parent=None):
        super(Edge, self).__init__(parent)
        self._src = src
        self._dst = dst

    @property
    def src(self):
        return self._src

    @property
    def dst(self):
        return self._dst

    src = Property(Attribute, src.fget, constant=True)
    dst = Property(Attribute, dst.fget, constant=True)


class Status(Enum):
    """
    """
    NONE = 1
    SUBMITTED_EXTERN = 2
    SUBMITTED_LOCAL = 3
    RUNNING = 4
    ERROR = 5
    KILLED = 6
    SUCCESS = 7


class StatusData:
    """
    """

    def __init__(self, nodeName, nodeType):
        self.status = Status.NONE
        self.nodeName = nodeName
        self.nodeType = nodeType
        self.graph = ''
        self.commandLine = None
        self.env = None

    def reset(self):
        self.status = Status.NONE
        self.graph = ''
        self.commandLine = None
        self.env = None

    def toDict(self):
        return self.__dict__

    def fromDict(self, d):
        self.status = Status._member_map_[d['status']]
        self.nodeName = d.get('nodeName', '')
        self.nodeType = d.get('nodeType', '')
        self.graph = d.get('graph', '')
        self.commandLine = d.get('commandLine', '')
        self.env = d.get('env', '')


runningProcesses = {}

@atexit.register
def clearProcessesStatus():
    global runningProcesses
    for k, v in runningProcesses.iteritems():
        v.upgradeStatusTo(Status.KILLED)


class Node(BaseObject):
    """
    """

    # Regexp handling complex attribute names with recursive understanding of Lists and Groups
    # i.e: a.b, a[0], a[0].b.c[1]
    attributeRE = re.compile(r'\.?(?P<name>\w+)(?:\[(?P<index>\d+)\])?')

    def __init__(self, nodeDesc, parent=None, **kwargs):
        super(Node, self).__init__(parent)
        self._name = None  # type: str
        self.graph = None  # type: Graph
        self.nodeDesc = meshroom.core.nodesDesc[nodeDesc]()
        self.packageName = self.nodeDesc.packageName
        self.packageVersion = self.nodeDesc.packageVersion
        self._cmdVars = {}
        self._attributes = DictModel(keyAttrName='name', parent=self)
        self.attributesPerUid = defaultdict(set)
        self._initFromDesc()
        for k, v in kwargs.items():
            self.attribute(k).value = v

        self.status = StatusData(self.name, self.nodeType)
        self.statistics = stats.Statistics()
        self._subprocess = None

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
            self._attributes.add(attribute_factory(attrDesc, None, False, self, self))

        for attrDesc in self.nodeDesc.outputs:
            assert isinstance(attrDesc, meshroom.core.desc.Attribute)
            self._attributes.add(attribute_factory(attrDesc, None, True, self, self))

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

    def toDict(self):
        attributes = {k: v.getExportValue() for k, v in self._attributes.objects.items()}
        return {
            'nodeType': self.nodeType,
            'packageName': self.packageName,
            'packageVersion': self.packageVersion,
            'attributes': {k: v for k, v in attributes.items() if v is not None},  # filter empty values
        }

    def updateInternals(self):
        self._cmdVars = {
            'cache': self.graph.cacheDir,
            'nodeType': self.nodeType,
        }
        for uidIndex, associatedAttributes in self.attributesPerUid.items():
            assAttr = [(a.getName(), a.uid(uidIndex)) for a in associatedAttributes]
            assAttr.sort()
            self._cmdVars['uid{}'.format(uidIndex)] = hash(tuple([b for a, b in assAttr]))

        # Evaluate input params
        for name, attr in self._attributes.objects.items():
            if attr.isOutput:
                continue  # skip outputs
            v = attr.value
            if isinstance(attr.attributeDesc, desc.ChoiceParam) and not attr.attributeDesc.exclusive:
                assert(isinstance(v, collections.Sequence) and not isinstance(v, basestring))
                v = attr.attributeDesc.joinChar.join(v)

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
            attr.value = attr.attributeDesc.value.format(
                **self._cmdVars)
            attr._invalidationValue = attr.attributeDesc.value.format(
                **cmdVarsNoCache)
            v = attr.value

            self._cmdVars[name] = '--{name} {value}'.format(name=name, value=v)
            self._cmdVars[name + 'Value'] = str(v)

            if v is not None and v is not '':
                self._cmdVars[attr.attributeDesc.group] = self._cmdVars.get(attr.attributeDesc.group, '') + \
                                                          ' ' + self._cmdVars[name]

        self.internalFolderChanged.emit()

    @property
    def internalFolder(self):
        return self.nodeDesc.internalFolder.format(**self._cmdVars)

    def statusFile(self):
        return os.path.join(self.graph.cacheDir, self.internalFolder, 'status')

    def statisticsFile(self):
        return os.path.join(self.graph.cacheDir, self.internalFolder, 'statistics')

    def logFile(self):
        return os.path.join(self.graph.cacheDir, self.internalFolder, 'log')

    def updateStatusFromCache(self):
        """
        Update node status based on status file content/existence.
        """
        statusFile = self.statusFile()
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

    def saveStatusFile(self):
        """
        Write node status on disk.
        """
        data = self.status.toDict()
        statusFilepath = self.statusFile()
        folder = os.path.dirname(statusFilepath)
        if not os.path.exists(folder):
            os.makedirs(folder)
        statusFilepathWriting = statusFilepath + '.writing.' + str(uuid.uuid4())
        with open(statusFilepathWriting, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)
        shutil.move(statusFilepathWriting, statusFilepath)

    def upgradeStatusTo(self, newStatus):
        """
        Upgrade node to the given status and save it on disk.
        """
        if newStatus.value <= self.status.status.value:
            print('WARNING: downgrade status on node "{}" from {} to {}'.format(self._name, self.status.status,
                                                                                newStatus))
        self.status.status = newStatus
        self.statusChanged.emit()
        self.saveStatusFile()

    def updateStatisticsFromCache(self):
        """
        """
        statisticsFile = self.statisticsFile()
        if not os.path.exists(statisticsFile):
            return
        with open(statisticsFile, 'r') as jsonFile:
            statisticsData = json.load(jsonFile)
        self.statistics.fromDict(statisticsData)

    def saveStatistics(self):
        data = self.statistics.toDict()
        statisticsFilepath = self.statisticsFile()
        folder = os.path.dirname(statisticsFilepath)
        if not os.path.exists(folder):
            os.makedirs(folder)
        statisticsFilepathWriting = statisticsFilepath + '.writing.' + str(uuid.uuid4())
        with open(statisticsFilepathWriting, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)
        shutil.move(statisticsFilepathWriting, statisticsFilepath)

    def isAlreadySubmitted(self):
        return self.status.status in (Status.SUBMITTED_EXTERN, Status.SUBMITTED_LOCAL, Status.RUNNING)

    def submit(self):
        self.upgradeStatusTo(Status.SUBMITTED_EXTERN)

    def beginSequence(self):
        self.upgradeStatusTo(Status.SUBMITTED_LOCAL)

    def stopProcess(self):
        self.nodeDesc.stop(self)

    def process(self):
        global runningProcesses
        runningProcesses[self.name] = self
        self.upgradeStatusTo(Status.RUNNING)
        self.statThread = stats.StatisticsThread(self)
        self.statThread.start()
        startTime = time.time()
        try:
            self.nodeDesc.process(self)
        except BaseException:
            self.upgradeStatusTo(Status.ERROR)
            raise
        finally:
            elapsedTime = time.time() - startTime
            print(' - elapsed time:', elapsedTime)
            # ask and wait for the stats thread to stop
            self.statThread.stopRequest()
            self.statThread.join()
            del runningProcesses[self.name]

        self.upgradeStatusTo(Status.SUCCESS)

    def endSequence(self):
        pass

    def getStatus(self):
        return self.status

    @property
    def statusName(self):
        return self.status.status.name

    def __repr__(self):
        return self.name

    name = Property(str, getName, constant=True)
    nodeType = Property(str, nodeType.fget, constant=True)
    attributes = Property(BaseObject, getAttributes, constant=True)
    internalFolderChanged = Signal()
    internalFolder = Property(str, internalFolder.fget, notify=internalFolderChanged)
    depthChanged = Signal()
    depth = Property(int, depth.fget, notify=depthChanged)
    statusChanged = Signal()
    statusName = Property(str, statusName.fget, notify=statusChanged)


WHITE = 0
GRAY = 1
BLACK = 2


class Visitor:
    # def initializeVertex(self, s, g):
    #     '''is invoked on every vertex of the graph before the start of the graph search.'''
    #     pass
    # def startVertex(self, s, g):
    #     '''is invoked on the source vertex once before the start of the search.'''
    #     pass
    def discoverVertex(self, u, g):
        """ is invoked when a vertex is encountered for the first time. """
        pass

    def examineEdge(self, e, g):
        '''is invoked on every out-edge of each vertex after it is discovered.'''
        pass
    def treeEdge(self, e, g):
        '''is invoked on each edge as it becomes a member of the edges that form the search tree. If you wish to record predecessors, do so at this event point.'''
        pass
    def backEdge(self, e, g):
        '''is invoked on the back edges in the graph.'''
        pass
    def forwardOrCrossEdge(self, e, g):
        '''is invoked on forward or cross edges in the graph. In an undirected graph this method is never called.'''
        pass
    def finishEdge(self, e, g):
        '''is invoked on the non-tree edges in the graph as well as on each tree edge after its target vertex is finished.'''
        pass
    def finishVertex(self, u, g):
        """ is invoked on a vertex after all of its out edges have been added to the search tree and all of the
        adjacent vertices have been discovered (but before their out-edges have been examined). """
        pass


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
        self._nodes = DictModel(keyAttrName='name', parent=self)
        self._edges = DictModel(keyAttrName='dst', parent=self)  # use dst attribute as unique key since it can only have one input connection
        self._cacheDir = ''

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

        self.cacheDir = os.path.join(os.path.abspath(os.path.dirname(filepath)), meshroom.core.cacheFolderName)
        self.name = os.path.splitext(os.path.basename(filepath))[0]
        for nodeName, nodeData in graphData.items():
            if not isinstance(nodeData, dict):
                raise RuntimeError('loadGraph error: Node is not a dict. File: {}'.format(filepath))
            n = Node(nodeData['nodeType'], parent=self, **nodeData['attributes'])
            # Add node to the graph with raw attributes values
            self._addNode(n, nodeName)

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
        self.stopExecutionRequested.connect(node.stopProcess)

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

    def removeNode(self, nodeName):
        """
        Remove the node identified by 'nodeName' from the graph
        and return in and out edges removed by this operation in two dicts {dstAttr.fullName(), srcAttr.fullName()}
        """
        node = self.node(nodeName)
        self._nodes.pop(nodeName)

        inEdges = {}
        outEdges = {}
        with GraphModification(self):
            for attr in node._attributes:
                for edge in self.outEdges(attr):
                    self.edges.remove(edge)
                    outEdges[edge.dst.fullName()] = edge.src.fullName()
                if attr in self.edges.keys():
                    edge = self.edges.pop(attr)
                    inEdges[edge.dst.fullName()] = edge.src.fullName()

        return inEdges, outEdges

    @Slot(str, result=Node)
    def addNewNode(self, nodeType, **kwargs):
        """

        :param nodeType:
        :param kwargs:
        :return:
        :rtype: Node
        """
        node = self.addNode(Node(nodeDesc=nodeType, parent=self, **kwargs))
        return node

    def _createUniqueNodeName(self, inputName):
        i = 1
        while i:
            newName = "{name}_{index}".format(name=inputName, index=i)
            if newName not in self._nodes.objects:
                return newName
            i += 1

    def node(self, nodeName):
        return self._nodes.get(nodeName)

    def attribute(self, fullName):
        # type: (str) -> Attribute
        """
        Return the attribute identified by the unique name 'fullName'.
        """
        node, attribute = fullName.split('.', 1)
        return self.node(node).attribute(attribute)

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

    def addEdge(self, srcAttr, dstAttr):
        assert isinstance(srcAttr, Attribute)
        assert isinstance(dstAttr, Attribute)
        if srcAttr.node.graph != self or dstAttr.node.graph != self:
            raise RuntimeError('The attributes of the edge should be part of a common graph.')
        if dstAttr in self.edges.keys():
            raise RuntimeError('Destination attribute "{}" is already connected.'.format(dstAttr.fullName()))
        edge = Edge(srcAttr, dstAttr)
        self.edges.add(edge)
        dstAttr.valueChanged.emit()
        dstAttr.isLinkChanged.emit()
        self.update()
        return edge

    def addEdges(self, *edges):
        with GraphModification(self):
            for edge in edges:
                self.addEdge(*edge)

    def removeEdge(self, dstAttr):
        if dstAttr not in self.edges.keys():
            raise RuntimeError('Attribute "{}" is not connected'.format(dstAttr.fullName()))
        edge = self.edges.pop(dstAttr)
        dstAttr.valueChanged.emit()
        dstAttr.isLinkChanged.emit()
        self.update()
        return edge

    def getDepth(self, node):
        # TODO: would be better to use bfs instead of recursive function
        inputEdges = self.getInputEdges(node)
        if not inputEdges:
            return 0
        inputDepths = [e.src.node.depth for e in inputEdges]
        return max(inputDepths) + 1

    def getInputEdges(self, node):
        return set([edge for edge in self.edges if edge.dst.node is node])

    def _getInputEdgesPerNode(self):
        nodeEdges = defaultdict(set)

        for edge in self.edges:
            nodeEdges[edge.dst.node].add(edge.src.node)

        return nodeEdges

    def dfs(self, visitor, startNodes=None, longestPathFirst=False):
        nodeChildren = self._getInputEdgesPerNode()
        minMaxDepthPerNode = self.minMaxDepthPerNode() if longestPathFirst else None
        colors = {}
        for u in self._nodes:
            colors[u] = WHITE
        if startNodes:
            if longestPathFirst:
                startNodes = sorted(startNodes, key=lambda item: item.depth)
            for startNode in startNodes:
                self.dfsVisit(startNode, visitor, colors, nodeChildren, longestPathFirst, minMaxDepthPerNode)
        else:
            leaves = self.getLeaves()
            if longestPathFirst:
                leaves = sorted(leaves, key=lambda item: item.depth)
            for u in leaves:
                if colors[u] == WHITE:
                    self.dfsVisit(u, visitor, colors, nodeChildren, longestPathFirst, minMaxDepthPerNode)

    def dfsVisit(self, u, visitor, colors, nodeChildren, longestPathFirst, minMaxDepthPerNode):
        colors[u] = GRAY
        visitor.discoverVertex(u, self)
        # d_time[u] = time = time + 1
        children = nodeChildren[u]
        if longestPathFirst:
            children = sorted(children, reverse=True, key=lambda item: minMaxDepthPerNode[item][1])
        for v in children:
            visitor.examineEdge((u, v), self)
            if colors[v] == WHITE:
                visitor.treeEdge((u, v), self)
                # (u,v) is a tree edge
                self.dfsVisit(v, visitor, colors, nodeChildren, longestPathFirst, minMaxDepthPerNode)  # TODO: avoid recursion
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
        return (nodes, edges)

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
            if vertex.status.status in (Status.SUBMITTED_EXTERN,
                                        Status.SUBMITTED_LOCAL):
                print('WARNING: node "{}" is already submitted.'.format(vertex.name))
            if vertex.status.status is Status.RUNNING:
                print('WARNING: node "{}" is already running.'.format(vertex.name))
            if vertex.status.status is not Status.SUCCESS:
                nodes.append(vertex)

        def finishEdge(edge, graph):
            if (edge[0].status.status is not Status.SUCCESS) and (edge[1].status.status is not Status.SUCCESS):
                edges.append(edge)

        visitor.finishVertex = finishVertex
        visitor.finishEdge = finishEdge
        self.dfs(visitor=visitor, startNodes=startNodes)
        return (nodes, edges)

    def minMaxDepthPerNode(self, startNodes=None):
        """
        Compute the min and max depth for each node.

        :param startNodes: list of starting nodes. Use all leaves if empty.
        :return: {node: (minDepth, maxDepth)}
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

        for e in self.edges.objects.values():
            ee = (e.dst.node, e.src.node)
            assert ee in edgesScore
            assert edgesScore[ee] != 0
            if edgesScore[ee] == 1:
                flowEdges.append(ee)
        return flowEdges

    def _applyExpr(self):
        with GraphModification(self):
            for node in self._nodes:
                node._applyExpr()

    def toDict(self):
        return {k: node.toDict() for k, node in self._nodes.objects.items()}

    @Slot(result=str)
    def asString(self):
        return str(self.toDict())

    @Slot(str)
    def save(self, filepath):
        """
        """
        data = self.toDict()
        with open(filepath, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)

    def updateInternals(self, startNodes=None):
        nodes, edges = self.dfsOnFinish(startNodes=startNodes)
        for node in nodes:
            node.updateInternals()

    def updateStatusFromCache(self):
        for node in self._nodes:
            node.updateStatusFromCache()

    def updateStatisticsFromCache(self):
        for node in self._nodes:
            node.updateStatisticsFromCache()

    def update(self):
        if not self._updateEnabled:
            self._updateRequested = True
        self.updateInternals()
        self.updateStatusFromCache()

    def stopExecution(self):
        """ Request graph execution to be stopped """
        self.stopExecutionRequested.emit()

    def submittedNodes(self):
        """ Return the list of submitted nodes inside this Graph """
        return [node for node in self.nodes if node.isAlreadySubmitted()]

    def clearSubmittedNodes(self):
        """ Reset the status of already submitted nodes to Status.NONE """
        [node.upgradeStatusTo(Status.NONE) for node in self.submittedNodes()]

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
        self.cacheDirChanged.emit()

    nodes = Property(BaseObject, nodes.fget, constant=True)
    edges = Property(BaseObject, edges.fget, constant=True)
    cacheDirChanged = Signal()
    cacheDir = Property(str, cacheDir.fget, cacheDir.fset, notify=cacheDirChanged)

    stopExecutionRequested = Signal()


def loadGraph(filepath):
    """
    """
    graph = Graph("")
    graph.load(filepath)
    return graph


def getAlreadySubmittedNodes(nodes):
    out = []
    for node in nodes:
        if node.isAlreadySubmitted():
            out.append(node)
    return out


def execute(graph, toNodes=None, force=False):
    """
    """
    if force:
        nodes, edges = graph.dfsOnFinish(startNodes=toNodes)
    else:
        nodes, edges = graph.dfsToProcess(startNodes=toNodes)
        nodesInConflict = getAlreadySubmittedNodes(nodes)

        if nodesInConflict:
            nodesStatus = set([node.status.status.name for node in nodesInConflict])
            nodesName = [node.name for node in nodesInConflict]
            #raise RuntimeError(
            print(
                'WARNING: Some nodes are already submitted with status: {}\n'
                'Nodes: {}'.format(
                ', '.join(nodesStatus),
                ', '.join(nodesName),
                ))

    print('Nodes to execute: ', str([n.name for n in nodes]))

    for node in nodes:
        node.beginSequence()

    for i, node in enumerate(nodes):
        try:
            print('\n[{i}/{N}] {nodeName}'.format(i=i + 1, N=len(nodes), nodeName=node.nodeType))
            node.process()
        except Exception as e:
            logging.error("Error on node computation: {}".format(e))
            graph.clearSubmittedNodes()
            return

    for node in nodes:
        node.endSequence()
