import os
import traceback
import logging
from threading import Thread
from PySide6.QtCore import Qt, QMetaObject, QThread, QEventLoop, QTimer
from enum import Enum
from meshroom.common import strtobool

DEBUGGING = False
if strtobool(os.environ.get("DEBUGGING", "0")):
    DEBUGGING = True
    import debugpy

import meshroom
from meshroom.common import BaseObject, DictModel, Property, Signal, Slot
from meshroom.core.node import Node, Status, ExecMode
from meshroom.core.graph import Graph
from meshroom.core.submitter import jobManager, BaseSubmittedJob
import meshroom.core.graph


class State(Enum):
    """
    State of the Thread that is computing nodes
    """
    IDLE = 0
    RUNNING = 1
    STOPPED = 2
    DEAD = 3
    ERROR = 4


class TaskThread(QThread):
    """
    A thread with a pile of nodes to compute
    """
    def __init__(self, manager):
        QThread.__init__(self)
        self._state = State.IDLE
        self._manager = manager
        self.forceCompute = False
        # Connect to manager's chunk creation handler
        self.createChunksSignal.connect(manager.createChunks, Qt.QueuedConnection)

    def isRunning(self):
        return self._state == State.RUNNING

    def waitForChunkCreation(self, node):
        if node._chunksCreated:
            return True

        loop = QEventLoop()

        # A timer is used to make sure we do not indefinitely block the taskManager
        timer = QTimer()
        timer.timeout.connect(loop.quit)
        timer.setSingleShot(True)
        timer.start(1*60*1000)  # 1 min timeout

        # Connect to completion signal
        def onChunksCreated(createdNode):
            if createdNode == node:
                loop.quit()

        self._manager.chunksCreated.connect(onChunksCreated)

        try:
            # Start the event loop - will block until signal or timeout
            loop.exec()
            if not node._chunksCreated:
                logging.error(f"Timeout or failure creating chunks for {node.name}")
                return False
            return True
        finally:
            self._manager.chunksCreated.disconnect(onChunksCreated)
            timer.stop()
    
    def clearNodes(self, node):
        nodesToRemove, _ = self._manager._graph.dfsOnDiscover(startNodes=[node], reverse=True)
        # remove following nodes from the task queue
        for n in nodesToRemove[1:]:  # exclude current node
            try:
                self._manager._nodesToProcess.remove(n)
            except ValueError:
                # Node already removed (for instance a global clear of _nodesToProcess)
                pass
            # clearSubmittedChunks may create NodeChunk QObjects; those must be  
            # created on the main thread so QML can safely connect to them.  
            QMetaObject.invokeMethod(n, "clearSubmittedChunks", Qt.QueuedConnection)

    def run(self):
        """ Consume compute tasks. """
        if DEBUGGING:
            debugpy.debug_this_thread()

        self._state = State.RUNNING
        stopAndRestart = False

        for nId, node in enumerate(self._manager._nodesToProcess):
            if node not in self._manager._nodesToProcess:
                # Node was removed from the processing list
                continue

            # Skip already finished/running nodes or nodes in compatibility mode
            if node.isFinishedOrRunning() or node.isCompatibilityNode:
                continue

            # Preprocess
            try:
                node.preprocess(self.forceCompute)
            except Exception as exc:
                if node._preprocessChunk.isStopped():
                    stopAndRestart = True
                else:
                    logging.error(f"Error on node preprocess: {exc}")
                    self.clearNodes(node)
                for chunk in node._chunks:
                    if chunk.isAlreadySubmitted():
                        chunk.upgradeStatusTo(Status.NONE, ExecMode.NONE)
                if node.nodeDesc.hasPostprocess:
                    node._postprocessChunk.upgradeStatusTo(Status.NONE, ExecMode.NONE)
                break

            # Request chunk creation if not already done
            if not node._chunksCreated:
                self.createChunksSignal.emit(node)
                # Wait for chunk creation to complete
                if not self.waitForChunkCreation(node):
                    logging.error(f"Failed to create chunks for {node.name}, stopping the process")
                    break
            else:
                node._updateNodeSize()

            # if a node does not exist anymore, node.chunks becomes a PySide property
            try:
                multiChunks = len(node.chunks) > 1
            except TypeError:
                continue

            # Process
            processHasFailed = False
            for cId, chunk in enumerate(node.chunks):
                if chunk.isFinishedOrRunning() or not self.isRunning():
                    continue

                if self._manager.isChunkCancelled(chunk):
                    continue

                _nodeName, _node, _nbNodes = node.nodeType, nId+1, len(self._manager._nodesToProcess)

                if multiChunks:
                    _chunk, _nbChunks = cId+1, len(node.chunks)
                    logging.info(f"[{_node}/{_nbNodes}]({_chunk}/{_nbChunks}) {_nodeName}")
                else:
                    logging.info(f"[{_node}/{_nbNodes}] {_nodeName}")
                try:
                    chunk.process(self.forceCompute)
                except Exception as exc:
                    processHasFailed = True
                    if chunk.isStopped():
                        stopAndRestart = True
                        break
                    else:
                        logging.error(f"Error on node computation: {exc}")
                        self.clearNodes(node)

            if processHasFailed:
                if node.nodeDesc.hasPostprocess:
                    node._postprocessChunk.upgradeStatusTo(Status.NONE, ExecMode.NONE)
                break
            # Postprocess
            try:
                node.postprocess(self.forceCompute)
            except Exception as exc:
                if node._postprocessChunk.isStopped():
                    stopAndRestart = True
                else:
                    logging.error(f"Error on node postprocess: {exc}")
                    self.clearNodes(node)

        if stopAndRestart:
            self._state = State.STOPPED
            self._manager.restartRequested.emit()
        else:
            self._manager._nodesToProcess = []
            self._state = State.DEAD

    # Signals and properties
    createChunksSignal = Signal(BaseObject)


