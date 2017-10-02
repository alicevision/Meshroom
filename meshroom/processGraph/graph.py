from __future__ import print_function

import hashlib
import json
import os
import psutil
import shutil
import uuid
from collections import defaultdict
from enum import Enum  # available by default in python3. For python2: "pip install enum34"
from pprint import pprint

from . import stats
from meshroom import processGraph as pg
from meshroom.common import BaseObject, Model, Slot, Signal, Property

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


def hash(v):
    hashObject = hashlib.sha1(str(v).encode('utf-8'))
    return hashObject.hexdigest()


class Attribute(BaseObject):
    """
    """

    def __init__(self, name, node, attributeDesc, parent = None):
        super(Attribute, self).__init__(parent)
        self._name = name
        self.node = node  # type: Node
        self.attributeDesc = attributeDesc
        self._value = getattr(attributeDesc, 'value', None)
        self._label = getattr(attributeDesc, 'label', None)

    def absoluteName(self):
        return '{}.{}.{}'.format(self.node.graph.name, self.node.name, self._name)

    def fullName(self):
        """ Name inside the Graph: nodeName.name """
        return '{}.{}'.format(self.node.name, self._name)

    def getName(self):
        """ Attribute name """
        return self._name

    def getLabel(self):
        return self._label

    def getValue(self):
        return self._value

    def setValue(self, value):
        if self._value == value:
            return
        self._value = value
        self.valueChanged.emit()

    def uid(self):
        """
        """
        if self.attributeDesc.isOutput:
            # only dependent of the linked node uid, so it is independent
            # from the cache folder which may be used in the filepath.
            return self.node.uid()
        if self.isLink():
            return self.node.graph.edges[self].uid()
        if isinstance(self._value, basestring):
            return hash(str(self._value))
        return hash(self._value)

    def isLink(self):
        """
        If the attribute is a link to another attribute.
        """
        if self.attributeDesc.isOutput:
            return False
        else:
            return self in self.node.graph.edges

    def getLinkParam(self):
        if not self.isLink():
            return None
        return self.node.graph.edges[self]

    def _applyExpr(self):
        """
        For string parameters with an expression (when loaded from file),
        this function convert the expression into a real edge in the graph
        and clear the string value.
        """
        v = self._value
        if isinstance(v, basestring) and len(v) > 2 and v[0] == '{' and v[-1] == '}':
            # value is a link to another attribute
            g = self.node.graph
            link = v[1:-1]
            linkNode, linkAttr = link.split('.')
            g.addEdge(g.node(linkNode).attribute(linkAttr), self)
            self._value = ""

    def getExportValue(self):
        value = self._value
        # print('getExportValue: ', self.name(), value, self.isLink())
        if self.isLink():
            value = '{' + self.node.graph.edges[self].fullName() + '}'
        return value

    name = Property(str, getName, constant=True)
    label = Property(str, getLabel, constant=True)
    valueChanged = Signal()
    value = Property("QVariant", getValue, setValue, notify=valueChanged)


class Status(Enum):
    """
    """
    NONE = 1
    SUBMITTED_EXTERN = 2
    SUBMITTED_LOCAL = 3
    RUNNING = 4
    ERROR = 5
    SUCCESS = 6


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

    def toDict(self):
        return self.__dict__

    def fromDict(self, d):
        self.status = Status._member_map_[d['status']]
        self.nodeName = d.get('nodeName', '')
        self.nodeType = d.get('nodeType', '')
        self.graph = d.get('graph', '')
        self.commandLine = d.get('commandLine', '')
        self.env = d.get('env', '')


