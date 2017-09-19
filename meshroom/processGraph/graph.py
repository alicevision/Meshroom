from __future__ import print_function

import hashlib
import json
import os
import psutil
import shutil
import subprocess
import threading
import time
import uuid
from collections import defaultdict
from enum import Enum  # available by default in python3. For python2: "pip install enum34"
from pprint import pprint

from meshroom import processGraph as pg

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


class Attribute:
    """
    """

    def __init__(self, name, node, attributeDesc):
        self.attrName = name
        self.node = node
        self._value = attributeDesc.__dict__.get('value', None)
        self.attributeDesc = attributeDesc

    def absoluteName(self):
        return '{}.{}.{}'.format(self.node.graph.name, self.node.name, self.attrName)

    def name(self):
        """
        Name inside the Graph.
        """
        return '{}.{}'.format(self.node.name, self.attrName)

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
            g.addEdge(g.nodes[linkNode].attributes[linkAttr], self)
            self._value = ""

    def getExportValue(self):
        value = self._value
        # print('getExportValue: ', self.name(), value, self.isLink())
        if self.isLink():
            value = '{' + self.node.graph.edges[self].name() + '}'
        return value


class Status(Enum):
    """
    """
    NONE = 1
    SUBMITTED_EXTERN = 2
    SUBMITTED_LOCAL = 3
    RUNNING = 4
    ERROR = 5
    SUCCESS = 6


class Statistics:
    """
    """

    def __init__(self):
        self.duration = 0  # computation time set at the end of the execution
        self.cpuUsage = []
        self.nbCores = 0
        self.cpuFreq = 0
        self.ramUsage = []  # store cpuUsage every minute
        self.ramAvailable = 0  # GB
        self.vramUsage = []
        self.vramAvailable = 0  # GB
        self.swapUsage = []
        self.swapAvailable = 0

    def toDict(self):
        return self.__dict__

    def fromDict(self, d):
        self.__dict__ = d


class StatusData:
    """
    """

    def __init__(self, nodeName, nodeType):
        self.status = Status.NONE
        self.nodeName = nodeName
        self.nodeType = nodeType
        self.statistics = Statistics()
        self.graph = ''

    def toDict(self):
        return {k: (v.toDict() if getattr(v, "toDict", None) else v) for k, v in self.__dict__.items()}

    def fromDict(self, d):
        self.status = Status._member_map_[d['status']]
        self.nodeName = d['nodeName']
        self.nodeType = d['nodeType']
        self.statistics.fromDict(d['statistics'])
        self.graph = d['graph']


bytesPerGiga = 1024. * 1024. * 1024.


class StatisticsThread(threading.Thread):
    def __init__(self, node):
        threading.Thread.__init__(self)
        self.node = node
        self.running = True
        self.statistics = self.node.status.statistics
        self.initStats()

    def initStats(self):
        self.lastTime = time.time()
        self.statistics.duration = 0
        self.statistics.cpuUsage = []
        self.statistics.nbCores = psutil.cpu_count(logical=False)
        self.statistics.cpuFreq = psutil.cpu_freq()[2]
        self.statistics.ramUsage = []
        self.statistics.ramAvailable = psutil.virtual_memory().total / bytesPerGiga
        self.statistics.swapUsage = []
        self.statistics.swapAvailable = psutil.swap_memory().total / bytesPerGiga
        self.statistics.vramUsage = []
        self.statistics.vramAvailable = 0
        self.updateStats()

    def updateStats(self):
        self.lastTime = time.time()
        self.statistics.cpuUsage.append(psutil.cpu_percent(interval=0.1, percpu=True))
        self.statistics.ramUsage.append(psutil.virtual_memory().percent)
        self.statistics.swapUsage.append(psutil.swap_memory().percent)
        self.statistics.vramUsage.append(0)
        self.node.saveStatusFile()

    def run(self):
        while self.running:
            if time.time() - self.lastTime > 10:
                self.updateStats()
            time.sleep(1)


