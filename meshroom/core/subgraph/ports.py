"""
Ports of the subgraphs: the named values entering and leaving a subgraph (GraphInput / GraphOutput nodes)
and the matching attributes of the nodes that run it (SubGraph).

The ports are the children of AnySet attributes, edited in the user interface like any AnySet child
(connect to add one, rename, change its label, reorder, remove). They are also written in a hidden string
attribute (the "port spec"), so that templates (which do not save output attributes) keep them: a JSON list
of {"name", "type", "label"}, plus "desc" (the full description: choices, items of a group...) for the types
that are not simple ones. A plain list of names, each optionally followed by a type
("image, mask, count:IntParam"), is read too.

The type of a port is any attribute type (a frame range group, a choice...), the one of the attribute connected
to it; the default one, LiveValue, holds any value.
"""
import json
import logging
import re
from typing import Iterable, List, Optional, Tuple

# Attribute types of the ports (desc class names)
PORT_TYPES = ("LiveValue", "IntParam", "FloatParam", "StringParam", "BoolParam", "File")
DEFAULT_PORT_TYPE = "LiveValue"

_PORT_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# A port: (name, type, label, full description or None). The full description (see
# meshroom.core.desc.serialization) is kept for the types that are not simple (groups, choices, lists...)
Port = Tuple[str, str, str, Optional[dict]]


def _port(name: str, portType: str = "", label: str = "", description: Optional[dict] = None) -> Port:
    portType = portType or DEFAULT_PORT_TYPE
    if portType not in PORT_TYPES and not description:
        portType = DEFAULT_PORT_TYPE
    if portType == DEFAULT_PORT_TYPE:
        description = None
    return name, portType, label or name, description


def parsePortSpec(spec) -> List[Port]:
    """
    The (name, type, label, description) of the ports of a port spec (see the module documentation).
    Invalid or duplicated names are skipped, unknown types without description replaced by LiveValue.
    """
    if not isinstance(spec, str) or not spec.strip():
        return []
    items = []
    if spec.lstrip().startswith("["):
        try:
            items = [(item.get("name", ""), item.get("type", ""), item.get("label", ""), item.get("desc"))
                     for item in json.loads(spec) if isinstance(item, dict)]
        except ValueError:
            logging.warning(f"[SubGraph] Invalid port spec: {spec}")
            return []
    else:
        for item in re.split(r"[,\n;]", spec):
            name, _, portType = item.strip().partition(":")
            items.append((name.strip(), portType.strip(), "", None))
    ports = []
    names = set()
    for name, portType, label, description in items:
        if not name:
            continue
        if not _PORT_NAME.match(name) or name in names:
            logging.warning(f"[SubGraph] Invalid or duplicated port name '{name}' skipped.")
            continue
        names.add(name)
        ports.append(_port(name, portType, label, description))
    return ports


def formatPortSpec(ports: Iterable[tuple]) -> str:
    """ The port spec (JSON) of a list of (name, type[, label[, description]]); empty without ports. """
    ports = [_port(*port) for port in ports]
    if not ports:
        return ""
    data = []
    for name, portType, label, description in ports:
        item = {"name": name, "type": portType, "label": label}
        if description:
            item["desc"] = description
        data.append(item)
    return json.dumps(data)


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
    """ The ports of the children of an AnySet attribute (with the full description of the complex types). """
    from meshroom.core.desc.serialization import describeAttribute
    ports = []
    for child in anySet.value:
        portType = type(child.desc).__name__
        # Also for the simple types: their default value and range
        description = None if portType == DEFAULT_PORT_TYPE else describeAttribute(child.desc)
        ports.append(_port(child.name, portType, child.label, description))
    return ports


def sameDescription(first: Optional[dict], second: Optional[dict]) -> bool:
    """ Whether two full descriptions of ports match, whatever their names and labels. """
    def strip(data):
        return {key: value for key, value in (data or {}).items() if key not in ("name", "label")}
    return strip(first) == strip(second)


