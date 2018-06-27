from __future__ import print_function

import json
import logging
import os
import re
import weakref
from collections import defaultdict
from contextlib import contextmanager

from enum import Enum

import meshroom.core
from meshroom.common import BaseObject, DictModel, Slot, Signal, Property
from meshroom.core.attribute import Attribute
from meshroom.core.node import node_factory, Status

# Replace default encoder to support Enums

DefaultJSONEncoder = json.JSONEncoder  # store the original one

class MyJSONEncoder(DefaultJSONEncoder):  # declare a new one with Enum support
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.name
        return DefaultJSONEncoder.default(self, obj)  # use the default one for all other types


json.JSONEncoder = MyJSONEncoder  # replace the default implementation with our new one


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

                n = node_factory(nodeData['nodeType'],
                                 # allow simple retro-compatibility, though cache might get invalidated
                                 skipInvalidAttributes=True,
                                 **nodeData['attributes'])

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
        with GraphModification(self):
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

        n = self.addNode(node_factory(nodeType, False, **kwargs), uniqueName=name)
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


def executeGraph(graph, toNodes=None, forceCompute=False, forceStatus=False):
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

