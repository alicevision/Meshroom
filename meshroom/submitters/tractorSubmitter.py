#!/usr/bin/env python

import re
import os
import json
import getpass
import logging
import shlex
from collections import namedtuple

from meshroom.core.submitter import BaseSubmitter

from tractor.api import author

currentDir = os.path.dirname(os.path.realpath(__file__))
binDir = os.path.dirname(os.path.dirname(os.path.dirname(currentDir)))

REZ_DELIMITER_PATTERN = re.compile(r"(-|==|>=|>|<=|<)")
TRACTOR_JOB_URL = "http://tractor-engine/tv/#jid={jid}"
LICENSES_MAP = {
    'mtoa': 'arnold',
    'houdiniE': 'houdinie', 
}

Chunk = namedtuple("chunk", ["iteration", "start", "end"])


def get_job_packages():
    """ Get list of packages required for the job
    Depends on env var and current rez context
    """
    reqPackages = []
    if 'REZ_REQUEST' in os.environ:
        packages = os.environ.get('REZ_USED_REQUEST', '').split()
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
        usedPackages = set()  # Use set to remove duplicates
        for p in packages:
            if p.startswith('~') or p.startswith("!"):
                continue
            v = REZ_DELIMITER_PATTERN.split(p)
            usedPackages.add(v[0])
        for p in usedPackages:
            # Use "==" to make sure we have the same version in the job that the one we have in the env
            # where meshroom is launched
            reqPackages.append("==".join([p, resolvedVersions[p]]))
        logging.debug(f"TractorSubmitter: REZ Packages: {str(reqPackages)}")
    elif 'REZ_MESHROOM_VERSION' in os.environ:
        reqPackages.append(f"meshroom-{os.environ.get('REZ_MESHROOM_VERSION', '')}")
    return reqPackages


def filterRequirements(requirements):
    """ Filter and process requirements for Tractor
    >>> filterRequirements({'minNbCore': 1, 'maxNbCore': 5, 'ramUse': 1024*64, 'service': 'RenderHigh64'}
        {'service': 'RenderHigh64 && @.nCPUs >= 1 && @.nCPUs <= 5 && (1024 * @.mem) > 65536)'}
    """
    _requirements = {}
    serviceAdd = []
    for req in requirements:
        if req == 'minNbCore':
            serviceAdd.append( '@.nCPUs >= %d' % requirements[req] )
        elif req == 'maxNbCore':
            serviceAdd.append( '@.nCPUs <= %d' % requirements[req] )
        elif req == 'ramUse':
            serviceAdd.append( '(1024 * @.mem) > %d)' % requirements[req] )
        else:
            _requirements[req] = requirements[req]
    if serviceAdd:
        _serviceAdd = ' && '.join(serviceAdd)
        if 'service' in _requirements:
            _requirements['service'] += ' && ' + _serviceAdd
        else:
            _requirements['service'] = _serviceAdd
    return _requirements


def rezWrapCommand(cmd, useCurrentContext: bool = True, otherRezPkg: list[str] = None):
    """ Wrap command to be runned using rez
    :param cmd: command to run
    :type cmd: bool
    :param useCurrentContext: use current rez context to retrieve a list of rez packages
    :type useCurrentContext: bool
    :param otherRezPkg: Additionnal rez packages
    :type otherRezPkg: list[str]
    """
    packages = set()
    if useCurrentContext:
        packages.add(os.environ.get('REZ_RESOLVE', ''))
    if otherRezPkg:
        packages.update(otherRezPkg)
    packagesStr = " ".join([p for p in packages if p])
    if packagesStr:
        rezBin = "rez"
        if "REZ_BIN" in os.environ:
            rezBin = os.environ["REZ_BIN"]
        elif "REZ_PACKAGES_ROOT" in os.environ:
            rezBin = os.path.join(os.environ["REZ_PACKAGES_ROOT"], "/bin/rez")
        return f"{rezBin} env {packagesStr} -- {cmd}"
    return cmd


def toTractorEnv(environment):
    """ Format env for Tractor """
    return [f"setenv {k}={v}" for k, v in environment.items()]


class TractorTask:
    """ Stores a task and the additional tasks spawned for each chunks
    Will be helpful later to resubmit only failed chunks for example
    """
    
    def __init__(self, task):
        self.task = task
        self.chunkTasks = {}
    
    def addChunkTask(self, chunk, task):
        self.chunkTasks[chunk] = task


