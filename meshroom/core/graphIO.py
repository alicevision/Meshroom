from enum import Enum
from typing import Any, TYPE_CHECKING, Union

import meshroom
from meshroom.core import Version
from meshroom.core.node import Node

if TYPE_CHECKING:
    from meshroom.core.graph import Graph


class GraphIO:
    """Centralize Graph file keys and IO version."""

    __version__ = "2.0"

    class Keys(object):
        """File Keys."""

        # Doesn't inherit enum to simplify usage (GraphIO.Keys.XX, without .value)
        Header = "header"
        NodesVersions = "nodesVersions"
        ReleaseVersion = "releaseVersion"
        FileVersion = "fileVersion"
        Graph = "graph"

    class Features(Enum):
        """File Features."""

        Graph = "graph"
        Header = "header"
        NodesVersions = "nodesVersions"
        PrecomputedOutputs = "precomputedOutputs"
        NodesPositions = "nodesPositions"

    @staticmethod
    def getFeaturesForVersion(fileVersion: Union[str, Version]) -> tuple["GraphIO.Features", ...]:
        """Return the list of supported features based on a file version.

        Args:
            fileVersion (str, Version): the file version

        Returns:
            tuple of GraphIO.Features: the list of supported features
        """
        if isinstance(fileVersion, str):
            fileVersion = Version(fileVersion)

        features = [GraphIO.Features.Graph]
        if fileVersion >= Version("1.0"):
            features += [
                GraphIO.Features.Header,
                GraphIO.Features.NodesVersions,
                GraphIO.Features.PrecomputedOutputs,
            ]

        if fileVersion >= Version("1.1"):
            features += [GraphIO.Features.NodesPositions]

        return tuple(features)


class GraphSerializer:
    """Standard Graph serializer."""

    def __init__(self, graph: "Graph") -> None:
        self._graph = graph

    def serialize(self) -> dict:
        """
        Serialize the Graph.
        """
        return {
            GraphIO.Keys.Header: self.serializeHeader(),
            GraphIO.Keys.Graph: self.serializeContent(),
        }

    @property
    def nodes(self) -> list[Node]:
        return self._graph.nodes

    def serializeHeader(self) -> dict:
        """Build and return the graph serialization header.

        The header contains metadata about the graph, such as the:
            - version of the software used to create it.
            - version of the file format.
            - version of the nodes types used in the graph.
            - template flag.

        Args:
            nodes: (optional) The list of nodes to consider for node types versions - use all nodes if not specified.
            template: Whether the graph is going to be serialized as a template.
        """
        header: dict[str, Any] = {}
        header[GraphIO.Keys.ReleaseVersion] = meshroom.__version__
        header[GraphIO.Keys.FileVersion] = GraphIO.__version__
        header[GraphIO.Keys.NodesVersions] = self._getNodeTypesVersions()
        return header

    def _getNodeTypesVersions(self) -> dict[str, str]:
        """Get registered versions of each node types in `nodes`, excluding CompatibilityNode instances."""
        nodeTypes = set([node.nodeDesc.__class__ for node in self.nodes if isinstance(node, Node)])
        nodeTypesVersions = {
            nodeType.__name__: meshroom.core.nodeVersion(nodeType, "0.0") for nodeType in nodeTypes
        }
        # Sort them by name (to avoid random order changing from one save to another).
        return dict(sorted(nodeTypesVersions.items()))

    def serializeContent(self) -> dict:
        """Graph content serialization logic."""
        return {node.name: self.serializeNode(node) for node in sorted(self.nodes, key=lambda n: n.name)}

    def serializeNode(self, node: Node) -> dict:
        """Node serialization logic."""
        return node.toDict()


class TemplateGraphSerializer(GraphSerializer):
    """Serializer for serializing a graph as a template."""

    def serializeHeader(self) -> dict:
        header = super().serializeHeader()
        header["template"] = True
        return header

    def serializeNode(self, node: Node) -> dict:
        """Adapt node serialization to template graphs.
        
        Instead of getting all the inputs and internal attribute keys, only get the keys of
        the attributes whose value is not the default one.
        The output attributes, UIDs, parallelization parameters and internal folder are
        not relevant for templates, so they are explicitly removed from the returned dictionary.
        """
        # For now, implemented as a post-process to update the default serialization.
        nodeData = super().serializeNode(node)

        inputKeys = list(nodeData["inputs"].keys())

        internalInputKeys = []
        internalInputs = nodeData.get("internalInputs", None)
        if internalInputs:
            internalInputKeys = list(internalInputs.keys())

        for attrName in inputKeys:
            attribute = node.attribute(attrName)
            # check that attribute is not a link for choice attributes
            if attribute.isDefault and not attribute.isLink:
                del nodeData["inputs"][attrName]

        for attrName in internalInputKeys:
            attribute = node.internalAttribute(attrName)
            # check that internal attribute is not a link for choice attributes
            if attribute.isDefault and not attribute.isLink:
                del nodeData["internalInputs"][attrName]

        # If all the internal attributes are set to their default values, remove the entry
        if len(nodeData["internalInputs"]) == 0:
            del nodeData["internalInputs"]

        del nodeData["outputs"]
        del nodeData["uid"]
        del nodeData["internalFolder"]
        del nodeData["parallelization"]

        return nodeData


