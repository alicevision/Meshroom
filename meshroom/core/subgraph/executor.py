"""
Execution of the subgraphs: chains of live nodes (desc.LiveNode) run in memory, in topological order,
in one context (see contexts.py), without chunks, cache folders or files between the nodes.

A subgraph is read from its serialized form (the "graph" of a .mg / .mgt file, or of the "subGraph"
attribute of a SubGraph node), not from a core Graph: no Qt object is built and the descriptors are only
instantiated, so that running a template from the Python shell of a software costs about the same as
running the scripts of its nodes one after the other.

Values between nodes are any Python objects (an image buffer, a hou.Node...). A node input connected to
the output of another node gets the value that node returned; otherwise its value stored in the graph, or
the default value of its descriptor.

GraphInput / GraphOutput nodes (at most one of each) are the interface of the subgraph: the values given
to `run` come out of the GraphInput ports, and the values entering the GraphOutput ports are returned.

Loops (see Loop): the whole subgraph is run several times, either a number of iterations (the outputs of
an iteration feeding the inputs of the same name of the next one) or once per frame of a frame range.
The live nodes read the loop state with ctx.iteration, ctx.frame, ctx.loop.
"""
import json
import logging
import os
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from .contexts import LiveContext, createContext

# A link to another attribute in a serialized graph: "{NodeName.attribute}" (or "{NodeName.group.child}")
_LINK = re.compile(r"^\{(?P<node>[A-Za-z_][\w]*)\.(?P<attribute>[^{}]+)\}$")


class SubGraphError(RuntimeError):
    """ An error of a subgraph execution, naming the node where it happened. """

    def __init__(self, message: str, nodeName: str = ""):
        super().__init__(f"{nodeName}: {message}" if nodeName else message)
        self.nodeName = nodeName


class Cancelled(Exception):
    pass


class Loop:
    """
    How a subgraph is repeated:
    - mode "none": once;
    - mode "count": `iterations` times; the outputs of an iteration feed the inputs of the same name of
      the next one (e.g. a feedback for a fractal);
    - mode "frames": once per frame from `first` to `last` (included) every `step` frames; independent
      iterations, which can be split between several machines (each runs a sub-range).
    """

    MODES = ("none", "count", "frames")

    def __init__(self, mode: str = "none", iterations: int = 1, first: int = 1, last: int = 1, step: int = 1,
                 frames: Optional[List[int]] = None):
        if mode not in self.MODES:
            raise ValueError(f"Unknown loop mode '{mode}' (none, count, frames).")
        self.mode = mode
        self.iterations = max(0, int(iterations))
        self.first, self.last, self.step = int(first), int(last), max(1, int(step))
        # Explicit frames of a frame loop (a part of the range, run by one task of the farm)
        self._frames = [int(frame) for frame in frames] if frames is not None else None

    @property
    def frames(self) -> List[int]:
        """ All the frames of a frame loop (empty for the other modes). """
        if self.mode != "frames":
            return []
        if self._frames is not None:
            return list(self._frames)
        return list(range(self.first, self.last + 1, self.step))

    def subset(self, start: int, end: int) -> "Loop":
        """ The same frame loop restricted to its frames [start:end] (by index). """
        return Loop("frames", first=self.first, last=self.last, step=self.step, frames=self.frames[start:end])

    def steps(self) -> List[Tuple[int, Optional[int]]]:
        """ The (iteration, frame) of each run of the subgraph (frame None outside of a frame loop). """
        if self.mode == "count":
            return [(i, None) for i in range(self.iterations)]
        if self.mode == "frames":
            return list(enumerate(self.frames))
        return [(0, None)]

    def asDict(self) -> dict:
        data = {"mode": self.mode, "iterations": self.iterations, "first": self.first, "last": self.last,
                "step": self.step}
        if self._frames is not None:
            data["frames"] = list(self._frames)
        return data

    @classmethod
    def fromDict(cls, data: Optional[dict]) -> "Loop":
        return cls(**data) if data else cls()


