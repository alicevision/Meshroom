import logging
from threading import Thread
from enum import Enum

import meshroom
from meshroom.common import BaseObject, DictModel, Property


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

        for nId, node in enumerate(self._manager._nodesToProcess):

            # skip already finished/running nodes
            if node.isFinishedOrRunning():
                continue

            # if a node does not exist anymore, node.chunks becomes a PySide property
            try:
                multiChunks = len(node.chunks) > 1
            except TypeError:
                continue

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
                        pass
                    else:
                        logging.error("Error on node computation: {}".format(e))
                        nodesToRemove, _ = self._manager._graph.nodesFromNode(node)
                        # remove following nodes from the task queue
                        for n in nodesToRemove[1:]:  # exclude current node
                            try:
                                self._manager._nodesToProcess.remove(n)
                            except ValueError:
                                # Node already removed (for instance a global clear of _nodesToProcess)
                                pass
                            n.clearSubmittedChunks()

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

    def compute(self, graph=None, toNodes=None, forceCompute=False):
        """
        Start graph computation, from root nodes to leaves - or nodes in 'toNodes' if specified.
        Computation tasks (NodeChunk) happen in a separate thread (see TaskThread).

        :param graph: the graph to consider.
        :param toNodes: specific leaves, all graph leaves if None.
        :param forceCompute: force the computation despite nodes status.
        """
        self._graph = graph

        if self._thread._state != State.RUNNING:
            self._nodes.clear()
            externEmpty = any(node.isAlreadySubmitted() for node in self._nodesExtern)
            if not externEmpty:
                self._nodes.update(self._nodesExtern)
            else:
                self._nodesExtern = []

        if forceCompute:
            nodes, edges = graph.dfsOnFinish(startNodes=toNodes)
        else:
            allNodes, edges = graph.dfsToProcess(startNodes=toNodes)
            nodes = [node for node in allNodes if not node.isAlreadySubmittedOrFinished()]

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

    def onNodeDestroyed(self, obj, name):
        """
        Remove node from the taskmanager when it's destroyed in the graph
        :param obj:
        :param name:
        :return:
        """
        if name in self._nodes.keys():
            self._nodes.pop(name)

    def removeNode(self, node):
        """ Remove node from the Task Manager. """
        if self._nodes.contains(node):
            self._nodes.pop(node.name)
        if node in self._nodesToProcess:
            self._nodesToProcess.remove(node)
        if node in self._nodesExtern:
            self._nodesExtern.remove(node)

    def clear(self):
        """
        Remove all the nodes from the taskmanager
        :return:
        """
        self._nodes.clear()
        self._nodesExtern = []
        self._nodesToProcess = []

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

    def submit(self, graph=None, submitter=None, toNodes=None):
        """
        Nodes are send to the renderfarm
        :param graph:
        :param submitter:
        :param toNodes:
        :return:
        """

        # ensure submitter is properly set
        sub = meshroom.core.submitters.get(submitter, None)
        if sub is None:
            raise RuntimeError("Unknown Submitter : " + submitter)

        if self._thread._state != State.RUNNING:
            self._nodes.clear()

            externEmpty = True
            for node in self._nodesExtern:
                if node.isAlreadySubmitted():
                    externEmpty = False
                    break

            if not externEmpty:
                self._nodes.update(self._nodesExtern)
            else:
                self._nodesExtern = []

        nodesToProcess, edgesToProcess = graph.dfsToProcess(startNodes=toNodes)
        flowEdges = graph.flowEdges(startNodes=toNodes)
        edgesToProcess = set(edgesToProcess).intersection(flowEdges)

        try:
            res = sub.submit(nodesToProcess, edgesToProcess, graph.filepath)
            if res:
                for node in nodesToProcess:
                    node.destroyed.connect(lambda obj=None, name=node.name: self.onNodeDestroyed(obj, name))
                    node.submit()  # update node status
            self._nodes.update(nodesToProcess)
            self._nodesExtern.extend(nodesToProcess)
        except Exception as e:
            logging.error("Error on submit : {}".format(e))

    nodes = Property(BaseObject, lambda self: self._nodes, constant=True)


def getAlreadySubmittedChunks(nodes):
    """
    Check if nodes already have been submitted
    :param nodes:
    :return:
    """
    out = []
    for node in nodes:
        for chunk in node.chunks:
            if chunk.isAlreadySubmitted():
                out.append(chunk)
    return out
