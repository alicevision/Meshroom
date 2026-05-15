#!/usr/bin/env python

from __future__ import annotations

import sys
import logging
import operator

from enum import IntFlag, auto
from typing import Optional, Dict, List
from itertools import accumulate

import meshroom
from meshroom.common import BaseObject, Property


logger = logging.getLogger("Submitter")
logger.setLevel(logging.INFO)


class SubmitterOptionsEnum(IntFlag):
    RETRIEVE = auto()       # Can retrieve job (read job tasks, ...)
    INTERRUPT_JOB = auto()  # Can interrupt
    RESUME_JOB = auto()     # Can resume after interruption
    EDIT_TASKS = auto()     # Can edit tasks
    ATTACH_JOB = auto()     # Can attach a job that will execute after another job

    @classmethod
    def get(cls, option):
        if isinstance(option, str):
            # Try to cast to SubmitterOptionsEnum
            option = getattr(cls, option.upper(), None)
        elif isinstance(option, int):
            option = cls(option)
        if isinstance(option, cls):
            return option
        return 0

# SubmitterOptionsEnum.ALL = SubmitterOptionsEnum(SubmitterOptionsEnum._all_bits_)  # _all_bits_ -> py 3.11
SubmitterOptionsEnum.ALL = list(accumulate(SubmitterOptionsEnum, operator.__ior__))[-1]


class SubmitterOptions:
    def __init__(self, *args):
        self._options = 0
        for option in args:
            self.addOption(option)

    def addOption(self, option):
        option = SubmitterOptionsEnum.get(option)
        self._options |= option

    def includes(self, option):
        option = SubmitterOptionsEnum.get(option)
        return self._options & option > 0

    def __iter__(self):
        for o in SubmitterOptionsEnum:
            if self.includes(o):
                yield(o)

    def __repr__(self):
        if self._options == 0:
            return f"<SubmitterOptions NONE>"
        if self._options == SubmitterOptionsEnum.ALL:
            return f"<SubmitterOptions ALL>"
        return f"<SubmitterOptions {'|'.join([o.name for o in self])}>"


class OrderedTaskType(IntFlag):
    PLACEHOLDER = 0
    """No command: just here to have dependencies"""
    PREPROCESS = 1
    """Task that executes a node preprocess method"""
    EXPANDING = 2
    """Task that will spawn tasks on execution"""
    CHUNK = 3
    """Task that will expand during the processing"""
    POSTPROCESS = 4
    """Task that executes a node postprocess method"""


class OrderedTask:
    def __init__(self, taskType, node = None, iteration : int = -1):
        self.taskType: OrderedTaskType = taskType
        self.node = node  # BaseNode
        self.iteration = iteration
        self.dependencies = []
    
    def addDependency(self, otherTask: OrderedTask):
        self.dependencies.append(otherTask)
    
    def __repr__(self):
        if self.taskType == OrderedTaskType.PLACEHOLDER:
            string = f"<OrderedTask placeholder {id(self)}"
            if self.node:
                string += f" node={self.node._name}"
            return string + f">"
        string = f"<OrderedTask {self.node._uid[:5]} {self.node.name} {self.taskType.name} ("
        if self.iteration >= 0:
            string += f"iteration={self.iteration}, "
        string += f"{len(self.dependencies)} deps)>"
        return string


class OrderedNode:
    """ Intermediate structure used to order tasks """

    def __init__(self, node, dependencies=None):
        # node can be None for placeholder tasks (tasks that don't do anything else than regrouping dependencies)
        self.node = node  # BaseNode
        self.dependencies: list[OrderedNode] = dependencies or []  # Tasks that need to run before the current one

    @property
    def isPlaceholder(self) -> bool:
        """ If the node is None then it's just a void item to be used as a task placeholder """
        return self.node is None

    @property
    def isExpanding(self) -> bool:
        """ Expanding nodes are nodes whose number of chunks has not been determined yet. 
        It will be resolved when the node processing starts. Therefore a first process is launched that 
        will create chunks and then chunk tasks are created later (from the submitted process).
        """
        return not self.node._chunksCreated

    @property
    def chunksIterations(self) -> list[int]:
        """ Get all iterations to process.
        Used in the case where the node is parallelized and when we know how many chunks are executed.
        It should not be called if `self.isExpanding` therefore we return None
        """
        if self.isExpanding:
            return None
        if self.node.isParallelized:
            _, _, nbBlocks = self.node.nodeDesc.parallelization.getSizes(self.node)
            iterationsToIgnore = []
            for c in self.node._chunks:
                if c._status.checkStatus("SUCCESS"):
                    iterationsToIgnore.append(c.range.iteration)
            if nbBlocks > 0:
                return [k for k in range(nbBlocks) if k not in iterationsToIgnore]
        return [-1]

    @property
    def hasPreprocess(self) -> bool:
        return self.node.nodeDesc.hasPreprocess

    @property
    def hasPostprocess(self) -> bool:
        return self.node.nodeDesc.hasPostprocess
    
    def __repr__(self):
        depsNames = "|".join([t.node.name for t in self.dependencies])
        if self.isPlaceholder:
            return f"<OrderedNode:placeholder deps=[{depsNames}]>"
        else:
            return f"<OrderedNode node={self.node.name} deps=[{depsNames}]>"


