#!/usr/bin/env python
# coding:utf-8

import threading
import time

from pathlib import Path

from meshroom.core.plugins.local.service import PluginService, PluginServiceError
from meshroom.core.plugins.local.task import PluginTask, PluginTaskKind, PluginTaskStatus
from meshroom.core.plugins.local.taskQueue import PluginTaskQueue


class FakeService(PluginService):
    """ A minimal PluginService, fully controlled by the test instead of doing real work. """

    def __init__(self, pluginName="myPlugin", hold=None, fail=None):
        """
        Args:
            pluginName: the name of the plugin the service acts on.
            hold: an Event the service waits on before finishing, or None to finish right away.
            fail: an exception the service raises instead of finishing, or None to succeed.
        """
        super().__init__("fake", pluginName, Path("."))
        self._hold = hold
        self._fail = fail

    def _run(self):
        """ Report progress, wait for "hold" to be released (checking for cancellation), then fail or succeed. """
        self._reportProgress("Working", 0.5)
        if self._hold:
            while not self._hold.wait(0.01):
                self._checkCancel()
        self._checkCancel()
        if self._fail:
            raise self._fail


class SignalRecorder:
    """ Records the arguments of every emission of the signal it is connected to. """

    def __init__(self):
        self.calls = []

    def onEmit(self, *args):
        self.calls.append(args)


def waitUntil(predicate, timeout=2.0):
    """ Poll "predicate" until it returns True, or "timeout" seconds have passed. """
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        time.sleep(0.01)
    return predicate()


def task(service=None, pluginName="myPlugin"):
    """ Return a PluginTask running "service" (a successful FakeService by default). """
    return PluginTask(PluginTaskKind.INSTALL, pluginName, service or FakeService(pluginName))


class TestPluginTask:

    def test_succeeds(self):
        """ A successful service finishes the task with status SUCCEEDED and full progress. """
        t = task()
        t.launch()
        t.join()
        assert t.status == PluginTaskStatus.SUCCEEDED.name
        assert t.isFinished
        assert t.progress == 1.0
        assert t.error == ""

    def test_reportsProgress(self):
        """ The task exposes the progress reported by its service before it finishes. """
        hold = threading.Event()
        t = task(FakeService(hold=hold))
        t.launch()
        assert waitUntil(lambda: t.message == "Working")
        assert t.progress == 0.5
        hold.set()
        t.join()
        assert t.status == PluginTaskStatus.SUCCEEDED.name

    def test_fails(self):
        """ A service raising a PluginServiceError fails the task with its error message. """
        error = PluginServiceError("fake", "myPlugin", "step", "error")
        t = task(FakeService(fail=error))
        t.launch()
        t.join()
        assert t.status == PluginTaskStatus.FAILED.name
        assert t.error == "error"

    def test_unexpectedExceptionFails(self):
        """ A service raising any other exception also fails the task, instead of crashing the worker thread. """
        t = task(FakeService(fail=ValueError("Wrong")))
        t.launch()
        t.join()
        assert t.status == PluginTaskStatus.FAILED.name
        assert "ValueError" in t.error

    def test_cancelPending(self):
        """ A pending task is cancelled right away, without ever running its service. """
        t = task()
        t.cancel()
        assert t.status == PluginTaskStatus.CANCELLED.name
        assert t.isFinished

    def test_cancelRunning(self):
        """ A running task stops the next time its service checks for cancellation. """
        hold = threading.Event()
        t = task(FakeService(hold=hold))
        t.launch()
        assert waitUntil(t.isRunning)
        t.cancel()
        assert t.cancelRequested
        t.join()
        assert t.status == PluginTaskStatus.CANCELLED.name


class TestPluginTaskQueue:

    def test_runsImmediately(self):
        """ The first task added to an idle queue starts running right away. """
        queue = PluginTaskQueue()
        hold = threading.Event()
        added = queue._addTask(PluginTaskKind.INSTALL, "myPlugin", FakeService("myPlugin", hold=hold))
        assert added.isRunning()
        assert queue.busy
        hold.set()
        assert waitUntil(lambda: not queue.busy)

    def test_runsSequentially(self):
        """ Only one task runs at a time. The next one waits until the running one is over. """
        queue = PluginTaskQueue()
        holdA = threading.Event()
        taskA = queue._addTask(PluginTaskKind.INSTALL, "pluginA", FakeService("pluginA", hold=holdA))
        taskB = queue._addTask(PluginTaskKind.INSTALL, "pluginB", FakeService("pluginB"))
        assert taskA.isRunning()
        assert taskB.isPending()
        holdA.set()
        assert waitUntil(lambda: not queue.busy)
        assert taskB.status == PluginTaskStatus.SUCCEEDED.name

    def test_duplicatePluginNameIgnored(self):
        """ A plugin cannot have two tasks in progress at once. """
        queue = PluginTaskQueue()
        hold = threading.Event()
        queue._addTask(PluginTaskKind.INSTALL, "myPlugin", FakeService("myPlugin", hold=hold))
        second = queue._addTask(PluginTaskKind.UPDATE, "myPlugin", FakeService("myPlugin"))
        assert second is None
        hold.set()
        assert waitUntil(lambda: not queue.busy)

    def test_cancelAll(self):
        """ Cancelling the queue stops its running task and drops its pending ones. """
        queue = PluginTaskQueue()
        holdA = threading.Event()
        taskA = queue._addTask(PluginTaskKind.INSTALL, "pluginA", FakeService("pluginA", hold=holdA))
        taskB = queue._addTask(PluginTaskKind.INSTALL, "pluginB", FakeService("pluginB"))
        queue.cancelAll()
        assert waitUntil(lambda: not queue.busy)
        assert taskA.status == PluginTaskStatus.CANCELLED.name
        assert taskB.status == PluginTaskStatus.CANCELLED.name

    def test_clearFinished(self):
        """ Clearing the queue removes only the tasks that are finished. """
        queue = PluginTaskQueue()
        taskA = queue._addTask(PluginTaskKind.INSTALL, "pluginA", FakeService("pluginA"))
        assert waitUntil(lambda: taskA.isFinished)
        queue.clearFinished()
        assert list(queue.tasks) == []

    def test_taskFinishedSignal(self):
        """ The queue notifies each task's outcome through "taskFinished". """
        queue = PluginTaskQueue()
        recorder = SignalRecorder()
        queue.taskFinished.connect(recorder.onEmit)
        taskA = queue._addTask(PluginTaskKind.INSTALL, "pluginA", FakeService("pluginA"))
        assert waitUntil(lambda: len(recorder.calls) == 1)
        assert recorder.calls[0] == (taskA,)