class Node:
    """
    """
    name = None
    graph = None

    def __init__(self, nodeDesc, **kwargs):
        self.nodeDesc = pg.nodesDesc[nodeDesc]()
        self.attributes = {}
        self.attributesPerUid = defaultdict(set)
        self._initFromDesc()
        for k, v in kwargs.items():
            self.attributes[k]._value = v
        self.status = StatusData(self.name, self.nodeType())

    def __getattr__(self, k):
        try:
            # Throws exception if not in prototype chain
            # return object.__getattribute__(self, k) # doesn't work in python2
            return object.__getattr__(self, k)
        except AttributeError:
            try:
                return self.attributes[k]
            except KeyError:
                raise AttributeError(k)

    def _initFromDesc(self):
        # Init from class members
        for name, desc in self.nodeDesc.__class__.__dict__.items():
            if issubclass(desc.__class__, pg.desc.Attribute):
                self.attributes[name] = Attribute(name, self, desc)
        # Init from instance members
        for name, desc in self.nodeDesc.__dict__.items():
            if issubclass(desc.__class__, pg.desc.Attribute):
                self.attributes[name] = Attribute(name, self, desc)
        # List attributes per uid
        for name, attr in self.attributes.items():
            for uidIndex in attr.attributeDesc.uid:
                self.attributesPerUid[uidIndex].add(attr)

    def _applyExpr(self):
        for attr in self.attributes.values():
            attr._applyExpr()

    def nodeType(self):
        return self.nodeDesc.__class__.__name__

    def uid(self):
        return self.nodeUid

    def _updateUid(self):
        hashInputParams = [(attr.attrName, attr.uid()) for attr in self.attributes.values() if
                           not attr.attributeDesc.isOutput]
        hashInputParams.sort()
        self.nodeUid = hash(tuple([b for a, b in hashInputParams]))
        return self.nodeUid

    def getDepth(self):
        return self.graph.getDepth(self)

    def toDict(self):
        attributes = {k: v.getExportValue() for k, v in self.attributes.items()}
        return {
            'nodeType': self.nodeType(),
            'attributes': {k: v for k, v in attributes.items() if v is not None},  # filter empty values
        }

    def updateInternals(self):
        self._updateUid()

        self._cmdVars = {}
        for uidIndex, associatedAttributes in self.attributesPerUid.items():
            assAttr = [(a.attrName, a.uid()) for a in associatedAttributes]
            assAttr.sort()
            self._cmdVars['uid{}'.format(uidIndex)] = hash(tuple([b for a, b in assAttr]))

        for name, attr in self.attributes.items():
            if attr.attributeDesc.isOutput:
                attr._value = attr.attributeDesc.value.format(
                    cache=pg.cacheFolder,
                    nodeType=self.nodeType(),
                    **self._cmdVars)  # self._cmdVars only contains uids at this step

        for name, attr in self.attributes.items():
            linkAttr = attr.getLinkParam()
            v = attr._value
            if linkAttr:
                v = linkAttr._value

            self._cmdVars[name] = '--{name} {value}'.format(name=name, value=v)
            self._cmdVars[name + 'Value'] = str(v)
            self._cmdVars[attr.attributeDesc.group] = self._cmdVars.get(attr.attributeDesc.group, '') + ' ' + \
                                                      self._cmdVars[name]

    def internalFolder(self):
        return self.nodeDesc.internalFolder.format(nodeType=self.nodeType(), **self._cmdVars)

    def commandLine(self):
        return self.nodeDesc.commandLine.format(nodeType=self.nodeType(), **self._cmdVars)

    def statusFile(self):
        return os.path.join(pg.cacheFolder, self.internalFolder(), 'status')

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

    def upgradeStatusTo(self, newStatus):
        if int(newStatus.value) <= int(self.status.status.value):
            print('WARNING: downgrade status on node "{}" from {} to {}'.format(self.name, self.status.status.name,
                                                                                newStatus))
        self.status.status = newStatus
        self.saveStatusFile()

    def submit(self):
        self.upgradeStatusTo(pg.Status.SUBMITTED_EXTERN)

    def beginSequence(self):
        self.upgradeStatusTo(pg.Status.SUBMITTED_LOCAL)

    def process(self):
        self.upgradeStatusTo(pg.Status.RUNNING)
        statThread = StatisticsThread(self)
        statThread.start()
        try:
            with open(self.logFile(), 'w') as logF:
                cmd = self.commandLine()
                print(' =====> commandLine: ', cmd)
                print(' - logFile: ', self.logFile())
                subprocess.call(cmd, stdout=logF, stderr=logF, shell=True)
        except:
            self.upgradeStatusTo(pg.Status.ERROR)
            raise
        statThread.running = False
        statThread.join()

        self.upgradeStatusTo(pg.Status.SUCCESS)

    def endSequence(self):
        pass


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