class TaskManager(BaseObject):
    """
    Manage graph - local and external - computation tasks.
    """
    def __init__(self, parent: BaseObject = None):
        super().__init__(parent)
        self._graph = None
        self._nodes = DictModel(keyAttrName='_name', parent=self)
        self._nodesToProcess = []
        self._cancelledChunks = []
        self._nodesExtern = []
        # internal thread in which local tasks are executed
        self._thread = TaskThread(self)

        self._blockRestart = False
        self.restartRequested.connect(self.restart)

    def join(self):
        self._thread.wait()
        self._cancelledChunks = []

    @Slot(BaseObject)
    def createChunks(self, node: Node):
        """ Create chunks on main process """
        try:
            if not node._chunksCreated:
                node.createChunks()
            # Prepare all chunks
            node.initStatusOnCompute()
            self.chunksCreated.emit(node)
        except Exception as e:
            logging.error(f"Failed to create chunks for {node.name}: {e}")
            self.chunksCreated.emit(node)  # Still emit to unblock waiting thread

    def isChunkCancelled(self, chunk):
        for i, ch in enumerate(self._cancelledChunks):
            if ch == chunk:
                del self._cancelledChunks[i]
                return True
        return False

    def requestBlockRestart(self):
        """
        Block computing.
        Note: should only be used to completely stop computing.
        """
        self._blockRestart = True

    def blockRestart(self):
        """ Avoid the automatic restart of computing. """
        for node in self._nodesToProcess:
            chunkCount = 0
            for chunk in node.chunks:
                if chunk.status.status in (Status.SUBMITTED, Status.ERROR):
                    chunk.upgradeStatusTo(Status.NONE)
                    chunkCount += 1
            if chunkCount == len(node.chunks):
                self.removeNode(node, displayList=True)

        self._blockRestart = False
        self._nodesToProcess = []
        self._cancelledChunks = []
        self._thread._state = State.DEAD

    @Slot()
    def pauseProcess(self):
        if self._thread.isRunning():
            self.join()
        for node in self._nodesToProcess:
            if node.getGlobalStatus() == Status.STOPPED:
                # Remove node from the computing list
                self.removeNode(node, displayList=False, processList=True)

                # Remove output nodes from display and computing lists
                outputNodes = node.getOutputNodes(recursive=True, dependenciesOnly=True)
                for n in outputNodes:
                    if n.getGlobalStatus() in (Status.ERROR, Status.SUBMITTED):
                        n.upgradeStatusTo(Status.NONE)
                        self.removeNode(n, displayList=True, processList=True)

    @Slot()
    def restart(self):
        """
        Restart computing when thread has been stopped.
        Note: this is done like this to avoid app freezing.
        """
        # Make sure to wait the end of the current thread
        if self._thread.isRunning():
            self.join()

        # Avoid restart if thread was globally stopped
        if self._blockRestart:
            self.blockRestart()
            return

        if self._thread._state != State.STOPPED:
            return

        for node in self._nodesToProcess:
            if node.getGlobalStatus() == Status.STOPPED:
                # Remove node from the computing list
                self.removeNode(node, displayList=False, processList=True)

                # Remove output nodes from display and computing lists
                outputNodes = node.getOutputNodes(recursive=True, dependenciesOnly=True)
                for n in outputNodes:
                    if n.getGlobalStatus() in (Status.ERROR, Status.SUBMITTED):
                        n.upgradeStatusTo(Status.NONE)
                        self.removeNode(n, displayList=True, processList=True)

        # Start a new thread with the remaining nodes to compute
        self._thread = TaskThread(self)
        self._thread.start()

    def compute(self, graph: Graph = None, toNodes: list[Node] = None, forceCompute: bool = False, forceStatus: bool = False):
        """
        Start graph computation, from root nodes to leaves - or nodes in 'toNodes' if specified.
        Computation tasks (NodeChunk) happen in a separate thread (see TaskThread).

        :param graph: the graph to consider.
        :param toNodes: specific leaves, all graph leaves if None.
        :param forceCompute: force the computation despite nodes status.
        :param forceStatus: force the computation even if some nodes are submitted externally.
        """

        self._graph = graph

        self.updateNodes()
        self._cancelledChunks = []

        if forceCompute:
            nodes, edges = graph.dfsOnFinish(startNodes=toNodes)
            self.checkCompatibilityNodes(graph, nodes, "COMPUTATION")  # name of the context is important for QML
            self.checkDuplicates(nodes, "COMPUTATION")  # name of the context is important for QML
        else:
            # Check dependencies of toNodes
            if not toNodes:
                toNodes = graph.getLeafNodes(dependenciesOnly=True)
            toNodes = list(toNodes)
            toNodes = [node for node in toNodes if not node.isBackdropNode]
            allReady = self.checkNodesDependencies(graph, toNodes, "COMPUTATION")

            # At this point, toNodes is a list
            # If it is empty, we raise an error to avoid passing through dfsToProcess
            if not toNodes:
                self.raiseImpossibleProcess("COMPUTATION")

            nodes, edges = graph.dfsToProcess(startNodes=toNodes)
            if not nodes:
                logging.warning('Nothing to compute')
                return
            self.checkCompatibilityNodes(graph, nodes, "COMPUTATION")  # name of the context is important for QML
            self.checkDuplicates(nodes, "COMPUTATION")  # name of the context is important for QML

            nodes = [node for node in nodes if not self.contains(node)]  # be sure to avoid non-real conflicts
            nodes = list(set(nodes))
            nodes = sorted(nodes, key=lambda x: x.depth)

            chunksInConflict = self.getAlreadySubmittedChunks(nodes)

            if chunksInConflict:
                chunksStatus = {chunk.status.status.name for chunk in chunksInConflict}
                chunksName = [node.name for node in chunksInConflict]
                # Warning: Syntax and terms are parsed on QML side to recognize the error
                # Syntax : [Context] ErrorType: ErrorMessage
                msg = f'[COMPUTATION] Already Submitted:\nWARNING - Some nodes are already submitted with status: ' \
                      f'{", ".join(chunksStatus)}\nNodes: {", ".join(chunksName)}'

                if forceStatus:
                    logging.warning(msg)
                else:
                    raise RuntimeError(msg)

        for node in nodes:
            node.destroyed.connect(lambda obj=None, name=node.name: self.onNodeDestroyed(obj, name))
            node.initStatusOnCompute(forceCompute)

        self._nodes.update(nodes)
        self._nodesToProcess.extend(nodes)

        if self._thread._state == State.IDLE:
            self._thread.start()
        elif self._thread._state in (State.DEAD, State.ERROR):
            self._thread = TaskThread(self)
            self._thread.start()

        # At the end because it raises a WarningError but should not stop processing
        if not allReady:
            self.raiseDependenciesMessage("COMPUTATION")

    def onNodeDestroyed(self, obj, name):
        """
        Remove node from the taskmanager when it is destroyed in the graph
        :param obj:
        :param name:
        :return:
        """
        if name in self._nodes.keys():
            self._nodes.pop(name)

    def contains(self, node):
        return node in self._nodes.values()

    def containsNodeName(self, name):
        """ Check if a node with the argument name belongs to the display list. """
        if name in self._nodes.keys():
            return True
        return False

    def removeNode(self, node, displayList=True, processList=False, externList=False):
        """ Remove node from the Task Manager.

            Args:
                node (Node): node to remove.
                displayList (bool): remove from the display list.
                processList (bool): remove from the nodesToProcess list.
                externList (bool): remove from the nodesExtern list.
        """
        if displayList and self._nodes.contains(node):
            self._nodes.pop(node.name)
        if processList and node in self._nodesToProcess:
            self._nodesToProcess.remove(node)
        if externList and node in self._nodesExtern:
            self._nodesExtern.remove(node)

    def clear(self):
        """
        Remove all the nodes from the taskmanager
        :return:
        """
        self._nodes.clear()
        self._nodesExtern = []
        self._nodesToProcess = []

    def updateNodes(self):
        """
        Update task manager nodes lists by checking the nodes status.
        """
        self._nodesExtern = [node for node in self._nodesExtern if node.isExtern() and node.isAlreadySubmitted()]
        newNodes = [node for node in self._nodes if node.isAlreadySubmitted()]
        if len(newNodes) != len(self._nodes):
            self._nodes.clear()
            self._nodes.update(newNodes)

    def update(self, graph):
        """
        Add all the nodes that are being rendered in a renderfarm to the taskmanager when new graph is loaded
        :param graph:
        :return:
        """
        for node in graph._nodes:
            if node.isAlreadySubmitted() and node._chunks.size() > 0 and node.isExtern():
                self._nodes.add(node)
                self._nodesExtern.append(node)

    def checkCompatibilityNodes(self, graph, nodes, context):
        compatNodes = []
        for node in nodes:
            if node in graph._compatibilityNodes.values():
                compatNodes.append(node.nameToLabel(node.name))
        if compatNodes:
            # Warning: Syntax and terms are parsed on QML side to recognize the error
            # Syntax : [Context] ErrorType: ErrorMessage
            raise RuntimeError(f"[{context}] Compatibility Issue:\n"
                               f"Cannot compute because of these incompatible nodes:\n"
                               f"{sorted(compatNodes)}")

    def checkDuplicates(self, nodesToProcess, context):
        for node in nodesToProcess:
            for duplicate in node.duplicates:
                if duplicate in nodesToProcess:
                    # Warning: Syntax and terms are parsed on QML side to recognize the error
                    # Syntax : [Context] ErrorType: ErrorMessage
                    raise RuntimeError(f"[{context}] Duplicates Issue:\n"
                                       f"Cannot compute because there are some duplicate nodes to process:\n\n"
                                       f"First match: '{node.nameToLabel(node.name)}' and '{node.nameToLabel(duplicate.name)}'\n\n"
                                       f"There can be other duplicate nodes in the list. "
                                       f"Please, check the graph and try again.")

    def checkNodesDependencies(self, graph, toNodes, context):
        """
        Check dependencies of nodes to process.
        Update toNodes with computable/submittable nodes only.

        Returns:
            bool: True if all the nodes can be processed. False otherwise.
        """
        ready = []
        computed = []
        inputNodes = []
        for node in toNodes:
            if node.isInputNode:
                inputNodes.append(node)
            elif context == "COMPUTATION":
                if graph.canComputeTopologically(node) and graph.canSubmitOrCompute(node) % 2 == 1:
                    ready.append(node)
                elif node.isComputed:
                    computed.append(node)
            elif context == "SUBMITTING":
                if graph.canComputeTopologically(node) and graph.canSubmitOrCompute(node) > 1:
                    ready.append(node)
                elif node.isComputed:
                    computed.append(node)
            else:
                raise ValueError("Argument 'context' must be: 'COMPUTATION' or 'SUBMITTING'")

        if len(ready) + len(computed) + len(inputNodes) != len(toNodes):
            toNodes.clear()
            toNodes.extend(ready)
            return False

        return True

    def raiseDependenciesMessage(self, context):
        # Warning: Syntax and terms are parsed on QML side to recognize the error
        # Syntax : [Context] ErrorType: ErrorMessage
        raise RuntimeWarning(f"[{context}] Unresolved dependencies:\n"
                             f"Some nodes cannot be computed in LOCAL/submitted in EXTERN because of "
                             f"unresolved dependencies.\n\n"
                             f"Nodes which are ready will be processed.")

    def raiseImpossibleProcess(self, context):
        # Warning: Syntax and terms are parsed on QML side to recognize the error
        # Syntax : [Context] ErrorType: ErrorMessage
        raise RuntimeError(f"[{context}] Impossible Process:\n"
                           f"There is no node able to be processed.")

    def submit(self, graph, submitter=None, toNodes=None, submitLabel="{projectName}"):
        """
        Nodes are send to the renderfarm
        :param graph:
        :param submitter:
        :param toNodes:
        :return:
        """
        # Ensure submitter is properly set
        sub = None
        if submitter:
            sub = meshroom.core.submitters.get(submitter, None)
        elif len(meshroom.core.submitters) >= 1:
            # if only one submitter available use it
            allSubmitters = meshroom.core.submitters.values()
            sub = next(iter(allSubmitters))  # retrieve the first element
        if sub is None:
            # Warning: Syntax and terms are parsed on QML side to recognize the error
            # Syntax : [Context] ErrorType: ErrorMessage
            raise RuntimeError(f"[SUBMITTING] Unknown Submitter:\n"
                               f"Unknown Submitter called '{submitter}'. "
                               f"Available submitters are: '{str(meshroom.core.submitters.keys())}'.")

        # TODO : If possible with the submitter (ATTACH_JOB)

        # Update task manager's lists
        self.updateNodes()
        graph.update()

        # Check dependencies of toNodes
        if not toNodes:
            toNodes = graph.getLeafNodes(dependenciesOnly=True)
        toNodes = list(toNodes)
        toNodes = [node for node in toNodes if not node.isBackdropNode]
        allReady = self.checkNodesDependencies(graph, toNodes, "SUBMITTING")

        # At this point, toNodes is a list
        # If it is empty, we raise an error to avoid passing through dfsToProcess
        if not toNodes:
            self.raiseImpossibleProcess("SUBMITTING")

        nodesToProcess, edgesToProcess = graph.dfsToProcess(startNodes=toNodes)
        if not nodesToProcess:
            logging.warning('Nothing to compute')
            return
        self.checkCompatibilityNodes(graph, nodesToProcess, "SUBMITTING")  # name of the context is important for QML
        self.checkDuplicates(nodesToProcess, "SUBMITTING")  # name of the context is important for QML

        # Update nodes status
        for node in nodesToProcess:
            node.destroyed.connect(lambda obj=None, name=node.name: self.onNodeDestroyed(obj, name))
            node.initStatusOnSubmit()
            jobManager.resetNodeJob(node)

        graph.updateMonitoredFiles()

        flowEdges = graph.flowEdges(startNodes=toNodes)
        edgesToProcess = set(edgesToProcess).intersection(flowEdges)

        logging.info(f"Nodes to process: {nodesToProcess}")
        logging.info(f"Edges to process: {edgesToProcess}")

        try:
            res = sub.submit(nodesToProcess, edgesToProcess, graph.filepath, submitLabel=submitLabel)
            if res:
                if isinstance(res, BaseSubmittedJob):
                    jobManager.addJob(res, nodesToProcess)
            else:
                for node in nodesToProcess:
                    # TODO : Notify the node that there was an issue on submit
                    pass
            self._nodes.update(nodesToProcess)
            self._nodesExtern.extend(nodesToProcess)

            # At the end because it raises a WarningError but should not stop processing
            if not allReady:
                self.raiseDependenciesMessage("SUBMITTING")
        except Exception as exc:
            logging.error(f"Error on submit : {exc}\n{traceback.format_exc()}")

    def submitFromFile(self, graphFile, submitter, toNode=None, submitLabel="{projectName}"):
        """
        Submit the given graph via the given submitter.
        """
        graph = meshroom.core.graph.loadGraph(graphFile)
        self.submit(graph, submitter, toNode, submitLabel=submitLabel)

    def getAlreadySubmittedChunks(self, nodes):
        """
        Check if nodes have already been submitted in another Meshroom instance.
        :param nodes:
        :return:
        """
        out = []
        for node in nodes:
            for chunk in node.chunks:
                # Already submitted/running chunks in another task manager
                if chunk.isAlreadySubmitted() and not self.containsNodeName(chunk.statusNodeName):
                    out.append(chunk)
        return out

    nodes = Property(BaseObject, lambda self: self._nodes, constant=True)
    chunksCreated = Signal(BaseObject)
    restartRequested = Signal()