class OrderedTasks:
    """ Build and provide access to tasks that are ordered

    Note: 
        We change a bit the logic from the meshroom graph because here the last node to be processed
        is the "root" and its dependencies are the "children". This is necessary because this is usually
        the order where the tasks will be created on the farm (we create one task, then add other tasks as
        dependencies, and not we create a task, then we add a task to execute next as we do it here).
    
    TODO: Keep the meshroom order and just provide an `inverse` method.
    """

    def __init__(self, nodes, edges):
        # First correctly order the nodes
        self._firstLevelorderedNodes: list[list[OrderedNode]] = self.__orderNodes(nodes, edges)
        # Now create all the OrderedChunkTask objects
        self.rootTask = OrderedTask(taskType=OrderedTaskType.PLACEHOLDER)
        self._nodeUidToLastTask: Dict[str, OrderedTask] = {}  # { _uid: lastTaskToProcess }
        self.__orderTasks()

    def display(self, task:OrderedTask=None, level=0):
        if task is None:
            task = self.rootTask
        logger.debug(f"{' '*4*level}[{level:02d}] {task}")
        for child in task.dependencies:
            self.display(child, level+1)

    def iterOnTasks(self, current:OrderedTask=None, skipRootTask=False):
        skipCurrent = (current is None) and skipRootTask
        if current is None:
            current = self.rootTask
        if not skipCurrent:
            yield current
        for task in current.dependencies:
            yield from self.iterOnTasks(task)

    def __iter__(self):
        yield from self.iterOnTasks()

    def __orderNodes(self, nodes, edges):
        """
        Take all the nodes and connections and order them by processing step
        0 is the root nodes (can be executed last)
        Then 1 is the level with the direct dependencies for the root nodes, and etc...
        
        At the end return only the 1st level nodes
        """
        # uid -> orderedNode
        nodeToOrderedNode = {n._uid: OrderedNode(n) for n in nodes}
        # Build dependency relationships from edges
        for u, v in edges:
            # Change a bit the ordering logic of Meshroom :
            # parent task is the last one to be executed, child are their dependencies
            parentTask = nodeToOrderedNode[u._uid]
            childTask = nodeToOrderedNode[v._uid]
            parentTask.dependencies.append(childTask)

        # Create a task 
        rootNode = OrderedNode(None, dependencies=nodeToOrderedNode.values())
        # Find each node depth (= what level the node is)
        depthByNode = {}
        self.__updateDepth([rootNode], depthByNode, currentDepth=-1)
        # Regroup nodes by level
        levels = list(set(l for l in list(depthByNode.values())))
        nodesByLevels = [[t for t, l in depthByNode.items() if l == lev] for lev in levels]
        return nodesByLevels[0]

    def __updateDepth(self, nodes: List[OrderedNode], depthByNode, currentDepth=0):
        """ Compute the depth for each """
        for orderedNode in nodes:
            if currentDepth > depthByNode.get(orderedNode, -1):
                depthByNode[orderedNode] = currentDepth
            if orderedNode.dependencies:
                self.__updateDepth(orderedNode.dependencies, depthByNode, currentDepth+1)

    def __orderTasks(self):
        """ Use the nodesByLevel info to create all tasks to send to the submitter """
        # Start from a root task
        self._nodeUidToLastTask = {}
        for n in self._firstLevelorderedNodes:
            self.__createNodeTasks(n, self.rootTask)

    def __createNodeTasks(self, orderedNode: OrderedNode, parentTask: OrderedTask):
        """ Create tasks corresponding to a node and link them correctly.
        Also link them to the parent task, and recursively create children tasks.
        """
        logger.debug(f"* (createNodeTasks) node {orderedNode.node._name}, parent {parentTask.node}")
        # Check if task has already been created
        visited = (nodeUid:=orderedNode.node._uid) in self._nodeUidToLastTask
        if visited:
            logger.debug("  -> is visited")
            # If task is already created simply create the connection
            lastTask = self._nodeUidToLastTask[nodeUid]
            parentTask.addDependency(lastTask)
            return
        # Create node tasks
        if orderedNode.isPlaceholder:
            logger.debug("  -> is placeholder")
            task = OrderedTask(OrderedTaskType.PLACEHOLDER, orderedNode.node)
            firstTask = lastTask = task
        else:
            lastTask = firstTask = None
            # Create pre/post tasks if needed
            if orderedNode.hasPostprocess:
                logger.debug("  -> postprocess")
                lastTask = OrderedTask(OrderedTaskType.POSTPROCESS, orderedNode.node)
            if orderedNode.hasPreprocess:
                logger.debug("  -> preprocess")
                firstTask = OrderedTask(OrderedTaskType.PREPROCESS, orderedNode.node)
            # Process
            if orderedNode.isExpanding:
                logger.debug("  -> is expanding")
                expandingTask = OrderedTask(OrderedTaskType.EXPANDING, orderedNode.node)
                if lastTask:
                    lastTask.addDependency(expandingTask)
                else:
                    lastTask = expandingTask
                if firstTask:
                    expandingTask.addDependency(firstTask)
                else:
                    firstTask = expandingTask
            else:
                logger.debug(f"  -> has chunks : {orderedNode.chunksIterations}")
                # Create and link chunks
                if len(orderedNode.chunksIterations):
                    # Create placeholders for pre/post
                    lastTask = lastTask if lastTask else OrderedTask(OrderedTaskType.PLACEHOLDER, orderedNode.node)
                    firstTask = firstTask if firstTask else OrderedTask(OrderedTaskType.PLACEHOLDER, orderedNode.node)
                    for iteration in orderedNode.chunksIterations:
                        logger.debug(f"    - chunk {iteration}")
                        chunkTask = OrderedTask(OrderedTaskType.CHUNK, orderedNode.node, iteration=iteration)
                        lastTask.addDependency(chunkTask)
                        chunkTask.addDependency(firstTask)
                else:  # Handle 0 chunks case
                    if firstTask and lastTask:
                        lastTask.addDependency(firstTask)
                    elif firstTask:
                        lastTask = firstTask
                    elif lastTask:
                        firstTask = lastTask
                    else:
                        firstTask = lastTask = OrderedTask(OrderedTaskType.PLACEHOLDER, orderedNode.node)
        # Add parent dependency
        parentTask.addDependency(lastTask)
        # Create children
        for n in orderedNode.dependencies:
            logger.debug(f"  -> create deps {n}")
            self.__createNodeTasks(n, firstTask)
        # Add the last task to execute for this node to _nodeUidToLastTask
        self._nodeUidToLastTask[nodeUid] = lastTask
        logger.debug(f"  -> done {orderedNode.node._name}")


