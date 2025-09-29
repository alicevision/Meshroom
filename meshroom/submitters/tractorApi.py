#!/usr/bin/env python

import os
import shlex
import getpass
import uuid
from string import Template
import itertools

from tractor.api import author


TRACTOR_JOB_URL = "http://tractor-engine/tv/#jid={jid}"


LICENSES_MAP = {
    'mtoa': 'arnold',
    'houdiniE': 'houdinie', 
}


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


def rezWrapCommand(cmd, rezResolve=True, otherRezPkg=None):
    """ Wrap command to be runned using rez
    :param cmd: command to run
    :type cmd: bool
    :param rezResolve: use current rez context to retrieve a list of rez packages
    :type rezResolve: bool
    :param otherRezPkg: other rez packages to add
    :type otherRezPkg: list
    Example:
    >>> rezWrapCommand('miMayaBatch --pyscript /tmp/foo.py', rezResolve=True)
    [...]/rez env [...] -- miMayaBatch --pyscript /tmp/foo.py 
    >>> rezWrapCommand('miMayaBatch --pyscript /tmp/foo.py', rezResolve=False, otherRezPkg=['animtestMaya-dev'])
    [...]/rez env animtestMaya-dev -- miMayaBatch --pyscript /tmp/foo.py 
    """

    packages = ''

    if rezResolve:
        packages = os.environ.get('REZ_RESOLVE', '')
   
    if otherRezPkg:
        packages += ' ' + ' '.join(otherRezPkg)

    if packages:
        rezBin = "rez"
        if "REZ_BIN" in os.environ:
            rezBin = os.environ.get("REZ_BIN", "")
        elif "REZ_PACKAGES_ROOT" in os.environ:
            rezBin = os.environ.get("REZ_PACKAGES_ROOT", "") + "/bin/rez"
        
        return "%s env %s -- %s" % (rezBin, packages, cmd)

    return cmd


def toTractorEnv(environment):
    """ Format env for Tractor """
    envKey = []
    for (key, value) in environment.items():
        envKey.append('setenv %s=%s' % (key, value))
    return envKey


class SubmitterTemplate(Template):
    ''' Support @-based (instead of $-based) substitutions
    '''
    delimiter = '@'


def connectTasks(parent, child):
    if parent not in child._parents:
        child._parents.append(parent)
    if child not in parent._children:
        parent._children.append(child)


def getLimits(licenses, requirements):
    taskLimits = [LICENSES_MAP.get(license, license) for license in licenses]
    if 'limits' in requirements:
        taskLimits.extend(requirements['limits'])
    if 'DEFAULT_TRACTOR_LIMIT' in os.environ:
        taskLimits.append(os.environ['DEFAULT_TRACTOR_LIMIT'])
    return taskLimits



class TractorTaskCreator:
    def __init__(self, task, job):
        self.task = task
        self.chunks = self.task.getChunks()
        
        taskEnv = job.environment.copy()
        rezArgs = {
            'rezResolve': True,
            'otherRezPkg': None,
        }
        if self.task.rezPackages:
            rezArgs['rezResolve'] = False
            rezArgs['otherRezPkg'] = self.task.rezPackages

        if self.chunks:
            # Empty task with multiple commands (sub-tasks) to execute in parallel
            self.tractorCmd = None
        else:
            # Simple task with only one command to execute
            cmd = self.task.command
            if self.task.execViaRez:
                cmd = rezWrapCommand(cmd, **rezArgs)
            self.tractorCmd = shlex.split(cmd)

        if self.task.environment:
            taskEnv.update(self.environment)
            
        # Licenses --> tractor handle licenses as limits
        requirements = filterRequirements(job.requirements)
        self.limits = getLimits(self.task.licenses, requirements)
        
        # Requirements
        taskRequirements = requirements.copy()
        if self.task.requirements:
            taskRequirements.update(self.task.requirements)

        taskRequirements = filterRequirements(taskRequirements)
        
        self.service = taskRequirements.get('service', os.environ['DEFAULT_TRACTOR_SERVICE'])
        self.env = taskEnv
        self.rezArgs = rezArgs
        
        self.taskTags = self.task.tags.copy()
    
    def cookChunkTask(self, tractorTask, chk):
        # Substitute
        _cmd = SubmitterTemplate(self.task.command)
        chunkDict = {'start': chk[0], 'end': chk[-1]}
        cmd = _cmd.safe_substitute(**chunkDict)
        if self.task.execViaRez:
            cmd = rezWrapCommand(cmd, **self.rezArgs)
        # Create command task
        tractorTaskCmd = tractorTask.newTask(
            title=self.task.name + '_%s_%s' % (chk[0], chk[-1]),
            argv=shlex.split(cmd),
            service=self.service,
            metadata=str(self.taskTags),
        )
        # licenses are handled via 'tags'
        tractorTaskCmd.cmds[0].tags = self.limits
        # set environment on command
        tractorTaskCmd.cmds[0].envkey = toTractorEnv(self.env)
        
        return tractorTaskCmd
    
    def cook(self):
        tractorTask = author.Task(
            title=self.task.name,
            argv=self.tractorCmd,
            service=self.service,
            metadata=str(self.taskTags),
        )

        childTasks = []
        if not self.chunks:
            for cmd in tractorTask.cmds:
                cmd.tags = self.limits
                cmd.envkey = toTractorEnv(self.env)
        else:
            # sub commands
            for chk in self.chunks:
                childTasks.append(self.cookChunkTask(tractorTask, chk))
        
        return tractorTask, childTasks



