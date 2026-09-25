from __future__ import annotations

import itertools
import logging
import threading

from enum import Enum
from typing import Optional

from meshroom.common import BaseObject, Property, Signal, Slot
from meshroom.core.plugins.local.service import PluginService, PluginServiceCancelled, PluginServiceError


class PluginTaskKind:
    """
    The kinds of PluginTask.
    Each value corresponds to the concrete PluginService subclass run by the task:
    - INSTALL: PluginInstaller.
    - UPDATE: PluginUpdater.
    - REMOVE: PluginUninstaller.
    """
    INSTALL = "install"
    UPDATE = "update"
    REMOVE = "remove"


class PluginTaskStatus(Enum):
    """
    The lifecycle of a PluginTask:
    - PENDING: the task has not been launched yet.
    - RUNNING: the task's service is executing in its worker thread.
    - SUCCEEDED: the service completed without error.
    - FAILED: the service raised a PluginServiceError, or an unexpected exception.
    - CANCELLED: the task was cancelled before launch, or the service stopped after a cancel request.
    """
    PENDING = 0
    RUNNING = 1
    SUCCEEDED = 2
    FAILED = 3
    CANCELLED = 4


# The statuses at which a PluginTask is done and will not change anymore.
_TASK_FINISHED = (PluginTaskStatus.SUCCEEDED, PluginTaskStatus.FAILED, PluginTaskStatus.CANCELLED)


class PluginTask(BaseObject):
    """
    A PluginTask runs a single PluginService (installation, update or removal of a plugin) in a worker thread,
    and exposes its state to the UI.

    A task can be cancelled at any time. A pending task is cancelled right away, whereas a running task stops
    the next time its service checks for cancellation.
    """

    # Shared counter assigning each PluginTask instance a unique, incrementing id.
    _ids = itertools.count(1)

    def __init__(self, kind: str, pluginName: str, service: PluginService, parent: BaseObject = None):
        """
        Args:
            kind: the kind of task.
            pluginName: the name of the plugin the task acts on.
            service: the service to run.
            parent: the parent of the task.
        """
        super().__init__(parent)
        self._id: int = next(PluginTask._ids)
        self._kind: str = kind
        self._pluginName: str = pluginName
        self._service: PluginService = service
        self._status: PluginTaskStatus = PluginTaskStatus.PENDING
        self._progress: float = 0.0
        self._message: str = ""
        self._error: str = ""
        self._cancelRequested: bool = False
        self._cancelEvent: threading.Event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self._progressReported.connect(self._onProgressReported)
        self._finishedWith.connect(self._onFinishedWith)

    # Signals
    statusChanged = Signal()
    progressChanged = Signal()
    messageChanged = Signal()
    errorChanged = Signal()
    cancelRequestedChanged = Signal()
    finished = Signal()

    # Emitted by the worker thread, received by the thread the task lives in.
    _progressReported = Signal(str, float)
    _finishedWith = Signal(str, str)

    # Properties
    id = Property(int, lambda self: self._id, constant=True)
    kind = Property(str, lambda self: self._kind, constant=True)
    pluginName = Property(str, lambda self: self._pluginName, constant=True)
    status = Property(str, lambda self: self._status.name, notify=statusChanged)
    isFinished = Property(bool, lambda self: self._status in _TASK_FINISHED, notify=statusChanged)
    progress = Property(float, lambda self: self._progress, notify=progressChanged)
    message = Property(str, lambda self: self._message, notify=messageChanged)
    error = Property(str, lambda self: self._error, notify=errorChanged)
    cancelRequested = Property(bool, lambda self: self._cancelRequested, notify=cancelRequestedChanged)

    def isPending(self) -> bool:
        """ Whether the task is waiting to be launched. """
        return self._status == PluginTaskStatus.PENDING

    def isRunning(self) -> bool:
        """ Whether the task is running. """
        return self._status == PluginTaskStatus.RUNNING

    def launch(self) -> None:
        """
        Start running the service in a worker thread. Does nothing if the task is not pending.
        The task is running as soon as this returns.
        """
        if not self.isPending():
            return
        self._setStatus(PluginTaskStatus.RUNNING)
        self._thread = threading.Thread(target=self._run, name=f"PluginTask_{self._id}", daemon=True)
        self._thread.start()

    @Slot()
    def cancel(self) -> None:
        """
        Cancel the task: a pending task never runs, a running task is asked to stop.
        Does nothing if the task is already finished.
        """
        if self.isPending():
            self._finish(PluginTaskStatus.CANCELLED, "")
        elif self.isRunning() and not self._cancelRequested:
            self._cancelEvent.set()
            self._cancelRequested = True
            self.cancelRequestedChanged.emit()

    def join(self, timeout: Optional[float] = None) -> None:
        """
        Wait for the worker thread to end. Does nothing if the task has not been launched.

        Args:
            timeout: the maximum time to wait, in seconds, or None.
        """
        if self._thread:
            self._thread.join(timeout)

    def _run(self) -> None:
        """
        Run the service. This is the target of the worker thread: it only reports the progress
        and the outcome of the service through signals.
        """
        def onProgress(message: str, percent: float) -> None:
            self._progressReported.emit(message, percent)

        try:
            self._service.execute(onProgress, self._cancelEvent.is_set)
        except PluginServiceCancelled:
            self._finishedWith.emit(PluginTaskStatus.CANCELLED.name, "")
        except PluginServiceError as exc:
            logging.error(exc)
            self._finishedWith.emit(PluginTaskStatus.FAILED.name, exc.error)
        except Exception as exc:
            logging.exception(f"Plugin task {self._kind} '{self._pluginName}' failed unexpectedly")
            self._finishedWith.emit(PluginTaskStatus.FAILED.name, f"{type(exc).__name__}: {exc}")
        else:
            self._finishedWith.emit(PluginTaskStatus.SUCCEEDED.name, "")

    @Slot(str, float)
    def _onProgressReported(self, message: str, percent: float) -> None:
        """ Update the progress of the task with the one reported by the service. """
        if self._status != PluginTaskStatus.RUNNING:
            return
        if message != self._message:
            self._message = message
            self.messageChanged.emit()
        percent = min(max(percent, 0.0), 1.0)
        if percent != self._progress:
            self._progress = percent
            self.progressChanged.emit()

    @Slot(str, str)
    def _onFinishedWith(self, statusName: str, error: str) -> None:
        """ Finish the task with the outcome reported by the worker thread. """
        self._finish(PluginTaskStatus[statusName], error)

    def _finish(self, status: PluginTaskStatus, error: str) -> None:
        """
        Set the final status of the task, then notify that it is finished.

        Args:
            status: the final status of the task.
            error: the error message of a failed task, empty otherwise.
        """
        if self._status in _TASK_FINISHED:
            return
        if error != self._error:
            self._error = error
            self.errorChanged.emit()
        if status == PluginTaskStatus.SUCCEEDED and self._progress != 1.0:
            self._progress = 1.0
            self.progressChanged.emit()
        self._setStatus(status)
        self.finished.emit()

    def _setStatus(self, status: PluginTaskStatus) -> None:
        """ Set the status of the task and notify the change. """
        self._status = status
        self.statusChanged.emit()
