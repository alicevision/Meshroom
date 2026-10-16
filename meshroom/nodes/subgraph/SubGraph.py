__version__ = "1.0"

import json
import math
import shlex

from meshroom.core import desc
from meshroom.core.subgraph import contextClass, resolveContextName, run
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
    Runs a subgraph of live nodes as one task: the software of its context (Python, Houdini...) is opened
    once, the live nodes run one after the other in memory, then it is closed. Double-click the node to
    edit its subgraph.

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

    def getPythonExecutable(self, chunk) -> str:
        """ The interpreter of the context when it cannot run in Python (e.g. hython for Houdini). """
        plan = nodePlan(chunk.node)
        if plan is not None:
            context = contextClass(resolveContextName(plan, chunk.node.context.value))
            if not context.isAvailable() and context.interpreter():
                return " ".join(shlex.quote(arg) for arg in context.interpreter())
        return self.pythonExecutable

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
            outputs = run(plan, inputs, context=node.context.value, loop=loop, logger=chunk.logger,
                          variables={"nodeName": node.name}, ownsSession=True)
            for child in node.outs.value:
                if child.name in outputs:
                    child.value = _storable(outputs[child.name])
        finally:
            chunk.logManager.end()
