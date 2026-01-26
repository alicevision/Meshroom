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

from localFarm import LocalFarmEngine


class FarmLauncher:
    def __init__(self, root=None):
        self.root = Path(root or Path.home() / ".local_farm")
        self.pidFile = self.root / "farm.pid"
        self.logFile = self.root / "backend.log"

    def clean(self):
        """Clean farm backend files"""
        if self.logFile.exists():
            self.logFile.unlink()
        if (self.root / "jobs").exists():
            shutil.rmtree(str((self.root / "jobs")))

    def start(self):
        """Start the farm backend"""
        if self.is_running():
            print("Farm backend is already running")
            return
        self.clean()

        print("Starting farm backend...")
        # Get path to backend script
        backendScript = Path(__file__).parent / "localFarmBackend.py"
        # Start backend as daemon
        with open(self.logFile, 'a') as log:
            subprocess.Popen(
                [sys.executable, str(backendScript), str(self.root)],
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
        """Stop the farm backend"""
        if not self.is_running():
            print("Farm backend is not running")
            return
        
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

    def status(self, allInfos=False):
        """Show status of the farm backend"""
        if self.is_running():
            pid = self.getFarmPid()
            print(f"Farm backend is running (PID: {pid})")
            
            # Try to get job list
            try:
                client = LocalFarmEngine(root=self.root)
                response = client.list_jobs()
                jobs = response.get('jobs', {})
                print(f"Active jobs: {len(jobs)}")
                for jid, job in jobs.items():
                    taskByStatus = defaultdict(set)
                    for task in job['tasks']:
                        status = task.get("status", "UNKNOWN")
                        taskByStatus[status].add(task.get("tid"))
                    print(f"  - {jid}: {job['status']} ({len(job['tasks'])} tasks) -> {dict(taskByStatus)}")
                    if allInfos:
                        for task in job['tasks']:
                            print(f"      * Task {task['tid']}: {task}")
                    print("")
            except Exception as e:
                print(f"Could not get job list: {e}")
        else:
            print("Farm backend is not running")
    
    def is_running(self):
        """Check if backend is running"""
        pid = self.getFarmPid()
        print(f"Check if {pid} is running")
        if pid is None:
            return False
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False

    def getFarmPid(self):
        """Get PID of running backend"""
        if not self.pidFile.exists():
            return None
        try:
            return int(self.pidFile.read_text())
        except:
            return None


def main(root, command):
    launcher = FarmLauncher(root=root)
    if command == 'start':
        return launcher.start()
    elif command == 'stop':
        return launcher.stop()
    elif command == 'restart':
        return launcher.restart()
    elif command == 'status':
        return launcher.status()
    elif command == 'fullInfos':
        return launcher.status(allInfos=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Local Farm Launcher')
    parser.add_argument('root', help='Farm directory path')
    parser.add_argument('command', choices=['start', 'stop', 'restart', 'status', 'fullInfos'], help='Command to execute')
    args = parser.parse_args()
    main(args.root, args.command)
