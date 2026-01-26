#!/usr/bin/env python

import os
import re
import shutil
import logging
from pathlib import Path
from typing import List, Dict
from meshroom.core.submitter import BaseSubmitter, SubmitterOptions, BaseSubmittedJob, SubmitterOptionsEnum
from meshroom.core.node import Status
from collections import namedtuple, defaultdict

from localfarm.localFarm import Task, Job, LocalFarmEngine


logger = logging.getLogger("LocalFarmSubmitter")
logger.setLevel(logging.INFO)


DEFAULT_FARM_PATH = os.getenv("MR_LOCAL_FARM_PATH", os.path.join(os.path.expanduser("~"), ".local_farm"))
REZ_DELIMITER_PATTERN = re.compile(r"(-|==|>=|>|<=|<)")
MESHROOM_ROOT = Path(__file__).resolve().parent.parent.parent


Chunk = namedtuple("chunk", ["iteration", "start", "end"])
CreatedTask = namedtuple("task", ["task", "chunkParams"])


def wrapMeshroomBin(_bin):
    if shutil.which(_bin):
        # The alias exists so use it directly
        return _bin
    binFolder = str(MESHROOM_ROOT / "bin")
    return os.path.join(binFolder, _bin)


def getResolvedVersionsDict():
    """ Get a dict {packageName: version} corresponding to the current context. """
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
    Get list of packages required for the job.
    Depends on env var and current rez context.

    By default we use the "==" delimiter to make sure we have the same version
    in the job that the one we have in the env where Meshroom is launched.
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
        logging.debug(f"LocalFarmSubmitter: REZ Packages: {str(reqPackages)}")
    elif 'REZ_MESHROOM_VERSION' in os.environ:
        reqPackages.add(f"meshroom{packagesDelimiter}{os.environ.get('REZ_MESHROOM_VERSION', '')}")
    return list(reqPackages)


