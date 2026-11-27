from types import SimpleNamespace

import pytest

# The app module imports PySide6 (and needs libEGL): skip when it is not available
app = pytest.importorskip("meshroom.ui.app", exc_type=ImportError)
from meshroom.ui.projectInfo import ProjectStatus  # noqa: E402

MeshroomApp = app.MeshroomApp


class DeferredThread:
    """ Replaces threading.Thread: the reads run when the test calls `runAll`, in the order it chooses. """
    started = []

    def __init__(self, target, daemon=False):
        self.target = target

    def start(self):
        DeferredThread.started.append(self.target)


def makeApp(paths, reads):
    """ Return a stub with the state used by the recent project methods of MeshroomApp. `reads` collects the paths
    actually read; the emitted results are applied right away, like the queued connection would on the main thread. """
    stub = SimpleNamespace(_recentProjectFiles=[{"path": p, "info": {}} for p in paths],
                           _projectInfoRequests={}, _lastProjectInfoRequest=0, _refreshRequest=0, changes=0)
    infos = iter(range(1000))

    def readProjectInfo(path):
        reads.append(path)
        return {"status": ProjectStatus.NOT_COMPUTED, "readId": next(infos)}

    stub._readProjectInfo = readProjectInfo
    stub._projectFileEntry = lambda path, info: {"path": path, "info": info}
    stub._projectInfosRead = SimpleNamespace(emit=lambda request, result: MeshroomApp._applyProjectInfos(stub, request, result))
    stub.recentProjectFilesChanged = SimpleNamespace(emit=lambda: setattr(stub, "changes", stub.changes + 1))
    stub._readProjectInfosAsync = lambda p: MeshroomApp._readProjectInfosAsync(stub, p)
    return stub


@pytest.fixture
def deferredThreads(monkeypatch):
    DeferredThread.started = []
    monkeypatch.setattr(app, "Thread", DeferredThread)
    return DeferredThread.started


def test_olderReadDoesNotOverwriteNewerOne(tmp_path, deferredThreads):
    path = str(tmp_path / "a.mg")
    stub = makeApp([path], [])

    MeshroomApp.refreshRecentProjectFiles(stub)
    # A refresh is ignored while the previous one is running
    MeshroomApp.refreshRecentProjectFiles(stub)
    assert len(deferredThreads) == 1
    refresh, = deferredThreads

    # The project is read again (e.g. saved), and this newer read ends first
    stub._readProjectInfosAsync([path])
    deferredThreads[1]()
    newerInfo = stub._recentProjectFiles[0]["info"]
    refresh()
    assert stub._recentProjectFiles[0]["info"] is newerInfo
    assert stub._projectInfoRequests == {}
    # The refresh is over: a new one can start
    MeshroomApp.refreshRecentProjectFiles(stub)
    assert len(deferredThreads) == 3

    # The older read ends first, while the newer one is still running: its result is dropped
    stub._readProjectInfosAsync([path])
    deferredThreads[2]()
    assert stub._recentProjectFiles[0]["info"] is newerInfo
    deferredThreads[3]()
    assert stub._recentProjectFiles[0]["info"] is not newerInfo
    assert stub._projectInfoRequests == {}


def test_unchangedReadDoesNotUpdateTheList(tmp_path, deferredThreads):
    path = str(tmp_path / "a.mg")
    stub = makeApp([path], [])
    stub._readProjectInfo = lambda p: {"status": ProjectStatus.NOT_COMPUTED}
    for _ in range(2):
        MeshroomApp.refreshRecentProjectFiles(stub)
        deferredThreads[-1]()
    assert stub.changes == 1


def test_computedUnmodifiedProjectIsNotReadAgain(tmp_path, deferredThreads):
    path = tmp_path / "a.mg"
    path.write_text("{}")
    reads = []
    stub = makeApp([str(path)], reads)
    modified = int(path.stat().st_mtime * 1000)
    stub._recentProjectFiles[0]["info"] = {"status": ProjectStatus.COMPUTED, "modified": modified}

    MeshroomApp.refreshRecentProjectFiles(stub)
    deferredThreads[-1]()
    assert reads == []

    # Not computed: read again even if not modified
    stub._recentProjectFiles[0]["info"] = {"status": ProjectStatus.PARTIAL, "modified": modified}
    MeshroomApp.refreshRecentProjectFiles(stub)
    deferredThreads[-1]()
    assert reads == [str(path)]
