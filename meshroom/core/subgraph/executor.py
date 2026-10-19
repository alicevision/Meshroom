import json
import logging
import os
import re
import tempfile
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple

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


def _frameNumber(frame):
    """ A frame as an int when it is a whole frame, else a float (sub-frame). """
    frame = float(frame)
    return int(frame) if frame.is_integer() else frame


class Loop:
    """
    How a subgraph is repeated:
    - mode "none": once;
    - mode "count": `iterations` times; the outputs of an iteration feed the inputs of the same name of
      the next one (e.g. a feedback for a fractal);
    - mode "frames": once per frame from `first` to `last` (included) every `step` frames; independent
      iterations, which can be split between several machines (each runs a sub-range);
    - mode "items": once per item of a list (e.g. shots, assets, layers); independent iterations too, the
      current item is ctx.item (and the "item" output of GraphInput).
    """

    MODES = ("none", "count", "frames", "items")
    # Names of the modes in the user interface
    ALIASES = {"frameRange": "frames", "itemList": "items"}

    def __init__(self, mode: str = "none", iterations: int = 1, first: int = 1, last: int = 1, step: int = 1,
                 frames: Optional[List[int]] = None, items: Optional[List] = None):
        mode = self.ALIASES.get(mode, mode)
        if mode not in self.MODES:
            raise ValueError(f"Unknown loop mode '{mode}' (none, count, frameRange, itemList).")
        self.items = list(items) if items is not None else []
        self.mode = mode
        self.iterations = max(0, int(iterations))
        # The step can be a fraction of frame (e.g. 0.1 for a cache with sub-frames)
        step = float(step)
        if step <= 0:
            raise ValueError(f"The step of a frame loop must be positive ({step}).")
        self.first, self.last = int(first), int(last)
        self.step = int(step) if step.is_integer() else step
        # Explicit frames of a frame loop (a part of the range, run by one task of the farm)
        self._frames = [_frameNumber(frame) for frame in frames] if frames is not None else None

    @property
    def frames(self) -> List[int]:
        """ All the frames of a frame loop (empty for the other modes). """
        if self.mode != "frames":
            return []
        if self._frames is not None:
            return list(self._frames)
        if isinstance(self.step, int):
            return list(range(self.first, self.last + 1, self.step))
        # Sub-frames: computed from the first frame (no accumulated error), rounded to 1e-6
        count = int((self.last - self.first) / self.step + 1e-9) + 1
        return [_frameNumber(round(self.first + index * self.step, 6)) for index in range(count)]

    @property
    def size(self) -> int:
        """ The number of independent steps that can be split between tasks (frames or items), else 1. """
        if self.mode == "frames":
            return len(self.frames)
        if self.mode == "items":
            return len(self.items)
        return 1

    def subset(self, start: int, end: int) -> "Loop":
        """ The same frame / item loop restricted to its frames / items [start:end] (by index). """
        if self.mode == "items":
            return Loop("items", items=self.items[start:end])
        return Loop("frames", first=self.first, last=self.last, step=self.step, frames=self.frames[start:end])

    def steps(self) -> List[Tuple[int, Optional[int]]]:
        """ The (iteration, frame) of each run of the subgraph (frame None outside of a frame loop). """
        if self.mode == "count":
            return [(i, None) for i in range(self.iterations)]
        if self.mode == "frames":
            return list(enumerate(self.frames))
        if self.mode == "items":
            return [(i, None) for i in range(len(self.items))]
        return [(0, None)]

    def itemAt(self, iteration: int):
        """ The item of an iteration of an item loop (None for the other modes). """
        return self.items[iteration] if self.mode == "items" and 0 <= iteration < len(self.items) else None

    def asDict(self) -> dict:
        data = {"mode": self.mode, "iterations": self.iterations, "first": self.first, "last": self.last,
                "step": self.step}
        if self._frames is not None:
            data["frames"] = list(self._frames)
        if self.mode == "items":
            data["items"] = list(self.items)
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
                 parent: Optional["RunContext"] = None, onNode: Optional[Callable[[str, str, str], None]] = None):
        self.context = context
        self.loop = loop
        self.iteration = 0
        self.frame: Optional[int] = None
        # Current item of an item loop
        self.item = None
        self.variables = variables if variables is not None else {}
        self.logger = logger or logging.getLogger("meshroom.subgraph")
        self._cancel = cancel
        # Run context of the enclosing subgraph (nested subgraphs), None at the top
        self.parent = parent
        self.nodeName = ""
        # Called with (node name, status, message) as the nodes of the subgraph run (see NodeStatus)
        self.onNode = onNode

    def report(self, nodeName: str, status: str, message: str = ""):
        """ Report the status of a node of the subgraph (only for the top subgraph, never failing the run). """
        if self.onNode is None or self.parent is not None:
            return
        try:
            self.onNode(nodeName, status, message)
        except Exception as e:  # a display problem must not stop the run
            logging.debug(f"[SubGraph] Node status not reported: {e}")

    def checkCancelled(self):
        if self._cancel is not None and self._cancel():
            raise Cancelled()

    def child(self, loop: Loop) -> "RunContext":
        """ The run context of a nested subgraph: the same session, its own loop, the shared variables. """
        return RunContext(self.context, loop, self.variables, self.logger, self._cancel, parent=self)


