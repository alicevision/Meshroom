#!/usr/bin/env python

"""
Local Farm : A simple local job runner
"""

from __future__ import annotations  # For forward references in type hints

import logging
import json
import socket
import uuid
import traceback
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Generator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s][%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger("LocalFarm")
logger.setLevel(logging.INFO)


class LocalFarmClient:
    """ Client to communicate with the farm backend. """

    def __init__(self, root):
        self.root = Path(root)
        self.tcpPortFile = self.root / "backend.port"
        self._sock = None

    def connect(self):
        """ Connect to the backend. """
        if self._sock is not None:
            return self._sock

        logger.info(f"Connect to farm located at {self.root}")
        if self.tcpPortFile.exists():
            try:
                port = int(self.tcpPortFile.read_text())
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(("localhost", port))
                self._sock = sock
                return sock
            except Exception as e:
                logger.error(f"Could not connect via TCP: {e}")
                raise ConnectionError("Cannot connect to farm backend")
        raise ConnectionError("Farm backend not found")

    def reconnect(self):
        logger.info("Reconnecting client")
        self._sock = None
        return self.connect()

    def disconnect(self):
        """Explicitly close the connection."""
        logger.info(f"Disconnecting client {self._sock}")
        if self._sock:
            self._sock.close()
            self._sock = None

    def _call(self, method, **params):
        """ Make an query to the backend. """
        request = {
            "method": method,
            "params": params
        }
        def get_response(sock):
            response_data = b""
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk
                if b"\n" in chunk:
                    break
            response = json.loads(response_data.decode("utf-8"))
            if not response.get("success"):
                raise RuntimeError(response.get("error", "Unknown error"))
            return response
        try:
            sock = self.connect()
            # Send request
            request_data = json.dumps(request) + "\n"
            sock.sendall(request_data.encode("utf-8"))
            return get_response(sock)
        except (BrokenPipeError, ConnectionResetError):
            # Connection lost, try to reconnect once
            sock = self.reconnect()
            request_data = json.dumps(request) + "\n"
            sock.sendall(request_data.encode("utf-8"))
            return get_response(sock)
        except Exception as err:
            logger.error(f"Could not send request: {err}\n" + "\n".join(traceback.format_stack()))

    def submit_job(self, job: Job):
        """ Submit the job to the farm. """
        # Create the job
        createdJob = self._call("create_job", name=job.name)
        jid = createdJob["jid"]
        # Create the tasks
        tasksCreated = {}
        for task in job.tasksDFS():
            parentTasks = job.getTaskDependencies(task)
            deps = []
            for parentTask in parentTasks:
                if parentTask not in tasksCreated:
                    raise RuntimeError(f"Parent task {parentTask.name} not created yet")
                deps.append(tasksCreated[parentTask])
            createdTask = self._call("create_task",
                jid=jid, name=task.name, command=task.command,
                metadata=task.metadata, dependencies=deps, env=task.env)
            tasksCreated[task] = createdTask["tid"]
        # Submit the job
        self._call("submit_job", jid=jid)
        return {"jid": jid}

    def create_additional_task(self, jid, tid, task):
        """ Create new task in an existing job. """
        createdTask = self._call("expand_task",
            jid=jid, name=task.name, command=task.command,
            metadata=task.metadata, parentTid=tid, env=task.env)
        return {"tid": createdTask["tid"]}

    def get_job_info(self, jid):
        """ Get job status. """
        return self._call("get_job_info", jid=jid)["result"]

    def pause_job(self, jid):
        """ Pause a job. """
        return self._call("pause_job", jid=jid)

    def unpause_job(self, jid):
        """ Resume a job. """
        return self._call("unpause_job", jid=jid)

    def interrupt_job(self, jid):
        """ Interrupt a job. """
        return self._call("interrupt_job", jid=jid)

    def restart_job(self, jid):
        """ Restart a job. """
        return self._call("restart_job", jid=jid)

    def restart_error_tasks(self, jid):
        """ Restart error tasks. """
        return self._call("restart_error_tasks", jid=jid)

    def stop_task(self, jid, tid):
        """ Stop a specific task. """
        return self._call("stop_task", jid=jid, tid=tid)

    def skip_task(self, jid, tid):
        """ Stop a specific task. """
        return self._call("skip_task", jid=jid, tid=tid)

    def restart_task(self, jid, tid):
        """ Restart a task. """
        return self._call("restart_task", jid=jid, tid=tid)

    def list_jobs(self) -> list:
        """ List all jobs. """
        return self._call("list_jobs")["jobs"]

    def get_job_status(self, jid: int) -> dict:
        for job in self.list_jobs():
            if job["jid"] == jid:
                return job
        return {}

    def get_job_errors(self, jid: int) -> str:
        """ Get job error logs. """
        return self._call("get_job_errors", jid=jid)["result"]

    def ping(self):
        """ Check if backend is alive. """
        try:
            self.connect().close()
            return True
        except Exception:
            return False


class LocalFarmClientContext(LocalFarmClient):
    def __init__(self, root):
        super().__init__(root)

    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, *args):
        self.disconnect()


