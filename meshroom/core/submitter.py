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
    _usedUids = set()

    def __init__(self, taskType, node = None, iteration : int = -1):
        self.taskType: OrderedTaskType = taskType
        self.node = node  # BaseNode
        self.iteration = iteration
        self.dependencies = []
        self.uid = self._generateUid()

    @property
    def nodeName(self):
        return self.node.name if self.node else "NONE"

    @classmethod
    def _generateUid(cls) -> int:
        nextUid = max(cls._usedUids) + 1 if len(cls._usedUids) > 0 else 0
        cls._usedUids.add(nextUid)
        return nextUid

    def addDependency(self, otherTask: OrderedTask):
        self.dependencies.append(otherTask)

    @property
    def shortName(self):
        sn = self.nodeName if self.node else "NONE"
        if self.taskType == OrderedTaskType.CHUNK:
            sn += f"_{self.iteration if self.iteration >=0 else 'allchunks'}"
        else:
            sn += f"_{self.taskType.name}"
        return f"{self.uid:03d} {sn}"

    def __repr__(self):
        if self.taskType == OrderedTaskType.PLACEHOLDER:
            string = f"<OrderedTask {self.uid:04d} type=placeholder"
            string += f" node={self.node._name}>" if self.node else ">"
            return string
        string = f"<OrderedTask {self.uid:04d}"
        string += f" type={self.taskType.name}"
        string += f" node={self.node._name} ({self.node._uid[:5]})"
        if self.iteration >= 0:
            string += f" iteration={self.iteration}"
        string += f" ({len(self.dependencies)} deps)>"
        return string


class OrderedNode:
    """ Intermediate structure used to order tasks """

    def __init__(self, node, dependencies=None):
        # node can be None for placeholder tasks (tasks that don't do anything else than regrouping dependencies)
        self.node = node  # BaseNode
        self.dependencies: list[OrderedNode] = dependencies or []  # Tasks that need to run before the current one
    
    @property
    def nodeName(self):
        return self.node.name if self.node else "NONE"

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
        depsNames = "|".join([t.nodeName for t in self.dependencies])
        if self.isPlaceholder:
            return f"<OrderedNode:placeholder deps=[{depsNames}]>"
        else:
            return f"<OrderedNode node={self.nodeName} deps=[{depsNames}]>"


