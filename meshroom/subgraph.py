"""
Run Meshroom subgraphs from the Python shell of a software (Houdini, Maya, Nuke) or any Python script,
in the current session: the nodes run one after the other in this session, the values going from node to
node in memory. The session prevails: e.g. a HoudiniScene node gives the open scene, and the nodes only
computing the scene path in Meshroom (a pipeline node) are not run.

    import meshroom.subgraph
    outputs = meshroom.subgraph.run("/path/to/turntable.mgt", {"asset": "/path/asset.usd"})
    outputs = meshroom.subgraph.run("/path/to/comp.mgt", frames=(1001, 1100))
    outputs = meshroom.subgraph.run("/path/to/setup.mgt", items="mr_001, mr_002, mr_003")
    outputs = meshroom.subgraph.run("/path/to/project.mg", node="SubGraph_1")
    outputs = meshroom.subgraph.run("/path/to/setup.mgt", set={"HoudiniSetFrameRange_1.frameRange.start": 1001})

Meshroom (and its dependencies, such as psutil) must be importable: add its folder to PYTHONPATH, and
the folders of the plugins providing the live nodes to MESHROOM_NODES_PATH / MESHROOM_PLUGINS_PATH.
"""
import logging
from typing import Optional, Sequence, Union

from meshroom.core.subgraph import Loop, SubGraphError, SubGraphPlan, contextNames, run as _run

__all__ = ["run", "load", "nodeSubGraph", "Loop", "SubGraphError", "contextNames", "ensureNodes"]

_nodesLoaded = False
# The variables giving the plugins, when they were loaded: plugins set after (e.g. by a script of the software)
# are loaded at the next call
_PLUGIN_VARIABLES = ("MESHROOM_PLUGINS_PATH", "MESHROOM_USER_PLUGINS_PATH", "MESHROOM_REZ_PLUGINS",
                     "MESHROOM_USER_REZ_PLUGINS", "MESHROOM_NODES_PATH")
_loadedPluginVariables = None


def _pluginVariables() -> tuple:
    import os
    return tuple(os.environ.get(name, "") for name in _PLUGIN_VARIABLES)


def ensureNodes():
    """
    Load the node types (built-in nodes and plugins) if they are not loaded yet, and the plugins again when
    the variables giving them changed since (MESHROOM_USER_REZ_PLUGINS...).
    """
    global _nodesLoaded, _loadedPluginVariables
    variables = _pluginVariables()
    if _nodesLoaded and variables == _loadedPluginVariables:
        return
    import meshroom.core
    from meshroom.core.subgraph.contexts import HoudiniContext
    # In Houdini: its USD modules first, before plugins import another USD
    HoudiniContext.preloadHostUsd()
    if meshroom.core.pluginManager.getNodeDescProvider("GraphInput") is None:
        meshroom.core.initNodes()
        meshroom.core.initPlugins()
    elif variables != _loadedPluginVariables and any(variables):
        # Nodes already loaded (by Meshroom, or before the plugin variables were set): load the plugins
        if _loadedPluginVariables is not None:
            logging.info("[SubGraph] The plugin variables changed: loading the plugins.")
        meshroom.core.initNodes()
        meshroom.core.initPlugins()
    _nodesLoaded = True
    _loadedPluginVariables = variables


def load(source) -> SubGraphPlan:
    """ The plan of a subgraph (template path, JSON, or serialized graph dict), to run it several times. """
    ensureNodes()
    return SubGraphPlan.cached(source)


def nodeSubGraph(projectPath: str, nodeName: str):
    """
    The subgraph of a SubGraph node of a project (.mg): its embedded subgraph, else its template.
    """
    return _projectNode(projectPath, nodeName)[0]


