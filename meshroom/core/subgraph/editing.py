"""
Editing of subgraphs: entering a node running a subgraph (SubGraph) shows its subgraph as
a graph of its own; leaving it writes the subgraph back in the node (embedded subgraph), or in its
template file when the node only references a template.

SubGraphStack keeps the path from the project graph to the shown subgraph, without any Qt dependency
(the UI keeps one, see meshroom/ui/graph.py).
"""
import json
import logging
from typing import List, Optional

from meshroom.core.graph import Graph
from meshroom.core.graphIO import GraphIO

from .executor import readGraphData
from .nodes import nodeGraphSource

SUBGRAPH_NODE_TYPES = ("SubGraph",)


def isSubGraphNode(node) -> bool:
    return node is not None and getattr(node, "nodeType", "") in SUBGRAPH_NODE_TYPES


def serializeSubGraph(graph: Graph) -> str:
    """ The JSON saved in the "subGraph" attribute: the graph in the template form (non-default values). """
    return json.dumps(graph.serialize(asTemplate=True), indent=1, sort_keys=True)


def buildSubGraph(node, parent=None) -> Graph:
    """ A Graph with the nodes of the subgraph of a node (empty if it has none yet). """
    source = nodeGraphSource(node)
    data = readGraphData(source) if source is not None else {}
    graph = Graph(node.name, parent)
    graph._deserialize({GraphIO.Keys.Header: {GraphIO.Keys.FileVersion: GraphIO.__version__, GraphIO.Keys.Template: True},
                        GraphIO.Keys.Graph: data})
    return graph


def _repairPorts(graphInput, node):
    """
    Give the inputs of a node running a subgraph, and the ports of its GraphInput, the description of the
    attributes connected to the node (types, choices, group items): those saved by a former version could have
    lost them (a frame range group or choices holding any value, a multiple choice become a single one...).
    """
    from meshroom.core.desc.serialization import describeAttribute
    from .nodes import _PortSync
    from .ports import DEFAULT_PORT_TYPE, PORT_TYPES, anySetPorts, sameDescription, syncAnySet
    nodePorts = []
    for child, port in zip(list(node.ins.value), anySetPorts(node.ins)):
        # The description of the connected attribute is the most accurate one
        source = child.inputLink if child.isLink else None
        sourceType = type(source.desc).__name__ if source is not None else ""
        if sourceType and sourceType not in PORT_TYPES and sourceType in (port[1], DEFAULT_PORT_TYPE):
            port = (port[0], sourceType, port[2], describeAttribute(source.desc))
        nodePorts.append(port)
    if nodePorts != anySetPorts(node.ins):
        with _PortSync(node):
            syncAnySet(node.ins, nodePorts)
    nodePorts = {port[0]: port for port in nodePorts}
    # Ports not connected on the node: the description of the attributes they are connected to in the subgraph
    graph = graphInput.graph
    for child, port in zip(list(graphInput.ports.value), anySetPorts(graphInput.ports)):
        source = nodePorts.get(port[0])
        if source is not None and source[1] != DEFAULT_PORT_TYPE and node.ins.value.get(port[0]).isLink:
            continue
        destinations = [edge.dst for edge in graph.edges if edge.src is child] if graph is not None else []
        for destination in destinations:
            destinationType = type(destination.desc).__name__
            if destinationType != DEFAULT_PORT_TYPE and destinationType in (port[1], DEFAULT_PORT_TYPE):
                nodePorts[port[0]] = (port[0], destinationType, port[2], describeAttribute(destination.desc))
                break
    ports = []
    for port in anySetPorts(graphInput.ports):
        nodePort = nodePorts.get(port[0])
        upgrade = nodePort is not None and (
            (port[1] == DEFAULT_PORT_TYPE and nodePort[1] != DEFAULT_PORT_TYPE)
            or (port[1] == nodePort[1] != DEFAULT_PORT_TYPE and nodePort[3] and not sameDescription(port[3], nodePort[3])))
        ports.append((port[0], nodePort[1], port[2], nodePort[3]) if upgrade else port)
    if ports != anySetPorts(graphInput.ports):
        syncAnySet(graphInput.ports, ports)


