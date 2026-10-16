"""
Ports of the subgraphs: the named values entering and leaving a subgraph (GraphInput / GraphOutput nodes)
and the matching attributes of the nodes that run it (SubGraph, LiveSubGraph).

The ports are the children of AnySet attributes, edited in the user interface like any AnySet child
(connect to add one, rename, change its label, reorder, remove). They are also written in a hidden string
attribute (the "port spec"), so that templates (which do not save output attributes) keep them: a JSON list
of {"name", "type", "label"}. A plain list of names, each optionally followed by a type
("image, mask, count:IntParam"), is read too.

The type of a port is an attribute type; the default one, LiveValue, holds any value.
"""
import json
import logging
import re
from typing import Iterable, List, Tuple

# Attribute types of the ports (desc class names)
PORT_TYPES = ("LiveValue", "IntParam", "FloatParam", "StringParam", "BoolParam", "File")
DEFAULT_PORT_TYPE = "LiveValue"

_PORT_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# A port: (name, type, label)
Port = Tuple[str, str, str]


def _port(name: str, portType: str = "", label: str = "") -> Port:
    portType = portType or DEFAULT_PORT_TYPE
    if portType not in PORT_TYPES:
        portType = DEFAULT_PORT_TYPE
    return name, portType, label or name


def parsePortSpec(spec) -> List[Port]:
    """
    The (name, type, label) of the ports of a port spec (see the module documentation).
    Invalid or duplicated names are skipped, unknown types replaced by LiveValue.
    """
    if not isinstance(spec, str) or not spec.strip():
        return []
    items = []
    if spec.lstrip().startswith("["):
        try:
            items = [(item.get("name", ""), item.get("type", ""), item.get("label", ""))
                     for item in json.loads(spec) if isinstance(item, dict)]
        except ValueError:
            logging.warning(f"[SubGraph] Invalid port spec: {spec}")
            return []
    else:
        for item in re.split(r"[,\n;]", spec):
            name, _, portType = item.strip().partition(":")
            items.append((name.strip(), portType.strip(), ""))
    ports = []
    names = set()
    for name, portType, label in items:
        if not name:
            continue
        if not _PORT_NAME.match(name) or name in names:
            logging.warning(f"[SubGraph] Invalid or duplicated port name '{name}' skipped.")
            continue
        names.add(name)
        ports.append(_port(name, portType, label))
    return ports


def formatPortSpec(ports: Iterable[tuple]) -> str:
    """ The port spec (JSON) of a list of (name, type[, label]); empty without ports. """
    ports = [_port(*port) for port in ports]
    if not ports:
        return ""
    return json.dumps([{"name": name, "type": portType, "label": label} for name, portType, label in ports])


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


def anySetPorts(anySet) -> List[Port]:
    """ The (name, type, label) of the children of an AnySet attribute (LiveValue for other types). """
    return [_port(child.name, type(child.desc).__name__, child.label) for child in anySet.value]


def syncAnySet(anySet, ports: Iterable[tuple]) -> bool:
    """
    Make the children of an AnySet attribute match a list of (name, type[, label]): remove the children
    that are not in the list (and their connections), add the missing ones, update the labels and the
    order. A child of the same name is kept with its connections, whatever its type.
    Returns whether something changed.
    """
    ports = [_port(*port) for port in ports]
    wanted = {name: label for name, _, label in ports}
    changed = False
    graph = anySet.node.graph if anySet.node else None
    for child in list(anySet.value):
        if child.name in wanted:
            continue
        if graph is not None:
            for edge in list(graph.edges):
                if edge.src is child or edge.dst is child:
                    graph.removeEdge(edge.dst)
        anySet.removeAttribute(child)
        changed = True
    existing = {child.name: child for child in anySet.value}
    for index, (name, portType, label) in enumerate(ports):
        child = existing.get(name)
        if child is None:
            anySet.insertAttribute({"name": name, "label": label, "type": portType, "value": None},
                                   min(index, len(anySet.value)))
            changed = True
            continue
        if child.label != label:
            anySet.renameAttribute(child, name, label)
            changed = True
        if list(anySet.value).index(child) != index:
            anySet.moveAttribute(child, index)
            changed = True
    return changed
