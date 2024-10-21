import logging
from threading import Thread
from enum import Enum

import meshroom
from meshroom.common import BaseObject, DictModel, Property, Signal, Slot
from meshroom.core.node import Status
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


class TaskThread(Thread):
    """
    A thread with a pile of nodes to compute
    """
    def __init__(self, manager):
        Thread.__init__(self, target=self.run)
        self._state = State.IDLE
        self._manager = manager
        self.forceCompute = False

    def isRunning(self):
        return self._state == State.RUNNING

    def run(self):
        """ Consume compute tasks. """
        self._state = State.RUNNING

        stopAndRestart = False

        for nId, node in enumerate(self._manager._nodesToProcess):

            # skip already finished/running nodes
            if node.isFinishedOrRunning():
                continue

            # if a node does not exist anymore, node.chunks becomes a PySide property
            try:
                multiChunks = len(node.chunks) > 1
            except TypeError:
                continue

            node.preprocess()
            for cId, chunk in enumerate(node.chunks):
                if chunk.isFinishedOrRunning() or not self.isRunning():
                    continue

                if multiChunks:
                    logging.info('[{node}/{nbNodes}]({chunk}/{nbChunks}) {nodeName}'.format(
                        node=nId+1, nbNodes=len(self._manager._nodesToProcess),
                        chunk=cId+1, nbChunks=len(node.chunks), nodeName=node.nodeType))
                else:
                    logging.info('[{node}/{nbNodes}] {nodeName}'.format(
                        node=nId+1, nbNodes=len(self._manager._nodesToProcess), nodeName=node.nodeType))
                try:
                    chunk.process(self.forceCompute)
                except Exception as e:
                    if chunk.isStopped():
                        stopAndRestart = True
                        break
                    else:
                        logging.error("Error on node computation: {}".format(e))
                        nodesToRemove, _ = self._manager._graph.dfsOnDiscover(startNodes=[node], reverse=True)
                        # remove following nodes from the task queue
                        for n in nodesToRemove[1:]:  # exclude current node
                            try:
                                self._manager._nodesToProcess.remove(n)
                            except ValueError:
                                # Node already removed (for instance a global clear of _nodesToProcess)
                                pass
                            n.clearSubmittedChunks()
            node.postprocess()

            if stopAndRestart:
                break

        if stopAndRestart:
            self._state = State.STOPPED
            self._manager.restartRequested.emit()
        else:
            self._manager._nodesToProcess = []
            self._state = State.DEAD


