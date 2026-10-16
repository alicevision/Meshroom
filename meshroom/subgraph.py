"""
Run Meshroom subgraphs from the Python shell of a software (Houdini, Maya, Nuke) or any Python script,
in the current session: the live nodes run one after the other in memory, as fast as running their
scripts directly, without any cache file.

    import meshroom.subgraph
    outputs = meshroom.subgraph.run("/path/to/turntable.mgt", {"asset": "/path/asset.usd"})
    outputs = meshroom.subgraph.run("/path/to/comp.mgt", frames=(1001, 1100))

Meshroom (and its dependencies, such as psutil) must be importable: add its folder to PYTHONPATH, and
the folders of the plugins providing the live nodes to MESHROOM_NODES_PATH / MESHROOM_PLUGINS_PATH.
"""
import logging
from typing import Optional, Sequence, Union

from meshroom.core.subgraph import Loop, SubGraphError, SubGraphPlan, contextNames, run as _run

__all__ = ["run", "load", "Loop", "SubGraphError", "contextNames", "ensureNodes"]

_nodesLoaded = False


def ensureNodes():
    """ Load the node types (built-in nodes and plugins) once, if they are not loaded yet. """
    global _nodesLoaded
    if _nodesLoaded:
        return
    import meshroom.core
    if meshroom.core.pluginManager.getNodeDescProvider("GraphInput") is None:
        meshroom.core.initNodes()
        meshroom.core.initPlugins()
    _nodesLoaded = True


def load(source) -> SubGraphPlan:
    """ The plan of a subgraph (template path, JSON, or serialized graph dict), to run it several times. """
    ensureNodes()
    return SubGraphPlan.cached(source)


def run(source, inputs: Optional[dict] = None, context: Optional[str] = None,
        frames: Optional[Union[Sequence[int], tuple]] = None, step: int = 1, iterations: Optional[int] = None,
        variables: Optional[dict] = None, logger: Optional[logging.Logger] = None) -> dict:
    """
    Run a subgraph in the current interpreter and return the values of its GraphOutput ports.

    Args:
        source: a template path (.mgt / .mg), a JSON string, a serialized graph dict, or a plan from load().
        inputs: values of its GraphInput ports {port name: value}, any Python objects.
        context: "houdini", "maya", "nuke", "python"...; by default the one needed by its nodes. From the
                 software itself, its session is used as it is (nothing is opened or closed).
        frames: a tuple (first, last) to run it once per frame (every `step` frames), or a list of frames.
        iterations: run it N times, the outputs feeding the inputs of the same name.
        variables: values shared by the nodes (ctx.variables).

    Raises:
        SubGraphError: an error in a node (its name is in the message).
    """
    ensureNodes()
    if frames is not None and iterations is not None:
        raise ValueError("Use either frames or iterations.")
    if frames is not None:
        if isinstance(frames, tuple) and len(frames) == 2:
            loop = Loop("frames", first=frames[0], last=frames[1], step=step)
        else:
            loop = Loop("frames", frames=list(frames))
    elif iterations is not None:
        loop = Loop("count", iterations=iterations)
    else:
        loop = Loop()
    return _run(source, inputs, context=context, loop=loop, variables=variables, logger=logger)
