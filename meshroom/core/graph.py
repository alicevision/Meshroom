from __future__ import print_function

import hashlib
import json
import os
import psutil
import re
import shutil
import time
import uuid
from collections import defaultdict
from enum import Enum  # available by default in python3. For python2: "pip install enum34"
from pprint import pprint

from . import stats
from meshroom import core as pg
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
        self._isOutput = getattr(attributeDesc, 'isOutput', False)

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

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self._value == value:
            return
        self._value = value
        self.valueChanged.emit()

    @property
    def isOutput(self):
        return self._isOutput

    def uid(self):
        """
        """
        if self.attributeDesc.isOutput:
            # only dependent of the linked node uid, so it is independent
            # from the cache folder which may be used in the filepath.
            return self.node.uid()
        if self.isLink:
            return self.getLinkParam().uid()
        if isinstance(self._value, basestring):
            return hash(str(self._value))
        return hash(self._value)

    @property
    def isLink(self):
        """
        If the attribute is a link to another attribute.
        """
        if self.attributeDesc.isOutput:
            return False
        else:
            return self in self.node.graph.edges.keys()

    def getLinkParam(self):
        if not self.isLink:
            return None
        return self.node.graph.edge(self).src

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
        value = self._value
        # print('getExportValue: ', self.name(), value, self.isLink())
        if self.isLink:
            value = '{' + self.getLinkParam().fullName() + '}'
        return value

    name = Property(str, getName, constant=True)
    label = Property(str, getLabel, constant=True)
    valueChanged = Signal()
    value = Property("QVariant", value.fget, value.fset, notify=valueChanged)
    isOutput = Property(bool, isOutput.fget, constant=True)
    isLinkChanged = Signal()
    isLink = Property(bool, isLink.fget, notify=isLinkChanged)


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
        self._cmdVars = {}
        self._attributes = Model(parent=self)
        self.attributesPerUid = defaultdict(set)
        self._initFromDesc()
        for k, v in kwargs.items():
            self.attribute(k)._value = v
        self.status = StatusData(self.name, self.nodeType())
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

    @property
    def depth(self):
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
            attr.value = attr.attributeDesc.value.format(
                nodeType=self.nodeType(),
                **self._cmdVars)
            v = attr._value

            self._cmdVars[name] = '--{name} {value}'.format(name=name, value=v)
            self._cmdVars[name + 'Value'] = str(v)

            if v is not None and v is not '':
                self._cmdVars[attr.attributeDesc.group] = self._cmdVars.get(attr.attributeDesc.group, '') + \
                                                          ' ' + self._cmdVars[name]

        self.internalFolderChanged.emit()

    @property
    def internalFolder(self):
        return self.nodeDesc.internalFolder.format(nodeType=self.nodeType(), **self._cmdVars)

    def commandLine(self):
        return self.nodeDesc.commandLine.format(nodeType=self.nodeType(), **self._cmdVars)

    def statusFile(self):
        return os.path.join(pg.cacheFolder, self.internalFolder, 'status')

    def statisticsFile(self):
        return os.path.join(pg.cacheFolder, self.internalFolder, 'statistics')

    def logFile(self):
        return os.path.join(pg.cacheFolder, self.internalFolder, 'log')

    def updateStatusFromCache(self):
        """
        Need up-to-date UIDs.
        """
        statusFile = self.statusFile()
        if not os.path.exists(statusFile):
            self.upgradeStatusTo(Status.NONE)
            return
        with open(statusFile, 'r') as jsonFile:
            statusData = json.load(jsonFile)
        self.status.fromDict(statusData)
        self.statusChanged.emit()

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
        self.statusChanged.emit()
        self.saveStatusFile()
    
    def isAlreadySubmitted(self):
        return self.status.status in (Status.SUBMITTED_EXTERN, Status.SUBMITTED_LOCAL, Status.RUNNING)

    def submit(self):
        self.upgradeStatusTo(Status.SUBMITTED_EXTERN)

    def beginSequence(self):
        self.upgradeStatusTo(Status.SUBMITTED_LOCAL)

    def stopProcess(self):
        if self._subprocess:
            self._subprocess.terminate()

    def process(self):
        self.upgradeStatusTo(Status.RUNNING)
        statThread = stats.StatisticsThread(self)
        statThread.start()
        startTime = time.time()
        try:
            with open(self.logFile(), 'w') as logF:
                cmd = self.commandLine()
                print(' - commandLine:', cmd)
                print(' - logFile:', self.logFile())
                self._subprocess = psutil.Popen(cmd, stdout=logF, stderr=logF, shell=True)

                # store process static info into the status file
                self.status.commandLine = cmd
                # self.status.env = self.proc.environ()
                # self.status.createTime = self.proc.create_time()

                statThread.proc = self._subprocess
                stdout, stderr = self._subprocess.communicate()
                self._subprocess.wait()
                
                self.status.returnCode = self._subprocess.returncode

            if self._subprocess.returncode != 0:
                logContent = ''
                with open(self.logFile(), 'r') as logF:
                    logContent = ''.join(logF.readlines())
                self.upgradeStatusTo(Status.ERROR)
                raise RuntimeError('Error on node "{}":\nLog:\n{}'.format(self.name, logContent))
        except:
            self.upgradeStatusTo(Status.ERROR)
            raise
        finally:
	    elapsedTime = time.time() - startTime
	    print(' - elapsed time:', elapsedTime)
            self._subprocess = None
            # ask and wait for the stats thread to terminate
            statThread.stopRequest()
            statThread.join()

        self.upgradeStatusTo(Status.SUCCESS)

    def endSequence(self):
        pass

    def getStatus(self):
        return self.status

    @property
    def statusName(self):
        return self.status.status.name

    name = Property(str, getName, constant=True)
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
        self._nodes = Model(parent=self)
        self._edges = Model(keyAttrName="dst", parent=self)  # use dst attribute as unique key since it can only have one input connection

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
        self.stopExecutionRequested.connect(node.stopProcess)

        # Trigger internal update when an attribute is modified
        for attr in node.attributes:  # type: Attribute
            attr.valueChanged.connect(self.updateInternals)

        node._applyExpr()
        return node

    def outEdges(self, attribute):
        """ Return the list of edges starting from the given attribute """
        # type: (Attribute,) -> [Edge]
        return [edge for edge in self.edges if edge.src == attribute]

    def removeNode(self, nodeName):
        node = self.node(nodeName)
        self._nodes.pop(nodeName)

        edges = {}
        for attr in node._attributes:
            for edge in self.outEdges(attr):
                self.edges.remove(edge)
                edges[edge.dst.fullName()] = edge.src.fullName()
            if attr in self.edges.keys():
                edge = self.edges.pop(attr)
                edges[edge.dst.fullName()] = edge.src.fullName()

        self.updateInternals()
        return edges

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

    def findNodeCandidates(self, nodeNameExpr):
        pattern = re.compile(nodeNameExpr)
        return [v for k, v in self._nodes.objects.items() if pattern.match(k)]

    def findNodes(self, nodesExpr):
        out = []
        for nodeName in nodesExpr:
            candidates = self.findNodeCandidates('^' + nodeName)
            if not candidates:
                raise KeyError('No node candidate for "{}"'.format(nodeName))
            elif len(candidates) > 1:
                raise KeyError('Multiple node candidates for "{}": {}'.format(nodeName, str([c.name for c in candidates])))
            out.append(candidates[0])
        return out

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
        return edge

    def addEdges(self, *edges):
        for edge in edges:
            self.addEdge(*edge)

    def removeEdge(self, dstAttr):
        if dstAttr not in self.edges.keys():
            raise RuntimeError('Attribute "{}" is not connected'.format(dstAttr.fullName()))
        edge = self.edges.pop(dstAttr)
        dstAttr.valueChanged.emit()
        dstAttr.isLinkChanged.emit()
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

    def dfs(self, visitor, startNodes=None):
        nodeChildren = self._getInputEdgesPerNode()
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

    def stopExecution(self):
        """ Request graph execution to be stopped """
        self.stopExecutionRequested.emit()

    @property
    def nodes(self):
        return self._nodes

    @property
    def edges(self):
        return self._edges

    nodes = Property(BaseObject, nodes.fget, constant=True)
    edges = Property(BaseObject, edges.fget, constant=True)

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
        nodes = graph.dfsNodesOnFinish(startNodes=toNodes)
    else:
        nodes = graph.dfsNodesToProcess(startNodes=toNodes)
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
        print('\n[{i}/{N}] {nodeName}'.format(i=i+1, N=len(nodes), nodeName=node.nodeType()))
        node.process()

    for node in nodes:
        node.endSequence()
