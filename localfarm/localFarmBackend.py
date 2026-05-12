#!/usr/bin/env python

"""
Local Farm : A simple local job runner
"""

import os
import sys
import random
import argparse
import json
import shlex
import time
import signal
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Union, Dict, List
from enum import Enum
# For the tcp server
import threading
from socketserver import BaseRequestHandler, ThreadingTCPServer

FARM_MAX_PARALLEL_TASKS = 10
MAX_BYTES_REQUEST = 4096  # 8192 / 65536 if needed

PathLike = Union[str, Path]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(name)s][%(levelname)s] %(message)s'
)
logger = logging.getLogger("LocalFarmBackend")
logger.setLevel(logging.DEBUG)


class Status(Enum):
    NONE = 0
    SUBMITTED = 1
    RUNNING = 2
    ERROR = 3
    STOPPED = 4
    KILLED = 5
    SUCCESS = 6
    PAUSED = 7


class Task:
    def __init__(self, jid: str, tid: str, label: str, command: str, metadata: dict, jobDir: PathLike, env: dict = None):
        self.jid: str = jid
        self.tid: str = tid
        self.parentTids = []  # Tasks that must be completed before this one
        self.childTids = []   # Task that depend on this one
        self.label: str = label
        self.command: str = command
        self.metadata: dict = metadata or {}
        self.env: dict = env or {}
        self.taskDir: Path = Path(jobDir) / "tasks"
        self.taskDir.mkdir(parents=True, exist_ok=True)
        self.status: Status = Status.NONE
        self.created_at = datetime.now()
        self.started_at = None
        self.finished_at = None
        self.returnCode = None
        self.process = None
        self.logFile: Path = self.taskDir / f"{tid}.log"
    
    @property
    def duration_string(self):
        end_time = self.finished_at or datetime.now()
        if not self.started_at:
            return 0
        return str(end_time - self.started_at)

    def to_dict(self):
        return {
            "jid": self.jid,
            "tid": self.tid,
            "label": self.label,
            "command": self.command,
            "metadata": self.metadata,
            "env": self.env,
            "status": self.status.name,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "returnCode": self.returnCode
        }