class NodeStatus:
    """ Statuses of the nodes of a run (RunContext.report): shown on the nodes by the user interface. """
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    # Not run because a node before it failed
    UPSTREAM_ERROR = "UPSTREAM_ERROR"
    # Not run: not needed for the outputs in this context
    SKIPPED = "SKIPPED"


def _nodeDescFor(nodeType: str):
    import meshroom.core
    provider = meshroom.core.pluginManager.getNodeDescProvider(nodeType)
    if provider is None:
        import os
        if not any(os.environ.get(name) for name in ("MESHROOM_PLUGINS_PATH", "MESHROOM_USER_PLUGINS_PATH",
                                                     "MESHROOM_REZ_PLUGINS", "MESHROOM_USER_REZ_PLUGINS")):
            raise SubGraphError(f"Unknown node type '{nodeType}': no plugin is declared in this environment "
                                f"(MESHROOM_USER_REZ_PLUGINS, MESHROOM_PLUGINS_PATH... are not set; they come from the "
                                f"meshroom rez package).")
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


def contextOf(nodeDesc) -> Tuple[str, ...]:
    """
    The contexts a node can run in: its `context` (live nodes), else deduced from the interpreter of a task
    node (hython: houdini, mayapy: maya, nuke: nuke), else "any".
    """
    context = getattr(nodeDesc, "context", None)
    if context:
        return (context,) if isinstance(context, str) else tuple(context)
    executable = os.path.basename(str(getattr(nodeDesc, "pythonExecutable", "") or "")).lower()
    for name, context in (("hython", "houdini"), ("mayapy", "maya"), ("nuke", "nuke")):
        if name in executable:
            return (context,)
    return ("any",)


def environmentNode(plan, contextName: str):
    """
    (nodeDesc, provider) of the first task node of a subgraph needing a context (e.g. a Houdini node of a
    pipeline plugin, with pythonExecutable = "hython"), None if there is none: the subgraph is started in
    another process like that node would be (its interpreter, the process environment of its plugin).
    """
    from meshroom.core import pluginManager
    for name in sorted(plan.nodeDescs):
        nodeDesc = plan.nodeDescs[name]
        if contextName in contextOf(nodeDesc) and getattr(nodeDesc, "pythonExecutable", None):
            provider = pluginManager.getNodeDescProvider(plan.graphData[name]["nodeType"])
            if provider is not None:
                return nodeDesc, provider
    return None


def _topAttributeName(attribute) -> str:
    """ The name of the top-level attribute of an attribute (itself, or the group / list containing it). """
    while attribute.root is not None:
        attribute = attribute.root
    return attribute.name


def _plainValue(attribute):
    """ The value of an attribute as plain Python values (dicts for groups and AnySets, lists for lists). """
    from meshroom.core.attribute import GroupAttribute, ListAttribute
    if attribute.isLink and attribute.inputLink is not None:
        # A connected group gives the values of its source (its children are not connected themselves)
        return _plainValue(attribute.inputLink)
    if isinstance(attribute, GroupAttribute):
        return {child.name: _plainValue(child) for child in attribute.value}
    if isinstance(attribute, ListAttribute):
        return [_plainValue(child) for child in attribute.value]
    return attribute.value


