import os
import json
import pytest
import time
import tempfile
from meshroom.core.node import NodeChunk, Status, StatusData
from meshroom.core import desc
from meshroom.core.node import StatusData

def test_nodechunk_update_status_from_cache(tmp_path):
    """
    Test NodeChunk.updateStatusFromCache behavior:
      - When no status file exists, the status is reset.
      - When a valid status file is present (with status SUCCESS), _status is updated.
    """
    # A dummy signal implementation which supports connect, emit and being called.
    class DummySignal:
        def __init__(self):
            self.callbacks = []
        def connect(self, func):
            self.callbacks.append(func)
        def emit(self, *args, **kwargs):
            for cb in self.callbacks:
                cb(*args, **kwargs)
        def __call__(self, *args, **kwargs):
            return self.emit(*args, **kwargs)
    # A dummy callable object that behaves like a signal and has a __name__ attribute.
    class DummyCallable:
        def __init__(self, func=None):
            self.func = func if func is not None else (lambda *args, **kwargs: None)
            self.callbacks = []
        def connect(self, func):
            self.callbacks.append(func)
        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)
        @property
        def __name__(self):
            return self.func.__name__
    # A simple FakeGraph with a cacheDir property.
    class FakeGraph:
        def __init__(self, cache_dir):
            self.cacheDir = cache_dir
    # A FakeNode that provides the minimal interface required by NodeChunk.
    # Its globalExecModeChanged attribute is a callable signal-like object.
    class FakeNode:
        def __init__(self, name, nodeType, pkgName, pkgVersion, internal_folder, graph):
            self._name = name
            self.name = name
            self.nodeType = nodeType
            self.packageName = pkgName
            self.packageVersion = pkgVersion
            self.internalFolder = internal_folder
            self.graph = graph
            self.internalFolderChanged = DummySignal()
            self.globalExecModeChanged = DummyCallable()
        
        def getName(self):
            return self._name
    # Setup a temporary cache directory and a fake graph.
    cache_dir = str(tmp_path / "cache")
    os.makedirs(cache_dir, exist_ok=True)
    fake_graph = FakeGraph(cache_dir)
    # Create the internal folder and a fake node.
    internal_folder = "dummy_folder"
    os.makedirs(os.path.join(cache_dir, internal_folder), exist_ok=True)
    fake_node = FakeNode(
        name="testNode",
        nodeType="dummyType",
        pkgName="dummyPkg",
        pkgVersion="1.0",
        internal_folder=internal_folder,
        graph=fake_graph
    )
    # Create a default range (blockSize == 0 by default) and instantiate NodeChunk.
    r = desc.Range(iteration=0, blockSize=0)
    chunk = NodeChunk(fake_node, r)
    # Ensure that the status file does not exist.
    status_file_path = chunk.statusFile
    if os.path.exists(status_file_path):
        os.remove(status_file_path)
    # Call updateStatusFromCache: since no status file exists, status should be reset.
    chunk.updateStatusFromCache()
    assert chunk._status.status.name == "NONE"
    assert chunk.statusFileLastModTime == -1
    # Create a status file with valid JSON data.
    status_data = {
        "status": "SUCCESS",
        "execMode": "NONE",
        "nodeName": fake_node.name,
        "nodeType": fake_node.nodeType,
        "packageName": fake_node.packageName,
        "packageVersion": fake_node.packageVersion,
        "graph": "",
        "commandLine": None,
        "env": None,
        "startDateTime": "2023-01-01 00:00:00.000000",
        "endDateTime": "2023-01-01 00:00:10.000000",
        "elapsedTime": 10,
        "hostname": "dummyHost",
        "sessionUid": "dummySession"
    }
    with open(status_file_path, "w") as f:
        json.dump(status_data, f, indent=4)
    # Update the modification time to simulate a recent write.
    os.utime(status_file_path, None)
    time.sleep(0.1)
    # Call updateStatusFromCache again. It should detect the status file and update _status.
    chunk.updateStatusFromCache()
    assert chunk._status.status.name == "SUCCESS"
    assert chunk.statusFileLastModTime != -1
    # Clean up by removing the status file.
    os.remove(status_file_path)