class Job:
    def __init__(self, jid: str, label: str, farmRoot: PathLike, maxParallel: int=4):
        self.jid: str = jid
        self.label: str = label
        self.submitted: bool = False
        self.jobDir: Path = Path(farmRoot) / "jobs" / str(jid)
        self.jobDir.mkdir(parents=True, exist_ok=True)
        self.lastJid = 0
        self.status: Status = Status.NONE
        self.created_at = datetime.now()
        self.started_at = None
        self.tasks: List[Task] = []
        self.maxParallel: int = maxParallel
        # Runtime tasks status
        self.__stoppedTasks = []

    def to_dict(self):
        return {
            "jid": self.jid,
            "label": self.label,
            "submitted": self.submitted,
            "status": self.status.name,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "tasks": [t.to_dict() for t in self.tasks],
            "maxParallel": self.maxParallel
        }

    @property
    def errorLogs(self):
        errorLog = ""
        for task in self.tasks:
            if task.status in (Status.ERROR, Status.STOPPED, Status.KILLED):
                errorLog += f"Task {task.tid} failed :\n{task.logFile.read_text()}\n"
        return errorLog

    @property
    def rootTasks(self):
        return [t for t in self.tasks if len(t.parentTids) == 0]

    def addTaskDependency(self, parentTask: Task, childTask: Task):
        parentTask.childTids.append(childTask.tid)
        childTask.parentTids.append(parentTask.tid)

    def canStartTask(self, task: Task):
        for parentTid in task.parentTids:
            parentTask = next((t for t in self.tasks if t.tid == parentTid), None)
            if parentTask and parentTask.status != Status.SUCCESS:
                return False
        return True

    def getNextTaskToProcess(self):
        # TODO : better to use the DFS implemented in localFarm.py
        # Function to explore tasks
        def exploreTask(task):
            if task.status == Status.SUBMITTED:
                return task
            if task.status != Status.SUCCESS:
                return None
            children = [t for t in self.tasks if t.tid in task.childTids]
            for taskCandidate in children:
                submittedTask = exploreTask(taskCandidate)
                if submittedTask:
                    return submittedTask
            return None
        for task in self.rootTasks:
            submittedTask = exploreTask(task)
            if submittedTask:
                return submittedTask
        return None

    def start(self):
        self.status = Status.RUNNING
        self.started_at = datetime.now()
        for task in self.tasks:
            task.status = Status.SUBMITTED

    def updateStatusFromTasks(self):
        for task in self.tasks:
            if task.status in (Status.ERROR, Status.STOPPED, Status.KILLED):
                self.status = Status.STOPPED
                return
            elif task.status == Status.RUNNING:
                self.status = Status.RUNNING
                return

    def interrupt(self):
        logger.info(f"Interrupt job {self.jid}")
        self.status = Status.STOPPED
        for task in self.tasks:
            if task.status == Status.RUNNING and task.process:
                logger.info(f"Interrupt task {task.tid}")
                self.__stoppedTasks.append(task)
                task.process.terminate()
                task.status = Status.STOPPED
        logger.info(f"Job {self.jid} interrupted")

    def restart(self):
        self.interrupt()
        self.start()

    def restartErrorTasks(self):
        self.status = Status.RUNNING
        for task in self.tasks:
            if task.status in (Status.ERROR, Status.STOPPED, Status.KILLED):
                task.status = Status.SUBMITTED

    def resume(self):
        logger.info(f"Resume job {self.jid}")
        self.status = Status.RUNNING
        for task in self.__stoppedTasks:
            if task.status == Status.STOPPED:
                task.status = Status.SUBMITTED
        self.__stoppedTasks = []

    def stopTask(self, tid):
        for task in self.tasks:
            if task.tid == tid:
                if task.process and task.process.poll() is None:
                    task.process.terminate()
                task.status = Status.STOPPED
                logger.info(f"Task {tid} stopped")
                return True
        return False

    def skipTask(self, tid):
        task = next((t for t in self.tasks if t.tid == tid), None)
        if not task:
            return False
        task.status = Status.SUCCESS
        if task.process and task.process.poll() is None:
            task.process.terminate()
        logger.info(f"Task {tid} skipped")
        return True

    def restartTask(self, tid):
        for task in self.tasks:
            if task.tid == tid:
                if task.process and task.process.poll() is None:
                    task.process.terminate()
                task.status = Status.SUBMITTED
                task.started_at = None
                task.finished_at = None
                task.return_code = None
                task.process = None
                logger.info(f"Task {tid} rescheduled")
                return True
        return False