class BaseSubmittedJob:
    """
    Interface to manipulate the job via Meshroom
    """

    def __init__(self, jobId, submitter):
        self.jid = jobId
        self.submitterName: str = submitter._name
        self.submitterOptions: SubmitterOptions = submitter._options

    def __repr__(self):
        return f"<{self.__class__.__name__} {self.jid}>"

    # Task actions
    # For all methods if If iteration is -1 then it kills all the tasks for the given node

    def stopChunkTask(self, node, iteration):
        """ This will kill one task.
        If iteration is -1 then it kills all the tasks for the given node
        """
        if self.submitterOptions.includes(SubmitterOptionsEnum.INTERRUPT_JOB):
            raise NotImplementedError(f"'stopChunkTask' method must be implemented in subclasses")
        else:
            raise RuntimeError(f"Submitter {self.__class__.__name__} cannot interrupt the job")

    def skipChunkTask(self, node, iteration):
        """ This will kill one task """
        if self.submitterOptions.includes(SubmitterOptionsEnum.INTERRUPT_JOB):
            raise NotImplementedError("'skipChunkTask' method must be implemented in subclasses")
        else:
            raise RuntimeError(f"Submitter {self.__class__.__name__} cannot interrupt the job")

    def restartChunkTask(self, node, iteration):
        """ This will kill one task """
        if self.submitterOptions.includes(SubmitterOptionsEnum.RESUME_JOB):
            raise NotImplementedError("'restartChunkTask' method must be implemented in subclasses")
        else:
            raise RuntimeError(f"Submitter {self.__class__.__name__} cannot interrupt the job")

    # Job actions

    def pauseJob(self):
        """ This will pause the job : new tasks will not be processed """
        if self.submitterOptions.includes(SubmitterOptionsEnum.INTERRUPT_JOB):
            raise NotImplementedError("'pauseJob' method must be implemented in subclasses")
        else:
            raise RuntimeError(f"Submitter {self.__class__.__name__} cannot interrupt the job")

    def resumeJob(self):
        """ This will unpause the job """
        if self.submitterOptions.includes(SubmitterOptionsEnum.RESUME_JOB):
            raise NotImplementedError("'resumeJob' method must be implemented in subclasses")
        else:
            raise RuntimeError(f"Submitter {self.__class__.__name__} cannot interrupt the job")

    def interruptJob(self):
        """ This will interrupt the job (and kill running tasks) """
        if self.submitterOptions.includes(SubmitterOptionsEnum.INTERRUPT_JOB):
            raise NotImplementedError("'interruptJob' method must be implemented in subclasses")
        else:
            raise RuntimeError(f"Submitter {self.__class__.__name__} cannot interrupt the job")

    def restartErrorTasks(self):
        if self.submitterOptions.includes(SubmitterOptionsEnum.RESUME_JOB):
            raise NotImplementedError("'restartErrorTasks' method must be implemented in subclasses")
        else:
            raise RuntimeError(f"Submitter {self.__class__.__name__} cannot restart the job")


