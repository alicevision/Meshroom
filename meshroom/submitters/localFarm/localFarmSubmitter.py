#!/usr/bin/env python

import os
import re
import shutil
import logging
from pathlib import Path
from typing import Dict, List
from collections import namedtuple

from meshroom import _MESHROOM_ROOT
from meshroom.core.submitter import BaseSubmitter, SubmitterOptions, BaseSubmittedJob, SubmitterOptionsEnum
from meshroom.core.submitter import OrderedTask, OrderedTaskType

from localfarm.localFarmClient import Task, Job, LocalFarmClientContext


logger = logging.getLogger("LocalFarmSubmitter")
logger.setLevel(logging.INFO)


DEFAULT_FARM_PATH = os.getenv("MR_LOCAL_FARM_PATH", os.path.join(os.path.expanduser("~"), ".local_farm"))
REZ_DELIMITER_PATTERN = re.compile(r"(-|==|>=|>|<=|<)")


Chunk = namedtuple("chunk", ["iteration", "start", "end"])
CreatedTask = namedtuple("task", ["task", "chunkParams"])


def wrapMeshroomBin(_bin):
    if shutil.which(_bin):
        # The alias exists so use it directly
        return _bin
    binFolder = str(_MESHROOM_ROOT / "bin")
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


def rezWrapCommand(cmd: str, 
                   useCurrentContext: bool=False, 
                   otherRezPkg: List[str] = None, 
                   additionalEnv: dict=None) -> str:
    """Wrap command to be runned using rez.

    Args:
        cmd: command to run
        useCurrentContext: use current rez context to retrieve a list of rez packages.
        otherRezPkg: Additionnal rez packages.
        additionalEnv: Additional environment variables.

    Returns:
        the final command to execute
    """
    packages = set()
    if useCurrentContext:
        # In this case we want to use the full context
        packages.update([p for p in os.environ.get('REZ_RESOLVE', '').split(" ") if p])
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
        if additionalEnv:
            envVars = " ".join([f'{k}="{v}"' for k, v in additionalEnv.items()])
        return f"{rezBin} env {packagesStr} -- {envVars} {cmd}"
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

    def __getJobInfo(self):
        """ Find job. """
        with LocalFarmClientContext(self.farmPath) as client:
            self.__localJob = client.get_job_info(self.jid)
            self.__localJobTasks = {t.get("tid"): t for t in self.__localJob["tasks"]}

    @property
    def localfarmJob(self):
        self.__getJobInfo()
        return self.__localJob

    @property
    def localfarmTasks(self):
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
        with LocalFarmClientContext(self.farmPath) as client:
            for task in tasks:
                client.stop_task(self.jid, task["tid"])

    def skipChunkTask(self, node, iteration):
        """ This will skip one task. """
        tasks = self.__getChunkTasks(node._uid, iteration)
        with LocalFarmClientContext(self.farmPath) as client:
            for task in tasks:
                client.skip_task(self.jid, task["tid"])

    def restartChunkTask(self, node, iteration):
        """ This will restart one task. """
        tasks = self.__getChunkTasks(node._uid, iteration)
        with LocalFarmClientContext(self.farmPath) as client:
            for task in tasks:
                client.restart_task(self.jid, task["tid"])

    # Job actions

    def getJobErrors(self):
        """ Check for error in the job. """
        with LocalFarmClientContext(self.farmPath) as client:
            jobErrors = client.get_job_errors(self.jid)
        return jobErrors

    def pauseJob(self):
        """ This will pause the job: new tasks will not be processed. """
        with LocalFarmClientContext(self.farmPath) as client:
            client.pause_job(self.jid)

    def resumeJob(self):
        """ This will unpause the job. """
        with LocalFarmClientContext(self.farmPath) as client:
            client.unpause_job(self.jid)

    def interruptJob(self):
        """ This will interrupt the job (and kill running tasks). """
        with LocalFarmClientContext(self.farmPath) as client:
            client.interrupt_job(self.jid)

    def restartJob(self):
        """ Restart the whole job. """
        with LocalFarmClientContext(self.farmPath) as client:
            client.restart_job(self.jid)

    def restartErrorTasks(self):
        """ Restart all error tasks on the job. """
        with LocalFarmClientContext(self.farmPath) as client:
            client.restart_error_tasks(self.jid)


