#!/usr/bin/env python

import os
from time import sleep
from localfarm.localFarmClient import Task, Job, LocalFarmClient
from localfarm.localFarmLauncher import FarmLauncher
from collections import defaultdict
from typing import List


class TestLocalFarm:
    def __init__(self, farmPath):
        self.launcher = FarmLauncher(root=farmPath)
        self.client = LocalFarmClient(farmPath)

    def prepare(self):
        self.launcher.clean()
        self.launcher.start()

    def createTask(self, job: Job, i: int, sleepTime=2, dependencies: List[Task] = None):
        dependencies = dependencies or []
        task = Task(f"Task {i}", f"echo 'Hello from Task {i}' && sleep {sleepTime}")
        job.addTask(task)
        for parentTask in dependencies:
            job.addTaskDependency(task, parentTask)
        return task

    def expandTask(self, jid, tid, n=2):
        for i in range(n):
            task = Task(f"Expanded Task {i}", f"echo 'Hello from Expanded Task {i}' && sleep 5")
            self.client.create_additional_task(jid, tid, task)

    def getTasksByStatus(self, jid: int):
        jobInfo = self.client.get_job_status(jid)
        if not jobInfo:
            return {}
        taskByStatus = defaultdict(set)
        for task in jobInfo.get("tasks", []):
            status = task.get("status", "UNKNOWN")
            taskByStatus[status].add(task.get("tid"))
        return dict(taskByStatus)

    def run(self):
        # Create job
        job = Job("Example Job")
        job.setClient(self.client)
        # Add tasks
        task1 = self.createTask(job, 1, sleepTime=2, dependencies=[])
        task2 = self.createTask(job, 2, sleepTime=2, dependencies=[task1])
        task3 = self.createTask(job, 3, sleepTime=2, dependencies=[task1])
        task4 = self.createTask(job, 4, sleepTime=2, dependencies=[task2, task3])
        task5 = self.createTask(job, 5, sleepTime=2, dependencies=[task4])
        # Submit job
        res = job.submit()
        jid = res['jid']
        # Monitor job
        currentRunningTids = set()
        hasExpanded = False
        while True:
            sleep(1)
            tasks = self.getTasksByStatus(jid)
            if not tasks:
                print("No tasks found for job")
                break
            runningTids = tasks.get("RUNNING")
            activeTasks = tasks.get("SUBMITTED", set()).union(tasks.get("RUNNING", set()))
            if not activeTasks:
                print("All tasks completed")
                break
            if runningTids:
                runningTids = [int(t) for t in runningTids]
                newRunningTasks = set(runningTids)
                if currentRunningTids != newRunningTasks:
                    print(f"Now running tasks: {runningTids} (active tasks: {activeTasks})")
                    currentRunningTids = newRunningTasks
                expandingTid = 5
                if not hasExpanded and expandingTid in runningTids:
                    hasExpanded = True
                    print(f"Expanding task {expandingTid}")
                    self.expandTask(jid, expandingTid, n=2)

    def finish(self):
        self.client.disconnect()
        self.launcher.stop()
        # self.launcher.clean()


def test():
    farm_path = os.getenv("MR_LOCAL_FARM_PATH", os.path.join(os.path.expanduser("~"), ".local_farm"))
    # farm_path = "/s/prods/mvg/_source_global/users/sonoleta/tmp/local_farm"
    _test = TestLocalFarm(farm_path)
    try:
        _test.prepare()
        _test.run()
    except Exception as e:
        print(f"Test failed: {e}")
        _test.finish()
        raise e
    finally:
        _test.finish()


if __name__ == "__main__":
    test()