class RunContext:
    """
    What a live node receives with its inputs (desc.LiveNode.execute(ctx, inputs)): the execution context
    (`context`: the software session), the loop state (`iteration`, `frame`, `loop`), the variables shared
    by the nodes of the run (`variables`, a dict) and a logger.
    """

    def __init__(self, context: LiveContext, loop: Loop, variables: Optional[dict] = None,
                 logger: Optional[logging.Logger] = None, cancel: Optional[Callable[[], bool]] = None,
                 parent: Optional["RunContext"] = None):
        self.context = context
        self.loop = loop
        self.iteration = 0
        self.frame: Optional[int] = None
        self.variables = variables if variables is not None else {}
        self.logger = logger or logging.getLogger("meshroom.subgraph")
        self._cancel = cancel
        # Run context of the enclosing subgraph (nested subgraphs), None at the top
        self.parent = parent
        self.nodeName = ""

    def checkCancelled(self):
        if self._cancel is not None and self._cancel():
            raise Cancelled()

    def child(self, loop: Loop) -> "RunContext":
        """ The run context of a nested subgraph: the same session, its own loop, the shared variables. """
        return RunContext(self.context, loop, self.variables, self.logger, self._cancel, parent=self)


class PlanNode:
    """ A node of a subgraph ready to run: its descriptor instance and its serialized inputs. """

    def __init__(self, name: str, nodeType: str, nodeDesc, inputs: dict, internalInputs: dict):
        self.name = name
        self.nodeType = nodeType
        self.nodeDesc = nodeDesc
        self.inputs = inputs
        self.internalInputs = internalInputs
        # Names of the nodes this one reads (links)
        self.dependencies = sorted({link[0] for link in _links(inputs)})


def _links(value) -> List[Tuple[str, str]]:
    """ The (node, attribute) links found in a serialized value (nested in groups / lists too). """
    if isinstance(value, str):
        match = _LINK.match(value)
        return [(match.group("node"), match.group("attribute"))] if match else []
    if isinstance(value, dict):
        return [link for item in value.values() for link in _links(item)]
    if isinstance(value, (list, tuple)):
        return [link for item in value for link in _links(item)]
    return []


def _nodeDescFor(nodeType: str):
    import meshroom.core
    provider = meshroom.core.pluginManager.getNodeDescProvider(nodeType)
    if provider is None:
        raise SubGraphError(f"Unknown node type '{nodeType}' (is its plugin loaded?).")
    return provider.nodeDescClass()


def readGraphData(source) -> dict:
    """
    The serialized nodes {name: node data} of a subgraph, from a file path (.mg / .mgt), a JSON string, a
    whole graph file content (with "graph") or its "graph" dict itself.
    """
    if isinstance(source, str):
        text = source
        if not source.lstrip().startswith("{"):
            if not os.path.isfile(source):
                raise SubGraphError(f"Subgraph template not found: {source}")
            with open(source, "r", encoding="utf-8") as f:
                text = f.read()
        source = json.loads(text) if text.strip() else {}
    if not isinstance(source, dict):
        raise SubGraphError("A subgraph must be a JSON object.")
    return source.get("graph", source) if ("graph" in source or "header" in source) else source


_PLANS: Dict[tuple, "SubGraphPlan"] = {}