class Node(BaseObject):
    """
    """

    def __init__(self, nodeDesc, parent=None, **kwargs):
        super(Node, self).__init__(parent)
        self._name = None  # type: str
        self.graph = None  # type: Graph
        self.nodeDesc = pg.nodesDesc[nodeDesc]()
        self._attributes = Model(parent=self)
        self.attributesPerUid = defaultdict(set)
        self._initFromDesc()
        for k, v in kwargs.items():
            self.attribute(k)._value = v
        self.status = StatusData(self.name, self.nodeType())
        self.statistics = stats.Statistics()

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

    @Slot(str, result=Attribute)
    def attribute(self, name):
        return self._attributes.get(name)

    def getAttributes(self):
        return self._attributes

    def _initFromDesc(self):
        # Init from class members
        for name, desc in self.nodeDesc.__class__.__dict__.items():
            if issubclass(desc.__class__, pg.desc.Attribute):
                self._attributes.add(Attribute(name, self, desc))
        # Init from instance members
        for name, desc in self.nodeDesc.__dict__.items():
            if issubclass(desc.__class__, pg.desc.Attribute):
                self._attributes.add(Attribute(name, self, desc))
        # List attributes per uid
        for attr in self._attributes:
            for uidIndex in attr.attributeDesc.uid:
                self.attributesPerUid[uidIndex].add(attr)

    def _applyExpr(self):
        for attr in self._attributes:
            attr._applyExpr()

    def nodeType(self):
        return self.nodeDesc.__class__.__name__

    def uid(self):
        return self.nodeUid

    def _updateUid(self):
        hashInputParams = [(attr.getName(), attr.uid()) for attr in self._attributes if
                           not attr.attributeDesc.isOutput]
        hashInputParams.sort()
        self.nodeUid = hash(tuple([b for a, b in hashInputParams]))
        return self.nodeUid

    def getDepth(self):
        return self.graph.getDepth(self)

    def toDict(self):
        attributes = {k: v.getExportValue() for k, v in self._attributes.objects.items()}
        return {
            'nodeType': self.nodeType(),
            'attributes': {k: v for k, v in attributes.items() if v is not None},  # filter empty values
        }

    def updateInternals(self):
        self._updateUid()

        self._cmdVars = {
            'cache': pg.cacheFolder,
            }
        for uidIndex, associatedAttributes in self.attributesPerUid.items():
            assAttr = [(a.getName(), a.uid()) for a in associatedAttributes]
            assAttr.sort()
            self._cmdVars['uid{}'.format(uidIndex)] = hash(tuple([b for a, b in assAttr]))

        # Evaluate input params
        for name, attr in self._attributes.objects.items():
            if attr.attributeDesc.isOutput:
                continue # skip outputs
            linkAttr = attr.getLinkParam()
            if linkAttr:
                attr._value = linkAttr._value
            v = attr._value

            self._cmdVars[name] = '--{name} {value}'.format(name=name, value=v)
            self._cmdVars[name + 'Value'] = str(v)

            if v is not None and v is not '':
                self._cmdVars[attr.attributeDesc.group] = self._cmdVars.get(attr.attributeDesc.group, '') + \
                                                          ' ' + self._cmdVars[name]

        # Evaluate output params
        for name, attr in self._attributes.objects.items():
            if not attr.attributeDesc.isOutput:
                continue # skip inputs
            attr._value = attr.attributeDesc.value.format(
                nodeType=self.nodeType(),
                **self._cmdVars)
            v = attr._value

            self._cmdVars[name] = '--{name} {value}'.format(name=name, value=v)
            self._cmdVars[name + 'Value'] = str(v)

            if v is not None and v is not '':
                self._cmdVars[attr.attributeDesc.group] = self._cmdVars.get(attr.attributeDesc.group, '') + \
                                                          ' ' + self._cmdVars[name]


    def internalFolder(self):
        return self.nodeDesc.internalFolder.format(nodeType=self.nodeType(), **self._cmdVars)

    def commandLine(self):
        return self.nodeDesc.commandLine.format(nodeType=self.nodeType(), **self._cmdVars)

    def statusFile(self):
        return os.path.join(pg.cacheFolder, self.internalFolder(), 'status')

    def statisticsFile(self):
        return os.path.join(pg.cacheFolder, self.internalFolder(), 'statistics')

    def logFile(self):
        return os.path.join(pg.cacheFolder, self.internalFolder(), 'log')

    def updateStatusFromCache(self):
        """
        Need up-to-date UIDs.
        """
        statusFile = self.statusFile()
        if not os.path.exists(statusFile):
            self.status.status = Status.NONE
            return
        with open(statusFile, 'r') as jsonFile:
            statusData = json.load(jsonFile)
        self.status.fromDict(statusData)

    def saveStatusFile(self):
        """
        Need up-to-date UIDs.
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

    def upgradeStatusTo(self, newStatus):
        if int(newStatus.value) <= int(self.status.status.value):
            print('WARNING: downgrade status on node "{}" from {} to {}'.format(self._name, self.status.status.name,
                                                                                newStatus))
        self.status.status = newStatus
        self.saveStatusFile()
    
    def isAlreadySubmitted(self):
        return self.status.status in (Status.SUBMITTED_EXTERN, Status.SUBMITTED_LOCAL, Status.RUNNING)

    def submit(self):
        self.upgradeStatusTo(Status.SUBMITTED_EXTERN)

    def beginSequence(self):
        self.upgradeStatusTo(Status.SUBMITTED_LOCAL)

    def process(self):
        self.upgradeStatusTo(Status.RUNNING)
        statThread = stats.StatisticsThread(self)
        statThread.start()
        try:
            with open(self.logFile(), 'w') as logF:
                cmd = self.commandLine()
                print('\n =====> commandLine:\n', cmd, '\n')
                print(' - logFile: ', self.logFile())
                self.proc = psutil.Popen(cmd, stdout=logF, stderr=logF, shell=True)

                # store process static info into the status file
                self.status.commandLine = cmd
                # self.status.env = self.proc.environ()
                # self.status.createTime = self.proc.create_time()

                statThread.proc = self.proc
                stdout, stderr = self.proc.communicate()
                self.proc.wait()
                
                self.status.returnCode = self.proc.returncode

            if self.proc.returncode != 0:
                logContent = ''
                with open(self.logFile(), 'r') as logF:
                    logContent = ''.join(logF.readlines())
                self.upgradeStatusTo(Status.ERROR)
                raise RuntimeError('Error on node "{}":\nLog:\n{}'.format(self.name, logContent))
        except:
            self.upgradeStatusTo(Status.ERROR)
            raise
        statThread.running = False
        # Don't need to join, the thread will finish a bit later.
        # statThread.join()

        self.upgradeStatusTo(Status.SUCCESS)

    def endSequence(self):
        pass

    def getStatus(self):
        return self.status

    name = Property(str, getName, constant=True)
    attributes = Property(BaseObject, getAttributes, constant=True)


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

    # def examineEdge(self, e, g):
    #     '''is invoked on every out-edge of each vertex after it is discovered.'''
    #     pass
    # def treeEdge(self, e, g):
    #     '''is invoked on each edge as it becomes a member of the edges that form the search tree. If you wish to record predecessors, do so at this event point.'''
    #     pass
    # def backEdge(self, e, g):
    #     '''is invoked on the back edges in the graph.'''
    #     pass
    # def forwardOrCrossEdge(self, e, g):
    #     '''is invoked on forward or cross edges in the graph. In an undirected graph this method is never called.'''
    #     pass
    # def finishEdge(self, e, g):
    #     '''is invoked on the non-tree edges in the graph as well as on each tree edge after its target vertex is finished.'''
    #     pass
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
        self.edges = {}  # key/input <- value/output, it is organized this way because key/input can have only one connection.
        self._nodes = Model(parent=self)

    def clear(self):
        self._nodes.clear()
        self.edges = {}

    @Slot(str)
    def load(self, filepath):
        self.clear()
        with open(filepath) as jsonFile:
            graphData = json.load(jsonFile)
        if not isinstance(graphData, dict):
            raise RuntimeError('loadGraph error: Graph is not a dict. File: {}'.format(filepath))

        self.name = os.path.splitext(os.path.basename(filepath))[0]
        for nodeName, nodeData in graphData.items():
            if not isinstance(nodeData, dict):
                raise RuntimeError('loadGraph error: Node is not a dict. File: {}'.format(filepath))
            n = Node(nodeData['nodeType'], parent=self, **nodeData['attributes'])
            self.addNode(n, uniqueName=nodeName)
        self._applyExpr()

    def addNode(self, node, uniqueName=None):
        if node.graph is not None and node.graph != self:
            raise RuntimeError(
                'Node "{}" cannot be part of the Graph "{}", as it is already part of the other graph "{}".'.format(
                    node.nodeType(), self.name, node.graph.name))
        if uniqueName:
            assert uniqueName not in self._nodes.objects
            node._name = uniqueName
        else:
            node._name = self._createUniqueNodeName(node.nodeType())
        node.graph = self
        self._nodes.add(node)

        return node

    def removeNode(self, nodeName):
        node = self.node(nodeName)
        self._nodes.pop(nodeName)
        for attr in node._attributes:
            if attr in self.edges:
                self.edges.pop(attr)

    @Slot(str, result=Node)
    def addNewNode(self, nodeType, **kwargs):
        """

        :param nodeType:
        :param kwargs:
        :return:
        :rtype: Node
        """
        return self.addNode(Node(nodeDesc=nodeType, parent=self, **kwargs))

    def _createUniqueNodeName(self, inputName):
        i = 1
        while i:
            newName = "{name}_{index}".format(name=inputName, index=i)
            if newName not in self._nodes.objects:
                return newName
            i += 1

    def node(self, nodeName):
        return self._nodes.get(nodeName)

    def getLeaves(self):
        nodesWithOutput = set([outputAttr.node for outputAttr in self.edges.values()])
        return set(self._nodes) - nodesWithOutput

    def addEdge(self, outputAttr, inputAttr):
        assert isinstance(outputAttr, Attribute)
        assert isinstance(inputAttr, Attribute)
        if outputAttr.node.graph != self or inputAttr.node.graph != self:
            raise RuntimeError('The attributes of the edge should be part of a common graph.')
        if inputAttr in self.edges:
            raise RuntimeError('Input attribute "{}" is already connected.'.format(inputAttr.fullName()))
        self.edges[inputAttr] = outputAttr

    def addEdges(self, *edges):
        for edge in edges:
            self.addEdge(*edge)

    def getDepth(self, node):
        return len(self.dfsNodesOnFinish([node]))

    def _getNodeEdges(self):
        nodeEdges = defaultdict(set)

        for attrInput, attrOutput in self.edges.items():
            nodeEdges[attrInput.node].add(attrOutput.node)

        return nodeEdges

    def dfs(self, visitor, startNodes=None):
        nodeChildren = self._getNodeEdges()
        colors = {}
        for u in self._nodes:
            colors[u] = WHITE
        time = 0
        if startNodes:
            for startNode in startNodes:
                self.dfsVisit(startNode, visitor, colors, nodeChildren)
        else:
            leaves = self.getLeaves()
            for u in leaves:
                if colors[u] == WHITE:
                    self.dfsVisit(u, visitor, colors, nodeChildren)

    def dfsVisit(self, u, visitor, colors, nodeChildren):
        colors[u] = GRAY
        visitor.discoverVertex(u, self)
        # d_time[u] = time = time + 1
        for v in nodeChildren[u]:
            if colors[v] == WHITE:
                # (u,v) is a tree edge
                self.dfsVisit(v, visitor, colors, nodeChildren)  # TODO: avoid recursion
            elif colors[v] == GRAY:
                pass  # (u,v) is a back edge
            elif colors[v] == BLACK:
                pass  # (u,v) is a cross or forward edge
        colors[u] = BLACK
        visitor.finishVertex(u, self)

    def dfsNodesOnFinish(self, startNodes=None):
        nodes = []
        visitor = Visitor()
        visitor.finishVertex = lambda vertex, graph: nodes.append(vertex)
        self.dfs(visitor=visitor, startNodes=startNodes)
        return nodes

    def dfsNodesToProcess(self, startNodes=None):
        nodes = []
        visitor = Visitor()

        def finishVertex(vertex, graph):
            if vertex.status.status in (Status.SUBMITTED_EXTERN,
                                        Status.SUBMITTED_LOCAL):
                print('WARNING: node "{}" is already submitted.'.format(vertex.name))
            if vertex.status.status is Status.RUNNING:
                print('WARNING: node "{}" is already running.'.format(vertex.name))
            if vertex.status.status is not Status.SUCCESS:
                nodes.append(vertex)

        visitor.finishVertex = finishVertex
        self.dfs(visitor=visitor, startNodes=startNodes)
        return nodes

    def _applyExpr(self):
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
        pprint(data)
        with open(filepath, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)

    def updateInternals(self, startNodes=None):
        nodes = self.dfsNodesOnFinish(startNodes=startNodes)
        for node in nodes:
            node.updateInternals()

    def updateStatusFromCache(self):
        for node in self._nodes:
            node.updateStatusFromCache()

    def updateStatisticsFromCache(self):
        for node in self._nodes:
            node.updateStatisticsFromCache()

    def update(self):
        self.updateInternals()
        self.updateStatusFromCache()

    @property
    def nodes(self):
        return self._nodes

    nodes = Property(BaseObject, nodes.fget, constant=True)


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


def execute(graph, startNodes=None, force=False):
    """
    """
    if force:
        nodes = graph.dfsNodesOnFinish(startNodes=startNodes)
    else:
        nodes = graph.dfsNodesToProcess(startNodes=startNodes)
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

    print('execute: ', str([n.name for n in nodes]))

    for node in nodes:
        node.beginSequence()

    for node in nodes:
        node.process()

    for node in nodes:
        node.endSequence()