def rezWrapCommand(cmd, useCurrentContext=False, useRequestedContext=True, otherRezPkg: list[str] = None):
    """ Wrap command to be runned using rez.
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
    """ Interface to manipulate the job via Meshroom. """

    def __init__(self, jid, submitter, farmPath=None):
        super().__init__(jid, submitter)
        self.jid = jid
        self.submitter: LocalFarmSubmitter = submitter
        self.__localJob = None
        self.__localJobTasks = None
        self.farmPath = farmPath or DEFAULT_FARM_PATH
        self._engine = LocalFarmEngine(self.farmPath)

    def __getJobInfo(self):
        """ Find job. """
        self.__localJob = self._engine.get_job_info(self.jid)
        self.__localJobTasks = {t.get("tid"): t for t in self.__localJob["tasks"]}

    @property
    def localfarmJob(self):
        if not self.__localJob:
            self.__getJobInfo()
        return self.__localJob

    @property
    def localfarmTasks(self):
        if not self.__localJobTasks:
            self.__getJobInfo()
        return self.__localJobTasks

    def __getChunkTasks(self, nodeUid, iteration):
        tasks = []
        for _, task in self.localfarmTasks.items():
            taskNodeUid = task["metadata"].get("nodeUid", None)
            taskIt = task["metadata"].get("iteration", -1)
            if taskNodeUid == nodeUid and taskIt == iteration:
                tasks.append(task)
        return tasks

    # Task actions

    def stopChunkTask(self, node, iteration):
        """ This will kill one task. """
        tasks = self.__getChunkTasks(node._uid, iteration)
        for task in tasks:
            self._engine.stop_task(self.jid, task["tid"])

    def skipChunkTask(self, node, iteration):
        """ This will skip one task. """
        tasks = self.__getChunkTasks(node._uid, iteration)
        for task in tasks:
            self._engine.skip_task(self.jid, task["tid"])

    def restartChunkTask(self, node, iteration):
        """ This will restart one task. """
        tasks = self.__getChunkTasks(node._uid, iteration)
        for task in tasks:
            self._engine.restart_task(self.jid, task["tid"])

    # Job actions

    def getJobErrors(self):
        """ Check for error in the job. """
        return self._engine.get_job_errors(self.jid)

    def pauseJob(self):
        """ This will pause the job: new tasks will not be processed. """
        self._engine.pause_job(self.jid)

    def resumeJob(self):
        """ This will unpause the job. """
        self._engine.unpause_job(self.jid)

    def interruptJob(self):
        """ This will interrupt the job (and kill running tasks). """
        self._engine.interrupt_job(self.jid)

    def restartJob(self):
        """ Restart the whole job. """
        self._engine.restart_job(self.jid)

    def restartErrorTasks(self):
        """ Restart all error tasks on the job. """
        self._engine.restart_error_tasks(self.jid)


class LocalFarmSubmitter(BaseSubmitter):
    """ Meshroom submitter to localfarm. """

    _name = "LocalFarm"
    _options = SubmitterOptions(SubmitterOptionsEnum.ALL)

    dryRun = False
    environment = {}

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.farmPath = DEFAULT_FARM_PATH
        self.reqPackages = getRequestPackages()
        self.jobEnv = {}

    def setFarmPath(self, path: str):
        self.farmPath = path

    def setJobEnv(self, env: dict):
        self.jobEnv = env

    def retrieveJob(self, jid) -> LocalFarmJob:
        job = LocalFarmJob(jid, self, farmPath=self.farmPath)
        return job

    @staticmethod
    def getChunks(chunkParams) -> list[Chunk]:
        """ Get list of chunks. """
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
        cmdBin = wrapMeshroomBin("meshroom_createChunks")
        cmd = f"{cmdBin} --submitter LocalFarm {cmdArgs}"
        # Wrap with rez
        cmd = rezWrapCommand(cmd, otherRezPkg=rezPackages)
        return cmd

    def __createChunkTasks(self, job: Job, parentTask: Task, children: List[Task], chunkParams: dict) -> Task:
        cmdArgs = chunkParams.get("chunkCmdArgs")
        chunks = self.getChunks(chunkParams)
        for c in chunks:
            name = f"{parentTask.name}_{c.start}_{c.end}"
            meta = parentTask.metadata.copy()
            meta["iteration"] = c.iteration
            cmdBin = wrapMeshroomBin("meshroom_compute")
            cmd = f"{cmdBin} {cmdArgs} --iteration {c.iteration}"
            cmd = rezWrapCommand(cmd, otherRezPkg=self.reqPackages)
            chunkTask = Task(name=name, command=cmd, metadata=meta, env=self.jobEnv)
            job.addTask(chunkTask)
            for child in children:
                job.addTaskDependency(child, chunkTask)
            job.addTaskDependency(chunkTask, parentTask)

    def createTask(self, meshroomFile: str, node) -> CreatedTask:
        cmdArgs = f"--node {node.name} \"{meshroomFile}\" --extern"
        metadata = {"nodeUid": node._uid}

        if not node._chunksCreated:
            cmd = self.getExpandWrappedCmd(cmdArgs, self.reqPackages)
            task = Task(name=node.name, command=cmd, metadata=metadata, env=self.jobEnv)
            task = CreatedTask(task, None)

        elif node.isParallelized:
            _, _, nbBlocks = node.nodeDesc.parallelization.getSizes(node)
            iterationsToIgnore = []
            for c in node._chunks:
                if c._status.status == Status.SUCCESS:
                    iterationsToIgnore.append(c.range.iteration)
            chunkParams = {
                "start": 0, "end": nbBlocks - 1, "step": 1, 
                "ignoreIterations": iterationsToIgnore,
                "chunkCmdArgs": cmdArgs
            }
            task = Task(name=node.name, command="", metadata=metadata, env=self.jobEnv)
            task = CreatedTask(task, chunkParams)

        else:
            cmdBin = wrapMeshroomBin("meshroom_compute")
            cmd = f"{cmdBin} {cmdArgs} --iteration 0"
            cmd = rezWrapCommand(cmd, otherRezPkg=self.reqPackages)
            task = Task(name=node.name, command=cmd, metadata=metadata, env=self.jobEnv)
            task = CreatedTask(task, None)

        print("Created task: ", task)

        return task

    def buildDependencies(self, job: Job, nodeUidToTask: Dict[str, CreatedTask], edges):
        """ Gather and create dependencies.
        First we get all parents and all children for each task.
        Then for each task:
        - we add the dependency to their parent and children
        - if the task is a chunked task (which means multi iteration tasks) the we create the
          chunk tasks and add dependencies from chunk tasks to children tasks

        # TODO: there's a lot of confusion between nodes and tasks here
        """
        # Gather dependencies
        tasksParentsUids = defaultdict(set)
        tasksChildrenUids = defaultdict(set)
        for u, v in edges:
            # tasksParentsUids[v._uid].add(u._uid)
            # tasksChildrenUids[u._uid].add(v._uid)
            tasksParentsUids[u._uid].add(v._uid)
            tasksChildrenUids[v._uid].add(u._uid)
        # Create dependencies
        for taskUid, createdTask in nodeUidToTask.items():
            parentsTasks = [nodeUidToTask[tuid].task for tuid in tasksParentsUids.get(taskUid, set())]
            childrenTasks = [nodeUidToTask[tuid].task for tuid in tasksChildrenUids.get(taskUid, set())]
            # Create regular dependencies
            for parentTask in parentsTasks:
                job.addTaskDependency(createdTask.task, parentTask)
            for childTask in childrenTasks:
                job.addTaskDependency(childTask, createdTask.task)
            # Create chunk tasks if necessary
            if createdTask.chunkParams:
                self.__createChunkTasks(job, createdTask.task, childrenTasks, createdTask.chunkParams)

    def createJob(self, nodes, edges, filepath, submitLabel="{projectName}") -> LocalFarmJob:
        projectName = os.path.splitext(os.path.basename(filepath))[0]
        name = submitLabel.format(projectName=projectName)
        # Create job
        job = Job(name)
        # Create tasks
        nodeUidToTask: Dict[str, CreatedTask] = {}
        for node in nodes:
            if node._uid in nodeUidToTask:
                continue  # HACK: Should not be necessary
            createdTask: CreatedTask = self.createTask(filepath, node)
            job.addTask(createdTask.task)
            nodeUidToTask[node._uid] = createdTask
        # Build dependencies
        self.buildDependencies(job, nodeUidToTask, edges)
        # Submit job
        engine = LocalFarmEngine(self.farmPath)
        res = job.submit(engine)
        print(f"Submitted job : {res}")
        if self.dryRun:
            return True
        if len(res) == 0:
            return False
        submittedJob = LocalFarmJob(res.get("jid"), LocalFarmSubmitter, farmPath=self.farmPath)
        return submittedJob

    def createChunkTask(self, node, graphFile, **kwargs):
        """
        Dynamically create chunk tasks for the given node (executed by meshroom_createChunks).
        """
        # Retrieve current job/task info
        currentJid, currentTid = int(os.getenv("LOCALFARM_CURRENT_JID")), int(os.getenv("LOCALFARM_CURRENT_TID"))
        # Make sure we inherit current MESHROOM_PLUGINS_PATH for submission
        # TODO: later we can immplement a proper env inheriting system like what we have in tractor
        taskEnv = {
            "MESHROOM_PLUGINS_PATH": os.environ.get("MESHROOM_PLUGINS_PATH", "")
        }
        if self.jobEnv:
            taskEnv.update(self.jobEnv)
        # Get engine
        engine = LocalFarmEngine(self.farmPath)
        # Get chunk info
        cmdArgs = f"--node {node.name} \"{graphFile}\" --extern"
        _, _, nbBlocks = node.nodeDesc.parallelization.getSizes(node)
        if nbBlocks <= 0:
            return
        chunkRangeParams = {'start': 0, 'end': nbBlocks - 1, 'step': 1}
        # Create subtasks
        for chunk in self.getChunks(chunkRangeParams):
            name = f"{node.name}_{chunk.start}_{chunk.end}"
            metadata = {"nodeUid": node._uid, "iteration": chunk.iteration}
            cmdBin = wrapMeshroomBin("meshroom_compute")
            cmd = f"{cmdBin} {cmdArgs} --iteration {chunk.iteration}"
            cmd = rezWrapCommand(cmd, otherRezPkg=self.reqPackages)
            print("Additional chunk task command: ", cmd)
            task = Task(name=name, command=cmd, metadata=metadata, env=taskEnv)
            engine.create_additional_task(currentJid, currentTid, task)