class SubGraphPlan:
    """ The nodes of a subgraph in execution order (see the module documentation). """

    def __init__(self, graphData: dict):
        self.nodes: Dict[str, PlanNode] = {}
        for name, data in graphData.items():
            if not isinstance(data, dict) or "nodeType" not in data:
                continue
            nodeType = data["nodeType"]
            if nodeType in ("Backdrop",):
                continue
            nodeDesc = _nodeDescFor(nodeType)
            from meshroom.core import desc
            if not isinstance(nodeDesc, desc.LiveNode):
                raise SubGraphError(f"'{nodeType}' is not a live node: only live nodes can be in a subgraph.", name)
            self.nodes[name] = PlanNode(name, nodeType, nodeDesc, data.get("inputs", {}) or {},
                                        data.get("internalInputs", {}) or {})
        self.order = self._sort()
        inputs = [n for n in self.nodes.values() if getattr(n.nodeDesc, "subGraphRole", "") == "input"]
        outputs = [n for n in self.nodes.values() if getattr(n.nodeDesc, "subGraphRole", "") == "output"]
        if len(inputs) > 1 or len(outputs) > 1:
            raise SubGraphError("A subgraph has at most one GraphInput and one GraphOutput node.")
        self.graphInput = inputs[0] if inputs else None
        self.graphOutput = outputs[0] if outputs else None

    @classmethod
    def load(cls, source) -> "SubGraphPlan":
        return cls(readGraphData(source))

    @classmethod
    def cached(cls, source) -> "SubGraphPlan":
        """
        The plan of a subgraph, reused while its source does not change (a template file is read again
        when it is modified): nested subgraphs run at each iteration of a loop are only read once.
        """
        if isinstance(source, str) and not source.lstrip().startswith("{") and os.path.isfile(source):
            key = ("file", os.path.abspath(source), os.path.getmtime(source))
        else:
            key = ("data", source if isinstance(source, str) else json.dumps(source, sort_keys=True, default=str))
        plan = _PLANS.get(key)
        if plan is None:
            if len(_PLANS) > 64:
                _PLANS.clear()
            plan = _PLANS[key] = cls.load(source)
        return plan

    def _sort(self) -> List[PlanNode]:
        """ Topological order (Kahn); raises on a cycle or a link to a missing node. """
        for node in self.nodes.values():
            for dependency in node.dependencies:
                if dependency not in self.nodes:
                    raise SubGraphError(f"Link to an unknown node '{dependency}'.", node.name)
        remaining = {name: set(node.dependencies) for name, node in self.nodes.items()}
        order = []
        while remaining:
            ready = sorted(name for name, dependencies in remaining.items() if not dependencies)
            if not ready:
                raise SubGraphError(f"Cycle between the nodes: {', '.join(sorted(remaining))}.")
            for name in ready:
                order.append(self.nodes[name])
                del remaining[name]
            for dependencies in remaining.values():
                dependencies.difference_update(ready)
        return order

    @property
    def inputPortTypes(self) -> List[Tuple[str, str]]:
        """ The (name, type) of the input ports of the subgraph (those of its GraphInput node). """
        return self.graphInput.nodeDesc.ports(self.graphInput.inputs) if self.graphInput else []

    @property
    def outputPortTypes(self) -> List[Tuple[str, str]]:
        return self.graphOutput.nodeDesc.ports(self.graphOutput.inputs) if self.graphOutput else []

    @property
    def inputPorts(self) -> List[str]:
        return [name for name, _ in self.inputPortTypes]

    @property
    def outputPorts(self) -> List[str]:
        return [name for name, _ in self.outputPortTypes]

    def contextNames(self) -> List[str]:
        """ The contexts required by the nodes: those of the nodes that can only run in one context. """
        names = set()
        for node in self.order:
            contexts = node.nodeDesc.contexts()
            if len(contexts) == 1 and contexts[0] != "any":
                names.add(contexts[0])
        return sorted(names)

    def checkContext(self, contextName: str):
        """ Raise a SubGraphError if a node cannot run in that context. """
        for node in self.order:
            contexts = node.nodeDesc.contexts()
            if "any" not in contexts and contextName not in contexts:
                raise SubGraphError(f"'{node.nodeType}' cannot run in the '{contextName}' context "
                                    f"(only: {', '.join(contexts)}).", node.name)


def _resolve(value, results: Dict[str, Dict[str, Any]]):
    """ A serialized input value with its links replaced by the values computed by the upstream nodes. """
    if isinstance(value, str):
        match = _LINK.match(value)
        if not match:
            return value
        nodeName, attribute = match.group("node"), match.group("attribute")
        outputs = results.get(nodeName, {})
        if attribute in outputs:
            return outputs[attribute]
        # A child of an output group ("outputs.port")
        head, _, tail = attribute.partition(".")
        if head in outputs and isinstance(outputs[head], dict) and tail in outputs[head]:
            return outputs[head][tail]
        raise SubGraphError(f"No value for the link to '{nodeName}.{attribute}'.")
    if isinstance(value, dict):
        return {key: _resolve(item, results) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve(item, results) for item in value]
    return value


def _inputValues(node: PlanNode, results: Dict[str, Dict[str, Any]]) -> dict:
    """ The input values of a node: its serialized values (links resolved) over its descriptor defaults. """
    values = {}
    for attrDesc in node.nodeDesc.inputs:
        if attrDesc.name in node.inputs:
            values[attrDesc.name] = _resolve(node.inputs[attrDesc.name], results)
        else:
            values[attrDesc.name] = _defaultValue(attrDesc)
    # Inputs that are not in the descriptor (e.g. dynamic ports of an AnySet) are kept as they are
    for name, value in node.inputs.items():
        if name not in values:
            values[name] = _resolve(value, results)
    return values