class LocalFarmSubmitter(BaseSubmitter):
    """ Meshroom submitter to localfarm. """

    _name = "LocalFarm"
    _options = SubmitterOptions(SubmitterOptionsEnum.ALL)

    dryRun = False
    environment = {}
    disabled_rez = False

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

    def getExpandWrappedCmd(self, cmdArgs, rezPackages):
        # Wrap with create_chunks
        cmdBin = wrapMeshroomBin("meshroom_createChunks")
        cmd = f"{cmdBin} --submitter LocalFarm {cmdArgs}"
        # Wrap with rez
        if not self.disabled_rez:
            cmd = rezWrapCommand(cmd, otherRezPkg=rezPackages, additionalEnv=self.jobEnv)
        return cmd

    def createFarmTask(self, meshroomFile: str, orderedTask: OrderedTask, createdTasks: Dict[OrderedTask, Task]) -> Task:
        metadata = dict()
        if orderedTask.node:
            metadata = {"nodeUid": orderedTask.node._uid}
        
        if orderedTask.iteration >= 0:
            metadata["iteration"] = orderedTask.iteration
        elif orderedTask.taskType == OrderedTaskType.PREPROCESS:
            metadata["iteration"] = "preprocess"
        elif orderedTask.taskType == OrderedTaskType.POSTPROCESS:
            metadata["iteration"] = "postprocess"

        if orderedTask.taskType == OrderedTaskType.PLACEHOLDER:
            return Task(name=orderedTask.node.name if orderedTask.node else "", command="", metadata=metadata)
        
        cmdArgs = f"--node {orderedTask.node.name} \"{meshroomFile}\" --extern"
        
        if orderedTask.taskType == OrderedTaskType.EXPANDING:
            cmd = self.getExpandWrappedCmd(cmdArgs, self.reqPackages)
            task = Task(name=orderedTask.node.name, command=cmd, metadata=metadata, env=self.jobEnv)
        else:
            cmdBin = wrapMeshroomBin("meshroom_compute")
            cmd = f"{cmdBin} {cmdArgs}"
            if orderedTask.taskType == OrderedTaskType.PREPROCESS:
                cmd += f" --preprocess"
            elif orderedTask.taskType == OrderedTaskType.POSTPROCESS:
                cmd += f" --postprocess"
            elif orderedTask.taskType == OrderedTaskType.CHUNK:
                cmd += f" --iteration {orderedTask.iteration}"
            if not self.disabled_rez:
                cmd = rezWrapCommand(cmd, otherRezPkg=self.reqPackages, additionalEnv=self.jobEnv)
            task = Task(name=orderedTask.node.name, command=cmd, metadata=metadata, env=self.jobEnv)

        return task

    def createJob(self, orderedTasks, filepath, submitLabel="{projectName}") -> LocalFarmJob:
        projectName = os.path.splitext(os.path.basename(filepath))[0]
        name = submitLabel.format(projectName=projectName)
        # Create job
        job = Job(name)

        # Create tasks
        orderedTasks.display()
        createdTasks: Dict[OrderedTask, Task] = dict()
        for taskToCreate in orderedTasks.iterOnTasks():
            if taskToCreate in createdTasks.keys():
                continue
            createdTask = self.createFarmTask(filepath, taskToCreate, createdTasks)
            job.addTask(createdTask)
            createdTasks[taskToCreate] = createdTask

        for orderedTask, task in createdTasks.items():
            print(orderedTask, "->", task)

        for orderedTask, task in createdTasks.items():
            deps = [createdTasks.get(t) for t in orderedTask.dependencies]
            for dependency in deps:
                job.addTaskDependency(task, dependency)
    
        # Submit job
        with LocalFarmClientContext(self.farmPath) as client:
            res = job.submit(client)

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
        # Get chunk info
        cmdArgs = f"--node {node.name} \"{graphFile}\" --extern"
        _, _, nbBlocks = node.nodeDesc.parallelization.getSizes(node)
        if nbBlocks <= 0:
            return
        chunkRangeParams = {'start': 0, 'end': nbBlocks - 1, 'step': 1}
        # Create subtasks
        with LocalFarmClientContext(self.farmPath) as client:
            for chunk in self.getChunks(chunkRangeParams):
                name = f"{node.name}_{chunk.start}_{chunk.end}"
                metadata = {"nodeUid": node._uid, "iteration": chunk.iteration}
                cmdBin = wrapMeshroomBin("meshroom_compute")
                cmd = f"{cmdBin} {cmdArgs} --iteration {chunk.iteration}"
                if not self.disabled_rez:
                    cmd = rezWrapCommand(cmd, otherRezPkg=self.reqPackages, additionalEnv=self.jobEnv)
                print("Additional chunk task command: ", cmd)
                task = Task(name=name, command=cmd, metadata=metadata, env=taskEnv)
                client.create_additional_task(currentJid, currentTid, task)
