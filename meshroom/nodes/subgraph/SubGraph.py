__version__ = "1.0"

import json
import math
import os
import shlex

from meshroom.core import desc
from meshroom.core.subgraph import activeRunContext, contextClass, resolveContextName, run
from meshroom.core.subgraph.nodes import (contextParam, isFrameLoop, loopFromNode, loopParams, makeLocal, nodePlan,
                                          subGraphSourceParams, syncSubGraphPorts, watchSubGraphPorts, defaultSubGraph)
from meshroom.core.utils import VERBOSE_LEVEL


class FrameLoopSize:
    """ Size of a SubGraph node: its number of frames in a frame loop, else 1. """

    def __call__(self, node):
        if not isFrameLoop(node.loopMode.value):
            return 1
        return max(1, len(loopFromNode(node).frames))


class FrameLoopParallelization(desc.Parallelization):
    """ The frames of a frame loop split in tasks of `framesPerTask` frames (all in one task with 0). """

    def getSizes(self, node):
        size = max(1, node.size)
        perTask = node.framesPerTask.value if isFrameLoop(node.loopMode.value) else 0
        blockSize = perTask if perTask > 0 else size
        return blockSize, size, int(math.ceil(size / float(blockSize)))


def _storable(value):
    """ A value that can be saved with the outputs of the node (JSON), else its text. """
    try:
        json.dumps(value)
        return value
    except (TypeError, ValueError):
        return str(value)


class SubGraph(desc.Node):
    """
    Runs a subgraph as one task: the software of its context (Python, Houdini...) is opened once, the
    nodes of the subgraph (live nodes and task nodes) run one after the other in this session, the values
    going from node to node in memory, then it is closed. Inside another subgraph, it runs in the session
    of its parent. Double-click the node to edit its subgraph.

    The subgraph is embedded in the node, or read from a template (.mgt). Its GraphInput ports are the
    inputs of the node (`ins`), its GraphOutput ports its outputs (`outs`).

    Loops: the subgraph can run a number of iterations (the outputs feeding the inputs of the same name)
    or once per frame of a frame range, split in tasks of several frames on a farm.
    """
    category = "SubGraph"
    size = FrameLoopSize()
    parallelization = FrameLoopParallelization()

    inputs = subGraphSourceParams() + [contextParam()] + loopParams(withFarmSplit=True) + [
        desc.AnySet(
            name="ins",
            label="Inputs",
            description="Values given to the GraphInput ports of the subgraph.",
            exposed=True,
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
        ),
    ]

    outputs = [
        desc.AnySet(
            name="outs",
            label="Outputs",
            description="Values of the GraphOutput ports of the subgraph.",
            exposed=True,
        ),
    ]

    @classmethod
    def initDynamicAttributes(cls, node):
        syncSubGraphPorts(node)
        # Ports added / renamed on the node (e.g. by connecting an input) go into the subgraph
        watchSubGraphPorts(node)

    @classmethod
    def onNodeCreated(cls, node):
        # A new node starts with a GraphInput and a GraphOutput (they can be removed)
        if not node.subGraph.value and not node.template.value and not node.subGraph.isLink and not node.template.isLink:
            node.subGraph.value = defaultSubGraph()

    @classmethod
    def onSubGraphChanged(cls, node):
        syncSubGraphPorts(node)

    @classmethod
    def onTemplateChanged(cls, node):
        syncSubGraphPorts(node)

    @classmethod
    def onMakeLocalClicked(cls, node):
        makeLocal(node)

    @staticmethod
    def _environmentNode(node):
        """
        (nodeDesc, provider) of the first task node of the subgraph that needs the context of the subgraph
        (e.g. a Houdini node of a pipeline plugin, with pythonExecutable = "hython"), None if there is none:
        the subgraph task is then started like that node would be (same interpreter, same environment).
        """
        from meshroom.core import pluginManager
        from meshroom.core.subgraph import contextOf
        plan = nodePlan(node)
        if plan is None:
            return None
        contextName = resolveContextName(plan, node.context.value)
        for name in sorted(plan.nodeDescs):
            nodeDesc = plan.nodeDescs[name]
            if contextName in contextOf(nodeDesc) and getattr(nodeDesc, "pythonExecutable", None):
                provider = pluginManager.getNodeDescProvider(plan.graphData[name]["nodeType"])
                if provider is not None:
                    return nodeDesc, provider
        return None

    def getPythonExecutable(self, chunk) -> str:
        """
        The interpreter of the context: the one of a task node of the subgraph needing that context (as it
        would be started on its own), else the interpreter of the context (MESHROOM_HYTHON...) when the
        context cannot run in Python.
        """
        found = self._environmentNode(chunk.node)
        if found is not None:
            return found[0].pythonExecutable
        plan = nodePlan(chunk.node)
        if plan is not None:
            context = contextClass(resolveContextName(plan, chunk.node.context.value))
            if not context.isAvailable() and context.interpreter():
                return " ".join(shlex.quote(arg) for arg in context.interpreter())
        return self.pythonExecutable

    def getProcessProvider(self, chunk):
        """ The process environment of a task node of the subgraph needing its context (see getPythonExecutable). """
        found = self._environmentNode(chunk.node)
        return found[1] if found is not None else super().getProcessProvider(chunk)

    def processChunk(self, chunk):
        node = chunk.node
        try:
            chunk.logManager.start(node.verboseLevel.value)
            plan = nodePlan(node)
            if plan is None:
                raise RuntimeError("The node has no subgraph (no embedded subgraph nor template).")
            loop = loopFromNode(node)
            if loop.mode == "frames":
                # The frames of this task
                loop = loop.subset(chunk.range.start, chunk.range.end)
                chunk.logger.info(f"Frames: {loop.frames}")
            inputs = {child.name: child.value for child in node.ins.value}
            # Inside the run of another subgraph: the session of that run is used, values stay Python objects
            nested = activeRunContext() is not None
            outputs = run(plan, inputs, context=node.context.value, loop=loop, logger=chunk.logger,
                          variables=None if nested else {"nodeName": node.name}, ownsSession=True,
                          cacheDir=os.path.join(node.internalFolder, "subgraph"))
            for child in node.outs.value:
                if child.name in outputs:
                    child.value = outputs[child.name] if nested else _storable(outputs[child.name])
        finally:
            chunk.logManager.end()
