#!/usr/bin/env python
# coding:utf-8
import logging
import os
import time
from enum import Enum
from threading import Thread, Event, Lock
from multiprocessing.pool import ThreadPool

from PySide2.QtCore import Slot, QJsonValue, QObject, QUrl, Property, Signal, QPoint

from meshroom import multiview
from meshroom.common.qt import QObjectListModel
from meshroom.core.attribute import Attribute, ListAttribute
from meshroom.core.graph import Graph, Edge

from meshroom.core.taskManager import TaskManager

from meshroom.core.node import NodeChunk, Node, Status, ExecMode, CompatibilityNode, Position
from meshroom.core import submitters
from meshroom.ui import commands
from meshroom.ui.utils import makeProperty


class FilesModTimePollerThread(QObject):
    """
    Thread responsible for non-blocking polling of last modification times of a list of files.
    Uses a Python ThreadPool internally to split tasks on multiple threads.
    """
    timesAvailable = Signal(list)

    def __init__(self, parent=None):
        super(FilesModTimePollerThread, self).__init__(parent)
        self._thread = None
        self._mutex = Lock()
        self._threadPool = ThreadPool(4)
        self._stopFlag = Event()
        self._refreshInterval = 5  # refresh interval in seconds
        self._files = []

    def start(self, files=None):
        """ Start polling thread.

        Args:
            files: the list of files to monitor
        """
        if self._thread:
            # thread already running, return
            return
        self._stopFlag.clear()
        self._files = files or []
        self._thread = Thread(target=self.run)
        self._thread.start()

    def setFiles(self, files):
        """ Set the list of files to monitor

        Args:
            files: the list of files to monitor
        """
        with self._mutex:
            self._files = files

    def stop(self):
        """ Request polling thread to stop. """
        if not self._thread:
            return
        self._stopFlag.set()
        self._thread.join()
        self._thread = None

    @staticmethod
    def getFileLastModTime(f):
        """ Return 'mtime' of the file if it exists, -1 otherwise. """
        try:
            return os.path.getmtime(f)
        except OSError:
            return -1

    def run(self):
        """ Poll watched files for last modification time. """
        while not self._stopFlag.wait(self._refreshInterval):
            with self._mutex:
                files = list(self._files)
            times = self._threadPool.map(FilesModTimePollerThread.getFileLastModTime, files)
            with self._mutex:
                if files == self._files:
                    self.timesAvailable.emit(times)


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
        self.chunks = []
        self._filesTimePoller = FilesModTimePollerThread(parent=self)
        self._filesTimePoller.timesAvailable.connect(self.compareFilesTimes)
        self._filesTimePoller.start()
        self.setChunks(chunks)

    def setChunks(self, chunks):
        """ Set the list of chunks to monitor. """
        self.chunks = chunks
        self._filesTimePoller.setFiles(self.statusFiles)

    def stop(self):
        """ Stop the status files monitoring. """
        self._filesTimePoller.stop()

    @property
    def statusFiles(self):
        """ Get status file paths from current chunks. """
        return [c.statusFile for c in self.chunks]

    def compareFilesTimes(self, times):
        """
        Compare previous file modification times with results from last poll.
        Trigger chunk status update if file was modified since.

        Args:
            times: the last modification times for currently monitored files.
        """
        newRecords = dict(zip(self.chunks, times))
        for chunk, fileModTime in newRecords.items():
            # update chunk status if last modification time has changed since previous record
            if fileModTime != chunk.statusFileLastModTime:
                chunk.updateStatusFromCache()


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
        self._nodeWidth = 160  # implicit node width
        self._nodeHeight = 120   # implicit node height
        self._gridSpacing = 40  # column/line spacing between nodes

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

    def positionBoundingBox(self, nodes=None):
        """
        Return bounding box for a set of nodes as (x, y, width, height).

        Args:
            nodes (list of Node): the list of nodes or the whole graph if None

        Returns:
            list of int: the resulting bounding box (x, y, width, height)
        """
        if nodes is None:
            nodes = self.graph.nodes.values()
        first = nodes[0]
        bbox = [first.x, first.y, first.x, first.y]
        for n in nodes:
            bbox[0] = min(bbox[0], n.x)
            bbox[1] = min(bbox[1], n.y)
            bbox[2] = max(bbox[2], n.x)
            bbox[3] = max(bbox[3], n.y)

        bbox[2] -= bbox[0]
        bbox[3] -= bbox[1]
        return bbox

    def boundingBox(self, nodes=None):
        """
        Return bounding box for a set of nodes as (x, y, width, height).

        Args:
            nodes (list of Node): the list of nodes or the whole graph if None

        Returns:
            list of int: the resulting bounding box (x, y, width, height)
        """
        bbox = self.positionBoundingBox(nodes)
        bbox[2] += self._nodeWidth
        bbox[3] += self._nodeHeight
        return bbox

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
    def __init__(self, undoStack, taskManager, parent=None):
        super(UIGraph, self).__init__(parent)
        self._undoStack = undoStack
        self._taskManager = taskManager
        self._graph = Graph('', self)

        self._modificationCount = 0
        self._chunksMonitor = ChunksMonitor(parent=self)
        self._computeThread = Thread()
        self._computingLocally = self._submitted = False
        self._sortedDFSChunks = QObjectListModel(parent=self)
        self._layout = GraphLayout(self)
        self._selectedNode = None
        self._selectedNodes = QObjectListModel(parent=self)
        self._hoveredNode = None

        self.computeStatusChanged.connect(self.updateLockedUndoStack)

    def setGraph(self, g):
        """ Set the internal graph. """
        if self._graph:
            self.stopExecution()
            self.clear()
        oldGraph = self._graph
        self._graph = g
        if oldGraph:
            oldGraph.deleteLater()

        self._graph.updated.connect(self.onGraphUpdated)
        self._graph.update()
        self._taskManager.update(self._graph)
        # perform auto-layout if graph does not provide nodes positions
        if Graph.IO.Features.NodesPositions not in self._graph.fileFeatures:
            self._layout.reset()
            # clear undo-stack after layout
            self._undoStack.clear()
        else:
            bbox = self._layout.positionBoundingBox()
            if bbox[2] == 0 and bbox[3] == 0:
                self._layout.reset()
                # clear undo-stack after layout
                self._undoStack.clear()
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
        for chunk in self._sortedDFSChunks:
            chunk.statusChanged.disconnect(self.updateGraphComputingStatus)
        self._sortedDFSChunks.setObjectList(chunks)
        for chunk in self._sortedDFSChunks:
            chunk.statusChanged.connect(self.updateGraphComputingStatus)
        # provide ChunkMonitor with the update list of chunks
        self.updateChunkMonitor(self._sortedDFSChunks)
        # update graph computing status based on the new list of NodeChunks
        self.updateGraphComputingStatus()

    def updateChunkMonitor(self, chunks):
        """ Update the list of chunks for status files monitoring. """
        self._chunksMonitor.setChunks(chunks)

    def clear(self):
        if self._graph:
            self.clearNodeHover()
            self.clearNodeSelection()
            self._taskManager.clear()
            self._graph.clear()
        self._sortedDFSChunks.clear()
        self._undoStack.clear()

    def stopChildThreads(self):
        """ Stop all child threads. """
        self.stopExecution()
        self._chunksMonitor.stop()

    @Slot(str, result=bool)
    def loadGraph(self, filepath, setupProjectFile=True):
        g = Graph('')
        status = g.load(filepath, setupProjectFile)
        if not os.path.exists(g.cacheDir):
            os.mkdir(g.cacheDir)
        self.setGraph(g)
        return status

    @Slot(QUrl)
    def saveAs(self, url):
        if isinstance(url, (str)):
            localFile = url
        else:
            localFile = url.toLocalFile()
        # ensure file is saved with ".mg" extension
        if os.path.splitext(localFile)[-1] != ".mg":
            localFile += ".mg"
        self._graph.save(localFile)
        self._undoStack.setClean()
        # saving file on disk impacts cache folder location
        # => force re-evaluation of monitored status files paths
        self.updateChunkMonitor(self._sortedDFSChunks)

    @Slot()
    def save(self):
        self._graph.save()
        self._undoStack.setClean()

    @Slot()
    def updateLockedUndoStack(self):
        if self.isComputingLocally():
            self._undoStack.lockAtThisIndex()
        else:
            self._undoStack.unlock()

    @Slot(Node)
    def execute(self, node=None):
        nodes = [node] if node else None
        self._taskManager.compute(self._graph, nodes)
        self.updateLockedUndoStack()  # explicitly call the update while it is already computing

    @Slot()
    def stopExecution(self):
        if not self.isComputingLocally():
            return
        self._taskManager.requestBlockRestart()
        self._graph.stopExecution()
        self._taskManager._thread.join()

    @Slot(Node)
    def stopNodeComputation(self, node):
        """ Stop the computation of the node and update all the nodes depending on it. """
        if not self.isComputingLocally():
            return

        # Stop the node and wait Task Manager
        node.stopComputation()
        self._taskManager._thread.join()

    @Slot(Node)
    def cancelNodeComputation(self, node):
        """ Cancel the computation of the node and all the nodes depending on it. """
        if node.getGlobalStatus() == Status.SUBMITTED:
            # Status from SUBMITTED to NONE
            # Make sure to remove the nodes from the Task Manager list
            node.clearSubmittedChunks()
            self._taskManager.removeNode(node, displayList=True, processList=True)

            for n in node.getOutputNodes(recursive=True, dependenciesOnly=True):
                n.clearSubmittedChunks()
                self._taskManager.removeNode(n, displayList=True, processList=True)

    @Slot(Node)
    def submit(self, node=None):
        """ Submit the graph to the default Submitter.
        If a node is specified, submit this node and its uncomputed predecessors.
        Otherwise, submit the whole

        Notes:
            Default submitter is specified using the MESHROOM_DEFAULT_SUBMITTER environment variable.
        """
        self.save()  # graph must be saved before being submitted
        self._undoStack.clear()  # the undo stack must be cleared
        node = [node] if node else None
        self._taskManager.submit(self._graph, os.environ.get('MESHROOM_DEFAULT_SUBMITTER', ''), node)

    def updateGraphComputingStatus(self):
        # update graph computing status
        computingLocally = any([ch.status.execMode == ExecMode.LOCAL and ch.status.status in (Status.RUNNING, Status.SUBMITTED) for ch in self._sortedDFSChunks])
        submitted = any([ch.status.status == Status.SUBMITTED for ch in self._sortedDFSChunks])
        if self._computingLocally != computingLocally or self._submitted != submitted:
            self._computingLocally = computingLocally
            self._submitted = submitted
            self.computeStatusChanged.emit()

    def isComputing(self):
        """ Whether is graph is being computed, either locally or externally. """
        return self.isComputingLocally() or self.isComputingExternally()

    def isComputingExternally(self):
        """ Whether this graph is being computed externally. """
        return self._submitted

    def isComputingLocally(self):
        """ Whether this graph is being computed locally (i.e computation can be stopped). """
        ## One solution could be to check if the thread is still running,
        # but the latency in creating/stopping the thread can be off regarding the update signals.
        # isRunningThread = self._taskManager._thread.isRunning()
        ## Another solution is to retrieve the current status directly from all chunks status
        # isRunning = self._taskManager.hasRunningChunks()
        ## For performance reason, we use a precomputed value updated in updateGraphComputingStatus:
        return self._computingLocally

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

    @Slot(str)
    def beginModification(self, name):
        """ Begin a Graph modification. Calls to beginModification and endModification may be nested, but
        every call to beginModification must have a matching call to endModification. """
        self._modificationCount += 1
        self._undoStack.beginMacro(name)

    @Slot()
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

    def filterNodes(self, nodes):
        """Filter out the nodes that do not exist on the graph."""
        return [ n for n in nodes if n in self._graph.nodes.values() ]

    @Slot(Node, QPoint, QObject)
    def moveNode(self, node, position, nodes=None):
        """
        Move 'node' to the given 'position' and also update the positions of 'nodes' if neccessary.

        Args:
            node (Node): the node to move
            position (QPoint): the target position
            nodes (list[Node]): the nodes to update the position of
        """
        if not nodes:
            nodes = [node]
        nodes = self.filterNodes(nodes)
        if isinstance(position, QPoint):
            position = Position(position.x(), position.y())
        deltaX = position.x - node.x
        deltaY = position.y - node.y
        with self.groupedGraphModification("Move Selected Nodes"):
            for n in nodes:
                position = Position(n.x + deltaX, n.y + deltaY)
                self.push(commands.MoveNodeCommand(self._graph, n, position))

    @Slot(QObject)
    def removeNodes(self, nodes):
        """
        Remove 'nodes' from the graph.

        Args:
            nodes (list[Node]): the nodes to remove
        """
        nodes = self.filterNodes(nodes)
        if any([ n.locked for n in nodes ]):
            return
        with self.groupedGraphModification("Remove Selected Nodes"):
            for node in nodes:
                self.push(commands.RemoveNodeCommand(self._graph, node))

    @Slot(QObject)
    def removeNodesFrom(self, nodes):
        """
        Remove all nodes starting from 'startNode' to graph leaves.

        Args:
            startNode (Node): the node to start from.
        """
        with self.groupedGraphModification("Remove Nodes From Selected Nodes"):
            nodesToRemove, _ = self._graph.dfsOnDiscover(startNodes=nodes, reverse=True, dependenciesOnly=True)
            # Perform nodes removal from leaves to start node so that edges
            # can be re-created in correct order on redo.
            self.removeNodes(list(reversed(nodesToRemove)))

    @Slot(QObject, result="QVariantList")
    def duplicateNodes(self, nodes):
        """
        Duplicate 'nodes'.

        Args:
            nodes (list[Node]): the nodes to duplicate
        Returns:
            list[Node]: the list of duplicated nodes
        """
        nodes = self.filterNodes(nodes)
        # enable updates between duplication and layout to get correct depths during layout
        with self.groupedGraphModification("Duplicate Selected Nodes", disableUpdates=False):
            # disable graph updates during duplication
            with self.groupedGraphModification("Node duplication", disableUpdates=True):
                duplicates = self.push(commands.DuplicateNodesCommand(self._graph, nodes))
            # move nodes below the bounding box formed by the duplicated node(s)
            bbox = self._layout.boundingBox(duplicates)
            for n in duplicates:
                self.moveNode(n, Position(n.x, bbox[3] + self.layout.gridSpacing + n.y))
        return duplicates

    @Slot(QObject, result="QVariantList")
    def duplicateNodesFrom(self, nodes):
        """
        Duplicate all nodes starting from 'nodes' to graph leaves.

        Args:
            nodes (list[Node]): the nodes to start from.
        Returns:
            list[Node]: the list of duplicated nodes
        """
        with self.groupedGraphModification("Duplicate Nodes From Selected Nodes"):
            nodesToDuplicate, _ = self._graph.dfsOnDiscover(startNodes=nodes, reverse=True, dependenciesOnly=True)
            duplicates = self.duplicateNodes(nodesToDuplicate)
        return duplicates

    @Slot(QObject)
    def clearData(self, nodes):
        """ Clear data from 'nodes'. """
        nodes = self.filterNodes(nodes)
        for n in nodes:
            n.clearData()

    @Slot(QObject)
    def clearDataFrom(self, nodes):
        """
        Clear data from all nodes starting from 'nodes' to graph leaves.

        Args:
            nodes (list[Node]): the nodes to start from.
        """
        self.clearData(self._graph.dfsOnDiscover(startNodes=nodes, reverse=True, dependenciesOnly=True)[0])

    @Slot(Attribute, Attribute)
    def addEdge(self, src, dst):
        if isinstance(dst, ListAttribute) and not isinstance(src, ListAttribute):
            with self.groupedGraphModification("Insert and Add Edge on {}".format(dst.getFullNameToNode())):
                self.appendAttribute(dst)
                self._addEdge(src, dst.at(-1))
        else:
            self._addEdge(src, dst)

    def _addEdge(self, src, dst):
        with self.groupedGraphModification("Connect '{}'->'{}'".format(src.getFullNameToNode(), dst.getFullNameToNode())):
            if dst in self._graph.edges.keys():
                self.removeEdge(self._graph.edge(dst))
            self.push(commands.AddEdgeCommand(self._graph, src, dst))

    @Slot(Edge)
    def removeEdge(self, edge):
        if isinstance(edge.dst.root, ListAttribute):
            with self.groupedGraphModification("Remove Edge and Delete {}".format(edge.dst.getFullNameToNode())):
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

    @Slot()
    def forceNodesStatusUpdate(self):
        """ Force re-evaluation of graph's nodes status. """
        self._graph.updateStatusFromCache(force=True)

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

    @Slot(Node)
    def appendSelection(self, node):
        """ Append 'node' to the selection if it is not already part of the selection. """
        if not self._selectedNodes.contains(node):
            self._selectedNodes.append(node)

    @Slot("QVariantList")
    def selectNodes(self, nodes):
        """ Append 'nodes' to the selection. """
        for node in nodes:
            self.appendSelection(node)
        self.selectedNodesChanged.emit()

    @Slot(Node)
    def selectFollowing(self, node):
        """ Select all the nodes the depend on 'node'. """
        self.selectNodes(self._graph.dfsOnDiscover(startNodes=[node], reverse=True, dependenciesOnly=True)[0])

    @Slot(QObject, QObject)
    def boxSelect(self, selection, draggable):
        """
        Select nodes that overlap with 'selection'.
        Takes into account the zoom and position of 'draggable'.

        Args:
            selection: the rectangle selection widget.
            draggable: the parent widget that has position and scale data.
        """
        x = selection.x() - draggable.x()
        y = selection.y() - draggable.y()
        otherX = x + selection.width()
        otherY = y + selection.height()
        x, y, otherX, otherY = [ i / draggable.scale() for i in [x, y, otherX, otherY] ]
        if x == otherX or y == otherY:
            return
        for n in self._graph.nodes:
            bbox = self._layout.boundingBox([n])
            # evaluate if the selection and node intersect
            if not (x > bbox[2] + bbox[0] or otherX < bbox[0] or y > bbox[3] + bbox[1] or otherY < bbox[1]):
                self.appendSelection(n)
        self.selectedNodesChanged.emit()

    @Slot()
    def clearNodeSelection(self):
        """ Clear all node selection. """
        self._selectedNode = None
        self._selectedNodes.clear()
        self.selectedNodeChanged.emit()
        self.selectedNodesChanged.emit()

    def clearNodeHover(self):
        """ Reset currently hovered node to None. """
        self.hoveredNode = None

    undoStack = Property(QObject, lambda self: self._undoStack, constant=True)
    graphChanged = Signal()
    graph = Property(Graph, lambda self: self._graph, notify=graphChanged)
    taskManager = Property(TaskManager, lambda self: self._taskManager, constant=True)
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
    # Current main selected node
    selectedNode = makeProperty(QObject, "_selectedNode", selectedNodeChanged, resetOnDestroy=True)

    selectedNodesChanged = Signal()
    # Currently selected nodes
    selectedNodes = makeProperty(QObject, "_selectedNodes", selectedNodesChanged, resetOnDestroy=True)

    hoveredNodeChanged = Signal()
    # Currently hovered node
    hoveredNode = makeProperty(QObject, "_hoveredNode", hoveredNodeChanged, resetOnDestroy=True)