class Task:
    def __init__(self, name, command, tags=None, execViaRez=True, rezPackages=None, requirements=None, environment=None, **kwargs):
        self.uid = f"{name}_{uuid.uuid4().hex[:8]}"
        self.name = name
        self.command = command
        self.tags = tags or {}
        self.rezPackages = rezPackages or []
        self.execViaRez = execViaRez
        self.requirements = requirements or {}
        self.optionalArgs = kwargs
        self._children = []
        self._parents = []
        self.environment = environment or {}
        
        # Keyword args
        self.start = kwargs.get("start", -1)
        self.end = kwargs.get("end", -2)
        self.step = kwargs.get("step", 1)
        self.packetSize = kwargs.get("packetSize", 1)
        self.licenses = kwargs.get("licenses", [])
    
    def __repr__(self):
        return f"<Task {self.uid}>"

    def addChildren(self, tasks):
        if not isinstance(tasks, (list, tuple)):
            tasks = [tasks]
        for task in tasks:
            connectTasks(self, task)
    
    def addParents(self, tasks):
        if not isinstance(tasks, (list, tuple)):
            tasks = [tasks]
        for task in tasks:
            connectTasks(self, task)
    
    def getRezArgs(self):
        rezArgs = {
            'rezResolve': True,
            'otherRezPkg': None,
            }
        if self.rezPackages:
            rezArgs['rezResolve'] = False
            rezArgs['otherRezPkg'] = self.rezPackages
        return rezArgs
    
    def getService(self):
        return self.get("service", 
            self.requirements.get("service", 
                os.environ.get("DEFAULT_TRACTOR_SERVICE", "default")
            )
        )
    
    def getChunks(self):
        def chunk(it, size):
            it = iter(it)
            return iter(lambda: tuple(itertools.islice(it, size)), ())
        it = None
        frameRange = list(range(self.start, self.end+1, 1))
        if frameRange:
            it = chunk(frameRange, self.packetSize)
        return it



class TaskGraph:
    def __init__(self, job, tasks):
        self.job = job
        self._tasks = tasks
        self._jobTask = None
        self.__cooked = {}
    
    def __len__(self):
        return len(self._tasks)
    
    def addJobTask(self, rootTask):
        self._jobTask = rootTask
    
    def addTask(self, task):
        self.tasks.append(task)
        
    @property
    def roots(self):
        rootTasks = []
        for task in self._tasks:
            if not task._parents:
                rootTasks.append(task)
        return rootTasks

    @property
    def leaves(self):
        leavesTasks = []
        for task in self._tasks:
            if not task._children:
                leavesTasks.append(task)
        return leavesTasks
    
    def cookTask(self, task):
        if (task.uid in self.__cooked):
            tractorTask, chunkTasks = self.__cooked[task.uid]
            return tractorTask
        print(f"[TractorSubmitter] Create Tractor Task: {task.name}")
        tractorTask, chunkTasks = TractorTaskCreator(task, self.job).cook()
        self.__cooked[task.uid] = (tractorTask, chunkTasks)
        for child in task._children:
            childTask = self.cookTask(child)
            if chunkTasks:
                for t in chunkTasks:
                    t.addChild(childTask)
            else:
                tractorTask.addChild(childTask)
        return tractorTask
    
    def cook(self):
        for task in self.roots:
            child = self.cookTask(task)
            self._jobTask.addChild(child)



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
        self._tasks = []
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
        print(f"[TractorSubmitter] requirements: {requirements}")
        if 'service' not in requirements and 'DEFAULT_TRACTOR_SERVICE' not in os.environ:
            raise ValueError('Could not find DEFAULT_TRACTOR_SERVICE in env')
        service = requirements.get('service', os.environ['DEFAULT_TRACTOR_SERVICE'])
        return service
    
    def addTask(self, task):
        self._tasks.append(task)
        return task
    
    def cook(self):
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
        
        graph = TaskGraph(self, self._tasks)
        serialsubtasks = (len(graph.leaves) == 1)
        jobTask = tractorJob.newTask(title=self.name, argv=None, serialsubtasks=serialsubtasks)
        graph.addJobTask(jobTask)
        graph.cook()
        if len(graph) == 0:
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
            print("[TractorSubmitter] Job in TCL format :")
            print(job.asTcl())
            return {}
        else:
            jid = job.spool(block=block, owner=self.user)
            return {
                "id": jid,
                "url": TRACTOR_JOB_URL.format(jid=jid),
                "engine": "tractor",
            }
