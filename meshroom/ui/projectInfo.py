""" Summary of a project file for the homepage: source template, image count, thumbnail and computation status.

Qt-free so that it can be unit tested without a UI. The graph is not built: the project file is read as JSON and
the status files of its nodes are read from the cache folder.
"""
import json
import logging
import os
from typing import Callable, Dict, Optional

from meshroom.core import cacheFolderName
from meshroom.core.graphIO import GraphIO


class ProjectStatus:
    """ Global status of a project, from the status of its computable nodes. """
    NOT_COMPUTED = "notComputed"
    PARTIAL = "partial"
    COMPUTED = "computed"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    FAILED = "failed"
    UNKNOWN = "unknown"  # the project file could not be read
    MISSING = "missing"  # the project file is not on disk anymore


# Chunk statuses that set the status of a whole node, by priority: a node with a chunk still running is running
_NODE_STATUS_PRIORITY = ("ERROR", "RUNNING", "SUBMITTED", "STOPPED", "KILLED")


def cacheDirectory(filepath: str, header: dict) -> str:
    """ Return the cache folder of the project at `filepath`: the explicit one stored in its `header` if it exists,
    otherwise the default one next to the project file (same resolution as when the graph is loaded).
    """
    projectFolder = os.path.dirname(os.path.abspath(filepath))
    explicit = header.get(GraphIO.Keys.CacheDir)
    if isinstance(explicit, dict):
        absolute = explicit.get("absoluteCacheDir")
        relative = explicit.get("relativeCacheDir")
        if absolute and os.path.isdir(absolute):
            return absolute
        if relative and os.path.isdir(os.path.join(projectFolder, relative)):
            return os.path.join(projectFolder, relative)
    return os.path.join(projectFolder, cacheFolderName)


def _readStatus(path: str) -> Optional[dict]:
    """ Return the content of the status file at `path`, None if it cannot be read or is not a JSON object. """
    try:
        with open(path) as file:
            data = json.load(file)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def nodeStatus(nodeFolder: str) -> dict:
    """ Return the status of a node from the status files in its cache folder.

    Returns:
        dict: {"status": the Status name ("NONE" if never computed), "execMode": the ExecMode name,
               "chunks": number of chunks, "doneChunks": number of chunks computed successfully}
    """
    try:
        files = os.listdir(nodeFolder)
    except OSError:
        return {"status": "NONE", "execMode": "NONE", "chunks": 1, "doneChunks": 0}
    # Chunk status files are "<chunk>.status", or "status" for files computed before chunks were prefixed
    chunks = [s for s in (_readStatus(os.path.join(nodeFolder, f)) for f in files
                          if f == "status" or f.endswith(".status")) if s]
    if not chunks:
        # No chunk yet (e.g. submitted to a farm): the node status file holds the status
        statusData = _readStatus(os.path.join(nodeFolder, "nodeStatus")) or {}
        status = statusData.get("status", "NONE")
        return {"status": status, "execMode": statusData.get("execMode", "NONE"),
                "chunks": 1, "doneChunks": int(status == "SUCCESS")}
    statuses = [c.get("status", "NONE") for c in chunks]
    doneChunks = statuses.count("SUCCESS")
    status = next((s for s in _NODE_STATUS_PRIORITY if s in statuses), None)
    if status is None:
        status = "SUCCESS" if doneChunks == len(statuses) else "NONE"
    execMode = next((c.get("execMode", "NONE") for c in chunks if c.get("status") == status), "NONE")
    return {"status": status, "execMode": execMode, "chunks": len(chunks), "doneChunks": doneChunks}