class TractorTaskCreator:
    """ Builder class for tractor tasks """
    
    def __init__(self, task, job):
        """ Build task metadata """
        self.task = task
        self.chunks = self.task.getChunks()
        
        # self.env
        self.env = job.environment.copy()
        if self.task.environment:
            self.env.update(self.environment)
        
        # self.rezArgs
        self.rezArgs = {
            'useCurrentContext': True,
            'otherRezPkg': None,
        }
        if self.task.rezPackages:
            self.rezArgs['useCurrentContext'] = False
            self.rezArgs['otherRezPkg'] = self.task.rezPackages

        # self.tractorCmd
        if self.chunks:
            # Empty task with multiple commands (sub-tasks) to execute in parallel
            self.tractorCmd = None
        else:
            # Simple task with only one command to execute
            cmd = self.task.command
            if self.task.execViaRez:
                cmd = rezWrapCommand(cmd, **self.rezArgs)
            self.tractorCmd = shlex.split(cmd)

        # requirements
        # Licenses --> tractor handle licenses as limits
        requirements = filterRequirements(job.requirements)
        self.limits = [LICENSES_MAP.get(license, license) for license in self.task.licenses]
        if 'limits' in requirements:
            self.limits.extend(requirements['limits'])
        if 'DEFAULT_TRACTOR_LIMIT' in os.environ:
            self.limits.append(os.environ['DEFAULT_TRACTOR_LIMIT'])
        
        # Service
        taskRequirements = requirements.copy()
        # Requirements
        if self.task.requirements:
            taskRequirements.update(self.task.requirements)
        taskRequirements = filterRequirements(taskRequirements)
        self.service = taskRequirements.get('service', os.environ['DEFAULT_TRACTOR_SERVICE'])
        
        self.taskTags = self.task.tags.copy()
    
    def getLimits(self, requirements):
        taskLimits = [LICENSES_MAP.get(license, license) for license in self.task.licenses]
        if 'limits' in requirements:
            taskLimits.extend(requirements['limits'])
        if 'DEFAULT_TRACTOR_LIMIT' in os.environ:
            taskLimits.append(os.environ['DEFAULT_TRACTOR_LIMIT'])
        return taskLimits
    
    def cookChunkTask(self, tractorTask, chk):
        """ Cook individual chunk task """
        # Substitute
        cmd = self.task.command + f' --iteration {chk.iteration}'
        if self.task.execViaRez:
            cmd = rezWrapCommand(cmd, **self.rezArgs)
        # Create command task
        tractorTaskCmd = tractorTask.newTask(
            title=self.task.name + f"_{chk.start}_{chk.end}",
            argv=shlex.split(cmd),
            service=self.service,
            metadata=str(self.taskTags),
        )
        # licenses are handled via 'tags'
        tractorTaskCmd.cmds[0].tags = self.limits
        # set environment on command
        tractorTaskCmd.cmds[0].envkey = toTractorEnv(self.env)
        
        return tractorTaskCmd
    
    def cook(self) -> TractorTask:
        """ Creates the task
        Returns a TractorTask object
        """
        tractorTask = author.Task(
            title=self.task.name,
            argv=self.tractorCmd,
            service=self.service,
            metadata=str(self.taskTags),
        )
        res = TractorTask(tractorTask)
        if not self.chunks:
            for cmd in tractorTask.cmds:
                cmd.tags = self.limits
                cmd.envkey = toTractorEnv(self.env)
        else:
            # sub commands
            for chk in self.chunks:
                res.addChunkTask(chk, self.cookChunkTask(tractorTask, chk))
        return res
        

class Task:
    """ Object that represent a Node in meshroom that has been submitted to the farm.
    Each node should be created as a Task in the tractor submitter.
    However one Task object can spool multiple tractor task because we will create individual 
    tasks for chunks.
    """
    
    def __init__(self, name, uid, command, tags=None, execViaRez=True, rezPackages=None, requirements=None, environment=None, **kwargs):
        self.uid = uid
        self.name = name
        self.command = command
        self.tags = tags or {}
        self.rezPackages = rezPackages or []
        self.execViaRez = execViaRez
        self.requirements = requirements or {}
        self.optionalArgs = kwargs
        self._children = set()
        self._parents = set()
        self.environment = environment or {}
        
        # Keyword args
        self.chunkParams = kwargs.get("chunks")
        self.licenses = kwargs.get("licenses", [])
    
    def __repr__(self):
        return f"<Task {self.name} {self.uid}>"
    
    def __hash__(self):
        return hash(frozenset(["TractorTask", self.name, self.uid]))
    
    def __eq__(self, __value: object) -> bool:
        return hash(self) == hash(__value)

    def connect(self, task):
        """ Add a task in the children of the current task
        """
        if isinstance(task, (tuple, list)):
            for t in task:
                self.connect(t)
        else:
            self._children.add(task)  # Add task as current object children
            task._parents.add(self)   # Add current object as task parent
    
    def getChunks(self) -> list[Chunk]:
        """ Get list of chunks """
        it = None
        if self.chunkParams:
            start, end = self.chunkParams.get("start", -1), self.chunkParams.get("end", -2)
            size = self.chunkParams.get("packetSize", 1)
            frameRange = list(range(start, end+1, 1))
            if frameRange:
                slices = [frameRange[i:i + size] for i in range(0, len(frameRange), size)]
                it = [Chunk(i, item[0], item[-1]) for i, item in enumerate(slices)]
        return it


