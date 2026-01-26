#!/usr/bin/env python

"""
Launch :

>>> python farmLauncher.py $MR_LOCAL_FARM_PATH start
>>> python test.py
>>> python farmLauncher.py $MR_LOCAL_FARM_PATH stop

"""

import os
from localFarm import Task, Job, LocalFarmEngine

farm_path = os.getenv("MR_LOCAL_FARM_PATH", os.path.join(os.path.expanduser("~"), ".local_farm"))

def expand(jid, tid):
    farm = LocalFarmEngine(farm_path)
    task = Task("Expanded Task 1", "echo 'Hello from Expanded Task1' && sleep 5")
    farm.create_additional_task(jid, tid, task)
    task = Task("Expanded Task 2", "echo 'Hello from Expanded Task2' && sleep 5")
    farm.create_additional_task(jid, tid, task)

job = Job("Example Job")

task1 = Task("Task 1", "echo 'Hello from Task 1' && sleep 10")
job.addTask(task1)
task2 = Task("Task 2", "echo 'Hello from Task 2' && sleep 10")
job.addTask(task2)
task3 = Task("Task 3", "echo 'Hello from Task 3' && sleep 10")
job.addTask(task3)
task4 = Task("Task 4", "echo 'Hello from Task 4' && sleep 10")
job.addTask(task4)
task5 = Task("Task 5", "echo 'Hello from Task 5' && sleep 10")
job.addTask(task5)

job.addTaskDependency(task2, task1)
job.addTaskDependency(task3, task1)
job.addTaskDependency(task4, task2)
job.addTaskDependency(task4, task3)
job.addTaskDependency(task5, task4)

job.submit(farm_path)