def projectStatus(filepath: str, header: dict, graph: dict, isComputable: Callable[[str], bool]) -> dict:
    """ Return the computation status of a project from the status files of its computable nodes.

    Args:
        filepath: the project file.
        header: the header of the project file.
        graph: the graph of the project file ({node name: node data dict}).
        isComputable: returns whether a node type is computed (False for backdrops, init nodes...).

    Returns:
        dict: {"status": a ProjectStatus, "onFarm": bool, "computedNodes": int, "totalNodes": int,
               "progress": computed chunks / total chunks (0 to 1), "failedNode": name of a failed node or ""}
    """
    cacheDir = cacheDirectory(filepath, header)
    nodes = {}
    for name, data in graph.items():
        nodeType, uid = data.get("nodeType"), data.get("uid")
        if not isinstance(nodeType, str) or not isinstance(uid, str) or not uid or not isComputable(nodeType):
            continue
        nodes[name] = nodeStatus(os.path.join(cacheDir, nodeType, uid))

    statuses = [n["status"] for n in nodes.values()]
    computedNodes = statuses.count("SUCCESS")
    chunks = sum(n["chunks"] for n in nodes.values())
    failedNode = next((name for name, n in nodes.items() if n["status"] == "ERROR"), "")
    if failedNode:
        status = ProjectStatus.FAILED
    elif "RUNNING" in statuses:
        status = ProjectStatus.RUNNING
    elif "SUBMITTED" in statuses:
        status = ProjectStatus.SCHEDULED
    elif nodes and computedNodes == len(nodes):
        status = ProjectStatus.COMPUTED
    elif computedNodes:
        status = ProjectStatus.PARTIAL
    else:
        status = ProjectStatus.NOT_COMPUTED
    return {
        "status": status,
        "onFarm": any(n["execMode"] == "EXTERN" and n["status"] in ("RUNNING", "SUBMITTED") for n in nodes.values()),
        "computedNodes": computedNodes,
        "totalNodes": len(nodes),
        "progress": sum(n["doneChunks"] for n in nodes.values()) / chunks if chunks else 0.0,
        "failedNode": failedNode,
    }


def readProjectInfo(filepath: str, isComputable: Callable[[str], bool]) -> Dict:
    """ Return the summary of the project at `filepath` shown on the homepage.

    Args:
        filepath: the project file.
        isComputable: returns whether a node type is computed (see `projectStatus`).

    Returns:
        dict: {"sourceTemplate": {"name", "plugin"} or None, "imageCount": int, "thumbnail": path of the first
               image or "", "modified": modification time in ms since epoch (0 if missing)} and the `projectStatus`
               keys; "status" is ProjectStatus.UNKNOWN if the file cannot be read.
    """
    info = {"sourceTemplate": None, "imageCount": 0, "thumbnail": "", "modified": 0,
            "status": ProjectStatus.UNKNOWN, "onFarm": False, "computedNodes": 0, "totalNodes": 0,
            "progress": 0.0, "failedNode": ""}
    try:
        info["modified"] = int(os.path.getmtime(filepath) * 1000)
        with open(filepath) as file:
            fileData = json.load(file)
    except (OSError, ValueError) as e:
        logging.info(f"Could not read the project file {filepath}: {e}")
        return info
    # The file may be valid JSON without being a project: report it as unreadable
    if not isinstance(fileData, dict):
        return info
    header = fileData.get(GraphIO.Keys.Header, {})
    graph = fileData.get(GraphIO.Keys.Graph, {})
    if not isinstance(header, dict) or not isinstance(graph, dict):
        return info
    graph = {name: data for name, data in graph.items() if isinstance(data, dict)}

    sourceTemplate = header.get(GraphIO.Keys.SourceTemplate)
    if isinstance(sourceTemplate, dict) and isinstance(sourceTemplate.get("name"), str) and sourceTemplate["name"]:
        info["sourceTemplate"] = sourceTemplate
    # Images are listed in the "viewpoints" of the input nodes (CameraInit or alike)
    for node in graph.values():
        inputs = node.get("inputs")
        viewpoints = inputs.get("viewpoints") if isinstance(inputs, dict) else None
        if not isinstance(viewpoints, list):
            continue
        info["imageCount"] += len(viewpoints)
        firstPath = viewpoints[0].get("path") if viewpoints and isinstance(viewpoints[0], dict) else None
        if isinstance(firstPath, str) and not info["thumbnail"]:
            info["thumbnail"] = firstPath
    info.update(projectStatus(filepath, header, graph, isComputable))
    return info
