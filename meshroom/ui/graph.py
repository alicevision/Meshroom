#!/usr/bin/env python
# coding:utf-8
from collections.abc import Iterable
import logging
import os
import json
from enum import Enum
from threading import Thread, Event, Lock
from multiprocessing.pool import ThreadPool
from typing import Iterator, Optional, Union

from PySide6.QtCore import (
    Slot,
    QJsonValue,
    QObject,
    QUrl,
    Property,
    Signal,
    QPoint,
    QItemSelectionModel,
    QItemSelection,
)

from meshroom.core import sessionUid
from meshroom.common.qt import QObjectListModel
from meshroom.core.attribute import Attribute, ListAttribute
from meshroom.core.graph import Graph, Edge
from meshroom.core.graphIO import GraphIO

from meshroom.core.taskManager import TaskManager

from meshroom.core.node import NodeChunk, Node, Status, ExecMode, CompatibilityNode, Position
from meshroom.core import submitters
from meshroom.ui import commands
from meshroom.ui.utils import makeProperty


class PollerRefreshStatus(Enum):
    AUTO_ENABLED = 0  # The file watcher polls every single status file periodically
    DISABLED = 1  # The file watcher is disabled and never polls any file
    MINIMAL_ENABLED = 2  # The file watcher only polls status files for chunks that are either submitted or running


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
        if submitters:
            self._filePollerRefresh = PollerRefreshStatus.MINIMAL_ENABLED
        else:
            self._filePollerRefresh = PollerRefreshStatus.DISABLED

    def __del__(self):
        self._threadPool.terminate()
        self._threadPool.join()

    def start(self, files=None):
        """ Start polling thread.

        Args:
            files: the list of files to monitor
        """
        if self._filePollerRefresh is PollerRefreshStatus.DISABLED:
            return
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

    def onFilePollerRefreshChanged(self, value):
        """ Stop or start the file poller depending on the new refresh status. """
        self._filePollerRefresh = PollerRefreshStatus(value)
        if self._filePollerRefresh is PollerRefreshStatus.DISABLED:
            self.stop()
        else:
            self.start()
        self.filePollerRefreshReady.emit()

    filePollerRefresh = Property(int, lambda self: self._filePollerRefresh.value, constant=True)
    filePollerRefreshReady = Signal()  # The refresh status has been updated and is ready to be used


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
        self.monitorableChunks = []
        self.monitoredChunks = []
        self._filesTimePoller = FilesModTimePollerThread(parent=self)
        self._filesTimePoller.timesAvailable.connect(self.compareFilesTimes)
        self._filesTimePoller.start()
        self.setChunks(chunks)

        self.filePollerRefreshChanged.connect(self._filesTimePoller.onFilePollerRefreshChanged)
        self._filesTimePoller.filePollerRefreshReady.connect(self.onFilePollerRefreshUpdated)

    def setChunks(self, chunks):
        """
        Set the lists of chunks that can be monitored and that are monitored.
        When the file poller status is set to AUTO_ENABLED, the lists of monitorable and monitored chunks are identical.
        """
        self.monitorableChunks = chunks
        files, monitoredChunks = self.watchedStatusFiles
        self._filesTimePoller.setFiles(files)
        self.monitoredChunks = monitoredChunks

    def stop(self):
        """ Stop the status files monitoring. """
        self._filesTimePoller.stop()

    @property
    def statusFiles(self):
        """ Get status file paths from the monitorable chunks. """
        return [c.statusFile for c in self.monitorableChunks]

    @property
    def watchedStatusFiles(self):
        """
        Get the status file paths from the currently monitored chunks.
        Depending on the file poller status, the paths may either be those of all the current chunks, or those from the currently submitted/running chunks.
        """

        files = []
        chunks = []
        if self.filePollerRefresh is PollerRefreshStatus.AUTO_ENABLED.value:
            return self.statusFiles, self.monitorableChunks
        elif self.filePollerRefresh is PollerRefreshStatus.MINIMAL_ENABLED.value:
            for c in self.monitorableChunks:
                # When a chunk's status is ERROR, it may be externally re-submitted and it should thus still be monitored
                if c._status.status is Status.SUBMITTED or c._status.status is Status.RUNNING or c._status.status is Status.ERROR:
                    files.append(c.statusFile)
                    chunks.append(c)
        return files, chunks

    def compareFilesTimes(self, times):
        """
        Compare previous file modification times with results from last poll.
        Trigger chunk status update if file was modified since.

        Args:
            times: the last modification times for currently monitored files.
        """
        newRecords = dict(zip(self.monitoredChunks, times))
        for chunk, fileModTime in newRecords.items():
            # update chunk status if last modification time has changed since previous record
            if fileModTime != chunk.statusFileLastModTime:
                chunk.updateStatusFromCache()
                chunk.node.updateOutputAttr()

    def onFilePollerRefreshUpdated(self):
        """
        Upon an update of the file poller status, retrigger the generation of the list of status files for
        the chunks that are to be watched.
        In auto-refresh mode, this includes all the chunks' status files.
        In minimal auto-refresh mode, this includes only the chunks that are submitted or running.
        """
        if self.filePollerRefresh is not PollerRefreshStatus.DISABLED.value:
            files, chunks = self.watchedStatusFiles
            self._filesTimePoller.setFiles(files)
            self.monitoredChunks = chunks

    def onComputeStatusChanged(self):
        """
        When a chunk's status is updated, update the list of watched files with submitted and running chunks if the
        file poller status is minimal auto-refresh.
        """
        if self.filePollerRefresh is PollerRefreshStatus.MINIMAL_ENABLED.value:
            files, chunks = self.watchedStatusFiles
            self._filesTimePoller.setFiles(files)
            self.monitoredChunks = chunks

    filePollerRefreshChanged = Signal(int)
    filePollerRefresh = Property(int, lambda self: self._filesTimePoller.filePollerRefresh, notify=filePollerRefreshChanged)


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
        if not self.graph.nodes:
            return
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
        self._nodeSelection = QItemSelectionModel(self._graph.nodes, parent=self)
        self._hoveredNode = None

        self.submitLabel = "{projectName}"
        self.computeStatusChanged.connect(self.updateLockedUndoStack)
        self.filePollerRefreshChanged.connect(self._chunksMonitor.filePollerRefreshChanged)

    def setGraph(self, g):
        """ Set the internal graph. """
        if self._graph:
            self.stopExecution()
            # Clear all the locally submitted nodes at once before the graph gets changed, as it won't receive further updates
            if self._computingLocally:
                self._graph.clearLocallySubmittedNodes()
            self.clear()
        oldGraph = self._graph
        self._graph = g
        if oldGraph:
            oldGraph.deleteLater()

        self._graph.updated.connect(self.onGraphUpdated)
        self._taskManager.update(self._graph)

        # update and connect chunks when the graph is set for the first time
        self.updateChunks()

        # perform auto-layout if graph does not provide nodes positions
        if GraphIO.Features.NodesPositions not in self._graph.fileFeatures:
            self._layout.reset()
            # clear undo-stack after layout
            self._undoStack.clear()
        else:
            bbox = self._layout.positionBoundingBox()
            if bbox[2] == 0 and bbox[3] == 0:
                self._layout.reset()
                # clear undo-stack after layout
                self._undoStack.clear()

        self._nodeSelection.setModel(self._graph.nodes)
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
            chunk.statusChanged.disconnect(self._chunksMonitor.onComputeStatusChanged)
        self._sortedDFSChunks.setObjectList(chunks)
        for chunk in self._sortedDFSChunks:
            chunk.statusChanged.connect(self.updateGraphComputingStatus)
            chunk.statusChanged.connect(self._chunksMonitor.onComputeStatusChanged)
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

    @Slot(str)
    def loadGraph(self, filepath):
        g = Graph("")
        if filepath:
            g.load(filepath)
            if not os.path.exists(g.cacheDir):
                os.mkdir(g.cacheDir)
        self.setGraph(g)

    @Slot(str, bool, result=bool)
    def initFromTemplate(self, filepath, publishOutputs=False):
        graph = Graph("")
        if filepath:
            graph.initFromTemplate(filepath, publishOutputs=publishOutputs)
        self.setGraph(graph)

    @Slot(QUrl, result="QVariantList")
    @Slot(QUrl, QPoint, result="QVariantList")
    def importProject(self, filepath, position=None):
        if isinstance(filepath, (QUrl)):
            # depending how the QUrl has been initialized,
            # toLocalFile() may return the local path or an empty string
            localFile = filepath.toLocalFile()
            if not localFile:
                localFile = filepath.toString()
        else:
            localFile = filepath
        if isinstance(position, QPoint):
                position = Position(position.x(), position.y())
        yOffset = self.layout.gridSpacing + self.layout.nodeHeight
        return self.push(commands.ImportProjectCommand(self._graph, localFile, position=position, yOffset=yOffset))

    @Slot(QUrl)
    def saveAs(self, url):
        self._saveAs(url)

    @Slot(QUrl)
    def saveAsTemplate(self, url):
        self._saveAs(url, setupProjectFile=False, template=True)

    def _saveAs(self, url, setupProjectFile=True, template=False):
        """ Helper function for 'save as' features. """
        if isinstance(url, (str)):
            localFile = url
        else:
            localFile = url.toLocalFile()
        # ensure file is saved with ".mg" extension
        if os.path.splitext(localFile)[-1] != ".mg":
            localFile += ".mg"
        self._graph.save(localFile, setupProjectFile=setupProjectFile, template=template)
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

    @Slot()
    @Slot(Node)
    @Slot(list)
    def execute(self, nodes: Optional[Union[list[Node], Node]] = None):
        nodes = [nodes] if not isinstance(nodes, Iterable) and nodes else nodes
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

    @Slot()
    @Slot(Node)
    @Slot(list)
    def submit(self, nodes: Optional[Union[list[Node], Node]] = None):
        """ Submit the graph to the default Submitter.
        If a node is specified, submit this node and its uncomputed predecessors.
        Otherwise, submit the whole

        Notes:
            Default submitter is specified using the MESHROOM_DEFAULT_SUBMITTER environment variable.
        """
        self.save()  # graph must be saved before being submitted
        self._undoStack.clear()  # the undo stack must be cleared
        nodes = [nodes] if not isinstance(nodes, Iterable) and nodes else nodes
        self._taskManager.submit(self._graph, os.environ.get('MESHROOM_DEFAULT_SUBMITTER', ''), nodes, submitLabel=self.submitLabel)

    def updateGraphComputingStatus(self):
        # update graph computing status
        computingLocally = any([
                                (ch.status.execMode == ExecMode.LOCAL and
                                ch.status.sessionUid == sessionUid and
                                ch.status.status in (Status.RUNNING, Status.SUBMITTED))
                                    for ch in self._sortedDFSChunks])
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

    def moveNode(self, node: Node, position: Position):
        """
        Move `node` to the given `position`.

        Args:
            node: The node to move.
            position: The target position.
        """
        self.push(commands.MoveNodeCommand(self._graph, node, position))

    @Slot(QPoint)
    def moveSelectedNodesBy(self, offset: QPoint):
        """Move all the selected nodes by the given `offset`."""

        with self.groupedGraphModification("Move Selected Nodes"):
            for node in self.iterSelectedNodes():
                position = Position(node.x + offset.x(), node.y + offset.y())
                self.moveNode(node, position)

    @Slot()
    def removeSelectedNodes(self):
        """Remove selected nodes from the graph."""
        self.removeNodes(list(self.iterSelectedNodes()))

    @Slot(list)
    def removeNodes(self, nodes: list[Node]):
        """
        Remove 'nodes' from the graph.

        Args:
            nodes: The nodes to remove.
        """
        if any(n.locked for n in nodes):
            return

        with self.groupedGraphModification("Remove Nodes"):
            for node in nodes:
                self.push(commands.RemoveNodeCommand(self._graph, node))

    @Slot(list)
    def removeNodesFrom(self, nodes: list[Node]):
        """
        Remove all nodes starting from 'nodes' to graph leaves.

        Args:
            nodes: the nodes to start from.
        """
        with self.groupedGraphModification("Remove Nodes From Selected Nodes"):
            nodesToRemove, _ = self._graph.dfsOnDiscover(startNodes=nodes, reverse=True, dependenciesOnly=True)
            # filter out nodes that will be removed more than once
            uniqueNodesToRemove = list(dict.fromkeys(nodesToRemove))
            # Perform nodes removal from leaves to start node so that edges
            # can be re-created in correct order on redo.
            self.removeNodes(list(reversed(uniqueNodesToRemove)))

    @Slot(list, result=list)
    def duplicateNodes(self, nodes: list[Node]) -> list[Node]:
        """
        Duplicate 'nodes'.

        Args:
            nodes: the nodes to duplicate.

        Returns:
            The list of duplicated nodes.
        """
        nPositions = [(n.x, n.y) for n in self._graph.nodes]
        # enable updates between duplication and layout to get correct depths during layout
        with self.groupedGraphModification("Duplicate Selected Nodes", disableUpdates=False):
            # disable graph updates during duplication
            with self.groupedGraphModification("Node duplication", disableUpdates=True):
                duplicates = self.push(commands.DuplicateNodesCommand(self._graph, nodes))
            # move nodes below the bounding box formed by the duplicated node(s)
            bbox = self._layout.boundingBox(nodes)

            for n in duplicates:
                yPos = n.y + self.layout.gridSpacing + bbox[3]
                if (n.x, yPos) in nPositions:
                    # make sure the node will not be moved on top of another node
                    while (n.x, yPos) in nPositions:
                        yPos = yPos + self.layout.gridSpacing + self.layout.nodeHeight
                    self.moveNode(n, Position(n.x, yPos))
                else:
                    self.moveNode(n, Position(n.x, bbox[3] + self.layout.gridSpacing + n.y))
                nPositions.append((n.x, n.y))

        return duplicates

    @Slot(list, result=list)
    def duplicateNodesFrom(self, nodes: list[Node]) -> list[Node]:
        """
        Duplicate all nodes starting from 'nodes' to graph leaves.

        Args:
            node: The nodes to start from.
        Returns:
            The list of duplicated nodes.
        """
        with self.groupedGraphModification("Duplicate Nodes From Selected Nodes"):
            nodesToDuplicate, _ = self._graph.dfsOnDiscover(startNodes=nodes, reverse=True, dependenciesOnly=True)
            # filter out nodes that will be duplicated more than once
            uniqueNodesToDuplicate = list(dict.fromkeys(nodesToDuplicate))
            duplicates = self.duplicateNodes(uniqueNodesToDuplicate)
        return duplicates
    
    @Slot(Edge, result=bool)
    def canExpandForLoop(self, currentEdge):
        """ Check if the list attribute can be expanded by looking at all the edges connected to it. """
        listAttribute = currentEdge.src.root
        if not listAttribute:
            return False
        srcIndex = listAttribute.index(currentEdge.src)
        allSrc = [e.src for e in self._graph.edges.values()]
        for i in range(len(listAttribute)):
            if i == srcIndex:
                continue
            if listAttribute.at(i) in allSrc:
                return False
        return True

    @Slot(Edge, result=Edge)
    def expandForLoop(self, currentEdge):
        """ Expand 'node' by creating all its output nodes. """
        with self.groupedGraphModification("Expand For Loop Node"):
            listAttribute = currentEdge.src.root
            dst = currentEdge.dst

            for i in range(1, len(listAttribute)):
                duplicates = self.duplicateNodesFrom([dst.node])
                newNode = duplicates[0]
                previousEdge = self.graph.edge(newNode.attribute(dst.name))
                self.replaceEdge(previousEdge, listAttribute.at(i), previousEdge.dst)

            # Last, replace the edge with the first element of the list
            return self.replaceEdge(currentEdge, listAttribute.at(0), dst)

    @Slot(Edge)
    def collapseForLoop(self, currentEdge):
        """ Collapse 'node' by removing all its output nodes. """
        with self.groupedGraphModification("Collapse For Loop Node"):
            listAttribute = currentEdge.src.root
            srcIndex = listAttribute.index(currentEdge.src)
            allSrc = [e.src for e in self._graph.edges.values()]
            for i in reversed(range(len(listAttribute))):
                if i == srcIndex:
                    continue
                occurence = allSrc.index(listAttribute.at(i)) if listAttribute.at(i) in allSrc else -1
                if occurence != -1:
                    self.removeNodesFrom([self.graph.edges.at(occurence).dst.node])
                    # update the edges from allSrc
                    allSrc = [e.src for e in self._graph.edges.values()]

    @Slot()
    def clearSelectedNodesData(self):
        """Clear data from all selected nodes."""
        self.clearData(self.iterSelectedNodes())

    @Slot(list)
    def clearData(self, nodes: list[Node]):
        """ Clear data from 'nodes'. """
        for n in nodes:
            n.clearData()

    @Slot(list)
    def clearDataFrom(self, nodes: list[Node]):
        """
        Clear data from all nodes starting from 'nodes' to graph leaves.

        Args:
            nodes: The nodes to start from.
        """
        self.clearData(self._graph.dfsOnDiscover(startNodes=nodes, reverse=True, dependenciesOnly=True)[0])

    @Slot(Attribute, Attribute)
    def addEdge(self, src, dst):
        if isinstance(src, ListAttribute) and not isinstance(dst, ListAttribute):
            self._addEdge(src.at(0), dst)
        elif isinstance(dst, ListAttribute) and not isinstance(src, ListAttribute):
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

    @Slot(Edge, Attribute, Attribute, result=Edge)
    def replaceEdge(self, edge, newSrc, newDst):
        with self.groupedGraphModification("Replace Edge '{}'->'{}' with '{}'->'{}'".format(edge.src.getFullNameToNode(), edge.dst.getFullNameToNode(), newSrc.getFullNameToNode(), newDst.getFullNameToNode())):
            self.removeEdge(edge)
            self.addEdge(newSrc, newDst)
        return self._graph.edge(newDst)
    
    @Slot(Attribute, result=Edge)
    def getEdge(self, dst):
        return self._graph.edge(dst)

    @Slot(Attribute, "QVariant")
    def setAttribute(self, attribute, value):
        self.push(commands.SetAttributeCommand(self._graph, attribute, value))

    @Slot(Attribute)
    def resetAttribute(self, attribute):
        """ Reset 'attribute' to its default value """
        with self.groupedGraphModification("Reset Attribute '{}'".format(attribute.name)):
            # if the attribute is a ListAttribute, remove all edges
            if isinstance(attribute, ListAttribute):
                for edge in self._graph.edges:
                    # if the edge is connected to one of the ListAttribute's elements, remove it
                    if edge.src in attribute.value:
                        self.removeEdge(edge)
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
            sortedNodes = sorted(nodes, key=lambda x: x.name)
            for node in sortedNodes:
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

    @Slot(Attribute)
    def removeImage(self, image):
        with self.groupedGraphModification("Remove Image"):
            # look if the viewpoint's intrinsic is used by another viewpoint
            # if not, remove it
            intrinsicId = image.intrinsicId.value

            intrinsicUsed = False
            for intrinsic in self.cameraInit.attribute("viewpoints").getExportValue():
                if image.getExportValue() != intrinsic and intrinsic['intrinsicId'] == intrinsicId:
                    intrinsicUsed = True
                    break

            if not intrinsicUsed:
                #find the intrinsic and remove it
                for intrinsic in self.cameraInit.attribute("intrinsics"):
                    if intrinsic.getExportValue()["intrinsicId"] == intrinsicId:
                        self.removeAttribute(intrinsic)
                        break

            # After every check we finally remove the attribute
            self.removeAttribute(image)

    @Slot()
    def removeAllImages(self):
        with self.groupedGraphModification("Remove All Images"):
            self.push(commands.RemoveImagesCommand(self._graph, [self.cameraInit]))

    @Slot()
    def removeImagesFromAllGroups(self):
        with self.groupedGraphModification("Remove Images From All CameraInit Nodes"):
            self.push(commands.RemoveImagesCommand(self._graph, list(self.cameraInits)))

    @Slot(list)
    @Slot(list, int)
    def selectNodes(self, nodes, command=QItemSelectionModel.SelectionFlag.ClearAndSelect):
        """Update selection with `nodes` using the specified `command`."""
        indices = [self._graph._nodes.indexOf(node) for node in nodes]
        self.selectNodesByIndices(indices, command)

    @Slot(Node)
    @Slot(Node, int)
    def selectFollowing(self, node: Node, command=QItemSelectionModel.SelectionFlag.ClearAndSelect):
        """Select all the nodes that depend on `node`."""
        self.selectNodes(
            self._graph.dfsOnDiscover(startNodes=[node], reverse=True, dependenciesOnly=True)[0], command
        )
        self.selectedNode = node

    @Slot(int)
    @Slot(int, int)
    def selectNodeByIndex(self, index: int, command=QItemSelectionModel.SelectionFlag.ClearAndSelect):
        """Update selection with node at the given `index` using the specified `command`."""
        if isinstance(command, int):
            command = QItemSelectionModel.SelectionFlag(command)

        self.selectNodesByIndices([index], command)

        if self._nodeSelection.isRowSelected(index):
            self.selectedNode = self._graph.nodes.at(index)

    @Slot(list)
    @Slot(list, int)
    def selectNodesByIndices(
        self, indices: list[int], command=QItemSelectionModel.SelectionFlag.ClearAndSelect
    ):
        """Update selection with node at given `indices` using the specified `command`.
        
        Args:
            indices: The list of indices to select.
            command: The selection command to use.
        """
        if isinstance(command, int):
            command = QItemSelectionModel.SelectionFlag(command)

        itemSelection = QItemSelection()
        for index in indices:
            itemSelection.select(
                self._graph.nodes.index(index), self._graph.nodes.index(index)
            )

        self._nodeSelection.select(itemSelection, command)

        if self.selectedNode and not self.isSelected(self.selectedNode):
            self.selectedNode = None

    def iterSelectedNodes(self) -> Iterator[Node]:
        """Iterate over the currently selected nodes."""
        for idx in self._nodeSelection.selectedRows():
            yield self._graph.nodes.at(idx.row())

    @Slot(result=list)
    def getSelectedNodes(self) -> list[Node]:
        """Return the list of selected Node instances."""
        return list(self.iterSelectedNodes())

    @Slot(Node, result=bool)
    def isSelected(self, node: Node) -> bool:
        """Whether `node` is part of the current selection."""
        return self._nodeSelection.isRowSelected(self._graph.nodes.indexOf(node))

    @Slot()
    def clearNodeSelection(self):
        """Clear all node selection."""
        self.selectedNode = None
        self._nodeSelection.clear()

    def clearNodeHover(self):
        """ Reset currently hovered node to None. """
        self.hoveredNode = None

    @Slot(str)
    def setSelectedNodesColor(self, color: str):
        """ Sets the Provided color on the selected Nodes.

        Args:
            color (str): Hex code of the color to be set on the nodes.
        """
        # Update the color attribute of the nodes which are currently selected
        with self.groupedGraphModification("Set Nodes Color"):
            # For each of the selected nodes -> Check if the node has a color -> Apply the color if it has
            for node in self.iterSelectedNodes():
                if node.hasInternalAttribute("color"):
                    self.setAttribute(node.internalAttribute("color"), color)

    @Slot(result=str)
    def getSelectedNodesContent(self) -> str:
        """
        Serialize the current node selection and return it as JSON formatted string.

        Returns an empty string if the selection is empty.
        """
        if not self._nodeSelection.hasSelection():
            return ""
        graphData = self._graph.serializePartial(self.getSelectedNodes())
        return json.dumps(graphData, indent=4)

    @Slot(str, QPoint, result=list)
    def pasteNodes(self, serializedData: str, position: Optional[QPoint]=None) -> list[Node]:
        """
        Import string-serialized graph content `serializedData` in the current graph, optionally at the given 
        `position`.
        If the `serializedData` does not contain valid serialized graph data, nothing is done.

        This method can be used with the result of "getSelectedNodesContent".
        But it also accepts any serialized content that matches the graph data or graph content format.

        For example, it is enough to have:
        {"nodeName_1": {"nodeType":"CameraInit"}, "nodeName_2": {"nodeType":"FeatureMatching"}}
        in `serializedData` to create a default CameraInit and a default FeatureMatching nodes.

        Args:
            serializedData: The string-serialized graph data.
            position: The position where to paste the nodes. If None, the nodes are pasted at (0, 0).

        Returns:
            list: the list of Node objects that were pasted and added to the graph
        """
        try:
            graphData = json.loads(serializedData)
        except json.JSONDecodeError:
            logging.warning("Content is not a valid JSON string.")
            return []

        pos = Position(position.x(), position.y()) if position else Position(0, 0)
        result = self.push(commands.PasteNodesCommand(self._graph, graphData, pos))
        if result is False:
            logging.warning("Content is not a valid graph data.")
            return []
        return result


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

    nodeSelection = makeProperty(QObject, "_nodeSelection")

    hoveredNodeChanged = Signal()
    # Currently hovered node
    hoveredNode = makeProperty(QObject, "_hoveredNode", hoveredNodeChanged, resetOnDestroy=True)

    filePollerRefreshChanged = Signal(int)
    filePollerRefresh = Property(int, lambda self: self._chunksMonitor.filePollerRefresh, notify=filePollerRefreshChanged)