class Graph:
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

    def __init__(self, name):
        self.name = name
        self.nodes = {}
        self.edges = {}  # key/input <- value/output, it is organized this way because key/input can have only one connection.

    def addNode(self, node, uniqueName=None):
        if node.graph is not None and node.graph != self:
            raise RuntimeError(
                'Node "{}" cannot be part of the Graph "{}", as it is already part of the other graph "{}".'.format(
                    node.nodeType(), self.name, node.graph.name))
        if uniqueName:
            assert uniqueName not in self.nodes
            node.name = uniqueName
        else:
            node.name = self._createUniqueNodeName(node.nodeType())
        node.graph = self
        self.nodes[node.name] = node

        return node

    def addNewNode(self, nodeType, **kwargs):
        """

        :param nodeType:
        :param kwargs:
        :return:
        :rtype: Node
        """
        return self.addNode(Node(nodeDesc=nodeType, **kwargs))

    def _createUniqueNodeName(self, inputName):
        i = 1
        while i:
            newName = "{name}_{index}".format(name=inputName, index=i)
            if newName not in self.nodes:
                return newName
            i += 1

    def getLeaves(self):
        nodesWithOutput = set([outputAttr.node for outputAttr in self.edges.values()])
        return set(self.nodes.values()) - nodesWithOutput

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
        for u in self.nodes.values():
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
        for node in self.nodes.values():
            node._applyExpr()

    def toDict(self):
        return {k: node.toDict() for k, node in self.nodes.items()}

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
        for node in self.nodes.values():
            node.updateStatusFromCache()

    def update(self):
        self.updateInternals()
        self.updateStatusFromCache()


def loadGraph(filepath):
    """
    """
    with open(filepath) as jsonFile:
        graphData = json.load(jsonFile)
    if not isinstance(graphData, dict):
        raise RuntimeError('loadGraph error: Graph is not a dict. File: {}'.format(filepath))

    graph = Graph(os.path.splitext(os.path.basename(filepath))[0])
    for nodeName, nodeData in graphData.items():
        if not isinstance(nodeData, dict):
            raise RuntimeError('loadGraph error: Node is not a dict. File: {}'.format(filepath))
        n = Node(nodeData['nodeType'], **nodeData['attributes'])
        graph.addNode(n, uniqueName=nodeName)
    graph._applyExpr()
    return graph


def execute(graph, startNodes=None, force=False):
    """
    """
    if force:
        nodes = graph.dfsNodesOnFinish(startNodes=startNodes)
    else:
        nodes = graph.dfsNodesToProcess(startNodes=startNodes)

    print('execute: ', str([n.name for n in nodes]))

    for node in nodes:
        node.updateInternals()

    for node in nodes:
        node.beginSequence()

    for node in nodes:
        node.process()

    for node in nodes:
        node.endSequence()
