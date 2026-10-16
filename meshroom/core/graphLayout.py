"""
Tree layout of the nodes of a graph following their connections (graph editor key L): the graph flows
from left to right, each node sits just to the right of its inputs, and the inputs of a node are stacked
from top to bottom in the order of its input attributes (e.g. a node with inputs B then A: B on top, A
below). The first input stays on the row of the node, so that a main branch is a straight line.
"""
from typing import Callable, Dict, Iterable, List, Optional, Tuple


def _inputOrder(attribute) -> Tuple[int, int]:
    """ Order of an input attribute in its node: position of its root attribute, then its index in a list. """
    root = attribute.root if getattr(attribute, "root", None) is not None else attribute
    node = attribute.node
    try:
        position = [a.name for a in node.attributes].index(root.name)
    except ValueError:
        position = len(node.attributes)
    index = 0
    if root is not attribute:
        try:
            index = root.index(attribute)
        except Exception:
            index = 0
    return position, index


def layoutEdges(graph, nodes: Iterable, skip: Optional[Callable] = None) -> List[Tuple[object, object, tuple]]:
    """
    The connections between `nodes` used by the layout: (upstream node, downstream node, input order).
    Only the links from an output count (not the links between parameters); `skip(edge)` can leave out
    others (e.g. the hidden edges).
    """
    selected = set(nodes)
    result = []
    for edge in graph.edges:
        src, dst = edge.src, edge.dst
        if src.node not in selected or dst.node not in selected or src.node is dst.node:
            continue
        if not src.isOutput or (skip is not None and skip(edge)):
            continue
        result.append((src.node, dst.node, _inputOrder(dst)))
    return result


def treeLayout(nodes: List, edges: List[Tuple[object, object, tuple]], size: Callable[[object], Tuple[float, float]],
               origin: Tuple[float, float], positionOf: Callable[[object], Tuple[float, float]],
               columnSpacing: float = 60.0, rowSpacing: float = 30.0) -> Dict[object, Tuple[float, float]]:
    """
    Positions (top-left corners) of `nodes` laid out as a tree (see the module documentation).

    Args:
        nodes: the nodes to lay out.
        edges: (upstream node, downstream node, input order) between them (see layoutEdges).
        size: (width, height) of a node.
        origin: top-left corner of the layout.
        positionOf: current position of a node (the separate trees keep their vertical order).
    """
    nodes = list(nodes)
    inputs: Dict[object, List[Tuple[tuple, object]]] = {node: [] for node in nodes}
    outputs: Dict[object, List[object]] = {node: [] for node in nodes}
    for src, dst, order in edges:
        inputs[dst].append((order, src))
        outputs[src].append(dst)
    for node in nodes:
        inputs[node].sort(key=lambda item: item[0])

    # Columns: a node is one column left of its farthest downstream consumer (the outputs are on the
    # right, each input just left of the node using it)
    distance: Dict[object, int] = {}

    def distanceOf(node):
        if node not in distance:
            distance[node] = max((distanceOf(consumer) + 1 for consumer in outputs[node]), default=0)
        return distance[node]

    for node in nodes:
        distanceOf(node)
    maxDistance = max(distance.values(), default=0)
    column = {node: maxDistance - distance[node] for node in nodes}
    widths: Dict[int, float] = {}
    for node in nodes:
        widths[column[node]] = max(widths.get(column[node], 0.0), size(node)[0])
    columnX = {}
    x = origin[0]
    for index in range(maxDistance + 1):
        columnX[index] = x
        x += widths.get(index, 0.0) + columnSpacing

    # Rows: from the outputs, each node on the row of its first input, its other inputs below
    positions: Dict[object, Tuple[float, float]] = {}

    def place(node, top: float) -> float:
        """ Place a node and its inputs not placed yet from `top`: the bottom of what was placed. """
        positions[node] = (columnX[column[node]], top)
        bottom = top + size(node)[1] + rowSpacing
        current = top
        for _, upstream in inputs[node]:
            if upstream in positions:
                continue  # Shared by several nodes: placed with the first one
            current = place(upstream, current)
        return max(bottom, current)

    sinks = [node for node in nodes if not outputs[node]]
    sinks.sort(key=lambda node: (positionOf(node)[1], positionOf(node)[0]))
    top = origin[1]
    for node in sinks + nodes:
        if node not in positions:
            top = place(node, top)
    return positions