def _setPlainValue(attribute, value):
    """ Set an output attribute from a plain value (a dict sets the children of a group / AnySet). """
    from meshroom.core.attribute import GroupAttribute
    if isinstance(attribute, GroupAttribute) and isinstance(value, dict):
        for child in attribute.value:
            if child.name in value:
                _setPlainValue(child, value[child.name])
        return
    attribute.value = value


# Public names, for the nodes and the user interface
plainValue = _plainValue
setPlainValue = _setPlainValue


def findAttribute(graph, path: str):
    """ The attribute "Node.attribute" or "Node.group.child" of a graph; raises SubGraphError if missing. """
    nodeName, _, attributePath = path.partition(".")
    node = graph.node(nodeName)
    if node is None or not attributePath:
        raise SubGraphError(f"No attribute '{path}' (unknown node or attribute).")
    names = attributePath.split(".")
    if not node.hasAttribute(names[0]):
        raise SubGraphError(f"No attribute '{path}'.")
    attribute = node.attribute(names[0])
    for name in names[1:]:
        children = attribute.value
        attribute = children.get(name) if hasattr(children, "get") and name in children.keys() else None
        if attribute is None:
            raise SubGraphError(f"No attribute '{path}'.")
    return attribute


_PLANS: Dict[tuple, "SubGraphPlan"] = {}