class TaskGraph:
    """ Graph with Task objects
    The point of this class is to delegate task creation and to make sure we 
    don't create multiple times the same task.
    Also we store the created tasks and chunks info so that might be useful in the future
    """
    
    def __init__(self, job):
        self.job = job
        self._tasks = set()
        self.__cooked = {}
    
    def __len__(self):
        return len(self._tasks)
    
    @property
    def roots(self):
        return [task for task in self._tasks if not task._parents]

    @property
    def leaves(self):
        return [task for task in self._tasks if not task._children]
    
    def cookTask(self, task):
        """ Cook task, chunk tasks, and set tasks dependencies """
        if task.uid not in self.__cooked:
            logging.info(f"TractorSubmitter: Create Tractor Task: {task.name}")
            tractorTask = TractorTaskCreator(task, self.job).cook()
            self.__cooked[task.uid] = tractorTask
            for child in task._children:
                childTask = self.cookTask(child)
                if tractorTask.chunkTasks:
                    for chkTask in tractorTask.chunkTasks.values():
                        chkTask.addChild(childTask)
                else:
                    tractorTask.task.addChild(childTask)
        return self.__cooked[task.uid].task
    
    def cook(self, jobTask):
        """ Cook the graph (i.e. create all tractor tasks) and dependencies
        jobTask is the root task for the whole job
        """
        for task in self.roots:
            child = self.cookTask(task)
            jobTask.addChild(child)


class Job:
    _priorityDict = {
        "low": 4000,
        "normal": 5000,
        "high": 10000,
    }

    def __init__(self, name, tags=None, requirements=None, environment=None, user=None, comment="", paused=False):
        self.name = name
        self.tags = tags or {}
        self.requirements = requirements or {}
        self.environment = environment or {}
        self.user = user or getpass.getuser()
        self.comment = comment
        self.paused = paused
        self._graph = TaskGraph(self)
        self.share = ""
    
    def getShare(self):
        share = self.share
        if share:
            if isinstance(share, (str, bytes)):
                share = [share]
        elif 'DEFAULT_FARM_SHARE_TRACTOR' in os.environ:
            share = os.environ['DEFAULT_FARM_SHARE_TRACTOR'].split(',')
        return share
    
    def getService(self):
        requirements = filterRequirements(self.requirements)
        logging.info(f"TractorSubmitter: requirements: {requirements}")
        if 'service' not in requirements and 'DEFAULT_TRACTOR_SERVICE' not in os.environ:
            raise ValueError('Could not find DEFAULT_TRACTOR_SERVICE in env')
        service = requirements.get('service', os.environ['DEFAULT_TRACTOR_SERVICE'])
        return service
    
    def addTask(self, task):
        """ Add task and make sure it is unique """
        # Dont add the task if it has already been created
        for t in self._graph._tasks:
            if t == task:
                logging.error(f"TractorSubmitter: Task already created : {t}")
                return t
        self._graph._tasks.add(task)
        return task
    
    def cook(self):
        """ Cook job and tasks graph """
        # auto. add FARM_USER user
        self.environment['FARM_USER'] = self.user
        tags = self.tags.copy()
        env = self.environment.copy()
        # Create job
        tractorJob = author.Job(
            title=self.name,
            service=self.getService(),
            metadata=str(tags),
            envkey=toTractorEnv(env),
            paused=self.paused,
            comment=self.comment,
            spoolcwd='/tmp',
            projects=self.getShare()
        )
        
        serialsubtasks = (len(self._graph.leaves) == 1)
        jobTask = tractorJob.newTask(title=self.name, argv=None, serialsubtasks=serialsubtasks)
        self._graph.cook(jobTask)
        if len(self._graph) == 0:
            # tractor API will raise a RequiredValueError if no task are in job so we add a dummy one
            # note that the job will not even appear in Tractor web ui
            _ = tractorJob.newTask(title='dummy')
        
        return tractorJob
    
    def submit(self, priority="normal", share="", dryRun=False, block=False):
        """Submit to Tractor, or print TCL if dryRun."""
        if share:
            self.share = share

        job = self.cook()
        job.priority = self._priorityDict.get(priority, 5000)

        if dryRun:
            logging.info("TractorSubmitter: Job in TCL format :")
            logging.info(job.asTcl())
            return {}
        else:
            jid = job.spool(block=block, owner=self.user)
            return {"id": jid, "url": TRACTOR_JOB_URL.format(jid=jid)}



