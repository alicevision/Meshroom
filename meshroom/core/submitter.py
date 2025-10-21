#!/usr/bin/env python

import logging
import operator

from enum import IntFlag, auto
from typing import Optional
from itertools import accumulate

from meshroom.common import BaseObject, Property


logger = logging.getLogger("Submitter")
logger.setLevel(logging.INFO)


class SubmitterOptionsEnum(IntFlag):
    RETRIEVE = auto()       # Can retrieve job (read job tasks, ...)
    INTERRUPT_JOB = auto()  # Can interrupt
    RESUME_JOB = auto()     # Can resume after interruption
    EDIT_TASKS = auto()     # Can edit tasks

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

    def interruptJob(self):
        if self.submitterOptions.includes(SubmitterOptionsEnum.INTERRUPT_JOB):
            raise NotImplementedError("'interruptJob' method must be implemented in subclasses")
        else:
            raise RuntimeError(f"Submitter {self.__class__.__name__} cannot interrupt the job")

    # TODO : interrupt for specific node/chunk

    def resumeJob(self):
        if self.submitterOptions.includes(SubmitterOptionsEnum.RESUME_JOB):
            raise NotImplementedError("'resumeJob' method must be implemented in subclasses")
        else:
            raise RuntimeError(f"Submitter {self.__class__.__name__} cannot resume the job")

    # TODO : resume for specific node/chunk

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

    def createJob(self, nodes, edges, filepath, submitLabel="{projectName}"):
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
        job = self.createJob(nodes, edges, filepath, submitLabel)
        if not job:
            # Failed to create the job
            return None
        return job

    name = Property(str, lambda self: self._name, constant=True)