def showNodeValues(graphInput, node):
    """
    Show on a GraphInput node, while its subgraph is edited, the values it gets from the node running the
    subgraph: its ports get the values of the inputs of the node, its loop outputs the first step of the loop
    (they are only shown: the outputs are not saved with the subgraph, a run sets them again).
    """
    if graphInput.hasAttribute("loopMode"):
        graphInput.loopMode.value = node.loopMode.value
    from .executor import plainValue, setPlainValue
    nodeInputs = {child.name: plainValue(child) for child in node.ins.value}
    for port in graphInput.ports.value:
        if nodeInputs.get(port.name) is not None:
            try:
                setPlainValue(port, nodeInputs[port.name])
            except Exception as e:  # only shown: a value that does not fit the port is not shown
                logging.warning(f"[SubGraph] Value of '{port.name}' not shown on {graphInput.name}: {e}")
    from .nodes import isFrameLoop, loopFromNode
    loop = loopFromNode(node)
    frames = loop.frames
    values = {"iteration": 0,
              "item": loop.items[0] if loop.items else None,
              "frame": frames[0] if frames else None,
              }
    for name, value in values.items():
        if graphInput.hasAttribute(name):
            graphInput.attribute(name).value = value
    if graphInput.hasAttribute("frameStep") and isFrameLoop(node.loopMode.value):
        graphInput.frameStep.value = loop.step
    if graphInput.hasAttribute("frameRange") and isFrameLoop(node.loopMode.value):
        for child in graphInput.frameRange.value:
            child.value = {"start": loop.first, "stop": loop.last}.get(child.name)


class SubGraphLevel:
    """ A subgraph being edited: the graph containing its node, the node, and the subgraph content when entered. """

    def __init__(self, outerGraph: Graph, node, initialContent: str):
        self.outerGraph = outerGraph
        self.node = node
        self.initialContent = initialContent

    @property
    def isTemplate(self) -> bool:
        """ Whether the node only references a template (no embedded subgraph). """
        return not self.node.subGraph.value and bool(self.node.template.value)


class SubGraphStack:
    """ The path from the project graph to the subgraph being edited. """

    def __init__(self):
        self.levels: List[SubGraphLevel] = []

    def __len__(self):
        return len(self.levels)

    @property
    def rootGraph(self) -> Optional[Graph]:
        return self.levels[0].outerGraph if self.levels else None

    def names(self) -> List[str]:
        """ The names of the entered nodes, from the outermost one. """
        return [level.node.name for level in self.levels]

    def enter(self, currentGraph: Graph, node, parent=None) -> Graph:
        """ Enter a node of the current graph: returns the graph of its subgraph. """
        if not isSubGraphNode(node):
            raise ValueError(f"'{node.name}' does not contain a subgraph.")
        if node.subGraph.isLink or node.template.isLink:
            raise ValueError(f"The subgraph of '{node.name}' comes from a connection: it cannot be edited.")
        graph = buildSubGraph(node, parent)
        # Nodes of unknown types (their plugin is not loaded): their connections cannot be restored, and
        # writing the subgraph back would lose them
        unknown = sorted(f"{n.name} ({n.nodeType})" for n in graph.nodes if n.isCompatibilityNode)
        if unknown:
            raise ValueError(f"The subgraph of '{node.name}' has nodes whose type is not loaded (plugin missing in this "
                             f"environment): {', '.join(unknown)}. It is not opened, so that it is not modified.")
        graphInputs = [innerNode for innerNode in graph.nodes if getattr(innerNode.nodeDesc, "subGraphRole", "") == "input"]
        for graphInput in graphInputs:
            showNodeValues(graphInput, node)
        # Before repairing the ports: a repair is written back when leaving (the shown values are not)
        initialContent = serializeSubGraph(graph)
        for graphInput in graphInputs:
            _repairPorts(graphInput, node)
            showNodeValues(graphInput, node)
        self.levels.append(SubGraphLevel(currentGraph, node, initialContent))
        return graph

    @staticmethod
    def _write(level: SubGraphLevel, graph: Graph) -> bool:
        """ Write a subgraph in its node (or its template file) if it changed since it was entered. """
        content = serializeSubGraph(graph)
        if content == level.initialContent:
            return False
        if level.isTemplate:
            graph.save(level.node.template.value, setupProjectFile=False, template=True)
            # The ports of the node follow the template
            level.node.nodeDesc.onTemplateChanged(level.node)
        else:
            level.node.subGraph.value = content
        level.initialContent = content
        return True

    def commit(self, currentGraph: Graph) -> bool:
        """ Write the current subgraph in its node (or its template file). Returns whether it changed. """
        return self._write(self.levels[-1], currentGraph) if self.levels else False

    def exit(self, currentGraph: Graph) -> Graph:
        """ Leave the current subgraph (written back): returns the graph containing its node. """
        self.commit(currentGraph)
        return self.levels.pop().outerGraph

    def commitAll(self, currentGraph: Graph) -> Graph:
        """
        Write all the entered subgraphs back, from the current one up to the project graph, staying in the
        current subgraph (e.g. to save the project). Returns the project graph.
        """
        if not self.levels:
            return currentGraph
        graph = currentGraph
        for level in reversed(self.levels):
            self._write(level, graph)
            graph = level.outerGraph
        return graph