def _defaultValue(attrDesc):
    from meshroom.core import desc
    if isinstance(attrDesc, desc.GroupAttribute) and not isinstance(attrDesc, desc.AnySet):
        return {item.name: _defaultValue(item) for item in attrDesc.items}
    if isinstance(attrDesc, desc.ListAttribute):
        return []
    value = attrDesc.value
    return None if callable(value) else value


def runPlan(plan: SubGraphPlan, ctx: RunContext, inputs: Optional[dict] = None) -> dict:
    """
    Run a subgraph in an opened context, with its loop: the values of its GraphOutput ports (of the last
    iteration). `inputs` are the values of its GraphInput ports.
    """
    inputs = dict(inputs or {})
    outputs: dict = {}
    steps = ctx.loop.steps()
    for iteration, frame in steps:
        if ctx.loop.mode == "none" and ctx.parent is not None:
            # A nested subgraph without its own loop sees the iteration and frame of its parent
            iteration, frame = ctx.parent.iteration, ctx.parent.frame
        ctx.iteration, ctx.frame = iteration, frame
        outputs = _runOnce(plan, ctx, inputs)
        if ctx.loop.mode == "count":
            # Feedback: the outputs feed the inputs of the same name of the next iteration
            inputs.update({name: value for name, value in outputs.items() if name in plan.inputPorts or name in inputs})
    return outputs


def _runOnce(plan: SubGraphPlan, ctx: RunContext, inputs: dict) -> dict:
    results: Dict[str, Dict[str, Any]] = {}
    outputs: dict = {}
    for node in plan.order:
        ctx.checkCancelled()
        ctx.nodeName = node.name
        values = _inputValues(node, results)
        start = time.perf_counter()
        try:
            if node is plan.graphInput:
                produced = node.nodeDesc.executeInput(ctx, values, inputs)
            else:
                produced = node.nodeDesc.execute(ctx, values)
        except (SubGraphError, Cancelled):
            raise
        except Exception as e:
            raise SubGraphError(f"{type(e).__name__}: {e}", node.name) from e
        ctx.logger.debug("[SubGraph] %s (%s) in %.1f ms", node.name, node.nodeType, (time.perf_counter() - start) * 1000)
        results[node.name] = produced or {}
        if node is plan.graphOutput:
            outputs = dict(node.nodeDesc.collectOutputs(values))
    return outputs


def resolveContextName(plan: SubGraphPlan, context: Optional[str] = None) -> str:
    """ The context to run a plan in: `context` if given (not "auto"), else the one its nodes need, else "python". """
    if context and context != "auto":
        return context
    required = plan.contextNames()
    if len(required) > 1:
        raise SubGraphError(f"The nodes need several contexts: {', '.join(required)}.")
    return required[0] if required else "python"


def run(source, inputs: Optional[dict] = None, context: Optional[str] = None, loop: Optional[Loop] = None,
        variables: Optional[dict] = None, logger: Optional[logging.Logger] = None,
        cancel: Optional[Callable[[], bool]] = None, contextObject: Optional[LiveContext] = None) -> dict:
    """
    Run a subgraph (a template path, a JSON string or a serialized graph dict) in the current interpreter
    and return the values of its GraphOutput ports.

    Args:
        inputs: values of its GraphInput ports {port name: value}.
        context: name of the context (see contexts.py); by default the one required by the nodes, else "python".
        loop: how many times to run it (see Loop); once by default.
        variables: values shared by the nodes of the run (ctx.variables).
        contextObject: an already opened context (nested runs); it is then not closed.

    Raises:
        SubGraphError: an error in a node (its name is in the message).
    """
    plan = source if isinstance(source, SubGraphPlan) else SubGraphPlan.cached(source)
    loop = loop or Loop()
    ownContext = contextObject is None
    if ownContext:
        context = resolveContextName(plan, context)
        contextObject = createContext(context)
        if not contextObject.isAvailable():
            raise SubGraphError(f"The '{context}' context is not available in this interpreter "
                                f"(run it with: {' '.join(contextObject.interpreter()) or '?'}).")
        contextObject.open()
    try:
        plan.checkContext(contextObject.name)
        ctx = RunContext(contextObject, loop, variables, logger, cancel)
        return runPlan(plan, ctx, inputs)
    finally:
        if ownContext:
            contextObject.close()
