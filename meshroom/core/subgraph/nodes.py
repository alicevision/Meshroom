"""
Shared parts of the subgraph node descriptors (meshroom/nodes/subgraph): the attributes of the nodes
running a subgraph (SubGraph) and the synchronization of their ports.
"""
import functools
import json
import re
import logging
import os
from typing import Dict, Optional

from meshroom.core import desc

from .executor import Loop, SubGraphError, SubGraphPlan, _nodeDescFor, readGraphData
from .ports import PORT_TYPES, anySetPorts, formatPortSpec, parsePortSpec, syncAnySet


def portSpecParam(name: str = "portSpec", label: str = "Ports", value: str = "") -> desc.StringParam:
    """
    A port spec attribute (see ports.py): the ports of an AnySet attribute, kept in sync with its children,
    which are edited in the user interface (hidden, advanced).
    """
    return desc.StringParam(
        name=name,
        label=label,
        description="Ports, kept in sync with the children of the matching AnySet attribute (edit those).\n"
                    "Also accepts names separated by commas, each optionally followed by a type: 'image, count:IntParam'.\n"
                    f"Types: {', '.join(PORT_TYPES)} (LiveValue by default: any value); other types (groups, "
                    "choices...) are written with their full description.",
        value=value,
        invalidate=False,
        advanced=True,
        visible=False,
    )


def subGraphSourceParams() -> list:
    """ Where a subgraph is read from: embedded in the node and/or a template file. """
    return [
        desc.File(
            name="template",
            label="Template",
            description="Template (.mgt / .mg) of the subgraph, used when the subgraph is not embedded.",
            value="",
        ),
        desc.StringParam(
            name="subGraph",
            label="Embedded Subgraph",
            description="The subgraph saved in the node (its nodes in JSON), edited by entering the node.\n"
                        "When it is set, the template is not used.",
            value="",
            advanced=True,
        ),
        desc.PushButtonParam(
            name="makeLocal",
            label="Make Local",
            description="Copy the template in the node, to edit it without changing the template file.",
            enabled=lambda node: bool(node.template.value) and not node.subGraph.value,
        ),
    ]


# Loop modes shown in the user interface ("frames" is still read: projects saved before the rename)
LOOP_MODES = ("none", "count", "frameRange", "itemList")


def isFrameLoop(mode) -> bool:
    return mode in ("frameRange", "frames")


def isItemLoop(mode) -> bool:
    return mode in ("itemList", "items")


def parseItems(text) -> list:
    """ The items of an item list: separated by commas or new lines, spaces around them removed. """
    if isinstance(text, (list, tuple)):
        return [str(item).strip() for item in text if str(item).strip()]
    return [item.strip() for item in re.split(r"[,\n]", text or "") if item.strip()]


def contextParam() -> desc.ChoiceParam:
    from .contexts import contextNames
    return desc.ChoiceParam(
        name="context",
        label="Context",
        description="Software in which the live nodes run, opened once for the whole subgraph.\n"
                    " - auto: the one needed by the nodes (Python if none).",
        value="auto",
        values=["auto"] + contextNames(),
    )


def loopParams(withFarmSplit: bool = False) -> list:
    """ The loop attributes (see executor.Loop); `withFarmSplit` adds the frames per task of the farm. """
    params = [
        desc.ChoiceParam(
            name="loopMode",
            label="Loop",
            description="How the subgraph is repeated:\n"
                        " - none: once.\n"
                        " - count: a number of iterations, the outputs feeding the inputs of the same name.\n"
                        " - frameRange: once per frame of a frame range.\n"
                        " - itemList: once per item of a list (e.g. shots), the item given by GraphInput.",
            value="none",
            values=list(LOOP_MODES),
        ),
        desc.IntParam(
            name="iterations",
            label="Iterations",
            description="Number of iterations (count loop).",
            value=1,
            range=(0, 100, 1),
            enabled=lambda node: node.loopMode.value == "count",
        ),
        frameRangeGroup(isOutput=False),
        desc.StringParam(
            name="items",
            label="Items",
            description="Items of the item loop, separated by commas (or new lines): 'mr_001, mr_002, mr_003'.",
            value="",
            enabled=lambda node: isItemLoop(node.loopMode.value),
        ),
        desc.FloatParam(
            name="frameStep",
            label="Frame Step",
            description="Step between the frames of the frame loop; a fraction of frame for sub-frames (e.g. 0.1\n"
                        "for a cache with 10 samples per frame).",
            value=1.0,
            range=(0.01, 10.0, 0.01),
            enabled=lambda node: isFrameLoop(node.loopMode.value),
        ),
    ]
    if withFarmSplit:
        params.append(desc.IntParam(
            name="framesPerTask",
            label="Frames / Items Per Task",
            description="Frames (or items) run by each task (on several machines of a farm); 0: all in one task.",
            value=0,
            range=(0, 100, 1),
            enabled=lambda node: isFrameLoop(node.loopMode.value) or isItemLoop(node.loopMode.value),
        ))
    return params


