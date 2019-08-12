import logging
from threading import Thread
from enum import Enum

from meshroom.common import BaseObject, DictModel, Property

class State(Enum):
    IDLE = 0
    RUNNING = 1
    STOPPED = 2
    DEAD = 3
    ERROR = 4

class TaskThread(Thread):
    def __init__(self, manager):
        Thread.__init__(self, target=self.run)
        self._state = State.IDLE
        self._manager = manager
        self.forceCompute = False

    def run(self):
        self._state = State.RUNNING

        for n, node in enumerate(self._manager._nodesToProcess):
            if not node.isFinishedOrRunning():
                #try:
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
                                    self._manager._nodesToProcess.clear()

                                else:
                                    logging.error("Error on node computation: {}".format(e))
                                    nodesToDelete, _ = self._manager._graph.nodesFromNode(node)

                                    for nodeD in nodesToDelete:
                                        if nodeD != node:
                                            self._manager._nodesToProcess.remove(nodeD)
                                        nodeD.clearSubmittedChunks()

        self._state = State.DEAD

        self._manager._nodesToProcess.clear()


class TaskManager(BaseObject):
    def __init__(self, parent=None):
        super(TaskManager, self).__init__(parent)
        self._nodes = DictModel(keyAttrName='name', parent=self)
        self._nodesToProcess = DictModel(keyAttrName='name', parent=self)
        self._graph = None
        self._thread = TaskThread(self)

    def addNodes(self, graph=None, toNodes=None, forceCompute=False, forceStatus=False):
        self._graph = graph

        logging.info(self._thread._state)

        if self._thread._state in (State.IDLE, State.DEAD, State.ERROR, State.STOPPED):
            self._nodes.clear()

        if forceCompute:
            nodes, edges = graph.dfsOnFinish(startNodes=toNodes)
        else:
            allNodes, edges = graph.dfsToProcess(startNodes=toNodes)
            nodes = []
            for node in allNodes:
                if not node.isAlreadySubmittedOrFinished():
                    nodes.append(node)

        print('Nodes to execute: ', str([n.name for n in nodes]))

        for node in nodes:
            node.beginSequence(forceCompute)

        self._nodes.update(nodes)
        self._nodesToProcess.update(nodes)

        if self._thread._state == State.IDLE:
            self._thread.start()
        elif self._thread._state in (State.DEAD, State.ERROR):
            self._thread = TaskThread(self)
            self._thread.start()

    nodes = Property(BaseObject, lambda self: self._nodes, constant=True)

def getAlreadySubmittedChunks(nodes):
    out = []
    for node in nodes:
        for chunk in node.chunks:
            if chunk.isAlreadySubmitted():
                out.append(chunk)
    return out





