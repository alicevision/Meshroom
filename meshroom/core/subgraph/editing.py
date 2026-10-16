"""
Editing of subgraphs: entering a node running a subgraph (SubGraph, LiveSubGraph) shows its subgraph as
a graph of its own; leaving it writes the subgraph back in the node (embedded subgraph), or in its
template file when the node only references a template.

SubGraphStack keeps the path from the project graph to the shown subgraph, without any Qt dependency
(the UI keeps one, see meshroom/ui/graph.py).
"""
import json
from typing import List, Optional

from meshroom.core.graph import Graph
from meshroom.core.graphIO import GraphIO

from .executor import readGraphData
from .nodes import nodeGraphSource

SUBGRAPH_NODE_TYPES = ("SubGraph", "LiveSubGraph")


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
        # The GraphInput nodes show the outputs of the loop of the node (iteration, frame...)
        for innerNode in graph.nodes:
            if getattr(innerNode.nodeDesc, "subGraphRole", "") == "input" and innerNode.hasAttribute("loopMode"):
                innerNode.loopMode.value = node.loopMode.value
        self.levels.append(SubGraphLevel(currentGraph, node, serializeSubGraph(graph)))
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