def frameRangeGroup(isOutput: bool):
    """
    The frame range of a frame loop: a "frameRange" group with "start" and "stop" (as HoudiniSetFrameRange),
    so that the one of GraphInput connects at once to a node with the same group.
    """
    enabled = lambda node: isFrameLoop(node.loopMode.value)  # noqa: E731
    return desc.GroupAttribute(
        name="frameRange",
        label="Frame Range",
        description="First and last frame (included) of the frame loop.",
        exposed=True,
        enabled=enabled,
        items=[
            desc.IntParam(name="start", label="Start", description="First frame.",
                          value=None if isOutput else 1001, range=None, enabled=enabled),
            desc.IntParam(name="stop", label="Stop", description="Last frame (included).",
                          value=None if isOutput else 1001, range=None, enabled=enabled),
        ],
    )


def loopFromValues(values: dict) -> Loop:
    """ The Loop described by the loop attributes values {name: value} (frameRange: {"start", "stop"}). """
    frameRange = values.get("frameRange") or {}
    # frameFirst / frameLast: projects saved before the frame range group
    first = frameRange.get("start", values.get("frameFirst", 1001))
    last = frameRange.get("stop", values.get("frameLast", first))
    return Loop(values.get("loopMode") or "none", values.get("iterations", 1), first, last,
                values.get("frameStep", 1), items=parseItems(values.get("items", "")))


LOOP_ATTRIBUTES = ("loopMode", "iterations", "frameRange", "frameStep", "items")


def loopFromNode(node) -> Loop:
    values = {}
    for name in LOOP_ATTRIBUTES:
        if node.hasAttribute(name):
            attribute = node.attribute(name)
            values[name] = ({child.name: child.value for child in attribute.value} if name == "frameRange"
                            else attribute.value)
    return loopFromValues(values)


def graphSource(subGraph: str, template: str):
    """ The source of a subgraph (see executor.readGraphData): the embedded one, else the template. """
    if subGraph and subGraph.strip():
        return subGraph
    if template:
        return template
    return None


def nodeGraphSource(node):
    return graphSource(node.subGraph.value, node.template.value)


def nodePlan(node) -> Optional[SubGraphPlan]:
    """ The plan of the subgraph of a node, None if it has none. """
    source = nodeGraphSource(node)
    return SubGraphPlan.cached(source) if source is not None else None


def _subGraphRole(nodeType: str) -> str:
    """ "input" / "output" for the GraphInput / GraphOutput node types, "" otherwise (or unknown). """
    try:
        return getattr(_nodeDescFor(nodeType), "subGraphRole", "")
    except SubGraphError:
        return ""


def _roleNodes(graphData: dict) -> Dict[str, str]:
    """ {role: node name} of the first GraphInput / GraphOutput nodes of serialized nodes. """
    roles = {}
    for name in sorted(graphData):
        data = graphData[name]
        if isinstance(data, dict) and "nodeType" in data:
            role = _subGraphRole(data["nodeType"])
            if role and role not in roles:
                roles[role] = name
    return roles


def subGraphPorts(source):
    """
    The input and output (name, type, label) ports of a subgraph, from its GraphInput / GraphOutput nodes,
    without checking the other nodes. None when it cannot be read (logged).
    """
    if source is None:
        return [], []
    try:
        graphData = readGraphData(source)
    except (SubGraphError, ValueError, OSError) as e:
        logging.warning(f"[SubGraph] Cannot read the subgraph: {e}")
        return None
    roles = _roleNodes(graphData)
    ports = []
    for role in ("input", "output"):
        name = roles.get(role)
        spec = (graphData[name].get("inputs") or {}).get("portSpec", "") if name else ""
        ports.append(parsePortSpec(spec))
    return ports[0], ports[1]


class _PortSync:
    """ Prevents the synchronizations of the ports of a node from triggering each other. """

    def __init__(self, node):
        self.node = node

    def __enter__(self):
        self.node._subGraphPortSync = getattr(self.node, "_subGraphPortSync", 0) + 1

    def __exit__(self, *args):
        self.node._subGraphPortSync -= 1

    @staticmethod
    def active(node) -> bool:
        return getattr(node, "_subGraphPortSync", 0) > 0


def syncSubGraphPorts(node):
    """ Make the `ins` / `outs` attributes of a node running a subgraph match the ports of its subgraph. """
    if node.subGraph.isLink or node.template.isLink or _PortSync.active(node):
        return
    ports = subGraphPorts(nodeGraphSource(node))
    if ports is None:
        return
    with _PortSync(node):
        syncAnySet(node.attribute("ins"), ports[0])
        syncAnySet(node.attribute("outs"), ports[1])


