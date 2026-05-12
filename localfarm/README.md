# Meshroom Local Farm

This folder contains a local farm tool for Meshroom. It can be used in various ways:
- For testing we setup and launch the farm backend process and use it to test the submitting process
- We also added a submitter to be able to use it inside Meshroom

> [!NOTE]  
> Note that the local farm only works on Unix for now because we use `fork` for daemonization.
> We could implement the [`DETACHED_PROCESS`](https://stackoverflow.com/a/12854376) flag with `subprocess.Popen`
> to handle the farm on Windows.

## How to use

### Launch

First launch the farm process
```sh
python localfarm/localFarmLauncher.py start --root <FARM_ROOT>
```

The `FARM_ROOT` folder will contain the logs for each process and for the main process.

### Commands

- _start_: Launch the farm
- _clean_: Clean the files
- _stop_: Stop the farm process
- _restart_: Restart the farm process
- _status_: Check the status
- _fullInfo_: Display additional info

### Add jobs

The `test.py` script can be used to find examples on how to use it.
Basically here's how to create jobs and tasks:

```py
import os
import datetime
from time import sleep
from collections import defaultdict
from localfarm.localFarm import Task, Job, LocalFarmEngine

def now():
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S ")

def createTask(job, command, dependencies=[], _tasks=[]):
    i = len(_tasks)
    task = Task(f"Task {i}", f"echo '> Task {i}' && {command}")
    job.addTask(task)
    for parentTask in dependencies:
        job.addTaskDependency(task, parentTask)
    return task

def getTasksByStatus(jid):
    jobInfo = engine.get_job_status(jid)
    if not jobInfo:
        return {}
    taskByStatus = defaultdict(set)
    for task in jobInfo.get("tasks", []):
        status = task.get("status", "UNKNOWN")
        taskByStatus[status].add(task.get("tid"))
    return dict(taskByStatus)

# Get engine
engine = LocalFarmEngine(FARM_ROOT)
# Create job
job = Job("Example Job")
job.setEngine(engine)
# Add tasks
task1 = createTask(job, command="sleep 2", dependencies=[])
task2 = createTask(job, command="sleep 2", dependencies=[task1])
task3 = createTask(job, command="sleep 2", dependencies=[task1])
task4 = createTask(job, command="sleep 2", dependencies=[task2, task3])
task5 = createTask(job, command="sleep 2", dependencies=[task4])
# Submit job
res = job.submit()
jid = res['jid']
print(now() + f"-> job: {res}")

# Monitor job
currentRunningTids = set()
while True:
    sleep(1)
    tasks = getTasksByStatus(jid)
    if not tasks:
        print("No tasks found for job")
        break
    runningTids = tasks.get("RUNNING")
    activeTasks = tasks.get("SUBMITTED", set()).union(tasks.get("RUNNING", set()))
    if not activeTasks:
        print(now() + "All tasks completed")
        break
    if runningTids:
        runningTids = [int(t) for t in runningTids]
        newRunningTasks = set(runningTids)
        if currentRunningTids != newRunningTasks:
            print(now() + f"Now running tasks: {runningTids} (active tasks: {activeTasks})")
            currentRunningTids = newRunningTasks
```

And this gives:

```
10:54:36 -> job: {'jid': 1}
10:54:37 Now running tasks: [1] (active tasks: {1, 2, 3, 4, 5})
10:54:39 Now running tasks: [2, 3] (active tasks: {2, 3, 4, 5})
10:54:41 Now running tasks: [4] (active tasks: {4, 5})
10:54:44 Now running tasks: [5] (active tasks: {5})
10:54:47 All tasks completed
```

### Launch the backend from a python process

Instead of using the command line you can also use the launcher as an API:

```py
from localfarm.localFarmLauncher import FarmLauncher

# Launch
launcher = FarmLauncher(root=FARM_ROOT)
launcher.start()
# Add jobs & tasks & submit
...

# Check status
launcher.status()

# Stop the farm
launcher.stop()
```

And here are the logs:
```
<!-- Launch -->
Clean farm files...
Done.
Starting farm backend...
Farm root is: /homes/$USER/.local_farm
Farm backend started (PID: 6776)
Logs: /homes/$USER/.local_farm/backend.log

<!-- Interrogate status -->
Farm backend is running (PID: 6776)
[LocalFarm][INFO] Connect to farm located at FARM_ROOT
Active jobs: 1
  - 1: RUNNING (5 tasks) -> {'SUCCESS': {1}, 'RUNNING': {2, 3}, 'SUBMITTED': {4, 5}}

<!-- Stop the farm -->
Stopping farm backend (PID: 6776)...
Farm backend stopped
```

## Logs

Here are the files we can find on the farm root:
```
.
├── backend.log
├── backend.port
├── farm.pid
└── jobs
    └── jid
        └── tasks
            ├── tid_min.log
            ├── ...
            └── tid_max.log
```

- _backend.log_ contains the logs for the backend process
- _farm.pid_ contains the PID for the backend process
- _backend.port_ contains the port used for the TCP connection
- In the "jobs" folder, you can find all logs for the tasks of each job. The structure is: `jobs/{jid}/tasks/{tid}.log`