class LocalFarmEngine:
    def __init__(self, root: PathLike, maxParallel: int = FARM_MAX_PARALLEL_TASKS):
        self.root: Path = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        # Jobs
        self.jobs: Dict[int, Job] = {}
        self.lastJid = 0
        self.running = False
        self.lock = threading.RLock()
        # PID file
        self.pidFile = self.root / "farm.pid"
        self.pidFile.write_text(str(os.getpid()))
        # Socket path
        self.tcpPortFile = self.root / "backend.port"
        logger.info(f"Backend initialized at {self.root}")
        self.maxParallel: int = maxParallel

    def start(self):
        """ Start the server. """
        logger.info(f"Starting the server...")
        # Start the server to listen to queries
        self.running = True
        handler = lambda *args: LocalFarmRequestHandler(self, *args)
        self.server = ThreadingTCPServer(('localhost', 0), handler)
        port = self.server.server_address[1]
        self.tcpPortFile.write_text(str(port))
        logger.info(f"Server listening on TCP port: {port}")
        # Start server in separate thread
        serverThread = threading.Thread(target=self.server.serve_forever, daemon=True)
        serverThread.start()
        # Start task processor
        processThread = threading.Thread(target=self.taskRunner, daemon=True)
        processThread.start()
        # Wait for shutdown signal
        signal.signal(signal.SIGTERM, self.signalHandler)
        signal.signal(signal.SIGINT, self.signalHandler)
        try:
            while self.running:
                time.sleep(1)
        finally:
            self.cleanup()

    def signalHandler(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def taskRunner(self):
        """Background thread that processes tasks"""
        while self.running:
            try:
                with self.lock:
                    self.processJobs()
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Error in task processor: {e}", exc_info=True)

    def processJobs(self):
        """ Process all active jobs. """
        runningTasks = defaultdict(list)
        tasksToStart = defaultdict(list)
        for job in self.jobs.values():
            job.updateStatusFromTasks()
            if not job.submitted or job.status in [Status.PAUSED, Status.SUCCESS, Status.STOPPED]:
                continue
            elif job.status == Status.SUBMITTED:
                job.start()
            # Update running tasks
            runningTasks[job.jid] = [t for t in job.tasks if t.status == Status.RUNNING]
            # Update tasks to start
            for task in job.tasks:
                if task.status == Status.SUBMITTED:
                    if job.canStartTask(task):
                        tasksToStart[job].append(task)
                elif task.status == Status.RUNNING and task.process:
                    # Check if process finished
                    returncode = task.process.poll()
                    if returncode is not None:
                        self.finishTask(task, returncode)

            # Check if job is complete
            if any(t.status in [Status.ERROR, Status.STOPPED, Status.KILLED] for t in job.tasks):
                job.status = Status.ERROR
                logger.error(f"Job {job.jid} failed !")
            elif all(t.status in [Status.SUCCESS, Status.NONE] for t in job.tasks):
                job.status = Status.SUCCESS
                logger.info(f"Job {job.jid} finished !")
            # else : keep running or paused

        # Launch tasks
        nbRunningTasks = sum(len(tasks) for tasks in runningTasks.values())
        tasks = []
        for job, jobTasks in tasksToStart.items():
            # while True:
            #     nextTask = job.getNextTaskToProcess()
            #     if not nextTask:
            #         break
            for task in jobTasks:
                tasks.append((job, task))
        random.shuffle(tasks)  # Randomize task order to be fair between jobs
        for job, task in tasks:
            nbJobRunningTasks = len(runningTasks[job.jid])
            if job.maxParallel > nbJobRunningTasks and self.maxParallel > nbRunningTasks:
                nbRunningTasks += 1
                nbJobRunningTasks += 1
                self.startTask(task)

    def startTask(self, task: Task):
        """ Start a task process. """
        logger.info(f"Starting task {task.tid}: {task.command}")
        task.status = Status.RUNNING
        task.started_at = datetime.now()
        # Create log file
        additional_env = {
            "LOCALFARM_CURRENT_JID": str(task.jid),
            "LOCALFARM_CURRENT_TID": str(task.tid),
            "MR_LOCAL_FARM_PATH": str(self.root)
        }
        additional_env.update(task.env)
        process_env = os.environ.copy()
        process_env.update(additional_env)
        try:

            with open(task.logFile, "w") as log:
                log.write(f"# ========== Starting task {task.tid} at {task.started_at.isoformat()}"
                          f" (command=\"{task.command}\") ==========\n")
                log.write(f"# metadata: {task.metadata}\n")
                log.write(f"# process_env:\n")
                log.write(f"# Additional env variables:\n")
                for _k, _v in additional_env.items():
                    log.write(f"# - {str(_k)}={str(_v)}\n")
                log.write(f"\n")
                task.process = subprocess.Popen(
                    task.command,
                    # shlex.split(task.command),
                    stdout=log,
                    stderr=log,
                    cwd=task.taskDir,
                    env=process_env,
                    shell=True
                )
        except Exception as e:
            logger.error(f"Failed to start task {task.tid}: {e}")
            task.status = "error"
            task.finished_at = datetime.now()

    def finishTask(self, task: Task, returncode: int):
        task.finished_at = datetime.now()
        task.return_code = returncode
        if returncode == 0:
            task.status = Status.SUCCESS
            logger.info(f"Task {task.tid} completed after {task.duration_string}")
        else:
            task.status = Status.ERROR
            logger.error(f"Task {task.tid} failed with code {returncode}")
        with open(task.logFile, "a") as log:
            log.write(f"\n# ========== Task {task.tid} finished at {task.finished_at.isoformat()} with status {task.status} ==========\n")

    def cleanup(self):
        logger.info("Cleaning up...")
        with self.lock:
            for job in self.jobs.values():
                for task in job.tasks:
                    if task.process and task.process.poll() is None:
                        logger.info(f"Terminating task {task.tid}")
                        task.process.terminate()
                        try:
                            task.process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            task.process.kill()
        self.server.shutdown()
        self.pidFile.unlink(missing_ok=True)
        logger.info("Cleanup complete")

    # ======================
    # API Calls
    # ======================

    # Author

    def create_job(self, name):
        """ Create a new job. """
        with self.lock:
            # Generate new jid
            self.lastJid += 1
            jid = self.lastJid
            try:
                job = Job(jid, label=name, farmRoot=self.root)
            except Exception as err:
                return {"success": False, "error": str(err)}
            self.jobs[jid] = job
            logger.info(f"Created job {jid}")
            return {"success": True, "jid": jid}

    def create_task(self, jid, name, command, metadata, dependencies, env=None):
        """ Add a task to a job. """
        with self.lock:
            if jid not in self.jobs:
                return {"success": False, "error": "Job not found"}
            job = self.jobs[jid]
            job.lastJid += 1
            tid = job.lastJid
            task = Task(jid, tid, name, command, metadata, job.jobDir, env=env)
            job.tasks.append(task)
            for parentTid in dependencies:
                parentTask = next((t for t in job.tasks if t.tid == parentTid), None)
                if parentTask:
                    job.addTaskDependency(parentTask, task)
                else:
                    logger.warning(f"Task {tid} : Cannot add dependency to {parentTid}, task not found in job {jid}")
            logger.info(f"Added task {tid} to job {jid}")
            return {"success": True, "tid": tid}

    def expand_task(self, jid, name, command, metadata, parentTid, env=None):
        with self.lock:
            if jid not in self.jobs:
                logger.info(f"Available jobs: {list(self.jobs.keys())}")
                return {"success": False, "error": "Job not found"}
            job = self.jobs[jid]
            job.lastJid += 1
            tid = job.lastJid
            task = Task(jid, tid, name, command, metadata, job.jobDir, env=env)
            task.status = Status.SUBMITTED
            job.tasks.append(task)
            parentTask = next((t for t in job.tasks if t.tid == parentTid), None)
            if not parentTask:
                logger.error(f"Could not expand task {parentTid} : cannot find it in the job {job} ({jid})")
                return {"success": False, "error": f"Parent task {parentTid} not found in job {jid}"}
            for childTid in parentTask.childTids:
                childTask = next((t for t in job.tasks if t.tid == childTid), None)
                if not childTask:
                    logger.error(f"Could not find expanded task child {childTid}")
                job.addTaskDependency(task, childTask)
            logger.info(f"Added expanded task {tid} to job {jid}")
            return {"success": True, "tid": tid}

    def submit_job(self, jid):
        """ Create a new job. """
        with self.lock:
            if jid not in self.jobs:
                return {'success': False, "error": "Job not found"}
            try:
                job = self.jobs[jid]
                job.submitted = True
                job.status = Status.SUBMITTED
            except Exception as err:
                return {"success": False, "error": str(err)}
            logger.info(f"Submitted job {jid}")
            return {"success": True, "jid": jid}

    # Query

    def get_job_info(self, jid):
        """ Get job status. """
        with self.lock:
            if jid not in self.jobs:
                return {'success': False, "error": "Job not found"}
            job = self.jobs[jid]
            return {"success": True, "result": job.to_dict()}

    def get_job_errors(self, jid):
        """ Get job error logs. """
        with self.lock:
            if jid not in self.jobs:
                return {'success': False, "error": "Job not found"}
            job = self.jobs[jid]
            return {"success": True, "result": job.errorLogs}

    def pause_job(self, jid):
        """ Pause a job. """
        with self.lock:
            if jid not in self.jobs:
                return {"success": False, "error": "Job not found"}
            self.jobs[jid].status = Status.PAUSED
            logger.info(f"Job {jid} paused")
            return {"success": True}

    def unpause_job(self, jid):
        """ Resume a job. """
        with self.lock:
            if jid not in self.jobs:
                return {"success": False, "error": "Job not found"}
            self.jobs[jid].resume()
            return {"success": True}

    def interrupt_job(self, jid):
        """ Interrupt a job and kill running tasks. """
        with self.lock:
            if jid not in self.jobs:
                return {"success": False, "error": "Job not found"}
            self.jobs[jid].interrupt()
            return {"success": True}

    def restart_job(self, jid):
        """ Restarts a job and kill running tasks. """
        with self.lock:
            if jid not in self.jobs:
                return {"success": False, "error": "Job not found"}
            self.jobs[jid].restart()
            return {"success": True}

    def restart_error_tasks(self, jid):
        """ Restarts all error tasks in the job. """
        with self.lock:
            if jid not in self.jobs:
                return {"success": False, "error": "Job not found"}
            self.jobs[jid].restartErrorTasks()
            return {"success": True}

    def stop_task(self, jid, tid):
        """ Stop a specific task. """
        with self.lock:
            if jid not in self.jobs:
                return {"success": False, "error": "Job not found"}
            res = self.jobs[jid].stopTask(tid)
            if res:
                return {"success": True}
            else:
                return {"success": False, "error": "Task not found"}

    def skip_task(self, jid, tid):
        """ Stop a specific task. """
        with self.lock:
            if jid not in self.jobs:
                return {"success": False, "error": "Job not found"}
            res = self.jobs[jid].skipTask(tid)
            if res:
                return {"success": True}
            else:
                return {"success": False, "error": "Task not found"}

    def restart_task(self, jid, tid):
        """ Restart a task. """
        with self.lock:
            if jid not in self.jobs:
                return {"success": False, "error": "Job not found"}
            res = self.jobs[jid].restartTask(tid)
            if res:
                return {"success": True}
            else:
                return {"success": False, "error": "Task not found"}

    def list_jobs(self):
        """ List all jobs. """
        with self.lock:
            return {
                "success": True,
                "jobs": [job.to_dict() for job in self.jobs.values()]
            }


class LocalFarmRequestHandler(BaseRequestHandler):
    """ Handle requests. """

    def __init__(self, backend, *args, **kwargs):
        self.backend = backend
        super().__init__(*args, **kwargs)

    @property
    def pid(self):
        return self.server.server_address[1]

    def handle(self):
        """ Handle incoming requests (multiple per connection). """
        logger.debug("Connected to client")
        while True:
            try:
                connected = self.__read_and_answer_request()
                if not connected:
                    logger.debug("Disconnected from client")
                    return
            except ConnectionResetError:
                # Client disconnected abruptly
                logger.debug("Connection has been reset")
                return
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received: {e}")
                response = {"success": False, "error": "Invalid JSON"}
                self.request.sendall((json.dumps(response) + '\n').encode('utf-8'))
            except Exception as e:
                logger.error(f"Error handling request: {e}", exc_info=True)
                return
    
    def __read_and_answer_request(self):
        """ Read request, get response and send response """
        data = b""
        while True:
            token = self.request.recv(MAX_BYTES_REQUEST)
            if not token:
                # Client disconnected
                return False
            data += token
            if b"\n" in token:
                break
        if not data:
            return False
        request = json.loads(data.decode("utf-8"))
        logger.debug(f"Received request: {request}")
        # Dispatch method
        method = request.get("method")
        params = request.get("params", {})
        if not hasattr(self.backend, method):
            response = {"success": False, "error": f"Unknown request: {method}"}
        else:
            try:
                result = getattr(self.backend, method)(**params)
                response = result
            except Exception as e:
                logger.error(f"Error executing {method}: {e}", exc_info=True)
                response = {'success': False, 'error': str(e)}
        # Send response
        response_data = json.dumps(response) + '\n'
        self.request.sendall(response_data.encode('utf-8'))
        return True


def main(root):
    # Daemonize
    if os.fork() > 0:
        sys.exit(0)
    os.setsid()
    if os.fork() > 0:
        sys.exit(0)

    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    with open(os.devnull, 'r') as devnull:
        os.dup2(devnull.fileno(), sys.stdin.fileno())

    backend = LocalFarmEngine(root=root)
    backend.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Execute a Graph of processes.')
    parser.add_argument('--root', type=str, required=False, help='Root path for the farm.')
    args = parser.parse_args()
    root = args.root
    if not root:
        root = os.getenv("MR_LOCAL_FARM_PATH", os.path.join(os.path.expanduser("~"), ".local_farm"))
    main(root)