class SubGraphPlan:
    """
    A subgraph ready to run: its serialized nodes, read once. A Graph is built from it for each run
    (see `build`), so that the values set by a run do not stay for the next one.
    """

    def __init__(self, graphData: dict):
        self.graphData = {name: data for name, data in graphData.items() if isinstance(data, dict) and "nodeType" in data}
        self.nodeDescs = {}
        for name, data in self.graphData.items():
            if data["nodeType"] in ("Backdrop",):
                continue
            self.nodeDescs[name] = _nodeDescFor(data["nodeType"])
        inputs = [name for name, nodeDesc in self.nodeDescs.items() if getattr(nodeDesc, "subGraphRole", "") == "input"]
        outputs = [name for name, nodeDesc in self.nodeDescs.items() if getattr(nodeDesc, "subGraphRole", "") == "output"]
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
        when it is modified).
        """
        if isinstance(source, SubGraphPlan):
            return source
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

    def _ports(self, nodeName: Optional[str]) -> List[Tuple[str, str, str]]:
        if not nodeName:
            return []
        return self.nodeDescs[nodeName].ports(self.graphData[nodeName].get("inputs") or {})

    @property
    def inputPortTypes(self) -> List[Tuple[str, str, str]]:
        """ The (name, type, label) of the input ports of the subgraph (those of its GraphInput node). """
        return self._ports(self.graphInput)

    @property
    def outputPortTypes(self) -> List[Tuple[str, str, str]]:
        return self._ports(self.graphOutput)

    @property
    def inputPorts(self) -> List[str]:
        return [port[0] for port in self.inputPortTypes]

    @property
    def outputPorts(self) -> List[str]:
        return [port[0] for port in self.outputPortTypes]

    def contextNames(self) -> List[str]:
        """ The contexts required by the nodes: those of the nodes that can only run in one context. """
        names = set()
        for nodeDesc in self.nodeDescs.values():
            contexts = contextOf(nodeDesc)
            if len(contexts) == 1 and contexts[0] != "any":
                names.add(contexts[0])
        return sorted(names)

    def checkContext(self, contextName: str):
        """ Raise a SubGraphError if a node cannot run in that context. """
        for name, nodeDesc in self.nodeDescs.items():
            contexts = contextOf(nodeDesc)
            if "any" not in contexts and contextName not in contexts:
                raise SubGraphError(f"'{self.graphData[name]['nodeType']}' cannot run in the '{contextName}' context "
                                    f"(only: {', '.join(contexts)}).", name)

    def build(self, cacheDir: Optional[str] = None):
        """ A new Graph with the nodes of the subgraph (its cache folder: `cacheDir`, else a temporary one). """
        from meshroom.core.graph import Graph
        from meshroom.core.graphIO import GraphIO
        graph = Graph("subGraph")
        graph._deserialize({GraphIO.Keys.Header: {GraphIO.Keys.FileVersion: GraphIO.__version__,
                                                  GraphIO.Keys.Template: True},
                            GraphIO.Keys.Graph: json.loads(json.dumps(self.graphData))})
        graph.cacheDir = cacheDir or _temporaryCacheDir()
        return graph


_TEMPORARY_CACHE_DIR = None


def _temporaryCacheDir() -> str:
    """ The cache folder of the subgraphs run outside of a Meshroom task (one per process). """
    global _TEMPORARY_CACHE_DIR
    if _TEMPORARY_CACHE_DIR is None:
        _TEMPORARY_CACHE_DIR = tempfile.mkdtemp(prefix="meshroomSubGraph")
    return _TEMPORARY_CACHE_DIR


def _ignoredInputs(node, ctx: RunContext) -> set:
    ignoredInputs = getattr(node.nodeDesc, "ignoredInputs", None)
    return set(ignoredInputs(node, ctx) or ()) if callable(ignoredInputs) else set()


def executionOrder(graph, ctx: RunContext) -> list:
    """
    The nodes to run, in order: the nodes without downstream node (and the GraphOutput), and the nodes
    they read, except through the inputs they ignore in this run (see desc.BaseNode.ignoredInputs).
    """
    nodes = [node for node in graph.nodes if node.nodeDesc is not None]
    upstream = {node.name: [] for node in nodes}
    # Links from input attributes (a value typed in a node, e.g. a shot name): read without running the node
    readsInputOf = {node.name: set() for node in nodes}
    hasDownstream = set()
    for edge in graph.edges:
        src, dst = edge.src.node, edge.dst.node
        if src is dst or dst.name not in upstream or src.name not in upstream:
            continue
        if not edge.src.isOutput:
            readsInputOf[dst.name].add(src.name)
            continue
        upstream[dst.name].append((src, _topAttributeName(edge.dst)))
        hasDownstream.add(src.name)
    for name, sources in readsInputOf.items():
        hasDownstream.update(sources)
    goals = [node for node in nodes if node.name not in hasDownstream
             or getattr(node.nodeDesc, "subGraphRole", "") == "output"]

    needed = set()
    stack = list(goals)
    while stack:
        node = stack.pop()
        if node.name in needed:
            continue
        needed.add(node.name)
        ignored = _ignoredInputs(node, ctx)
        stack.extend(src for src, attributeName in upstream[node.name] if attributeName not in ignored)

    # Topological order of the needed nodes (stable: by name among the ready ones); a node reading an input
    # of a needed node runs after it, in case that node changes it
    remaining = {name: {src.name for src, _ in upstream[name] if src.name in needed} | (readsInputOf[name] & needed)
                 for name in needed}
    order = []
    while remaining:
        ready = sorted(name for name, sources in remaining.items() if not sources)
        if not ready:
            raise SubGraphError(f"Cycle between the nodes: {', '.join(sorted(remaining))}.")
        for name in ready:
            order.append(graph.node(name))
            del remaining[name]
        for sources in remaining.values():
            sources.difference_update(ready)
    return order


def _runTaskNode(node, ctx: RunContext):
    """ Run the chunks of a task node in this process (see the module documentation). """
    os.makedirs(node.internalFolder, exist_ok=True)
    if not node.getChunks() or not node._chunksCreated:
        node.createChunks()
    nodeDesc = node.nodeDesc
    nodeDesc.preprocess(node)
    for chunk in node.getChunks():
        ctx.checkCancelled()
        nodeDesc.processChunk(chunk)
    nodeDesc.postprocess(node)


def _runNode(node, ctx: RunContext, inputs: dict, plan: SubGraphPlan):
    from meshroom.core import desc
    nodeDesc = node.nodeDesc
    if isinstance(nodeDesc, desc.LiveNode):
        values = {attribute.name: _plainValue(attribute) for attribute in node.attributes if not attribute.isOutput}
        if node.name == plan.graphInput:
            produced = nodeDesc.executeInput(ctx, values, inputs)
        else:
            produced = nodeDesc.execute(ctx, values)
        for name, value in (produced or {}).items():
            if node.hasAttribute(name):
                _setPlainValue(node.attribute(name), value)
    elif isinstance(nodeDesc, (desc.Node, desc.CommandLineNode)):
        _runTaskNode(node, ctx)
    # Init nodes, backdrops: nothing to run


def stepNodes(graph, order: list, plan: SubGraphPlan, loopMode: str) -> set:
    """
    The names of the nodes run again at each step of a loop (the others only run at the first step): the
    nodes reading the loop state (the iteration / frame outputs of GraphInput, its ports in a count loop
    where they get the outputs of the previous step), the nodes declaring `runsEachStep = True` (live nodes
    by default: they can read ctx.frame; a nested SubGraph), and all the nodes after them.
    """
    from meshroom.core import desc
    stepOutputs = {"iteration", "frame", "item"} | ({"ports"} if loopMode == "count" else set())
    names = {node.name for node in order}
    varying = set()
    for node in order:
        nodeDesc = node.nodeDesc
        if node.name == plan.graphInput:
            varying.add(node.name)
        elif getattr(nodeDesc, "runsEachStep", isinstance(nodeDesc, desc.LiveNode)):
            varying.add(node.name)
    downstream = {name: [] for name in names}
    for edge in graph.edges:
        src, dst = edge.src.node, edge.dst.node
        if src.name not in names or dst.name not in names or not edge.src.isOutput:
            continue
        if src.name == plan.graphInput and _topAttributeName(edge.src) not in stepOutputs:
            continue
        downstream[src.name].append(dst.name)
    stack = list(varying)
    while stack:
        for name in downstream[stack.pop()]:
            if name not in varying:
                varying.add(name)
                stack.append(name)
    return varying


def runGraph(graph, plan: SubGraphPlan, ctx: RunContext, inputs: Optional[dict] = None) -> dict:
    """
    Run a subgraph Graph in an opened context, with its loop: the values of its GraphOutput ports (of the
    last iteration). `inputs` are the values of its GraphInput ports.
    """
    inputs = dict(inputs or {})
    outputs: dict = {}
    order = executionOrder(graph, ctx)
    eachStep = stepNodes(graph, order, plan, ctx.loop.mode)
    planned = {node.name for node in order}
    for node in graph.nodes:
        if node.name not in planned and node.nodeType != "Backdrop":
            ctx.report(node.name, NodeStatus.SKIPPED, "Not run: not needed for the outputs here "
                                                      "(e.g. the scene comes from the session of the software).")
    durations = {}
    for stepIndex, (iteration, frame) in enumerate(ctx.loop.steps()):
        item = ctx.loop.itemAt(iteration)
        if ctx.loop.mode == "none" and ctx.parent is not None:
            # A nested subgraph without its own loop sees the iteration, frame and item of its parent
            iteration, frame, item = ctx.parent.iteration, ctx.parent.frame, ctx.parent.item
        ctx.iteration, ctx.frame, ctx.item = iteration, frame, item
        if ctx.loop.mode != "none":
            ctx.context.beginStep(iteration, frame)
        for index, node in enumerate(order):
            if stepIndex > 0 and node.name not in eachStep:
                # Not depending on the loop: already run at the first step
                continue
            ctx.checkCancelled()
            ctx.nodeName = node.name
            ctx.report(node.name, NodeStatus.RUNNING)
            start = time.perf_counter()
            try:
                _runNode(node, ctx, inputs, plan)
            except (SubGraphError, Cancelled) as e:
                _reportFailure(ctx, order[index:], node.name, str(e))
                raise
            except Exception as e:
                _reportFailure(ctx, order[index:], node.name, f"{type(e).__name__}: {e}")
                raise SubGraphError(f"{type(e).__name__}: {e}", node.name) from e
            elapsed = time.perf_counter() - start
            durations[node.name] = durations.get(node.name, 0.0) + elapsed
            ctx.report(node.name, NodeStatus.SUCCESS, _durationText(durations[node.name]))
            ctx.logger.debug("[SubGraph] %s (%s) in %.1f ms", node.name, node.nodeType, elapsed * 1000)
        if plan.graphOutput:
            outputs = _plainValue(graph.node(plan.graphOutput).attribute("ports"))
        if ctx.loop.mode == "count":
            # Feedback: the outputs feed the inputs of the same name of the next iteration
            inputs.update({name: value for name, value in outputs.items() if name in plan.inputPorts or name in inputs})
    return outputs


def _durationText(seconds: float) -> str:
    return f"Done in {seconds * 1000:.0f} ms" if seconds < 1 else f"Done in {seconds:.2f} s"


def _reportFailure(ctx: RunContext, remaining: list, nodeName: str, message: str):
    """ Report a failed node, and the nodes that were still to run after it. """
    ctx.report(nodeName, NodeStatus.ERROR, message)
    for node in remaining[1:]:
        ctx.report(node.name, NodeStatus.UPSTREAM_ERROR, f"Not run: '{nodeName}' failed.")


def resolveContextName(plan: SubGraphPlan, context: Optional[str] = None) -> str:
    """ The context to run a plan in: `context` if given (not "auto"), else the one its nodes need, else "python". """
    if context and context != "auto":
        return context
    required = plan.contextNames()
    if len(required) > 1:
        raise SubGraphError(f"The nodes need several contexts: {', '.join(required)}.")
    return required[0] if required else "python"


_ACTIVE = threading.local()


def activeRunContext() -> Optional[RunContext]:
    """ The run context of the subgraph being run in this thread (None outside of a run). """
    stack = getattr(_ACTIVE, "stack", None)
    return stack[-1] if stack else None


def run(source, inputs: Optional[dict] = None, context: Optional[str] = None, loop: Optional[Loop] = None,
        variables: Optional[dict] = None, logger: Optional[logging.Logger] = None,
        cancel: Optional[Callable[[], bool]] = None, contextObject: Optional[LiveContext] = None,
        ownsSession: bool = False, overrides: Optional[dict] = None, cacheDir: Optional[str] = None,
        onNode: Optional[Callable[[str, str, str], None]] = None) -> dict:
    """
    Run a subgraph (a template path, a JSON string, a serialized graph dict or a SubGraphPlan) in the
    current interpreter and return the values of its GraphOutput ports.

    Args:
        inputs: values of its GraphInput ports {port name: value}.
        context: name of the context (see contexts.py); by default the one required by the nodes, else "python".
        loop: how many times to run it (see Loop); once by default.
        variables: values shared by the nodes of the run (ctx.variables).
        contextObject: an already opened context; it is then not closed. Inside the run of another subgraph
                       (a nested SubGraph node), the context of that run is used.
        ownsSession: whether the session of the software is used only for this run (a task of Meshroom or of
                     a farm), so that it can be cleaned when closed.
        overrides: {"Node.attribute": value} set before running ("Node.group.child" for a child).
        cacheDir: cache folder of the task nodes of the subgraph (a temporary folder by default).
        onNode: called with (node name, status, message) as its nodes run (see NodeStatus).

    Raises:
        SubGraphError: an error in a node (its name is in the message).
    """
    plan = SubGraphPlan.cached(source)
    loop = loop or Loop()
    parent = activeRunContext()
    if contextObject is None and parent is not None:
        contextObject = parent.context
    ownContext = contextObject is None
    if ownContext:
        context = resolveContextName(plan, context)
        contextObject = createContext(context, ownsSession)
        if not contextObject.isAvailable():
            raise SubGraphError(f"The '{context}' context is not available in this interpreter "
                                f"(run it with: {' '.join(contextObject.interpreter()) or '?'}).")
        contextObject.open()
    stack = getattr(_ACTIVE, "stack", None)
    if stack is None:
        stack = _ACTIVE.stack = []
    try:
        plan.checkContext(contextObject.name)
        if parent is not None:
            ctx = RunContext(contextObject, loop, parent.variables if variables is None else variables,
                             logger or parent.logger, cancel or parent._cancel, parent=parent)
        else:
            ctx = RunContext(contextObject, loop, variables, logger, cancel, onNode=onNode)
        graph = plan.build(cacheDir)
        for path, value in (overrides or {}).items():
            findAttribute(graph, path).value = value
        stack.append(ctx)
        try:
            return runGraph(graph, plan, ctx, inputs)
        finally:
            stack.pop()
    finally:
        if ownContext:
            contextObject.close()
