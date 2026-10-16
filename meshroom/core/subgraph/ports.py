"""
Ports of the subgraphs: the named values entering and leaving a subgraph (GraphInput / GraphOutput nodes)
and the matching attributes of the nodes that run it (SubGraph, LiveSubGraph).

The ports are written in a string attribute (a "port spec"): names separated by commas or new lines,
each optionally followed by an attribute type, e.g. "image, mask, count:IntParam". The default type,
LiveValue, holds any value. The children of an AnySet attribute are kept in sync with a spec (syncAnySet),
so that each port is an attribute that can be connected.
"""
import logging
import re
from typing import Iterable, List, Tuple

# Attribute types of the ports (desc class names)
PORT_TYPES = ("LiveValue", "IntParam", "FloatParam", "StringParam", "BoolParam", "File")
DEFAULT_PORT_TYPE = "LiveValue"

_PORT_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def parsePortSpec(spec) -> List[Tuple[str, str]]:
    """
    The (name, type) of the ports written in a port spec (see the module documentation).
    Invalid or duplicated names are skipped, unknown types replaced by LiveValue (with a warning).
    """
    if not isinstance(spec, str):
        return []
    ports = []
    names = set()
    for item in re.split(r"[,\n;]", spec):
        item = item.strip()
        if not item:
            continue
        name, _, portType = item.partition(":")
        name, portType = name.strip(), portType.strip() or DEFAULT_PORT_TYPE
        if not _PORT_NAME.match(name) or name in names:
            logging.warning(f"[SubGraph] Invalid or duplicated port name '{name}' skipped.")
            continue
        if portType not in PORT_TYPES:
            logging.warning(f"[SubGraph] Unknown port type '{portType}' for '{name}': {DEFAULT_PORT_TYPE} used.")
            portType = DEFAULT_PORT_TYPE
        names.add(name)
        ports.append((name, portType))
    return ports


def formatPortSpec(ports: Iterable[Tuple[str, str]]) -> str:
    """ The port spec of a list of (name, type). """
    return ", ".join(name if portType == DEFAULT_PORT_TYPE else f"{name}:{portType}" for name, portType in ports)


def anySetValues(serialized) -> dict:
    """
    {child name: value} of a serialized AnySet: {"children": [{"name", "value"...}]}, a list of such
    children, or already a {name: value} dict.
    """
    if isinstance(serialized, dict) and isinstance(serialized.get("children"), list):
        serialized = serialized["children"]
    if isinstance(serialized, list):
        return {child["name"]: child.get("value") for child in serialized if isinstance(child, dict) and "name" in child}
    if isinstance(serialized, dict):
        return {key: value for key, value in serialized.items() if key != "expanded"}
    return {}


def anySetPorts(anySet) -> List[Tuple[str, str]]:
    """ The (name, type) of the children of an AnySet attribute. """
    return [(child.name, type(child.desc).__name__) for child in anySet.value]


def syncAnySet(anySet, ports: Iterable[Tuple[str, str]]) -> bool:
    """
    Make the children of an AnySet attribute match a list of (name, type): remove the children that are
    not in the list or have another type (and their connections), add the missing ones in order.
    Returns whether something changed.
    """
    ports = list(ports)
    wanted = dict(ports)
    changed = False
    graph = anySet.node.graph if anySet.node else None
    for child in list(anySet.value):
        childType = type(child.desc).__name__
        if wanted.get(child.name) == childType:
            continue
        if graph is not None:
            for edge in list(graph.edges):
                if edge.src is child or edge.dst is child:
                    graph.removeEdge(edge.dst)
        anySet.removeAttribute(child)
        changed = True
    existing = {child.name for child in anySet.value}
    for index, (name, portType) in enumerate(ports):
        if name in existing:
            continue
        anySet.insertAttribute({"name": name, "label": name, "type": portType, "value": None},
                               min(index, len(anySet.value)))
        changed = True
    return changed