class TractorSubmitter(BaseSubmitter):
    """
    Meshroom submitter to tractor
    """
    
    dryRun = False
    environment = {}
    DEFAULT_TAGS = {'prod': ''}

    filepath = os.environ.get('TRACTORCONFIG', os.path.join(currentDir, 'tractorConfig.json'))
    config = json.load(open(filepath))
    
    def __init__(self, parent=None):
        super().__init__(name='Tractor', parent=parent)
        self.share = os.environ.get('MESHROOM_TRACTOR_SHARE', 'vfx')
        self.prod = os.environ.get('PROD', 'mvg')
        self.reqPackages = get_job_packages()
        if 'REZ_DEV_PACKAGES_ROOT' in os.environ:
            self.environment['REZ_DEV_PACKAGES_ROOT'] = os.environ['REZ_DEV_PACKAGES_ROOT']
        if 'REZ_PROD_PACKAGES_PATH' in os.environ:
            self.environment['REZ_PROD_PACKAGES_PATH'] = os.environ['REZ_PROD_PACKAGES_PATH']
        if 'PROD' in os.environ:
            self.environment['PROD'] = os.environ['PROD']
        if 'PROD_ROOT' in os.environ:
            self.environment['PROD_ROOT'] = os.environ['PROD_ROOT']

    def createTask(self, meshroomFile, node):
        tags = self.DEFAULT_TAGS.copy()  # copy to not modify default tags
        optionalArgs = {}
        logging.debug(f"TractorSubmitter: node: {node.name} ({node._uid})")
        if node.isParallelized:
            blockSize, fullSize, nbBlocks = node.nodeDesc.parallelization.getSizes(node)
            if nbBlocks > 1:  # Is it better like this ?
                optionalArgs["chunks"] = {'start': 0, 'end': nbBlocks - 1, 'step': 1}
        tags['nbFrames'] = node.size
        tags['prod'] = self.prod
        allRequirements = set()
        allRequirements.update(self.config['CPU'].get(node.nodeDesc.cpu.name, []))
        allRequirements.update(self.config['RAM'].get(node.nodeDesc.ram.name, []))
        allRequirements.update(self.config['GPU'].get(node.nodeDesc.gpu.name, []))
        exe = "meshroom_compute" if self.reqPackages else os.path.join(binDir, "meshroom_compute")
        taskCommand = f"{exe} --node {node.name} \"{meshroomFile}\" --extern"
        task = Task(
            name=node.name,
            uid=node._uid,  # Provide unicity info
            command=taskCommand,
            tags=tags,
            rezPackages=self.reqPackages,
            requirements={'service': str(','.join(allRequirements))},
            **optionalArgs)
        return task

    def submit(self, nodes, edges, filepath, submitLabel="{projectName}"):
        projectName = os.path.splitext(os.path.basename(filepath))[0]
        name = submitLabel.format(projectName=projectName)
        comment = filepath
        maxNodeSize = max([node.size for node in nodes])
        mainTags = {
            'prod': self.prod,
            'nbFrames': str(maxNodeSize),
            'comment': comment,
        }
        allRequirements = list(self.config.get('BASE', []))

        # Create Job Graph
        job = Job(
            name,
            tags=mainTags,
            requirements={'service': str(','.join(allRequirements))},
            environment=self.environment,
            user=os.environ.get('FARM_USER', os.environ.get('USER', getpass.getuser())),
        )

        nodeUidToTask = {}
        for node in nodes:
            if node._uid in nodeUidToTask:
                continue  # HACK: Should not be necessary
            task = self.createTask(filepath, node)
            task = job.addTask(task)  # Should not be necessary but we never know
            nodeUidToTask[node._uid] = task

        for u, v in edges:
            nodeUidToTask[u._uid].connect(nodeUidToTask[v._uid])

        res = job.submit(share=self.share, dryRun=self.dryRun)
        if self.dryRun:
            return True
        return len(res) > 0