def _replaceLinks(value, mapping: dict):
    """ A serialized value with its link expressions ("{Node.attr}") replaced according to `mapping`. """
    if isinstance(value, str):
        return mapping.get(value, value)
    if isinstance(value, dict):
        return {key: _replaceLinks(item, mapping) for key, item in value.items()}
    if isinstance(value, list):
        return [_replaceLinks(item, mapping) for item in value]
    return value


def _portType(attribute) -> str:
    return type(attribute.desc).__name__


def _portDescription(attribute):
    """ The full description of the port matching an attribute, for the types that are not simple ones. """
    from meshroom.core.desc.serialization import describeAttribute
    from .ports import PORT_TYPES
    return None if _portType(attribute) in PORT_TYPES else describeAttribute(attribute.desc)


def _uniquePortName(name: str, used: set) -> str:
    unique, index = name, 1
    while unique in used:
        unique, index = f"{name}_{index}", index + 1
    used.add(unique)
    return unique


def snapshotNodes(graph: Graph, nodes) -> dict:
    """
    What is needed to put nodes back in a graph after they were removed (see restoreNodes): their serialized
    form in an order where each node comes after the nodes it reads, and their connections to other nodes.
    """
    names = {node.name for node in nodes}
    remaining = {node.name: {edge.src.node.name for edge in graph.nodeInEdges(node) if edge.src.node.name in names}
                 for node in nodes}
    order = []
    while remaining:
        ready = sorted(name for name, sources in remaining.items() if not sources) or sorted(remaining)[:1]
        for name in ready:
            order.append(name)
            del remaining[name]
        for sources in remaining.values():
            sources.difference_update(ready)
    outEdges = [(edge.src.fullName, edge.dst.fullName) for edge in graph.edges
                if edge.src.node.name in names and edge.dst.node.name not in names]
    return {"nodes": [(name, graph.node(name).toDict()) for name in order], "outEdges": outEdges}


def restoreNodes(graph: Graph, snapshot: dict):
    """ Put back nodes removed from a graph (see snapshotNodes), with their connections. """
    from meshroom.core.graph import GraphModification
    from meshroom.core.nodeFactory import nodeFactory
    with GraphModification(graph):
        for name, nodeData in snapshot["nodes"]:
            graph.addNode(nodeFactory(nodeData, name), name)
        for srcName, dstName in snapshot["outEdges"]:
            src, dst = graph.anyAttribute(srcName), graph.anyAttribute(dstName)
            if src is not None and dst is not None:
                graph.addEdge(src, dst)


