from __future__ import annotations

import logging
import time

from pathlib import Path
from typing import Optional

from meshroom.common import BaseObject, ListModel, Property, Signal, Slot
from meshroom.core.plugins import meshroomPluginsFolder
from meshroom.core.plugins.record import PluginRecord
from meshroom.core.plugins.provider import getPluginProviderFromUrl
from meshroom.core.plugins.local.task import PluginTask, PluginTaskKind
from meshroom.core.plugins.local.service import PluginService
from meshroom.core.plugins.local.installer import PluginInstaller
from meshroom.core.plugins.local.uninstaller import PluginUninstaller
from meshroom.core.plugins.local.updater import PluginUpdater


class PluginTaskQueue(BaseObject):
    """
    A queue of PluginTasks, processing the local plugin services (install, update, remove) for the UI.

    The tasks run one at a time, in the order they were added.
    A task can be cancelled while it is waiting or running. The finished tasks stay in the queue, for the UI
    to report their outcome, until they are cleared.
    """

    def __init__(self, pluginsPath: Path = meshroomPluginsFolder, parent: BaseObject = None):
        """
        Args:
            pluginsPath: the folder the local plugins are installed in.
            parent: the parent of the queue.
        """
        super().__init__(parent)
        self._pluginsPath: Path = Path(pluginsPath)
        self._tasks = ListModel(parent=self)
        self._busy: bool = False
        self._runningTask: Optional[PluginTask] = None

    # Signals
    busyChanged = Signal()
    runningTaskChanged = Signal()
    taskFinished = Signal(BaseObject)  # A task reached a finished status.

    # Properties
    tasks = Property(BaseObject, lambda self: self._tasks, constant=True)
    busy = Property(bool, lambda self: self._busy, notify=busyChanged)
    runningTask = Property(BaseObject, lambda self: self._runningTask, notify=runningTaskChanged)

    @Slot(BaseObject, result=BaseObject)
    @Slot(BaseObject, str, result=BaseObject)
    def install(self, record: PluginRecord, version: str = "") -> Optional[PluginTask]:
        """
        Add the task installing the plugin described by "record".

        Args:
            record: the record of the plugin to install.
            version: the version to install, or the version of "record" if empty.

        Returns:
            PluginTask | None: the added task, or None.
        """
        provider = getPluginProviderFromUrl(record.url)
        if not provider:
            logging.error(f"Cannot install plugin '{record.name}': no plugin provider for '{record.url}'")
            return None
        return self._addTask(PluginTaskKind.INSTALL, record.name,
                             PluginInstaller(provider, record, version or None, self._pluginsPath))

    @Slot(str, result=BaseObject)
    @Slot(str, str, result=BaseObject)
    def update(self, pluginName: str, version: str = "") -> Optional[PluginTask]:
        """
        Add the task updating an installed plugin, with the version described by the record
        advertising an update for it.

        Args:
            pluginName: the name of the plugin to update.
            version: the version to install, or the version of the update record if empty.

        Returns:
            PluginTask | None: the added task, or None.
        """
        from meshroom.core import pluginManager

        plugin = pluginManager.getPlugin(pluginName)
        if not plugin:
            logging.error(f"Cannot update plugin '{pluginName}': it is not installed")
            return None
        record = pluginManager.getUpdateRecord(plugin)
        if not record:
            logging.error(f"Cannot update plugin '{pluginName}': no update is available")
            return None
        provider = getPluginProviderFromUrl(record.url)
        if not provider:
            logging.error(f"Cannot update plugin '{pluginName}': no plugin provider for '{record.url}'")
            return None
        return self._addTask(PluginTaskKind.UPDATE, pluginName,
                             PluginUpdater(provider, record, version or None, self._pluginsPath))

    @Slot(str, result=BaseObject)
    def remove(self, pluginName: str) -> Optional[PluginTask]:
        """
        Add the task removing an installed plugin.

        Args:
            pluginName: the name of the plugin to remove.

        Returns:
            PluginTask | None: the added task, or None.
        """
        return self._addTask(PluginTaskKind.REMOVE, pluginName, PluginUninstaller(pluginName, self._pluginsPath))

    @Slot(BaseObject)
    def cancel(self, task: PluginTask) -> None:
        """ Cancel a task of the queue: a pending task never runs, a running task is asked to stop. """
        task.cancel()

    @Slot()
    def cancelAll(self) -> None:
        """ Cancel all the tasks of the queue. """
        for task in list(self._tasks):
            task.cancel()

    @Slot()
    def clearFinished(self) -> None:
        """ Remove the finished tasks from the queue. """
        for task in [t for t in self._tasks if t.isFinished]:
            self._tasks.remove(task)

    def shutdown(self, timeout: float = 10.0) -> None:
        """
        Cancel all the tasks and wait for the running one to stop, so that it can clean up after itself
        instead of being killed with the application.

        Args:
            timeout: the maximum time to wait for the running task, in seconds.
        """
        self.cancelAll()
        if self._runningTask:
            self._runningTask.join(timeout)

    def waitForIdle(self, timeout: float = 10.0) -> bool:
        """
        Wait until all the tasks are over.

        Args:
            timeout: the maximum time to wait, in seconds.

        Returns:
            bool: whether the queue is idle.
        """
        deadline = time.monotonic() + timeout
        while self._busy and time.monotonic() < deadline:
            task = self._runningTask
            if task:
                task.join(0.05)
            else:
                time.sleep(0.01)
        return not self._busy

    def _addTask(self, kind: str, pluginName: str, service: PluginService) -> Optional[PluginTask]:
        """
        Add a task running "service" at the end of the queue, and start it if nothing else is running.

        Args:
            kind: the kind of task.
            pluginName: the name of the plugin the task acts on.
            service: the service to run.

        Returns:
            PluginTask | None: the added task, or None.
        """
        if any(t.pluginName == pluginName and not t.isFinished for t in self._tasks):
            logging.warning(f"Plugin '{pluginName}' already has a task in progress, ignoring the {kind} request")
            return None

        task = PluginTask(kind, pluginName, service, parent=self)
        task.finished.connect(lambda t=task: self._onTaskFinished(t))
        self._tasks.append(task)
        self._update()
        return task

    def _onTaskFinished(self, task: PluginTask) -> None:
        """ Notify that a task is over, then move on to the next one. """
        self.taskFinished.emit(task)
        self._update()

    def _update(self) -> None:
        """ Start the next pending task if none is running, and update the state of the queue. """
        if not any(t.isRunning() for t in self._tasks):
            for task in self._tasks:
                if task.isPending():
                    task.launch()
                    break

        runningTask = next((t for t in self._tasks if t.isRunning()), None)
        if runningTask is not self._runningTask:
            self._runningTask = runningTask
            self.runningTaskChanged.emit()

        busy = any(not t.isFinished for t in self._tasks)
        if busy != self._busy:
            self._busy = busy
            self.busyChanged.emit()
