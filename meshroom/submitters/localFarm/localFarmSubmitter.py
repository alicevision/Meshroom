#!/usr/bin/env python

import os
import sys
import re
import shutil
import logging
from typing import Optional
from meshroom.core.submitter import BaseSubmitter, SubmitterOptions, BaseSubmittedJob, SubmitterOptionsEnum
from meshroom.core.node import Status
from collections import namedtuple, defaultdict
from localFarm import Task, Job, LocalFarmEngine


logger = logging.getLogger("LocalFarmSubmitter")
logger.setLevel(logging.INFO)

farm_path = os.getenv("MR_LOCAL_FARM_PATH", os.path.join(os.path.expanduser("~"), ".local_farm"))


Chunk = namedtuple("chunk", ["iteration", "start", "end"])

REZ_DELIMITER_PATTERN = re.compile(r"(-|==|>=|>|<=|<)")

def getResolvedVersionsDict():
    """ Get a dict {packageName: version} corresponding to the current context """
    resolvedPackages = os.environ.get('REZ_RESOLVE', '').split()
    resolvedVersions = {}
    for r in resolvedPackages:
        if r.startswith('~'):  # remove implicit packages
            continue
        v = r.split('-')
        if len(v) == 2:
            resolvedVersions[v[0]] = v[1]
        elif len(v) > 2:  # Handle case with multiple hyphen-minus
            resolvedVersions[v[0]] = "-".join(v[1:])
    return resolvedVersions


def getRequestPackages(packagesDelimiter="=="):
    """ 
    Get list of packages required for the job
    Depends on env var and current rez context

    By default we use the "==" delimiter to make sure we have the same version
    in the job that the one we have in the env where meshroom is launched
    """
    reqPackages = set()
    if 'REZ_REQUEST' in os.environ:
        # Get the names of the packages that have been requested
        requestedPackages = os.environ.get('REZ_USED_REQUEST', '').split()
        usedPackages = set()  # Use set to remove duplicates
        for p in requestedPackages:
            if p.startswith('~') or p.startswith("!"):
                continue
            v = REZ_DELIMITER_PATTERN.split(p)
            usedPackages.add(v[0])
        # Add requested packages to the reqPackages set 
        resolvedVersions = getResolvedVersionsDict()
        for p in usedPackages:
            reqPackages.add(packagesDelimiter.join([p, resolvedVersions[p]]))
        logging.debug(f"TractorSubmitter: REZ Packages: {str(reqPackages)}")
    elif 'REZ_MESHROOM_VERSION' in os.environ:
        reqPackages.add(f"meshroom{packagesDelimiter}{os.environ.get('REZ_MESHROOM_VERSION', '')}")
    return list(reqPackages)


def rezWrapCommand(cmd, useCurrentContext=False, useRequestedContext=True, otherRezPkg: list[str] = None):
    """ Wrap command to be runned using rez
    :param cmd: command to run
    :type cmd: bool
    :param useCurrentContext: use current rez context to retrieve a list of rez packages
    :type useCurrentContext: bool
    :param useRequestedContext: use rez packages that have been requested (not the full context)  # TODO : remove it
    :type useRequestedContext: bool
    :param otherRezPkg: Additionnal rez packages
    :type otherRezPkg: list[str]
    """
    packages = set()
    if useCurrentContext:
        # In this case we want to use the full context
        packages.update([p for p in os.environ.get('REZ_RESOLVE', '').split(" ") if p])
    elif useRequestedContext:
        # In this case we want to use only packages in the rez request
        packages.update(getRequestPackages())
    # Add additional packages
    if otherRezPkg:
        packages.update(otherRezPkg)
    packagesStr = " ".join([p for p in packages if p])
    if packagesStr:
        rezBin = "rez"
        if "REZ_BIN" in os.environ and os.environ["REZ_BIN"]:
            rezBin = os.environ["REZ_BIN"]
        elif "REZ_PACKAGES_ROOT" in os.environ and os.environ["REZ_PACKAGES_ROOT"]:
            rezBin = os.path.join(os.environ["REZ_PACKAGES_ROOT"], "bin/rez")
        elif shutil.which("rez"):
            rezBin = shutil.which("rez")
        return f"{rezBin} env {packagesStr} -- {cmd}"
    return cmd


