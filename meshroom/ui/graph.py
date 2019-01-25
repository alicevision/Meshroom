#!/usr/bin/env python
# coding:utf-8
import logging
import os
from enum import Enum
from threading import Thread

from PySide2.QtCore import Slot, QJsonValue, QObject, QUrl, Property, Signal, QPoint

from meshroom.common.qt import QObjectListModel
from meshroom.core.attribute import Attribute, ListAttribute
from meshroom.core.graph import Graph, Edge, submitGraph, executeGraph
from meshroom.core.node import NodeChunk, Node, Status, CompatibilityNode, Position
from meshroom.core import submitters
from meshroom.ui import commands
from meshroom.ui.utils import makeProperty


class ChunksMonitor(QObject):
    """
    ChunksMonitor regularly check NodeChunks' status files for modification and trigger their update on change.

    When working locally, status changes are reflected through the emission of 'statusChanged' signals.
    But when a graph is being computed externally - either via a Submitter or on another machine,
    NodeChunks status files are modified by another instance, potentially outside this machine file system scope.
    Same goes when status files are deleted/modified manually.
    Thus, for genericity, monitoring is based on regular polling and not file system watching.
    """
    def __init__(self, chunks=(), parent=None):
        super(ChunksMonitor, self).__init__(parent)
        self.lastModificationRecords = dict()
        self.setChunks(chunks)
        # Check status files every x seconds
        # TODO: adapt frequency according to graph compute status
        self.startTimer(5000)

    def setChunks(self, chunks):
        """ Set the list of chunks to monitor. """
        self.clear()
        for chunk in chunks:
            f = chunk.statusFile
            # Store a record of {chunk: status file last modification}
            self.lastModificationRecords[chunk] = self.getFileLastModTime(f)
            # For local use, handle statusChanged emitted directly from the node chunk
            chunk.statusChanged.connect(self.onChunkStatusChanged)
        self.chunkStatusChanged.emit(None, -1)

    def clear(self):
        """ Clear the list of monitored chunks """
        for ch in self.lastModificationRecords:
            ch.statusChanged.disconnect(self.onChunkStatusChanged)
        self.lastModificationRecords.clear()

    def timerEvent(self, evt):
        self.checkFileTimes()

    def onChunkStatusChanged(self):
        """ React to change of status coming from the NodeChunk itself. """
        chunk = self.sender()
        assert chunk in self.lastModificationRecords
        # Update record entry for this file so that it's up-to-date on next timerEvent
        self.lastModificationRecords[chunk] = self.getFileLastModTime(chunk.statusFile)
        self.chunkStatusChanged.emit(chunk, chunk.status.status)

    @staticmethod
    def getFileLastModTime(f):
        """ Return 'mtime' of the file if it exists, -1 otherwise. """
        return os.path.getmtime(f) if os.path.exists(f) else -1

    def checkFileTimes(self):
        """ Check status files last modification time and compare with stored value """
        for chunk, t in self.lastModificationRecords.items():
            lastMod = self.getFileLastModTime(chunk.statusFile)
            if lastMod != t:
                self.lastModificationRecords[chunk] = lastMod
                chunk.updateStatusFromCache()
                logging.debug("Status for node {} changed: {}".format(chunk.node, chunk.status.status))

    chunkStatusChanged = Signal(NodeChunk, int)