class TaskManager(BaseObject):
    """
    Manage graph - local and external - computation tasks.
    """
    def __init__(self, parent=None):
        super(TaskManager, self).__init__(parent)
        self._graph = None
        self._nodes = DictModel(keyAttrName='_name', parent=self)
        self._nodesToProcess = []
        self._nodesExtern = []
        # internal thread in which local tasks are executed
        self._thread = TaskThread(self)

        self._blockRestart = False
        self.restartRequested.connect(self.restart)

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
        self._thread._state = State.DEAD

    @Slot()
    def restart(self):
        """
        Restart computing when thread has been stopped.
        Note: this is done like this to avoid app freezing.
        """
        # Make sure to wait the end of the current thread
        self._thread.join()

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

    def compute(self, graph=None, toNodes=None, forceCompute=False, forceStatus=False):
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

        if forceCompute:
            nodes, edges = graph.dfsOnFinish(startNodes=toNodes)
            self.checkCompatibilityNodes(graph, nodes, "COMPUTATION")  # name of the context is important for QML
            self.checkDuplicates(nodes, "COMPUTATION")  # name of the context is important for QML
        else:
            # Check dependencies of toNodes
            if not toNodes:
                toNodes = graph.getLeafNodes(dependenciesOnly=True)
            toNodes = list(toNodes)
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
                chunksStatus = set([chunk.status.status.name for chunk in chunksInConflict])
                chunksName = [node.name for node in chunksInConflict]
                # Warning: Syntax and terms are parsed on QML side to recognize the error
                # Syntax : [Context] ErrorType: ErrorMessage
                msg = '[COMPUTATION] Already Submitted:\nWARNING - Some nodes are already submitted with status: ' \
                      '{}\nNodes: {}'.format(', '.join(chunksStatus), ', '.join(chunksName))

                if forceStatus:
                    logging.warning(msg)
                else:
                    raise RuntimeError(msg)

        for node in nodes:
            node.destroyed.connect(lambda obj=None, name=node.name: self.onNodeDestroyed(obj, name))
            node.beginSequence(forceCompute)

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
        Remove node from the taskmanager when it's destroyed in the graph
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
            raise RuntimeError("[{}] Compatibility Issue:\n"
                               "Cannot compute because of these incompatible nodes:\n"
                               "{}".format(context, sorted(compatNodes)))

    def checkDuplicates(self, nodesToProcess, context):
        for node in nodesToProcess:
            for duplicate in node.duplicates:
                if duplicate in nodesToProcess:
                    # Warning: Syntax and terms are parsed on QML side to recognize the error
                    # Syntax : [Context] ErrorType: ErrorMessage
                    raise RuntimeError("[{}] Duplicates Issue:\n"
                                       "Cannot compute because there are some duplicate nodes to process:\n\n"
                                       "First match: '{}' and '{}'\n\n"
                                       "There can be other duplicate nodes in the list. "
                                       "Please, check the graph and try again.".
                                       format(context, node.nameToLabel(node.name), node.nameToLabel(duplicate.name)))

    def checkNodesDependencies(self, graph, toNodes, context):
        """
        Check dependencies of nodes to process.
        Update toNodes with computable/submittable nodes only.

        Returns:
            bool: True if all the nodes can be processed. False otherwise.
        """
        ready = []
        computed = []

        # The Node which does not have processing functionality
        incomputable = []

        for node in toNodes:
            # Input or Backdrop nodes
            if not node.isComputable:
                incomputable.append(node)
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

        if len(ready) + len(computed) + len(incomputable) != len(toNodes):
            toNodes.clear()
            toNodes.extend(ready)
            return False

        return True

    def raiseDependenciesMessage(self, context):
        # Warning: Syntax and terms are parsed on QML side to recognize the error
        # Syntax : [Context] ErrorType: ErrorMessage
        raise RuntimeWarning("[{}] Unresolved dependencies:\n"
                             "Some nodes cannot be computed in LOCAL/submitted in EXTERN because of "
                             "unresolved dependencies.\n\n"
                             "Nodes which are ready will be processed.".format(context))

    def raiseImpossibleProcess(self, context):
        # Warning: Syntax and terms are parsed on QML side to recognize the error
        # Syntax : [Context] ErrorType: ErrorMessage
        raise RuntimeError("[{}] Impossible Process:\n"
                           "There is no node able to be processed.".format(context))

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
        elif len(meshroom.core.submitters) == 1:
            # if only one submitter available use it
            allSubmitters = meshroom.core.submitters.values()
            sub = next(iter(allSubmitters))  # retrieve the first element
        if sub is None:
            # Warning: Syntax and terms are parsed on QML side to recognize the error
            # Syntax : [Context] ErrorType: ErrorMessage
            raise RuntimeError("[SUBMITTING] Unknown Submitter:\n"
                               "Unknown Submitter called '{submitter}'. Available submitters are: '{allSubmitters}'.".format(
                                submitter=submitter,
                                allSubmitters=str(meshroom.core.submitters.keys())
                                ))

        # Update task manager's lists
        self.updateNodes()
        graph.update()

        # Check dependencies of toNodes
        if not toNodes:
            toNodes = graph.getLeafNodes(dependenciesOnly=True)
        toNodes = list(toNodes)
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

        flowEdges = graph.flowEdges(startNodes=toNodes)
        edgesToProcess = set(edgesToProcess).intersection(flowEdges)

        logging.info("Nodes to process: {}".format(nodesToProcess))
        logging.info("Edges to process: {}".format(edgesToProcess))

        try:
            res = sub.submit(nodesToProcess, edgesToProcess, graph.filepath, submitLabel=submitLabel)
            if res:
                for node in nodesToProcess:
                    node.destroyed.connect(lambda obj=None, name=node.name: self.onNodeDestroyed(obj, name))
                    node.submit()  # update node status
            self._nodes.update(nodesToProcess)
            self._nodesExtern.extend(nodesToProcess)

            # At the end because it raises a WarningError but should not stop processing
            if not allReady:
                self.raiseDependenciesMessage("SUBMITTING")
        except Exception as e:
            logging.error("Error on submit : {}".format(e))

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
    restartRequested = Signal()
