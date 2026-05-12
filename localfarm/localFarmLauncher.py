#!/usr/bin/env python

import os
import shutil
import sys
import time
import signal
import argparse
from pathlib import Path
import subprocess
from collections import defaultdict

from localfarm.localFarmClient import LocalFarmClient


class FarmLauncher:
    def __init__(self, root=None):
        self.root = Path(root or Path.home() / ".local_farm")
        self.root.mkdir(parents=True, exist_ok=True)
        self.pidFile = self.root / "farm.pid"
        self.logFile = self.root / "backend.log"
        self.__client = None

    @property
    def client(self):
        if self.__client is None:
            self.__client = LocalFarmClient(root=self.root)
        return self.__client

    def clean(self):
        """ Clean farm backend files. """
        print("Clean farm files...")
        if self.logFile.exists():
            self.logFile.unlink()
        if (self.root / "jobs").exists():
            shutil.rmtree(str((self.root / "jobs")))
        if not self.is_running():
            self.pidFile.unlink(missing_ok=True)
            (self.root / "backend.port").unlink(missing_ok=True)
        print("Done.")

    def start(self):
        """ Start the farm backend. """
        if self.is_running():
            print("Farm backend is already running")
            return
        self.clean()

        print("Starting farm backend...")
        print(f"Farm root is: {self.root}")
        # Get path to backend script
        backendScript = Path(__file__).parent / "localFarmBackend.py"
        # Start backend as daemon
        with open(self.logFile, 'a') as log:
            subprocess.Popen(
                [sys.executable, str(backendScript), "--root", str(self.root)],
                stdout=log,
                stderr=log,
                # stderr=subprocess.PIPE,
                start_new_session=True
            )

        # Wait for it to start
        for _ in range(10):
            time.sleep(0.5)
            if self.is_running():
                print(f"Farm backend started (PID: {self.getFarmPid()})")
                print(f"Logs: {self.logFile}")
                return

        print("Failed to start farm backend")
        sys.exit(1)

    def stop(self):
        """ Stop the farm backend. """
        if not self.is_running():
            print("Farm backend is not running")
            return

        if self.__client:
            self.__client.disconnect()
            self.__client = None

        pid = self.getFarmPid()
        print(f"Stopping farm backend (PID: {pid})...")

        try:
            os.kill(pid, signal.SIGTERM)

            # Wait for it to stop
            for _ in range(10):
                time.sleep(0.5)
                if not self.is_running():
                    print("Farm backend stopped")
                    return

            # Force kill if still running
            print("Force killing farm backend...")
            os.kill(pid, signal.SIGKILL)

        except ProcessLookupError:
            print("Backend process not found")
            self.pidFile.unlink(missing_ok=True)

    def restart(self):
        """Restart the farm backend"""
        self.stop()
        time.sleep(1)
        self.start()

    def getJobsInfo(self):
        if self.is_running():
            # Try to get job list
            try:
                jobs = self.client.list_jobs()
                return jobs
            except Exception as e:
                raise ValueError(f"Could not fetch jobs: {e}")
        else:
            print("Farm backend is not running")
            return []

    def status(self, allInfo=False):
        """ Show status of the farm backend. """
        if self.is_running():
            pid = self.getFarmPid()
            print(f"Farm backend is running (PID: {pid})")

            # Try to get job list
            try:
                jobs = self.client.list_jobs()
                print(f"Active jobs: {len(jobs)}")
                for job in jobs:
                    jid = job.get("jid")
                    taskByStatus = defaultdict(set)
                    for task in job['tasks']:
                        status = task.get("status", "UNKNOWN")
                        taskByStatus[status].add(task.get("tid"))
                    print(f"  - {jid}: {job['status']} ({len(job['tasks'])} tasks) -> {dict(taskByStatus)}")
                    if allInfo:
                        for task in job['tasks']:
                            print(f"      * Task {task['tid']}: {task}")
                    print("")
            except Exception as e:
                print(f"Could not get job list: {e}")
        else:
            print("Farm backend is not running")

    def is_running(self):
        """ Check if backend is running. """
        pid = self.getFarmPid()
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False

    def getFarmPid(self):
        """ Get PID of running backend. """
        if not self.pidFile.exists():
            return None
        try:
            return int(self.pidFile.read_text())
        except Exception:
            return None


def main(root, command):
    launcher = FarmLauncher(root=root)
    if command == 'clean':
        return launcher.clean()
    if command == 'start':
        return launcher.start()
    elif command == 'stop':
        return launcher.stop()
    elif command == 'restart':
        return launcher.restart()
    elif command == 'status':
        return launcher.status()
    elif command == 'fullInfo':
        return launcher.status(allInfo=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Local Farm Launcher')
    parser.add_argument('command',
                        choices=['clean', 'start', 'stop', 'restart', 'status', 'fullInfo'],
                        help='Command to execute')
    parser.add_argument('--root', required=False, help='Farm directory path')
    args = parser.parse_args()

    root = args.root
    if not root:
        root = os.getenv("MR_LOCAL_FARM_PATH", os.path.join(os.path.expanduser("~"), ".local_farm"))

    main(root, args.command)