class LocalFarmJob(BaseSubmittedJob):
    """Interface to manipulate the job via Meshroom"""

    def __init__(self, jid, submitter):
        super().__init__(jid, submitter)
        self.jid = jid
        self.submitter: LocalFarmSubmitter = submitter
        self.__localJob = None
        self.__localJobTasks = None
        self.__farm = LocalFarmEngine(farm_path)

    def __getTractorInfos(self):
        """ Find job """
        self.__localJob = self.__farm.get_job_infos(self.jid)
        self.__localJobTasks = {t.get("tid"): t for t in self.__localJob["tasks"]}

    @property
    def tractorJob(self):
        if not self.__localJob:
            self.__getTractorInfos()
        return self.__localJob

    @property
    def tractorJobTasks(self):
        if not self.__localJobTasks:
            self.__getTractorInfos()
        return self.__localJobTasks

    def __getChunkTasks(self, nodeUid, iteration):
        tasks = []
        for _, task in self.tractorJobTasks.items():
            taskNodeUid = task["metadata"].get("nodeUid", None)
            taskIt = task["metadata"].get("iteration", -1)
            if taskNodeUid == nodeUid and taskIt == iteration:
                tasks.append(task)
        return tasks

    # Task actions

    def stopChunkTask(self, node, iteration):
        """ This will kill one task """
        tasks = self.__getChunkTasks(node._uid, iteration)
        for task in tasks:
            self.__farm.stop_task(self.jid, task["tid"])

    def skipChunkTask(self, node, iteration):
        """ This will kill one task """
        tasks = self.__getChunkTasks(node._uid, iteration)
        for task in tasks:
            self.__farm.skip_task(self.jid, task["tid"])

    def restartChunkTask(self, node, iteration):
        """ This will kill one task """
        tasks = self.__getChunkTasks(node._uid, iteration)
        for task in tasks:
            self.__farm.restart_task(self.jid, task["tid"])

    # Job actions

    def pauseJob(self):
        """ This will pause the job : new tasks will not be processed """
        self.__farm.pause_job(self.jid)

    def resumeJob(self):
        """ This will unpause the job """
        self.__farm.unpause_job(self.jid)

    def interruptJob(self):
        """ This will interrupt the job (and kill running tasks) """
        self.__farm.interrupt_job(self.jid)

    def restartJob(self):
        """ Restarts the whole job """
        self.__farm.restart_job(self.jid)
    
    def restartErrorTasks(self):
        """ Restart all error tasks on the job """
        self.__farm.restart_error_tasks(self.jid)