class OrderedTasks:
    """ Build and provide access to tasks that are ordered

    Note: 
        We change a bit the logic from the meshroom graph because here the last node to be processed
        is the "root" and its dependencies are the "children". This is necessary because this is usually
        the order where the tasks will be created on the farm (we create one task, then add other tasks as
        dependencies, and not we create a task, then we add a task to execute next as we do it here).
    
    TODO: Keep the meshroom order and just provide an `inverse` method.
    """

    def __init__(self, nodes, edges, reduceConnections=True):
        # First correctly order the nodes
        self.nodesByLevels = []
        self._firstLevelorderedNodes: list[OrderedNode] = self.__orderNodes(nodes, edges)
        if reduceConnections:
            allNodes = set()
            for nodes in self.nodesByLevels:
                allNodes.update(nodes)
            for node in allNodes:
                self.applyTransitiveReduction(node)
        # Now create all the OrderedChunkTask objects
        self.rootTask = OrderedTask(taskType=OrderedTaskType.PLACEHOLDER)
        self._nodeUidToBoundaryTasks: Dict[str, OrderedTask] = {}  # { _uid: (firstTaskToProcess, lastTaskToProcess) }
        self.__orderTasks()

    def display(self):
        logging.debug(f"{'='*10} ORDERED TASKS {'='*10}")
        def gatherTasks(task):
            allTasks = [task]
            for child in task.dependencies:
                allTasks.extend(gatherTasks(child))
            return allTasks
        tasks: list[OrderedTask] = gatherTasks(self.rootTask)
        for task in set(tasks):
            logging.debug(f"[{task.shortName}] {task} -> depends on {[t.shortName for t in task.dependencies]}")

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
            parentNode = nodeToOrderedNode[u._uid]
            childNode = nodeToOrderedNode[v._uid]
            parentNode.dependencies.append(childNode)

        # Create a task 
        rootNode = OrderedNode(None, dependencies=nodeToOrderedNode.values())
        # Find each node depth (= what level the node is)
        depthByNode = {}
        def __updateDepth(nodes: List[OrderedNode], currentDepth=0):
            """ Compute the depth for each """
            for orderedNode in nodes:
                if currentDepth > depthByNode.get(orderedNode, -1):
                    depthByNode[orderedNode] = currentDepth
                if orderedNode.dependencies:
                    __updateDepth(orderedNode.dependencies, currentDepth+1)
        __updateDepth([rootNode], currentDepth=-1)
        # Regroup nodes by level
        levels = list(set(l for l in list(depthByNode.values())))
        self.nodesByLevels = [[n for n, l in depthByNode.items() if l == lev] for lev in levels]
        logger.debug("---- NODE ORDERING ----")
        for levelIndex, levelNodes in enumerate(self.nodesByLevels):
            logger.debug(f"[LEVEL {levelIndex:03d}] : {', '.join([n.nodeName for n in levelNodes])}")
        return self.nodesByLevels[0]

    def applyTransitiveReduction(self, node: OrderedNode):
        """ Remove redundant dependencies.
        If we have A -> (B, C) and B -> C then we don't need A -> C, we will instead get A -> B -> C
        """
        def _updateLongestPaths(currentNode: OrderedNode, longestPathToNodes: dict, currentDepth: int):
            for dep in currentNode.dependencies:
                if dep in longestPathToNodes:
                    longestPathToNodes[dep] = max(longestPathToNodes[dep], currentDepth)
                _updateLongestPaths(dep, longestPathToNodes, currentDepth + 1)

        longestPathToNodes = {n: 1 for n in node.dependencies}
        for nodeDependency in node.dependencies:
            # Try to find a longer path than the direct one (depth 1)
            _updateLongestPaths(nodeDependency, longestPathToNodes, currentDepth=2)
        newDependencies = [n for n in node.dependencies if longestPathToNodes[n] == 1]
        if set(newDependencies) != set(node.dependencies):
            logging.debug(f"(Reduced dependencies) {node.nodeName} before={[n.nodeName for n in node.dependencies]}, after={[n.nodeName for n in newDependencies]}")
        node.dependencies = newDependencies
        for childNode in node.dependencies:
            self.applyTransitiveReduction(childNode)            

    def __orderTasks(self):
        """ Use the nodesByLevel info to create all tasks to send to the submitter
        """
        # Start from a root task
        self._nodeUidToBoundaryTasks = {}
        for n in self._firstLevelorderedNodes:
            self.__addNodeTasks(n, self.rootTask)

    def __addNodeTasks(self, orderedNode: OrderedNode, parentTask: OrderedTask):
        """ Recursive function that takes a node on a graph where nodes are already ordered,
        - creates the internal tasks of this node
        - connect the last task to the parent
        - call itself on the dependencies with the current last task as the new parentTask

        Note:
            The parent task is the first task on the node that executes _after_ the current node.
            We need to connect it to the _last task_ that we will create on the current node.

        Args:
            orderedNode: current node that we want to create internal tasks.
            parentTask: task on the parent node to connect to the first internal task that 
                        will be created for the current orderedNode.
        """
        logger.debug(f"* (addNodeTasks) node {orderedNode.node._name}, parent {parentTask.node}")
        # Check if task has already been created
        visited = (nodeUid := orderedNode.node._uid) in self._nodeUidToBoundaryTasks
        if visited:
            logger.debug("  -> is visited")
            # If task is already created simply create the connection
            firstTask, lastTask = self._nodeUidToBoundaryTasks[nodeUid]
            parentTask.addDependency(lastTask)
            return

        # Create tasks
        if orderedNode.isPlaceholder:
            logger.debug("  -> is placeholder")
            task = OrderedTask(OrderedTaskType.PLACEHOLDER, orderedNode.node)
            firstTask, lastTask = task
        elif orderedNode.isExpanding:
            logger.debug("  -> is expanding")
            firstTask, lastTask = self.__createExpandingChunkTasks(orderedNode)
        else:
            iterations: list[int] = orderedNode.chunksIterations
            logger.debug(f"  -> has chunks : {iterations}")
            firstTask, lastTask = self.__createProcessChunkTasks(orderedNode, iterations)

        # Parent depends on the last task of this node
        parentTask.addDependency(lastTask)

        # Children (dependencies of this node) attach to firstTask
        for n in orderedNode.dependencies:
            logger.debug(f"  -> create deps {n}")
            self.__addNodeTasks(n, firstTask)

        # Register the last task so revisited nodes connect correctly
        self._nodeUidToBoundaryTasks[nodeUid] = (firstTask, lastTask)
        logger.debug(f"  -> done {orderedNode.node._name}")

    def __createExpandingChunkTasks(self, orderedNode: OrderedNode):
        """ Create internal tasks corresponding to a node.
        Build the task chain : firstTask -> expanding -> lastTask.

        Note:
            If we have preprocess or postprocess chunks then they will be used for first/last tasks
            If we don't have them but we have multiple chunks then we will create placeholder tasks
            for first/last tasks because we need an anchor point for parent and children nodes. 
        """ 
        # Create preprocess & postprocess tasks
        preprocessTask, postprocessTask = self.__createPrePostTasks(orderedNode)

        # Create expanding chunk task
        expandingTask = OrderedTask(OrderedTaskType.EXPANDING, orderedNode.node)

        # Chain: preprocess -> expanding -> postprocess
        if preprocessTask:
            expandingTask.addDependency(preprocessTask)
        if postprocessTask:
            postprocessTask.addDependency(expandingTask)

        firstTask = preprocessTask or expandingTask
        lastTask = postprocessTask or expandingTask
        return firstTask, lastTask
    
    def __createProcessChunkTasks(self, orderedNode: OrderedNode, iterations: list[int]):
        """ Create internal tasks corresponding to a node.
        Build the task chain : firstTask -> expanding -> lastTask.
        
        Note:
            If we have preprocess or postprocess chunks then they will be used for first/last tasks
            If we don't have them but we have multiple chunks then we will create placeholder tasks
            for first/last tasks because we need an anchor point for parent and children nodes. 
        """ 
        # Create preprocess & postprocess tasks
        preprocessTask, postprocessTask = self.__createPrePostTasks(orderedNode)

        if not iterations:
            if preprocessTask and postprocessTask:
                postprocessTask.addDependency(preprocessTask)
                firstTask = preprocessTask
                lastTask = postprocessTask
            elif preprocessTask:
                firstTask = lastTask = preprocessTask
            elif postprocessTask:
                firstTask = lastTask = postprocessTask
            else:
                # Nothing to do — create a single placeholder
                placeholder = OrderedTask(OrderedTaskType.PLACEHOLDER, orderedNode.node)
                firstTask = lastTask = placeholder
            return firstTask, lastTask

        chunkTasks = []
        for iteration in iterations:
            logger.debug(f"    - chunk {iteration}")
            chunkTask = OrderedTask(OrderedTaskType.CHUNK, orderedNode.node, iteration=iteration)
            chunkTasks.append(chunkTask)

        multipleChunks = len(chunkTasks) > 1

        # Get chunkStart/chunkEnd
        if multipleChunks:
            # Need placeholders only when parallelized (multiple chunks)
            # unless pre/post tasks already serve that purpose
            chunkStart = preprocessTask or OrderedTask(OrderedTaskType.PLACEHOLDER, orderedNode.node)
            chunkEnd = postprocessTask or OrderedTask(OrderedTaskType.PLACEHOLDER, orderedNode.node)
        else:
            # Single chunk: use pre/post directly, no placeholders needed
            chunkStart = preprocessTask  # may be None
            chunkEnd = postprocessTask    # may be None

        # Link chunks to chunkStart/chunkEnd
        for chunkTask in chunkTasks:
            if chunkEnd:
                chunkEnd.addDependency(chunkTask)
            if chunkStart:
                chunkTask.addDependency(chunkStart)

        if multipleChunks:
            firstTask = chunkStart
            lastTask = chunkEnd
        else:
            chunkTask = chunkTasks[0]
            firstTask = preprocessTask or chunkTask
            lastTask = postprocessTask or chunkTask

        return firstTask, lastTask

    def __createPrePostTasks(self, orderedNode: OrderedNode):
        preprocessTask = None
        postprocessTask = None
        if orderedNode.hasPreprocess:
            logger.debug("  -> preprocess")
            preprocessTask = OrderedTask(OrderedTaskType.PREPROCESS, orderedNode.node)
        if orderedNode.hasPostprocess:
            logger.debug("  -> postprocess")
            postprocessTask = OrderedTask(OrderedTaskType.POSTPROCESS, orderedNode.node)
        return preprocessTask, postprocessTask


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