def defaultSubGraph() -> str:
    """ The subgraph of a new SubGraph node: a GraphInput and a GraphOutput, without ports. """
    from meshroom.core.graphIO import GraphIO
    return json.dumps({
        GraphIO.Keys.Header: {GraphIO.Keys.FileVersion: GraphIO.__version__, GraphIO.Keys.Template: True},
        GraphIO.Keys.Graph: {
            "GraphInput_1": {"nodeType": "GraphInput", "position": [0, 0], "inputs": {}},
            "GraphOutput_1": {"nodeType": "GraphOutput", "position": [800, 0], "inputs": {}},
        },
    }, indent=1)


def pushPortsToSubGraph(node):
    """
    Write the ports of the `ins` / `outs` attributes of a node (edited on the node: connections, renames)
    in the GraphInput / GraphOutput nodes of its subgraph, created if missing. A node referencing a template
    gets an embedded copy of it (the template file is not changed).
    """
    if node.subGraph.isLink or node.template.isLink or _PortSync.active(node):
        return
    source = nodeGraphSource(node)
    try:
        fileData = readGraphData(source) if source is not None else {}
    except (SubGraphError, ValueError, OSError) as e:
        logging.warning(f"[SubGraph] {node.name}: cannot update the ports of the subgraph: {e}")
        return
    graphData = json.loads(json.dumps(fileData))
    roles = _roleNodes(graphData)
    changed = False
    for role, anySetName, nodeType, position in (("input", "ins", "GraphInput", [0, 0]),
                                                 ("output", "outs", "GraphOutput", [800, 0])):
        spec = formatPortSpec(anySetPorts(node.attribute(anySetName)))
        name = roles.get(role)
        if name is None:
            if not spec:
                continue
            name = nodeType + "_1"
            while name in graphData:
                name += "_"
            graphData[name] = {"nodeType": nodeType, "position": position, "inputs": {}}
        inputs = graphData[name].setdefault("inputs", {})
        if formatPortSpec(parsePortSpec(inputs.get("portSpec", ""))) == spec:
            continue
        inputs["portSpec"] = spec
        # The children saved with the node are restored from the port spec
        graphData[name].pop("outputs", None)
        changed = True
    if not changed:
        return
    from meshroom.core.graphIO import GraphIO
    with _PortSync(node):
        if not node.subGraph.value and node.template.value:
            logging.info(f"[SubGraph] {node.name}: the template is copied in the node to change its ports.")
            node.template.value = ""
        node.subGraph.value = json.dumps({
            GraphIO.Keys.Header: {GraphIO.Keys.FileVersion: GraphIO.__version__, GraphIO.Keys.Template: True},
            GraphIO.Keys.Graph: graphData}, indent=1)


def watchSubGraphPorts(node):
    """ Write the ports edited on the node (`ins` / `outs` children) in its subgraph when they change. """
    slot = functools.partial(pushPortsToSubGraph, node)
    # Kept on the node: the signals of the standalone backend only keep weak references
    node._subGraphPortSlot = slot
    node.attribute("ins").flatStaticChildrenChanged.connect(slot)
    node.attribute("outs").flatStaticChildrenChanged.connect(slot)


def syncSpecPorts(node, specName: str, anySetName: str):
    """ Make the children of an AnySet attribute match a port spec attribute. """
    spec = node.attribute(specName)
    if spec.isLink or _PortSync.active(node):
        return
    with _PortSync(node):
        syncAnySet(node.attribute(anySetName), parsePortSpec(spec.value))


def writePortSpec(node, specName: str, anySetName: str):
    """ Write the children of an AnySet attribute (edited in the user interface) in its port spec attribute. """
    spec = node.attribute(specName)
    if spec.isLink or _PortSync.active(node):
        return
    value = formatPortSpec(anySetPorts(node.attribute(anySetName)))
    if formatPortSpec(parsePortSpec(spec.value)) != value:
        with _PortSync(node):
            spec.value = value


def watchSpecPorts(node, specName: str, anySetName: str):
    """ Keep a port spec attribute and the children of an AnySet attribute in sync, both ways. """
    syncSpecPorts(node, specName, anySetName)
    slot = functools.partial(writePortSpec, node, specName, anySetName)
    slots = getattr(node, "_portSpecSlots", None)
    if slots is None:
        slots = node._portSpecSlots = []
    slots.append(slot)
    node.attribute(anySetName).flatStaticChildrenChanged.connect(slot)


def makeLocal(node):
    """ Copy the template of a node in its embedded subgraph (JSON of the nodes). """
    template = node.template.value
    if not template or not os.path.isfile(template):
        raise SubGraphError(f"Template not found: {template}", node.name)
    with _PortSync(node):
        node.subGraph.value = json.dumps(readGraphData(template), indent=1)
        node.template.value = ""