class GraphLayout(QObject):
    """
    GraphLayout provides auto-layout features to a UIGraph.
    """

    class DepthMode(Enum):
        """ Defines available node depth mode to layout the graph automatically. """
        MinDepth = 0  # use node minimal depth
        MaxDepth = 1  # use node maximal depth

    # map between DepthMode and corresponding node depth attribute name
    _depthAttribute = {
        DepthMode.MinDepth: 'minDepth',
        DepthMode.MaxDepth: 'depth'
    }

    def __init__(self, graph):
        super(GraphLayout, self).__init__(graph)
        self.graph = graph
        self._depthMode = GraphLayout.DepthMode.MaxDepth
        self._nodeWidth = 140   # implicit node width
        self._nodeHeight = 80   # implicit node height
        self._gridSpacing = 15  # column/line spacing between nodes

    @Slot(Node, Node, int, int)
    def autoLayout(self, fromNode=None, toNode=None, startX=0, startY=0):
        """
        Perform auto-layout from 'fromNode' to 'toNode', starting from (startX, startY) position.

        Args:
            fromNode (BaseNode): where to start the auto layout from
            toNode (BaseNode): up to where to perform the layout
            startX (int): start position x coordinate
            startY (int): start position y coordinate
        """
        fromIndex = self.graph.nodes.indexOf(fromNode) if fromNode else 0
        toIndex = self.graph.nodes.indexOf(toNode) if toNode else self.graph.nodes.count - 1

        def getDepth(n):
            return getattr(n, self._depthAttribute[self._depthMode])

        maxDepth = max([getDepth(n) for n in self.graph.nodes.values()])
        grid = [[] for _ in range(maxDepth + 1)]

        # retrieve reference depth from start node
        zeroDepth = getDepth(self.graph.nodes.at(fromIndex)) if fromIndex > 0 else 0
        for i in range(fromIndex, toIndex + 1):
            n = self.graph.nodes.at(i)
            grid[getDepth(n) - zeroDepth].append(n)

        with self.graph.groupedGraphModification("Graph Auto-Layout"):
            for x, line in enumerate(grid):
                for y, node in enumerate(line):
                    px = startX + x * (self._nodeWidth + self._gridSpacing)
                    py = startY + y * (self._nodeHeight + self._gridSpacing)
                    self.graph.moveNode(node, Position(px, py))

    @Slot()
    def reset(self):
        """ Perform auto-layout on the whole graph. """
        self.autoLayout()

    def boundingBox(self, nodes=None):
        """
        Return bounding box for a set of nodes as (x, y, width, height).

        Args:
            nodes (list of Node): the list of nodes or the whole graph if None

        Returns:
            tuple of int: the resulting bounding box (x, y, width, height)
        """
        if nodes is None:
            nodes = self.graph.nodes.values()
        first = nodes[0]
        bbox = [first.x, first.y, first.x + self._nodeWidth, first.y + self._nodeHeight]
        for n in nodes:
            bbox[0] = min(bbox[0], n.x)
            bbox[1] = min(bbox[1], n.y)
            bbox[2] = max(bbox[2], n.x + self._nodeWidth)
            bbox[3] = max(bbox[3], n.y + self._nodeHeight)

        bbox[2] -= bbox[0]
        bbox[3] -= bbox[1]

        return tuple(bbox)

    def setDepthMode(self, mode):
        """ Set node depth mode to use. """
        if isinstance(mode, int):
            mode = GraphLayout.DepthMode(mode)
        if self._depthMode.value == mode.value:
            return
        self._depthMode = mode

    depthModeChanged = Signal()
    depthMode = Property(int, lambda self: self._depthMode.value, setDepthMode, notify=depthModeChanged)
    nodeHeightChanged = Signal()
    nodeHeight = makeProperty(int, "_nodeHeight", notify=nodeHeightChanged)
    nodeWidthChanged = Signal()
    nodeWidth = makeProperty(int, "_nodeWidth", notify=nodeWidthChanged)
    gridSpacingChanged = Signal()
    gridSpacing = makeProperty(int, "_gridSpacing", notify=gridSpacingChanged)


