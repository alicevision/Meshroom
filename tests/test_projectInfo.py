import json
import os

from meshroom.core import cacheFolderName
from meshroom.ui.projectInfo import ProjectStatus, readProjectInfo


def isComputable(nodeType):
    return nodeType != "Backdrop"


def writeProject(folder, graph, header=None):
    path = os.path.join(folder, "project.mg")
    with open(path, "w") as file:
        json.dump({"header": header or {}, "graph": graph}, file)
    return path


def writeStatus(folder, nodeType, uid, fileName, status, execMode="LOCAL"):
    nodeFolder = os.path.join(folder, cacheFolderName, nodeType, uid)
    os.makedirs(nodeFolder, exist_ok=True)
    with open(os.path.join(nodeFolder, fileName), "w") as file:
        json.dump({"status": status, "execMode": execMode}, file)


GRAPH = {
    "CameraInit_1": {"nodeType": "CameraInit", "uid": "u1",
                     "inputs": {"viewpoints": [{"path": "/img/a.jpg"}, {"path": "/img/b.jpg"}]}},
    "FeatureExtraction_1": {"nodeType": "FeatureExtraction", "uid": "u2"},
    "Backdrop_1": {"nodeType": "Backdrop", "uid": "u3"},
}


def test_projectInfoNotComputed(tmp_path):
    path = writeProject(tmp_path, GRAPH, {"sourceTemplate": {"name": "photogrammetry", "plugin": "AliceVision"}})
    info = readProjectInfo(path, isComputable)
    assert info["status"] == ProjectStatus.NOT_COMPUTED
    assert info["sourceTemplate"] == {"name": "photogrammetry", "plugin": "AliceVision"}
    assert info["imageCount"] == 2
    assert info["thumbnail"] == "/img/a.jpg"
    # The backdrop is not computed
    assert (info["computedNodes"], info["totalNodes"]) == (0, 2)
    assert info["modified"] > 0


def test_projectInfoStatuses(tmp_path):
    path = writeProject(tmp_path, GRAPH)
    writeStatus(tmp_path, "CameraInit", "u1", "0.status", "SUCCESS")
    info = readProjectInfo(path, isComputable)
    assert info["status"] == ProjectStatus.PARTIAL
    assert info["computedNodes"] == 1

    # 1 chunk out of 2 done on the running node
    writeStatus(tmp_path, "FeatureExtraction", "u2", "0.status", "SUCCESS")
    writeStatus(tmp_path, "FeatureExtraction", "u2", "1.status", "RUNNING", "EXTERN")
    info = readProjectInfo(path, isComputable)
    assert info["status"] == ProjectStatus.RUNNING
    assert info["onFarm"]
    assert info["progress"] == 2 / 3

    writeStatus(tmp_path, "FeatureExtraction", "u2", "1.status", "ERROR")
    info = readProjectInfo(path, isComputable)
    assert info["status"] == ProjectStatus.FAILED
    assert info["failedNode"] == "FeatureExtraction_1"

    writeStatus(tmp_path, "FeatureExtraction", "u2", "1.status", "SUCCESS")
    info = readProjectInfo(path, isComputable)
    assert info["status"] == ProjectStatus.COMPUTED
    assert info["progress"] == 1.0


def test_projectInfoSubmittedWithoutChunks(tmp_path):
    # A node submitted to a farm has a node status file but no chunk status file yet
    path = writeProject(tmp_path, GRAPH)
    writeStatus(tmp_path, "CameraInit", "u1", "nodeStatus", "SUBMITTED", "EXTERN")
    info = readProjectInfo(path, isComputable)
    assert info["status"] == ProjectStatus.SCHEDULED
    assert info["onFarm"]


def test_projectInfoExplicitCacheDir(tmp_path):
    cacheDir = tmp_path / "otherCache"
    path = writeProject(tmp_path, GRAPH, {"cacheDir": {"absoluteCacheDir": str(cacheDir), "relativeCacheDir": "otherCache"}})
    for nodeType, uid in (("CameraInit", "u1"), ("FeatureExtraction", "u2")):
        os.makedirs(cacheDir / nodeType / uid)
        with open(cacheDir / nodeType / uid / "status", "w") as file:
            json.dump({"status": "SUCCESS"}, file)
    assert readProjectInfo(path, isComputable)["status"] == ProjectStatus.COMPUTED


def test_projectInfoUnreadable(tmp_path):
    path = tmp_path / "broken.mg"
    path.write_text("{ not json")
    assert readProjectInfo(str(path), isComputable)["status"] == ProjectStatus.UNKNOWN
    assert readProjectInfo(str(tmp_path / "missing.mg"), isComputable)["status"] == ProjectStatus.UNKNOWN


def test_projectInfoCountsViewpointsOfAnyNode(tmp_path):
    graph = {"Images_1": {"nodeType": "OtherInit", "uid": "u1", "inputs": {"viewpoints": [{"path": "/img/a.jpg"}]}}}
    info = readProjectInfo(writeProject(tmp_path, graph), isComputable)
    assert (info["imageCount"], info["thumbnail"]) == (1, "/img/a.jpg")


def test_projectInfoRunningChunkOutranksStoppedChunk(tmp_path):
    path = writeProject(tmp_path, GRAPH)
    writeStatus(tmp_path, "FeatureExtraction", "u2", "0.status", "STOPPED")
    writeStatus(tmp_path, "FeatureExtraction", "u2", "1.status", "RUNNING")
    assert readProjectInfo(path, isComputable)["status"] == ProjectStatus.RUNNING


def test_projectInfoPrefixedStatusOutranksLegacyStatus(tmp_path):
    path = writeProject(tmp_path, GRAPH)
    writeStatus(tmp_path, "CameraInit", "u1", "0.status", "SUCCESS")
    writeStatus(tmp_path, "FeatureExtraction", "u2", "status", "ERROR")
    writeStatus(tmp_path, "FeatureExtraction", "u2", "0.status", "SUCCESS")
    assert readProjectInfo(path, isComputable)["status"] == ProjectStatus.COMPUTED


def test_projectInfoUnexpectedContent(tmp_path):
    # Valid JSON that is not a project
    path = tmp_path / "list.mg"
    path.write_text("[1, 2]")
    assert readProjectInfo(str(path), isComputable)["status"] == ProjectStatus.UNKNOWN
    # Nodes, inputs, viewpoints and status files of unexpected types are skipped
    graph = {
        "Broken_1": None,
        "Broken_2": {"nodeType": 3, "uid": ["u"], "inputs": "x"},
        "Images_1": {"nodeType": "OtherInit", "uid": "u1", "inputs": {"viewpoints": [{"path": 5}]}},
    }
    path = writeProject(tmp_path, graph)
    nodeFolder = tmp_path / cacheFolderName / "OtherInit" / "u1"
    os.makedirs(nodeFolder)
    (nodeFolder / "0.status").write_text("[]")
    info = readProjectInfo(path, isComputable)
    assert (info["status"], info["imageCount"], info["thumbnail"], info["totalNodes"]) == (ProjectStatus.NOT_COMPUTED, 1, "", 1)
    # A source template name that is not text is ignored
    path = writeProject(tmp_path, graph, {"sourceTemplate": {"name": 1}})
    assert readProjectInfo(path, isComputable)["sourceTemplate"] is None