def _needsNewChild(child, port: Port) -> bool:
    """ Whether the child of an AnySet must be recreated to match a port: other type, or other description. """
    from meshroom.core.desc.serialization import describeAttribute
    portType, description = port[1], port[3]
    if type(child.desc).__name__ != portType:
        return portType != DEFAULT_PORT_TYPE
    return bool(description) and not sameDescription(description, describeAttribute(child.desc))


def _insertChild(anySet, port: Port, index: int):
    """ Insert a child attribute for a port in an AnySet (any type, from its full description). """
    from meshroom.core.attribute import attributeFactory
    from meshroom.core.desc.serialization import buildAttributeDesc
    name, portType, label, description = port
    if description:
        attributeDesc = buildAttributeDesc(description, name=name, label=label)
    else:
        attributeDesc = buildAttributeDesc({"type": portType, "value": None}, name=name, label=label)
    child = attributeFactory(attributeDesc, value=None, isOutput=anySet.isOutput, node=anySet.node, root=anySet)
    if child.isOutput:
        child._isOutput = True
        child._desc._isDynamicValue = True
    anySet._value.insert(index, child)
    anySet.flatStaticChildrenChanged.emit()
    return child


def syncAnySet(anySet, ports: Iterable[tuple]) -> bool:
    """
    Make the children of an AnySet attribute match a list of ports (name, type[, label[, description]]):
    remove the children that are not in the list (and their connections), add the missing ones, recreate
    the ones whose type or description changed (keeping their connections when they are still valid), update the labels
    and the order. Returns whether something changed.
    """
    ports = [_port(*port) for port in ports]
    wanted = {port[0]: port for port in ports}
    changed = False
    graph = anySet.node.graph if anySet.node else None

    def connectedEdges(child):
        if graph is None:
            return []
        return [edge for edge in list(graph.edges) if edge.src is child or edge.dst is child]

    for child in list(anySet.value):
        port = wanted.get(child.name)
        if port is not None and not _needsNewChild(child, port):
            continue
        # Removed port, or a port whose type or description changed (e.g. choices lost by a former version)
        edges = [(edge.src, edge.dst) for edge in connectedEdges(child)]
        # A connection not applied yet (while loading, "{Node.attribute}") is kept as such
        linkExpression = getattr(child, "_linkExpression", None)
        # A value typed on the child (not its default) is kept by the recreated child
        from .executor import plainValue
        typedValue = plainValue(child) if not edges and not linkExpression and not child.isDefault else None
        for edge in connectedEdges(child):
            graph.removeEdge(edge.dst)
        index = list(anySet.value).index(child)
        anySet.removeAttribute(child)
        changed = True
        if port is not None:
            newChild = _insertChild(anySet, port, index)
            if linkExpression and not edges:
                newChild._linkExpression = linkExpression
            if typedValue is not None:
                from .executor import setPlainValue
                try:
                    setPlainValue(newChild, typedValue)
                except Exception as e:
                    logging.warning(f"[SubGraph] Value of '{newChild.fullName}' not kept ({e}).")
            for src, dst in edges:
                src, dst = (newChild, dst) if src is child else (src, newChild)
                try:
                    graph.addEdge(src, dst)
                except Exception as e:
                    logging.warning(f"[SubGraph] Connection {src.fullName} -> {dst.fullName} not restored: {e}")
    existing = {child.name: child for child in anySet.value}
    for index, port in enumerate(ports):
        name, _, label, _ = port
        child = existing.get(name)
        if child is None:
            _insertChild(anySet, port, min(index, len(anySet.value)))
            changed = True
            continue
        if child.label != label:
            anySet.renameAttribute(child, name, label)
            changed = True
        if list(anySet.value).index(child) != index:
            anySet.moveAttribute(child, index)
            changed = True
    return changed