def collapseIntoSubGraph(graph: Graph, nodes, position=None):
    """
    Replace nodes of a graph by a SubGraph node containing them. The connections from other nodes become
    inputs of the SubGraph node (ports of its GraphInput), the connections to other nodes its outputs (ports of
    its GraphOutput); the connections between the nodes stay inside.

    Returns:
        (the SubGraph node, a snapshot of the replaced nodes to put them back, see restoreNodes)
    """
    from meshroom.core.graphIO import GraphIO
    from meshroom.core.node import Position
    from .ports import formatPortSpec

    nodes = [node for node in nodes if node.nodeType not in ("Backdrop",)]
    if not nodes:
        raise ValueError("No node to put in a subgraph.")
    names = {node.name for node in nodes}
    snapshot = snapshotNodes(graph, nodes)

    usedInputs, usedOutputs = set(), set()
    inputPorts, outputPorts = {}, {}       # src fullName -> (port name, type, label, description)
    incoming, outgoing = [], []            # (src attribute, port name) / (port name, dst attribute)
    for edge in list(graph.edges):
        srcInside, dstInside = edge.src.node.name in names, edge.dst.node.name in names
        if dstInside and not srcInside:
            key = edge.src.fullName
            if key not in inputPorts:
                inputPorts[key] = (_uniquePortName(edge.src.name, usedInputs), _portType(edge.src), edge.src.label,
                                   _portDescription(edge.src))
                incoming.append((edge.src, inputPorts[key][0]))
        elif srcInside and not dstInside:
            key = edge.src.fullName
            if key not in outputPorts:
                outputPorts[key] = (_uniquePortName(edge.src.name, usedOutputs), _portType(edge.src), edge.src.label,
                                    _portDescription(edge.src))
            outgoing.append((outputPorts[key][0], edge.dst))

    # The nodes, with the links coming from other nodes going to the GraphInput ports
    mapping = {"{" + key + "}": "{GraphInput_1.ports." + port[0] + "}" for key, port in inputPorts.items()}
    graphData = {}
    for name, nodeData in snapshot["nodes"]:
        nodeData = dict(nodeData)
        for key in ("inputs", "internalInputs"):
            if key in nodeData:
                nodeData[key] = _replaceLinks(nodeData[key], mapping)
        nodeData.pop("outputs", None)
        nodeData.pop("uid", None)
        graphData[name] = nodeData
    xs = [node.position.x for node in nodes]
    ys = [node.position.y for node in nodes]
    spacing = 300
    graphData["GraphInput_1"] = {"nodeType": "GraphInput", "position": [min(xs) - spacing, int(sum(ys) / len(ys))],
                                 "inputs": {"portSpec": formatPortSpec(inputPorts.values())}}
    graphData["GraphOutput_1"] = {"nodeType": "GraphOutput", "position": [max(xs) + spacing, int(sum(ys) / len(ys))],
                                  "inputs": {"portSpec": formatPortSpec(outputPorts.values()), "ports": {"children": [
                                      dict({"name": port[0], "label": port[2], "type": port[1], "value": "{" + key + "}"},
                                           **({"desc": port[3]} if port[3] else {}))
                                      for key, port in outputPorts.items()]}}}
    content = json.dumps({GraphIO.Keys.Header: {GraphIO.Keys.FileVersion: GraphIO.__version__, GraphIO.Keys.Template: True},
                          GraphIO.Keys.Graph: graphData}, indent=1)

    for node in nodes:
        graph.removeNode(node.name)
    if position is None:
        position = Position(int(sum(xs) / len(xs)), int(sum(ys) / len(ys)))
    subGraphNode = graph.addNewNode("SubGraph", position=position, subGraph=content)
    for src, portName in incoming:
        graph.addEdge(src, subGraphNode.ins.value.get(portName))
    for portName, dst in outgoing:
        graph.addEdge(subGraphNode.outs.value.get(portName), dst)
    return subGraphNode, snapshot