class UIGraph(QObject):
    """ High level wrapper over core.Graph, with additional features dedicated to UI integration.

    UIGraph exposes undoable methods on its graph and computation in a separate thread.
    It also provides a monitoring of all its computation units (NodeChunks).
    """
    def __init__(self, filepath='', parent=None):
        super(UIGraph, self).__init__(parent)
        self._undoStack = commands.UndoStack(self)
        self._graph = Graph('', self)
        self._modificationCount = 0
        self._chunksMonitor = ChunksMonitor(parent=self)
        self._chunksMonitor.chunkStatusChanged.connect(self.onChunkStatusChanged)
        self._computeThread = Thread()
        self._running = self._submitted = False
        self._sortedDFSChunks = QObjectListModel(parent=self)
        self._layout = GraphLayout(self)
        self._selectedNode = None
        self._hoveredNode = None
        if filepath:
            self.load(filepath)

    def setGraph(self, g):
        """ Set the internal graph. """
        if self._graph:
            self.stopExecution()
            self.clear()
        self._graph = g
        self._graph.updated.connect(self.onGraphUpdated)
        self._graph.update()
        # perform auto-layout if graph does not provide nodes positions
        if Graph.IO.Features.NodesPositions not in self._graph.fileFeatures:
            self._layout.reset()
            self._undoStack.clear()  # clear undo-stack after layout
        self.graphChanged.emit()

    def onGraphUpdated(self):
        """ Callback to any kind of attribute modification. """
        # TODO: handle this with a better granularity
        self.updateChunks()

    def updateChunks(self):
        dfsNodes = self._graph.dfsOnFinish(None)[0]
        chunks = self._graph.getChunks(dfsNodes)
        # Nothing has changed, return
        if self._sortedDFSChunks.objectList() == chunks:
            return
        self._sortedDFSChunks.setObjectList(chunks)
        # Update the list of monitored chunks
        self._chunksMonitor.setChunks(self._sortedDFSChunks)

    def clear(self):
        if self._graph:
            self.clearNodeHover()
            self.clearNodeSelection()
            self._graph.deleteLater()
            self._graph = None
        self._sortedDFSChunks.clear()
        self._undoStack.clear()

    def load(self, filepath):
        g = Graph('')
        g.load(filepath)
        if not os.path.exists(g.cacheDir):
            os.mkdir(g.cacheDir)
        self.setGraph(g)

    @Slot(QUrl)
    def loadUrl(self, url):
        self.load(url.toLocalFile())

    @Slot(QUrl)
    def saveAs(self, url):
        localFile = url.toLocalFile()
        # ensure file is saved with ".mg" extension
        if os.path.splitext(localFile)[-1] != ".mg":
            localFile += ".mg"
        self._graph.save(localFile)
        self._undoStack.setClean()

    @Slot()
    def save(self):
        self._graph.save()
        self._undoStack.setClean()

    @Slot(Node)
    def execute(self, node=None):
        if self.computing:
            return
        nodes = [node] if node else None
        self._computeThread = Thread(target=self._execute, args=(nodes,))
        self._computeThread.start()

    def _execute(self, nodes):
        self.computeStatusChanged.emit()
        try:
            executeGraph(self._graph, nodes)
        except Exception as e:
            logging.error("Error during Graph execution {}".format(e))
        finally:
            self.computeStatusChanged.emit()

    @Slot()
    def stopExecution(self):
        if not self.isComputingLocally():
            return
        self._graph.stopExecution()
        self._computeThread.join()
        self.computeStatusChanged.emit()

    @Slot(Node)
    def submit(self, node=None):
        """ Submit the graph to the default Submitter.
        If a node is specified, submit this node and its uncomputed predecessors.
        Otherwise, submit the whole 

        Notes:
            Default submitter is specified using the MESHROOM_DEFAULT_SUBMITTER environment variable.
        """
        self.save()  # graph must be saved before being submitted
        node = [node] if node else None
        submitGraph(self._graph, os.environ.get('MESHROOM_DEFAULT_SUBMITTER', ''), node)

    def onChunkStatusChanged(self, chunk, status):
        # update graph computing status
        running = any([ch.status.status == Status.RUNNING for ch in self._sortedDFSChunks])
        submitted = any([ch.status.status == Status.SUBMITTED for ch in self._sortedDFSChunks])
        if self._running != running or self._submitted != submitted:
            self._running = running
            self._submitted = submitted
            self.computeStatusChanged.emit()

    def isComputing(self):
        """ Whether is graph is being computed, either locally or externally. """
        return self.isComputingLocally() or self.isComputingExternally()

    def isComputingExternally(self):
        """ Whether this graph is being computed externally. """
        return (self._running or self._submitted) and not self.isComputingLocally()

    def isComputingLocally(self):
        """ Whether this graph is being computed locally (i.e computation can be stopped). """
        return self._computeThread.is_alive()

    def push(self, command):
        """ Try and push the given command to the undo stack.

        Args:
            command (commands.UndoCommand): the command to push
        """
        return self._undoStack.tryAndPush(command)

    def groupedGraphModification(self, title, disableUpdates=True):
        """ Get a GroupedGraphModification for this Graph.

        Args:
            title (str): the title of the macro command
            disableUpdates (bool): whether to disable graph updates

        Returns:
            GroupedGraphModification: the instantiated context manager
        """
        return commands.GroupedGraphModification(self._graph, self._undoStack, title, disableUpdates)

    def beginModification(self, name):
        """ Begin a Graph modification. Calls to beginModification and endModification may be nested, but
        every call to beginModification must have a matching call to endModification. """
        self._modificationCount += 1
        self._undoStack.beginMacro(name)

    def endModification(self):
        """ Ends a Graph modification. Must match a call to beginModification. """
        assert self._modificationCount > 0
        self._modificationCount -= 1
        self._undoStack.endMacro()

    @Slot(str, QPoint, result=QObject)
    def addNewNode(self, nodeType, position=None, **kwargs):
        """ [Undoable]
        Create a new Node of type 'nodeType' and returns it.

        Args:
            nodeType (str): the type of the Node to create.
            position (QPoint): (optional) the initial position of the node
            **kwargs: optional node attributes values

        Returns:
            Node: the created node
        """
        if isinstance(position, QPoint):
            position = Position(position.x(), position.y())
        return self.push(commands.AddNodeCommand(self._graph, nodeType, position=position, **kwargs))

    @Slot(Node, QPoint)
    def moveNode(self, node, position):
        """
        Move 'node' to the given 'position'.

        Args:
            node (Node): the node to move
            position (QPoint): the target position
        """
        if isinstance(position, QPoint):
            position = Position(position.x(), position.y())
        self.push(commands.MoveNodeCommand(self._graph, node, position))

    @Slot(Node)
    def removeNode(self, node):
        self.push(commands.RemoveNodeCommand(self._graph, node))

    @Slot(Node)
    def removeNodesFrom(self, startNode):
        """
        Remove all nodes starting from 'startNode' to graph leaves.
        Args:
            startNode (Node): the node to start from.
        """
        with self.groupedGraphModification("Remove Nodes from {}".format(startNode.name)):
            # Perform nodes removal from leaves to start node so that edges
            # can be re-created in correct order on redo.
            [self.removeNode(node) for node in reversed(self._graph.nodesFromNode(startNode)[0])]

    @Slot(Attribute, Attribute)
    def addEdge(self, src, dst):
        if isinstance(dst, ListAttribute) and not isinstance(src, ListAttribute):
            with self.groupedGraphModification("Insert and Add Edge on {}".format(dst.getFullName())):
                self.appendAttribute(dst)
                self.push(commands.AddEdgeCommand(self._graph, src, dst.at(-1)))
        else:
            self.push(commands.AddEdgeCommand(self._graph, src, dst))

    @Slot(Edge)
    def removeEdge(self, edge):
        if isinstance(edge.dst.root, ListAttribute):
            with self.groupedGraphModification("Remove Edge and Delete {}".format(edge.dst.getFullName())):
                self.push(commands.RemoveEdgeCommand(self._graph, edge))
                self.removeAttribute(edge.dst)
        else:
            self.push(commands.RemoveEdgeCommand(self._graph, edge))

    @Slot(Attribute, "QVariant")
    def setAttribute(self, attribute, value):
        self.push(commands.SetAttributeCommand(self._graph, attribute, value))

    @Slot(Attribute)
    def resetAttribute(self, attribute):
        """ Reset 'attribute' to its default value """
        self.push(commands.SetAttributeCommand(self._graph, attribute, attribute.defaultValue()))

    @Slot(Node, bool, result="QVariantList")
    def duplicateNode(self, srcNode, duplicateFollowingNodes=False):
        """
        Duplicate a node an optionally all the following nodes to graph leaves.

        Args:
            srcNode (Node): node to start the duplication from
            duplicateFollowingNodes (bool): whether to duplicate all the following nodes to graph leaves

        Returns:
            [Nodes]: the list of duplicated nodes
        """
        title = "Duplicate Nodes from {}" if duplicateFollowingNodes else "Duplicate {}"
        # enable updates between duplication and layout to get correct depths during layout
        with self.groupedGraphModification(title.format(srcNode.name), disableUpdates=False):
            # disable graph updates during duplication
            with self.groupedGraphModification("Node duplication", disableUpdates=True):
                duplicates = self.push(commands.DuplicateNodeCommand(self._graph, srcNode, duplicateFollowingNodes))
            # move nodes below the bounding box formed by the duplicated node(s)
            bbox = self._layout.boundingBox(duplicates)
            for n in duplicates:
                self.moveNode(n, Position(n.x, bbox[3] + self.layout.gridSpacing + n.y))

        return duplicates

    @Slot(CompatibilityNode, result=Node)
    def upgradeNode(self, node):
        """ Upgrade a CompatibilityNode. """
        return self.push(commands.UpgradeNodeCommand(self._graph, node))

    @Slot()
    def upgradeAllNodes(self):
        """ Upgrade all upgradable CompatibilityNode instances in the graph. """
        with self.groupedGraphModification("Upgrade all Nodes"):
            nodes = [n for n in self._graph._compatibilityNodes.values() if n.canUpgrade]
            for node in nodes:
                self.upgradeNode(node)

    @Slot(Attribute, QJsonValue)
    def appendAttribute(self, attribute, value=QJsonValue()):
        if isinstance(value, QJsonValue):
            if value.isArray():
                pyValue = value.toArray().toVariantList()
            else:
                pyValue = None if value.isNull() else value.toObject()
        else:
            pyValue = value
        self.push(commands.ListAttributeAppendCommand(self._graph, attribute, pyValue))

    @Slot(Attribute)
    def removeAttribute(self, attribute):
        self.push(commands.ListAttributeRemoveCommand(self._graph, attribute))

    def clearNodeSelection(self):
        """ Clear node selection. """
        self.selectedNode = None

    def clearNodeHover(self):
        """ Reset currently hovered node to None. """
        self.hoveredNode = None

    undoStack = Property(QObject, lambda self: self._undoStack, constant=True)
    graphChanged = Signal()
    graph = Property(Graph, lambda self: self._graph, notify=graphChanged)
    nodes = Property(QObject, lambda self: self._graph.nodes, notify=graphChanged)
    layout = Property(GraphLayout, lambda self: self._layout, constant=True)

    computeStatusChanged = Signal()
    computing = Property(bool, isComputing, notify=computeStatusChanged)
    computingExternally = Property(bool, isComputingExternally, notify=computeStatusChanged)
    computingLocally = Property(bool, isComputingLocally, notify=computeStatusChanged)
    canSubmit = Property(bool, lambda self: len(submitters), constant=True)

    sortedDFSChunks = Property(QObject, lambda self: self._sortedDFSChunks, constant=True)
    lockedChanged = Signal()

    selectedNodeChanged = Signal()
    # Currently selected node
    selectedNode = makeProperty(QObject, "_selectedNode", selectedNodeChanged, resetOnDestroy=True)

    hoveredNodeChanged = Signal()
    # Currently hovered node
    hoveredNode = makeProperty(QObject, "_hoveredNode", hoveredNodeChanged, resetOnDestroy=True)