class LocalFarmSubmitter(BaseSubmitter):
    """
    Meshroom submitter to tractor
    """
    
    _name = "LocalFarm"
    _options = SubmitterOptions(SubmitterOptionsEnum.ALL)
    
    dryRun = False
    environment = {}

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.reqPackages = getRequestPackages()

    def retrieveJob(self, jid) -> LocalFarmJob:
        job = LocalFarmJob(jid, self)
        return job
    
    @staticmethod
    def getChunks(chunkParams) -> list[Chunk]:
        """ Get list of chunks """
        it = None
        ignoreIterations = chunkParams.get("ignoreIterations", [])
        if chunkParams:
            start, end = chunkParams.get("start", -1), chunkParams.get("end", -2)
            size = chunkParams.get("packetSize", 1)
            frameRange = list(range(start, end+1, 1))
            if frameRange:
                slices = [frameRange[i:i + size] for i in range(0, len(frameRange), size)]
                it = [Chunk(i, item[0], item[-1]) for i, item in enumerate(slices) if i not in ignoreIterations]
        return it
    
    @staticmethod
    def getExpandWrappedCmd(cmdArgs, rezPackages):
        # Wrap with create_chunks
        cmd = f"meshroom_createChunks --submitter LocalFarm {cmdArgs}"
        # Wrap with rez
        cmd = rezWrapCommand(cmd, otherRezPkg=rezPackages)
        # Wrap with tractor wrapper (will redirect stdout to stderr)
        # to make sure stdout only has the 
        wrapperModule = "tractorSubtaskWrapper.py"
        wrapperPath = os.path.join(os.environ["MR_SUBMITTERS_SCRITPS"], wrapperModule)
        cmd = f"{sys.executable} {wrapperPath} {cmd}"
        return cmd
    
    def __createTask(self, name: str, command: str, metadata: dict, dependencies: dict) -> Task:
        task = Task(name=name, command=command, metadata=metadata)
        return task
    
    def __createTaskWithChunks(self, name: str, commandArgs: str, chunkParams: dict, metadata: dict, dependencies: dict) -> Task:
        # Create chunks
        chunks = self.getChunks(chunkParams)
        task = self.__createTask(name=name, command=cmd, metadata=metadata)
        # Add chunks info to the task metadata
        chunkList = []
        for c in chunks:
            meta = metadata.copy()
            cmd = f"meshroom_compute {commandArgs}"
            cmd = rezWrapCommand(cmd, otherRezPkg=self.rezPackages)
            chunkList.append({
                "iteration": c.iteration,
                "start": c.start,
                "end": c.end
            })
        task.metadata["chunks"] = chunkList
        return task
    
    def createTask(self, meshroomFile: str, node) -> Task:
        expandingTask = False
        chunkParams = {}
        if not node._chunksCreated:
            expandingTask = True
        elif node.isParallelized:
            blockSize, fullSize, nbBlocks = node.nodeDesc.parallelization.getSizes(node)
            iterationsToIgnore = []
            for c in node._chunks:
                if c._status.status == Status.SUCCESS:
                    iterationsToIgnore.append(c.range.iteration)
            if nbBlocks > 0:
                chunkParams = {
                    "start": 0, "end": nbBlocks - 1, "step": 1, "ignoreIterations": iterationsToIgnore
                }
        else:
            chunkParams = {"start": 0, "end": 0, "step": 1}
        cmdArgs = f"--node {node.name} \"{meshroomFile}\" --extern"
        metadata = {"nodeUid": node._uid}
        if expandingTask:
            cmd = self.getExpandWrappedCmd(cmdArgs, self.reqPackages)
            task = self.__createTask(name=node.name, command=cmd, metadata=metadata, dependsOn=dependsOn)
            task = Task(name=name, command=command, metadata=metadata)
        elif self.chunks:
            task = self.__createTaskWithChunks(name=node.name, commandArgs=cmdArgs, chunkParams=chunkParams, metadata=metadata, dependsOn=dependsOn)
        else:
            # Simple task with only one command to execute
            cmd = f"meshroom_compute {self.taskCommandArgs}"
            cmd = rezWrapCommand(cmd, otherRezPkg=self.rezPackages)
            task = self.__createTask(name=node.name, command=cmd, metadata=metadata, dependsOn=dependsOn)
        return task

    def createJob(self, nodes, edges, filepath, submitLabel="{projectName}"):
        projectName = os.path.splitext(os.path.basename(filepath))[0]
        name = submitLabel.format(projectName=projectName)
        # Create job
        job = Job(name)
        # Get task deps
        deps = defaultdict(set)
        for parentNode, childNode in edges:
            deps[childNode._uid].add(parentNode._uid)
        # Create tasks
        nodeUidToTask: dict[str, Task] = {}
        for node in nodes:
            if node._uid in nodeUidToTask:
                continue  # HACK: Should not be necessary
            taskDeps = deps[node._uid]
            task = self.createTask(filepath, node)
            job.addTask(task)
            nodeUidToTask[node._uid] = task
        for u, v in edges:
            nodeUidToTask[u._uid].addChild(nodeUidToTask[v._uid])
        # Submit job
        res = job.submit(share=self.share, dryRun=self.dryRun)
        if self.dryRun:
            return True
        if len(res) == 0:
            return False
        submittedJob = LocalFarmJob(res.get("id"), LocalFarmSubmitter)
        return submittedJob

    def createChunkTask(self, node, graphFile, **kwargs):
        """
        Keyword args : cache, forceStatus, forceCompute
        """
        taskTags = self.DEFAULT_TAGS.copy()
        taskTags['nbFrames'] = node.size
        taskTags['prod'] = self.prod
        # Environment
        environment = self.environment.copy()
        environment['FARM_USER'] = os.environ.get('FARM_USER', os.environ.get('USER', getpass.getuser()))
        # Command
        cmdArgs = f"--node {node.name} \"{graphFile}\" --extern"
        # Add task to the queue
        queueChunkTask(
            node=node,
            cmdArgs=cmdArgs,
            service=self.getTaskService(node),
            tags=taskTags,
            rezPackages=self.reqPackages,
            environment=environment
        )
