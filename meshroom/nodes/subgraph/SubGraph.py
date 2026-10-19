__version__ = "1.0"

import json
import math
import os
import shlex

from meshroom.core import desc
from meshroom.core.subgraph import activeRunContext, contextClass, resolveContextName, run
from meshroom.core.subgraph.executor import plainValue, setPlainValue
from meshroom.core.subgraph.nodes import (contextParam, isFrameLoop, isItemLoop, loopFromNode, loopParams, makeLocal, nodePlan,
                                          subGraphSourceParams, syncSubGraphPorts, watchSubGraphPorts, defaultSubGraph)
from meshroom.core.utils import VERBOSE_LEVEL


class FrameLoopSize:
    """ Size of a SubGraph node: its number of frames (items) in a frame (item) loop, else 1. """

    def __call__(self, node):
        if not (isFrameLoop(node.loopMode.value) or isItemLoop(node.loopMode.value)):
            return 1
        return max(1, loopFromNode(node).size)


class FrameLoopParallelization(desc.Parallelization):
    """ The frames of a frame loop split in tasks of `framesPerTask` frames (all in one task with 0). """

    def getSizes(self, node):
        size = max(1, node.size)
        splittable = isFrameLoop(node.loopMode.value) or isItemLoop(node.loopMode.value)
        perTask = node.framesPerTask.value if splittable else 0
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

    Loops: the subgraph can run a number of iterations (the outputs feeding the inputs of the same name),
    once per frame of a frame range or once per item of a list, split in tasks of several frames / items on
    a farm.
    """
    category = "SubGraph"
    # In a loop of a parent subgraph, it runs at each step (its nodes can read the frame)
    runsEachStep = True
    size = FrameLoopSize()
    parallelization = FrameLoopParallelization()

    # The inputs first, the template last
    inputs = [
        desc.AnySet(
            name="ins",
            label="Inputs",
            description="Values given to the GraphInput ports of the subgraph (add one by connecting an attribute,\n"
                        "or with the + button).",
            exposed=True,
        ),
        contextParam(),
    ] + loopParams(withFarmSplit=True) + [
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
        ),
    ] + subGraphSourceParams()

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
        """ (nodeDesc, provider) of the task node of the subgraph giving its environment (see executor.environmentNode). """
        from meshroom.core.subgraph.executor import environmentNode
        plan = nodePlan(node)
        if plan is None:
            return None
        return environmentNode(plan, resolveContextName(plan, node.context.value))

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
            if loop.mode in ("frames", "items"):
                # The frames / items of this task
                loop = loop.subset(chunk.range.start, chunk.range.end)
                chunk.logger.info(f"Frames: {loop.frames}" if loop.mode == "frames" else f"Items: {loop.items}")
            inputs = {child.name: plainValue(child) for child in node.ins.value}
            # Inside the run of another subgraph: the session of that run is used, values stay Python objects
            nested = activeRunContext() is not None
            outputs = run(plan, inputs, context=node.context.value, loop=loop, logger=chunk.logger,
                          variables=None if nested else {"nodeName": node.name}, ownsSession=True,
                          cacheDir=os.path.join(node.internalFolder, "subgraph"))
            for child in node.outs.value:
                if child.name in outputs:
                    setPlainValue(child, outputs[child.name] if nested else _storable(outputs[child.name]))
        finally:
            chunk.logManager.end()