def test_nodechunk_stop_process(tmp_path):
    """
    Test NodeChunk.stopProcess behavior:
      - If the chunk status is RUNNING, stopProcess should upgrade the status to STOPPED and call the node descriptor's stopProcess.
      - If the chunk status is SUBMITTED, stopProcess should upgrade the status to NONE and call the node descriptor's stopProcess.
    """
    # Dummy signal implementation.
    class DummySignal:
        def __init__(self):
            self.callbacks = []
        def connect(self, func):
            self.callbacks.append(func)
        def emit(self, *args, **kwargs):
            for cb in self.callbacks:
                cb(*args, **kwargs)
        def __call__(self, *args, **kwargs):
            return self.emit(*args, **kwargs)
    # Dummy callable object that behaves like a signal.
    class DummyCallable:
        def __init__(self, func=None):
            self.func = func if func is not None else (lambda *args, **kwargs: None)
            self.callbacks = []
        def connect(self, func):
            self.callbacks.append(func)
        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)
        @property
        def __name__(self):
            return self.func.__name__
    class FakeGraph:
        def __init__(self, cache_dir):
            self.cacheDir = cache_dir
    # Dummy node descriptor with a stopProcess method.
    class DummyNodeDesc:
        def processChunk(self, chunk):
            pass
        def stopProcess(self, chunk):
            # Mark that stopProcess was called.
            chunk.stop_called = True
    # FakeNode provides the minimal interface required by NodeChunk.
    class FakeNode:
        def __init__(self, name, nodeType, pkgName, pkgVersion, internal_folder, graph):
            self._name = name
            self.name = name
            self.nodeType = nodeType
            self.packageName = pkgName
            self.packageVersion = pkgVersion
            self.internalFolder = internal_folder
            self.graph = graph
            self.internalFolderChanged = DummySignal()
            self.globalExecModeChanged = DummyCallable()
            # Assign the dummy node descriptor.
            self.nodeDesc = DummyNodeDesc()
        def getName(self):
            return self._name
    # Set up a temporary cache directory and fake graph.
    cache_dir = str(tmp_path / "cache")
    os.makedirs(cache_dir, exist_ok=True)
    fake_graph = FakeGraph(cache_dir)
    internal_folder = "dummy_folder"
    os.makedirs(os.path.join(cache_dir, internal_folder), exist_ok=True)
    fake_node = FakeNode(
        name="testNode",
        nodeType="dummyType",
        pkgName="dummyPkg",
        pkgVersion="1.0",
        internal_folder=internal_folder,
        graph=fake_graph
    )
    # Create a default range (with blockSize 0) and instantiate a NodeChunk.
    r = desc.Range(iteration=0, blockSize=0)
    chunk = NodeChunk(fake_node, r)
    # Test case 1: When status is RUNNING, stopProcess should upgrade it to STOPPED.
    chunk._status.status = Status.RUNNING
    chunk.stop_called = False
    chunk.stopProcess()
    assert chunk._status.status == Status.STOPPED, "When running, stopProcess should upgrade status to STOPPED."
    assert chunk.stop_called is True, "stopProcess of nodeDesc should have been called."
    # Test case 2: When status is SUBMITTED, stopProcess should upgrade it to NONE.
    chunk._status.status = Status.SUBMITTED
    chunk.stop_called = False
    chunk.stopProcess()
    assert chunk._status.status.name == "NONE", "When submitted, stopProcess should upgrade status to NONE."
    assert chunk.stop_called is True, "stopProcess of nodeDesc should have been called in the submitted case."
def test_statusdata_merge():
    """
    Test that merging two StatusData objects correctly updates
    startDateTime, endDateTime, and elapsedTime:
      - startDateTime should be the minimum of the two values.
      - endDateTime should be the maximum of the two values.
      - elapsedTime should be the sum of the two.
    """
    # Create first StatusData object with later start and earlier end.
    sd1 = StatusData("node", "type", "pkgName", "1.0")
    sd1.startDateTime = "2023-01-01 10:00:00.000000"
    sd1.endDateTime = "2023-01-01 10:00:05.000000"
    sd1.elapsedTime = 5
    # Create second StatusData object with an earlier start and later end.
    sd2 = StatusData("node", "type", "pkgName", "1.0")
    sd2.startDateTime = "2023-01-01 09:00:00.000000"
    sd2.endDateTime = "2023-01-01 10:00:10.000000"
    sd2.elapsedTime = 10
    # Merge the second status into the first.
    sd1.merge(sd2)
    # Expectation:
    # - startDateTime takes the earlier value from sd2.
    # - endDateTime takes the later value from sd2.
    # - elapsedTime is the sum: 5 + 10 = 15.
    assert sd1.startDateTime == "2023-01-01 09:00:00.000000", "startDateTime should be the minimum of the two."
    assert sd1.endDateTime == "2023-01-01 10:00:10.000000", "endDateTime should be the maximum of the two."
    assert sd1.elapsedTime == 15, "elapsedTime should be the sum of the elapsed times."