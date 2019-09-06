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
        self._state = State.RUNNING

        for n, node in enumerate(self._manager._nodesToProcess):
            if not node.isFinishedOrRunning():
                multiChunks = len(node.chunks) > 1
                for c, chunk in enumerate(node.chunks):
                    if multiChunks:
                        print('\n[{node}/{nbNodes}]({chunk}/{nbChunks}) {nodeName}'.format(
                            node=n + 1, nbNodes=len(self._manager._nodesToProcess),
                            chunk=c + 1, nbChunks=len(node.chunks), nodeName=node.nodeType))
                    else:
                        print('\n[{node}/{nbNodes}] {nodeName}'.format(
                            node=n + 1, nbNodes=len(self._manager._nodesToProcess), nodeName=node.nodeType))

                    if not chunk.isFinishedOrRunning() and self._state == State.RUNNING:
                        try:
                            chunk.process(self.forceCompute)

                        except Exception as e:
                            if chunk.isStopped():
                                self._state = State.STOPPED
                                self._manager._graph.clearSubmittedNodes()
                                self._manager._nodesToProcess = []

                            else:
                                logging.error("Error on node computation: {}".format(e))
                                nodesToDelete, _ = self._manager._graph.nodesFromNode(node)

                                for nodeD in nodesToDelete:
                                    if nodeD != node:
                                        try:
                                            self._manager._nodesToProcess.remove(nodeD)
                                        except:
                                            # Node already removed (for instance a global clear of _nodesToProcess)
                                            pass
                                    nodeD.clearSubmittedChunks()

        self._manager._nodesToProcess = []
        self._state = State.DEAD
        self._manager._uigraph.computeStatusChanged.emit()


class TaskManager(BaseObject):
    """
    Manage the nodes that have to be computed locally or on a renderfarm
    """
    def __init__(self, parent=None):
        super(TaskManager, self).__init__(parent)
        self._nodes = DictModel(keyAttrName='_name', parent=self)
        self._nodesToProcess = []
        self._nodesExtern = []
        self._graph = None
        self._thread = TaskThread(self)

    def compute(self, graph=None, toNodes=None, uigraph=None, forceCompute=False, forceStatus=False):
        """
        Nodes are to be computed locally are sent to a thread
        :param graph:
        :param toNodes:
        :param uigraph:
        :param forceCompute:
        :param forceStatus:
        :return:
        """
        self._graph = graph
        self._uigraph = uigraph

        if self._thread._state in (State.IDLE, State.DEAD, State.ERROR, State.STOPPED):
            try:
                self._nodes.clear()
            except:
                print("Task Manager nodes already empty")

            externEmpty = True
            for node in self._nodesExtern:
                if node.isAlreadySubmitted():
                    externEmpty = False
                    break

            if not externEmpty:
                self._nodes.update(self._nodesExtern)
            else:
                self._nodesExtern = []

        if forceCompute:
            nodes, edges = graph.dfsOnFinish(startNodes=toNodes)
        else:
            allNodes, edges = graph.dfsToProcess(startNodes=toNodes)
            nodes = []
            for node in allNodes:
                if not node.isAlreadySubmittedOrFinished():
                    nodes.append(node)

        logging.info('Nodes to execute: ', str([n.name for n in nodes]))

        for node in nodes:
            node.destroyed.connect(lambda obj=None, name=node.name: self.onNodeDestroyed(obj, name))
            node.beginSequence(forceCompute)

        self._nodes.update(nodes)
        self._nodesToProcess .extend(nodes)

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
        self._nodes.pop(name)

    def clear(self):
        """
        Remove all the nodes from the taskmanager
        :return:
        """
        self._nodes.clear()
        self._nodesExtern = []
        self._nodesToProcess = []



    def submit(self, graph=None, submitter=None, toNodes=None):
        """
        Nodes are send to the renderfarm
        :param graph:
        :param submitter:
        :param toNodes:
        :return:
        """
        if self._thread._state in (State.IDLE, State.DEAD, State.ERROR, State.STOPPED):
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

        sub = meshroom.core.submitters.get(submitter, None)
        if sub is None:
            raise RuntimeError("Unknown Submitter : " + submitter)

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