class JobManager(BaseObject):
    """ Central manager for all jobs """

    def __init__(self):
        super().__init__()
        self._jobs = {}  # jobId -> BaseSubmittedJob
        self._nodeToJob = {}  # node uid -> Job

    def addJob(self, job: BaseSubmittedJob, nodes):
        jid = job.jid
        if jid not in self._jobs:
            self._jobs[jid] = job
        for node in nodes:
            nodeUid = node._uid
            self._nodeToJob[nodeUid] = jid
            # Update the node status file to store the job ID
            node.setJobId(jid, job.submitterName)

    def resetNodeJob(self, node):
        node._nodeStatus.jobInfo = {}
        if node._uid in self._nodeToJob:
            del self._nodeToJob[node._uid]

    def getJob(self, jobId: str) -> Optional[BaseSubmittedJob]:
        return self._jobs.get(jobId)

    def removeJob(self, jobId: str):
        with self._lock:
            if jobId in self._jobs:
                del self._jobs[jobId]

    def getNodeJob(self, node):
        nodeUid = node._uid
        jobId = self._nodeToJob.get(nodeUid)
        if jobId:
            return self.getJob(jobId)
        return None

    def getAllNodesUIDForJob(self, job):
        return [n for n, j in self._nodeToJob.items() if j == job.jid]

    def retreiveJob(self, submitter, jid) -> Optional[BaseSubmittedJob]:
        if not submitter._options.includes(SubmitterOptionsEnum.RETRIEVE):
            return None
        job = submitter.retrieveJob(jid)
        return job


# Global instance that manages submitted jobs
jobManager = JobManager()


class BaseSubmitter(BaseObject):
    _options: SubmitterOptions = SubmitterOptions()
    _name = ""

    def __init__(self, parent=None):
        if not self._name:
            raise ValueError("Could not register submitter without name")
        super().__init__(parent)
        logger.info(f"Registered submitter {self._name} (options={self._options})")

    @property
    def name(self):
        return self._name

    def createJob(self, orderedTasks: OrderedTasks, filepath: str, submitLabel: str = "{projectName}"):
        """ Submit the given graph
         Returns:
             bool: whether the submission succeeded
        """
        raise NotImplementedError("'createJob' method must be implemented in subclasses")

    def createChunkTask(self, node, graphFile, **kwargs):
        if self._options.includes(SubmitterOptionsEnum.RESUME_JOB):
            raise NotImplementedError("'createChunkTask' method must be implemented in subclasses")
        else:
            raise RuntimeError(f"Submitter {self.name} cannot edit the job")

    def retrieveJob(self, jobId) -> BaseSubmittedJob:
        raise NotImplementedError("'retrieveJob' method must be implemented in subclasses")

    def submit(self, nodes, edges, filepath, submitLabel="{projectName}") -> BaseSubmittedJob:
        """ Submit the given graph
         Returns:
             bool: whether the submission succeeded
        """
        orderedTasks = OrderedTasks(nodes, edges)
        job = self.createJob(orderedTasks, filepath, submitLabel)
        if not job:
            # Failed to create the job
            return None
        return job

    @staticmethod
    def killRunningJob():
        """ Sometimes farms are automatically re-trying job once in case it was
        killed by a user who does not want their machine to be used. Unfortunately this
        means jobs will be launched twice even if they failed for a good reason.
        This function can be used to make sure the current job will not restart
        Note : the ERROR_NO_RETRY itself will not do anything. This function must be
        implemented on a case-by-case for each possible farm system
        """
        sys.exit(meshroom.MeshroomExitStatus.ERROR_NO_RETRY)

    name = Property(str, lambda self: self._name, constant=True)