class Task:
    def __init__(self, name, command, metadata=None, env=None):
        print(f"Create task with command {command}")
        self.uid = str(uuid.uuid1())
        self.name = name
        self.command = command
        self.metadata = metadata or {}
        self.env = env or {}

    def __repr__(self):
        return f"<Task {self.name}|{self.uid}>"

    def __hash__(self):
        return hash(self.uid)


class Job:
    def __init__(self, name):
        self.name = name
        self.tasks: Dict[str, Task] = {}
        self.dependencies: Dict[str: List[str]] = defaultdict(set)
        self.reverseDependencies: Dict[str: List[str]] = defaultdict(set)
        self._client: LocalFarmClient = None

    def setClient(self, client: LocalFarmClient):
        self._client = client

    def addTask(self, task):
        if task.name in self.tasks:
            raise ValueError(f"Task {task} already exists in job")
        self.tasks[task.uid] = task

    def addTaskDependency(self, task: Task, dependsOn: Task):
        if task.uid not in self.tasks:
            raise ValueError(f"Task {task} not found in job")
        if dependsOn.uid not in self.tasks:
            raise ValueError(f"Task {dependsOn} not found in job")
        self.dependencies[task.uid].add(dependsOn.uid)
        self.reverseDependencies[dependsOn.uid].add(task.uid)
        if self.hasCycle():
            # Rollback
            self.dependencies[task.uid].remove(dependsOn.uid)
            self.reverseDependencies[dependsOn.uid].remove(task.uid)
            raise ValueError("Adding this task creates a cycle in the job dependencies")

    def getTaskDependencies(self, task):
        return [self.tasks[depUid] for depUid in self.dependencies.get(task.uid, [])]

    def getRootTasks(self) -> List[Task]:
        roots = []
        for taskUid, task in self.tasks.items():
            if not self.dependencies.get(taskUid):
                roots.append(task)
        return roots

    def hasCycle(self) -> bool:
        """ Check there are no cycles in the task graph. """
        def exploreTask(taskUid, taskParents=None):
            taskParents = taskParents or set()
            if taskUid in taskParents:
                return True
            childrenParents = taskParents.copy()
            childrenParents.add(taskUid)
            for childUid in self.reverseDependencies[taskUid]:
                failed = exploreTask(childUid, childrenParents)
                if failed:
                    return True
            return False
        # Start from root and explore down
        roots = self.getRootTasks()
        if not roots:
            return True
        for task in roots:
            failed = exploreTask(task.uid)
            if failed:
                return True
        return False

    def tasksDFS(self) -> Generator[Task]:
        """
        Return tasks in topological order (dependencies before dependents).
        Tasks closer to roots appear first.
        """
        taskLevels = {}
        def exploreTask(task: str, currentLevel=0):
            if task in taskLevels:
                if currentLevel > taskLevels[task]:
                    taskLevels[task] = currentLevel
            else:
                taskLevels[task] = currentLevel
            for child in self.reverseDependencies[task]:
                exploreTask(child, currentLevel + 1)
        # Start from root and explore down
        for task in self.getRootTasks():
            exploreTask(task.uid)
        taskByLevel = defaultdict(list)
        for taskUid, level in taskLevels.items():
            taskByLevel[level].append(self.tasks[taskUid])
        levels = sorted(list(taskByLevel.keys()))
        for level in levels:
            tasks = taskByLevel[level]
            for task in tasks:
                yield task

    def submit(self, client: LocalFarmClient = None):
        client = client or self._client
        if client:
            result = client.submit_job(self)
            return result
        else:
            raise ValueError("No LocalFarmClient set for this job")


def test():
    #     _ B - D - F - G - H _
    #    /         /     \     \
    # A -         /       - I -- J
    #    \       /
    #     - C - E - K - L - M
    #                \_____/
    job = Job("job")
    for node in ["F", "B", "K", "J", "A", "M", "L", "E", "C", "D", "G", "H", "I"]:
        job.addTask(Task(node, ""))

    def addTaskDependencies(taskName, parentTaskName):
        task = next(t for t in job.tasks.values() if t.name == taskName)
        parentTask = next(t for t in job.tasks.values() if t.name == parentTaskName)
        job.addTaskDependency(task, parentTask)

    addTaskDependencies("B", "A")
    addTaskDependencies("C", "A")
    addTaskDependencies("D", "B")
    addTaskDependencies("E", "C")
    addTaskDependencies("F", "D")
    addTaskDependencies("C", "L")
    addTaskDependencies("F", "E")
    addTaskDependencies("K", "E")
    addTaskDependencies("M", "K")
    addTaskDependencies("G", "F")
    addTaskDependencies("H", "G")
    addTaskDependencies("I", "G")
    addTaskDependencies("J", "I")
    addTaskDependencies("J", "H")

    print("Tasks order : ", end="")
    for task in job.tasksDFS():
        print(f"{task.name} -> ", end="")
    print("END")