def _projectNode(projectPath: str, nodeName: str):
    """
    (subgraph source, input values, loop) of a SubGraph node of a project: its embedded subgraph (else its
    template), the values of its inputs that are not connections, and its loop settings.
    """
    from meshroom.core.subgraph import readGraphData
    from meshroom.core.subgraph.nodes import loopFromValues
    from meshroom.core.subgraph.ports import anySetValues
    graphData = readGraphData(projectPath)
    if nodeName not in graphData:
        raise SubGraphError(f"No node '{nodeName}' in {projectPath}.")
    nodeInputs = graphData[nodeName].get("inputs") or {}
    source = nodeInputs.get("subGraph") or nodeInputs.get("template")
    if not source:
        raise SubGraphError(f"The node '{nodeName}' has no subgraph.")
    # Values typed on the node; a connected input ("{Node.attr}") has no value outside of Meshroom
    values = {name: value for name, value in anySetValues(nodeInputs.get("ins")).items()
              if not (isinstance(value, str) and value.startswith("{") and value.endswith("}"))}
    from meshroom.core.subgraph.nodes import LOOP_ATTRIBUTES
    loop = loopFromValues({"loopMode": "none", "iterations": 1, "frameStep": 1,
                           **{name: nodeInputs[name] for name in LOOP_ATTRIBUTES + ("frameFirst", "frameLast")
                              if name in nodeInputs}})
    return source, values, loop


def run(source, inputs: Optional[dict] = None, context: Optional[str] = None,
        frames: Optional[Union[Sequence[int], tuple]] = None, step: float = 1, iterations: Optional[int] = None,
        variables: Optional[dict] = None, logger: Optional[logging.Logger] = None, node: Optional[str] = None,
        set: Optional[dict] = None, items: Optional[Sequence] = None, onNode=None) -> dict:
    """
    Run a subgraph in the current interpreter and return the values of its GraphOutput ports.

    Args:
        source: a template path (.mgt / .mg), a JSON string, a serialized graph dict, or a plan from load().
        inputs: values of its GraphInput ports {port name: value}, any Python objects.
        context: "houdini", "maya", "nuke", "python"...; by default the one needed by its nodes. From the
                 software itself, its session is used as it is (nothing is opened or closed).
        frames: a tuple (first, last) to run it once per frame (every `step` frames, e.g. 0.1 for sub-frames),
                or a list of frames.
        iterations: run it N times, the outputs feeding the inputs of the same name.
        items: run it once per item of a list (or of a text separated by commas): ctx.item, "item" of GraphInput.
        variables: values shared by the nodes (ctx.variables).
        node: with a project file (.mg) as source, the name of the SubGraph node whose subgraph is run; its
              input values (not connected) and its loop are used unless `inputs` / `frames` / `iterations`
              are given.
        set: values of attributes of the nodes, set before running: {"Node_1.attribute": value} (or
             "Node_1.group.child"), without declaring ports.
        onNode: called with (node name, status, message) as the nodes run: RUNNING, SUCCESS (message: its
                duration), ERROR (message: the error), UPSTREAM_ERROR (not run after an error), SKIPPED (not
                needed in this context).

    Raises:
        SubGraphError: an error in a node (its name is in the message).
    """
    ensureNodes()
    nodeLoop = None
    if node:
        source, nodeInputs, nodeLoop = _projectNode(source, node)
        inputs = {**nodeInputs, **(inputs or {})}
    if sum(value is not None for value in (frames, iterations, items)) > 1:
        raise ValueError("Use only one of frames, iterations, items.")
    if frames is None and iterations is None and items is None and nodeLoop is not None:
        loop = nodeLoop
    elif items is not None:
        from meshroom.core.subgraph.nodes import parseItems
        loop = Loop("items", items=parseItems(items))
    elif frames is not None:
        if isinstance(frames, tuple) and len(frames) == 2:
            loop = Loop("frames", first=frames[0], last=frames[1], step=step)
        else:
            loop = Loop("frames", frames=list(frames))
    elif iterations is not None:
        loop = Loop("count", iterations=iterations)
    else:
        loop = Loop()
    return _run(source, inputs, context=context, loop=loop, variables=variables, logger=logger, overrides=set,
                onNode=onNode)
