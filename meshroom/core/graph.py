import json
import logging
import os
import re
from typing import Any, Optional
from collections.abc import Iterable
import weakref
from collections import defaultdict, OrderedDict
from contextlib import contextmanager

from enum import Enum

import meshroom
import meshroom.core
from meshroom.common import BaseObject, DictModel, Slot, Signal, Property
from meshroom.core import Version
from meshroom.core.attribute import Attribute, ListAttribute, GroupAttribute
from meshroom.core.exception import GraphCompatibilityError, StopGraphVisit, StopBranchVisit
from meshroom.core.graphIO import GraphIO, GraphSerializer, TemplateGraphSerializer, PartialGraphSerializer
from meshroom.core.node import BaseNode, Status, Node, CompatibilityNode
from meshroom.core.nodeFactory import nodeFactory
from meshroom.core.mtyping import PathLike

# Replace default encoder to support Enums

DefaultJSONEncoder = json.JSONEncoder  # store the original one


class MyJSONEncoder(DefaultJSONEncoder):  # declare a new one with Enum support
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.name
        return DefaultJSONEncoder.default(self, obj)  # use the default one for all other types


json.JSONEncoder = MyJSONEncoder  # replace the default implementation with our new one


@contextmanager
def GraphModification(graph):
    """
    A Context Manager that can be used to trigger only one Graph update
    for a group of several modifications.
    GraphModifications can be nested.
    """
    if not isinstance(graph, Graph):
        raise ValueError("GraphModification expects a Graph instance")
    # Store update policy for nested usage
    enabled = graph.updateEnabled
    # Disable graph update for nested block
    # (does nothing if already disabled)
    graph.updateEnabled = False
    try:
        yield  # Execute nested block
    except Exception:
        raise
    finally:
        # Restore update policy
        graph.updateEnabled = enabled


class Edge(BaseObject):

    def __init__(self, src, dst, parent=None):
        super().__init__(parent)
        self._src = weakref.ref(src)
        self._dst = weakref.ref(dst)
        self._repr = f"<Edge> {self._src()} -> {self._dst()}"

    @property
    def src(self):
        return self._src()

    @property
    def dst(self):
        return self._dst()

    src = Property(Attribute, src.fget, constant=True)
    dst = Property(Attribute, dst.fget, constant=True)


WHITE = 0
GRAY = 1
BLACK = 2


class Visitor:
    """
    Base class for Graph Visitors that does nothing.
    Sub-classes can override any method to implement specific algorithms.
    """
    def __init__(self, reverse, dependenciesOnly):
        super().__init__()
        self.reverse = reverse
        self.dependenciesOnly = dependenciesOnly

    # def initializeVertex(self, s, g):
    #     '''is invoked on every vertex of the graph before the start of the graph search.'''
    #     pass
    # def startVertex(self, s, g):
    #     '''is invoked on the source vertex once before the start of the search.'''
    #     pass

    def discoverVertex(self, u, g):
        """ Is invoked when a vertex is encountered for the first time. """
        pass

    def examineEdge(self, e, g):
        """ Is invoked on every out-edge of each vertex after it is discovered."""
        pass

    def treeEdge(self, e, g):
        """ Is invoked on each edge as it becomes a member of the edges that form the search tree.
        If you wish to record predecessors, do so at this event point. """
        pass

    def backEdge(self, e, g):
        """ Is invoked on the back edges in the graph. """
        pass

    def forwardOrCrossEdge(self, e, g):
        """ Is invoked on forward or cross edges in the graph.
        In an undirected graph this method is never called."""
        pass

    def finishEdge(self, e, g):
        """ Is invoked on the non-tree edges in the graph
        as well as on each tree edge after its target vertex is finished. """
        pass

    def finishVertex(self, u, g):
        """ Is invoked on a vertex after all of its out edges have been added to the search tree and all of the
        adjacent vertices have been discovered (but before their out-edges have been examined). """
        pass


def changeTopology(func):
    """
    Graph methods modifying the graph topology (add/remove edges or nodes)
    must be decorated with 'changeTopology' for update mechanism to work as intended.
    """
    def decorator(self, *args, **kwargs):
        assert isinstance(self, Graph)
        # call method
        result = func(self, *args, **kwargs)
        # mark graph dirty
        self.dirtyTopology = True
        # request graph update
        self.update()
        return result
    return decorator


def blockNodeCallbacks(func):
    """
    Graph methods loading serialized graph content must be decorated with 'blockNodeCallbacks',
    to avoid attribute changed callbacks defined on node descriptions to be triggered during
    this process.
    """
    def inner(self, *args, **kwargs):
        self._loading = True
        try:
            return func(self, *args, **kwargs)
        finally:
            self._loading = False
    return inner


def generateTempProjectFilepath(tmpFolder=None):
    """
    Generate a temporary project filepath.
    This method is used to generate a temporary project file for the current graph.
    """
    from datetime import datetime
    if tmpFolder is None:
        from meshroom.env import EnvVar
        tmpFolder = EnvVar.get(EnvVar.MESHROOM_TEMP_PATH)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    return os.path.join(tmpFolder, f"meshroom_{timestamp}.mg")


class Graph(BaseObject):
    """
    _________________      _________________      _________________
    |               |      |               |      |               |
    |     Node A    |      |     Node B    |      |     Node C    |
    |               | edge |               | edge |               |
    |input    output|>---->|input    output|>---->|input    output|
    |_______________|      |_______________|      |_______________|

    Data structures:

        nodes = {'A': <nodeA>, 'B': <nodeB>, 'C': <nodeC>}
        edges = {B.input: A.output, C.input: B.output,}

    """

    def __init__(self, name: str = "", parent: BaseObject = None):
        super().__init__(parent)
        self.name: str = name
        self._loading: bool = False
        self._saving: bool = False
        self._updateEnabled: bool = True
        self._updateRequested: bool = False
        self.dirtyTopology: bool = False
        self._nodesMinMaxDepths = {}
        self._computationBlocked = {}
        self._canComputeLeaves: bool = True
        self._nodes = DictModel(keyAttrName='name', parent=self)
        # Edges: use dst attribute as unique key since it can only have one input connection
        self._edges = DictModel(keyAttrName='dst', parent=self)
        self._compatibilityNodes = DictModel(keyAttrName='name', parent=self)
        self._cacheDir: str = ''
        self._filepath: str = ''
        self._fileDateVersion = 0
        self.header = {}

    def clear(self):
        self._clearGraphContent()
        self.header.clear()
        self._unsetFilepath()

    def _clearGraphContent(self):
        self._edges.clear()
        # Tell QML nodes are going to be deleted
        for node in self._nodes:
            node.alive = False
        self._nodes.clear()
        self._compatibilityNodes.clear()

    @property
    def fileFeatures(self):
        """ Get loaded file supported features based on its version. """
        return GraphIO.getFeaturesForVersion(self.header.get(GraphIO.Keys.FileVersion, "0.0"))

    @property
    def isLoading(self):
        """ Return True if the graph is currently being loaded. """
        return self._loading
    
    @property
    def isSaving(self):
        """ Return True if the graph is currently being saved. """
        return self._saving

    @Slot(str)
    def load(self, filepath: PathLike):
        """
        Load a Meshroom Graph ".mg" file in place.

        Args:
            filepath: The path to the Meshroom Graph file to load.
        """
        self._setFilepath(filepath)
        self._deserialize(Graph._loadGraphData(filepath))
        self._fileDateVersion = os.path.getmtime(filepath)

    def initFromTemplate(self, filepath: PathLike, publishOutputs: bool = False):
        """
        Deserialize a template Meshroom Graph ".mg" file in place.

        When initializing from a template, the internal filepath of the graph instance is not set.
        Saving the file on disk will require to specify a filepath.

        Args:
            filepath: The path to the Meshroom Graph file to load.
            publishOutputs: (optional) Whether to keep 'Publish' nodes.
        """
        self._deserialize(Graph._loadGraphData(filepath))

        # Creating nodes from a template is conceptually similar to explicit node creation,
        # therefore the nodes descriptors' "onNodeCreated" callback is triggered for each
        # node instance created by this process.
        self._triggerNodeCreatedCallback(self.nodes)

        if not publishOutputs:
            with GraphModification(self):
                for node in [node for node in self.nodes if node.nodeType == "Publish"]:
                    self.removeNode(node.name)

    @staticmethod
    def _loadGraphData(filepath: PathLike) -> dict:
        """Deserialize the content of the Meshroom Graph file at `filepath` to a dictionnary."""
        with open(filepath) as file:
            graphData = json.load(file)
        return graphData

    @blockNodeCallbacks
    def _deserialize(self, graphData: dict):
        """Deserialize `graphData` in the current Graph instance.

        Args:
            graphData: The serialized Graph.
        """
        self._clearGraphContent()
        self.header.clear()

        self.header = graphData.get(GraphIO.Keys.Header, {})
        fileVersion = Version(self.header.get(GraphIO.Keys.FileVersion, "0.0"))
        graphContent = self._normalizeGraphContent(graphData, fileVersion)
        isTemplate = self.header.get(GraphIO.Keys.Template, False)

        with GraphModification(self):
            # iterate over nodes sorted by suffix index in their names
            for nodeName, nodeData in sorted(
                graphContent.items(), key=lambda x: self.getNodeIndexFromName(x[0])
            ):
                self._deserializeNode(nodeData, nodeName, self)

            # Create graph edges by resolving attributes expressions
            self._applyExpr()
            
        # Templates are specific: they contain only the minimal amount of 
        # serialized data to describe the graph structure.
        # They are not meant to be computed: therefore, we can early return here,
        # as uid conflict evaluation is only meaningful for nodes with computed data.
        if isTemplate:
            return

        # By this point, the graph has been fully loaded and an updateInternals has been triggered, so all the
        # nodes' links have been resolved and their UID computations are all complete.
        # It is now possible to check whether the UIDs stored in the graph file for each node correspond to the ones
        # that were computed.
        self._evaluateUidConflicts(graphContent)

    def _normalizeGraphContent(self, graphData: dict, fileVersion: Version) -> dict:
        graphContent = graphData.get(GraphIO.Keys.Graph, graphData)

        if fileVersion < Version("2.0"):
            # For internal folders, all "{uid0}" keys should be replaced with "{uid}"
            updatedFileData = json.dumps(graphContent).replace("{uid0}", "{uid}")

            # For fileVersion < 2.0, the nodes' UID is stored as:
            # "uids": {"0": "hashvalue"}
            # These should be identified and replaced with:
            # "uid": "hashvalue"
            uidPattern = re.compile(r'"uids": \{"0":.*?\}')
            uidOccurrences = uidPattern.findall(updatedFileData)
            for occ in uidOccurrences:
                uid = occ.split("\"")[-2]  # UID is second to last element
                newUidStr = fr'"uid": "{uid}"'
                updatedFileData = updatedFileData.replace(occ, newUidStr)
            graphContent = json.loads(updatedFileData)

        return graphContent

    def _deserializeNode(self, nodeData: dict, nodeName: str, fromGraph: "Graph"):
        # Retrieve version info from:
        #   1. nodeData: node saved from a CompatibilityNode
        #   2. nodesVersion in file header: node saved from a Node
        # If unvailable, the "version" field will not be set in `nodeData`.
        if "version" not in nodeData:
            if version := fromGraph._getNodeTypeVersionFromHeader(nodeData["nodeType"]):
                nodeData["version"] = version
        inTemplate = fromGraph.header.get(GraphIO.Keys.Template, False)
        node = nodeFactory(nodeData, nodeName, inTemplate=inTemplate)
        self._addNode(node, nodeName)
        return node

    def _getNodeTypeVersionFromHeader(self, nodeType: str, default: Optional[str] = None) -> Optional[str]:
        nodeVersions = self.header.get(GraphIO.Keys.NodesVersions, {})
        return nodeVersions.get(nodeType, default)

    def _evaluateUidConflicts(self, graphContent: dict):
        """
        Compare the computed UIDs of all the nodes in the graph with the UIDs serialized in `graphContent`. If there
        are mismatches, the nodes with the unexpected UID are replaced with "UidConflict" compatibility nodes.
  
        Args:
            graphContent: The serialized Graph content.
        """

        def _serializedNodeUidMatchesComputedUid(nodeData: dict, node: BaseNode) -> bool:
            """Returns whether the serialized UID matches the one computed in the `node` instance."""
            if isinstance(node, CompatibilityNode):
                return True
            serializedUid = nodeData.get("uid", None)
            computedUid = node._uid
            return serializedUid is None or computedUid is None or serializedUid == computedUid

        uidConflictingNodes = [
            node
            for node in self.nodes
            if not _serializedNodeUidMatchesComputedUid(graphContent[node.name], node)
        ]

        if not uidConflictingNodes:
            return

        logging.warning("UID Compatibility issues found: recreating conflicting nodes as CompatibilityNodes.")

        # A uid conflict is contagious: if a node has a uid conflict, all of its downstream nodes may be 
        # impacted as well, as the uid flows through connections.
        # Therefore, we deal with conflicting uid nodes by depth: replacing a node with a CompatibilityNode restores
        # the serialized uid, which might solve "false-positives" downstream conflicts as well.
        nodesSortedByDepth = sorted(uidConflictingNodes, key=lambda node: node.minDepth)
        for node in nodesSortedByDepth:
            nodeData = graphContent[node.name]
            # Evaluate if the node uid is still conflicting at this point, or if it has been resolved by an
            # upstream node replacement.
            if _serializedNodeUidMatchesComputedUid(nodeData, node):
                continue
            expectedUid = node._uid
            compatibilityNode = nodeFactory(graphContent[node.name], node.name, expectedUid=expectedUid)
            # This operation will trigger a graph update that will recompute the uids of all nodes,
            # allowing the iterative resolution of uid conflicts.
            self.replaceNode(node.name, compatibilityNode)


    def importGraphContentFromFile(self, filepath: PathLike) -> list[Node]:
        """Import the content (nodes and edges) of another Graph file into this Graph instance.

        Args:
            filepath: The path to the Graph file to import.

        Returns:
            The list of newly created Nodes.
        """
        graph = loadGraph(filepath)
        return self.importGraphContent(graph)

    @blockNodeCallbacks
    def importGraphContent(self, graph: "Graph") -> list[Node]:
        """
        Import the content (node and edges) of another `graph` into this Graph instance.

        Nodes are imported with their original names if possible, otherwise a new unique name is generated
        from their node type.

        Args:
            graph: The graph to import.

        Returns:
            The list of newly created Nodes.
        """

        def _renameClashingNodes():
            if not self.nodes:
                return
            unavailableNames = set(self.nodes.keys())
            for node in graph.nodes:
                if node._name in unavailableNames:
                    node._name = self._createUniqueNodeName(node.nodeType, unavailableNames)
                unavailableNames.add(node._name)

        def _importNodesAndEdges() -> list[Node]:
            importedNodes = []
            # If we import the content of the graph within itself,
            # iterate over a copy of the nodes as the graph is modified during the iteration.
            nodes = graph.nodes if graph is not self else list(graph.nodes)
            with GraphModification(self):
                for srcNode in nodes:
                    node = self._deserializeNode(srcNode.toDict(), srcNode.name, graph)
                    importedNodes.append(node)
                self._applyExpr()
            return importedNodes

        _renameClashingNodes()
        importedNodes = _importNodesAndEdges()
        return importedNodes

    @property
    def updateEnabled(self):
        return self._updateEnabled

    @updateEnabled.setter
    def updateEnabled(self, enabled):
        self._updateEnabled = enabled
        if enabled and self._updateRequested:
            # Trigger an update if requested while disabled
            self.update()
            self._updateRequested = False

    @changeTopology
    def _addNode(self, node, uniqueName):
        """
        Internal method to add the given node to this Graph, with the given name (must be unique).
        Attribute expressions are not resolved.
        """
        if node.graph is not None and node.graph != self:
            raise RuntimeError(
                'Node "{}" cannot be part of the Graph "{}", as it is already part of the other graph "{}".'.format(
                    node.nodeType, self.name, node.graph.name))

        assert uniqueName not in self._nodes.keys()
        node._name = uniqueName
        node.graph = self
        self._nodes.add(node)

    def addNode(self, node, uniqueName=None):
        """
        Add the given node to this Graph with an optional unique name,
        and resolve attributes expressions.
        """
        self._addNode(node, uniqueName if uniqueName else self._createUniqueNodeName(node.nodeType))
        # Resolve attribute expressions
        with GraphModification(self):
            node._applyExpr()
        return node

    def copyNode(self, srcNode, withEdges=False):
        """
        Get a copy instance of a node outside the graph.

        Args:
            srcNode (Node): the node to copy
            withEdges (bool): whether to copy edges

        Returns:
            Node, dict: the created node instance,
                        a dictionary of linked attributes with their original value (empty if withEdges is True)
        """
        with GraphModification(self):
            # create a new node of the same type and with the same attributes values
            # keep links as-is so that CompatibilityNodes attributes can be created with correct automatic description
            # (File params for link expressions)
            node = nodeFactory(srcNode.toDict(), srcNode.nodeType)  # use nodeType as name
            # skip edges: filter out attributes which are links by resetting default values
            skippedEdges = {}
            if not withEdges:
                for n, attr in node.attributes.items():
                    if attr.isOutput:
                        # edges are declared in input with an expression linking
                        # to another param (which could be an output)
                        continue
                    # find top-level links
                    if Attribute.isLinkExpression(attr.value):
                        skippedEdges[attr] = attr.value
                        attr.resetToDefaultValue()
                    # find links in ListAttribute children
                    elif isinstance(attr, (ListAttribute, GroupAttribute)):
                        for child in attr.value:
                            if Attribute.isLinkExpression(child.value):
                                skippedEdges[child] = child.value
                                child.resetToDefaultValue()
        return node, skippedEdges

    def duplicateNodes(self, srcNodes):
        """ Duplicate nodes in the graph with their connections.

        Args:
            srcNodes: the nodes to duplicate

        Returns:
            OrderedDict[Node, Node]: the source->duplicate map
        """
        # use OrderedDict to keep duplicated nodes creation order
        duplicates = OrderedDict()

        with GraphModification(self):
            duplicateEdges = {}
            # first, duplicate all nodes without edges and keep a 'source=>duplicate' map
            # keeps tracks of non-created edges for later remap
            for srcNode in srcNodes:
                node, edges = self.copyNode(srcNode, withEdges=False)
                duplicate = self.addNode(node)
                duplicateEdges.update(edges)
                duplicates.setdefault(srcNode, []).append(duplicate)

            # re-create edges taking into account what has been duplicated
            for attr, linkExpression in duplicateEdges.items():
                # logging.warning("attr={} linkExpression={}".format(attr.fullName, linkExpression))
                link = linkExpression[1:-1]  # remove starting '{' and trailing '}'
                # get source node and attribute name
                edgeSrcNodeName, edgeSrcAttrName = link.split(".", 1)
                edgeSrcNode = self.node(edgeSrcNodeName)
                # if the edge's source node has been duplicated (the key exists in the dictionary),
                # use the duplicate; otherwise use the original node
                if edgeSrcNode in duplicates:
                    edgeSrcNode = duplicates.get(edgeSrcNode)[0]
                self.addEdge(edgeSrcNode.attribute(edgeSrcAttrName), attr)

        return duplicates

    def outEdges(self, attribute):
        """ Return the list of edges starting from the given attribute """
        # type: (Attribute,) -> [Edge]
        return [edge for edge in self.edges if edge.src == attribute]

    def nodeInEdges(self, node):
        # type: (Node) -> [Edge]
        """ Return the list of edges arriving to this node """
        return [edge for edge in self.edges if edge.dst.node == node]

    def nodeOutEdges(self, node):
        # type: (Node) -> [Edge]
        """ Return the list of edges starting from this node """
        return [edge for edge in self.edges if edge.src.node == node]

    @changeTopology
    def removeNode(self, nodeName):
        """
        Remove the node identified by 'nodeName' from the graph.
        Returns:
            - a dictionary containing the incoming edges removed by this operation:
                {dstAttr.getFullNameToNode(), srcAttr.getFullNameToNode()}
            - a dictionary containing the outgoing edges removed by this operation:
                {dstAttr.getFullNameToNode(), srcAttr.getFullNameToNode()}
            - a dictionary containing the values, indices and keys of attributes that were connected to a ListAttribute
                prior to the removal of all edges:
                {dstAttr.getFullNameToNode(), (dstAttr.root.getFullNameToNode(), dstAttr.index, dstAttr.value)}
        """
        node = self.node(nodeName)
        inEdges = {}
        outEdges = {}
        outListAttributes = {}

        # Remove all edges arriving to and starting from this node
        with GraphModification(self):
            # Two iterations over the outgoing edges are necessary:
            # - the first one is used to collect all the information about the edges while they are all there
            #   (overall context)
            # - once we have collected all the information, the edges (and perhaps the entries in ListAttributes) can
            #   actually be removed
            for edge in self.nodeOutEdges(node):
                outEdges[edge.dst.getFullNameToNode()] = edge.src.getFullNameToNode()

                if isinstance(edge.dst.root, ListAttribute):
                    index = edge.dst.root.index(edge.dst)
                    outListAttributes[edge.dst.getFullNameToNode()] = (edge.dst.root.getFullNameToNode(),
                                                                       index, edge.dst.value
                                                                       if edge.dst.value else None)

            for edge in self.nodeOutEdges(node):
                self.removeEdge(edge.dst)

                # Remove the corresponding attributes from the ListAttributes instead of just emptying their values
                if isinstance(edge.dst.root, ListAttribute):
                    index = edge.dst.root.index(edge.dst)
                    edge.dst.root.remove(index)

            for edge in self.nodeInEdges(node):
                self.removeEdge(edge.dst)
                inEdges[edge.dst.getFullNameToNode()] = edge.src.getFullNameToNode()

            node.alive = False
            self._nodes.remove(node)
            self.update()

        return inEdges, outEdges, outListAttributes

    def addNewNode(
        self, nodeType: str, name: Optional[str] = None, position: Optional[str] = None, **kwargs
    ) -> Node:
        """
        Create and add a new node to the graph.

        Args:
            nodeType: the node type name.
            name: if specified, the desired name for this node. If not unique, will be prefixed (_N).
            position: the position of the node.
            **kwargs: keyword arguments to initialize the created node's attributes.

        Returns:
             The newly created node.
        """
        if name and name in self._nodes.keys():
            name = self._createUniqueNodeName(name)

        node = self.addNode(Node(nodeType, position=position, **kwargs), uniqueName=name)
        node.updateInternals()
        self._triggerNodeCreatedCallback([node])
        return node

    def _triggerNodeCreatedCallback(self, nodes: Iterable[Node]):
        """Trigger the `onNodeCreated` node descriptor callback for each node instance in `nodes`."""
        with GraphModification(self):
            for node in nodes:
                if node.nodeDesc:
                    node.nodeDesc.onNodeCreated(node)

    def _createUniqueNodeName(self, inputName: str, existingNames: Optional[set[str]] = None):
        """Create a unique node name based on the input name.

        Args:
            inputName: The desired node name.
            existingNames: (optional) If specified, consider this set for uniqueness check, instead of the list of nodes.
        """
        existingNodeNames = existingNames or set(self._nodes.objects.keys())

        idx = 1
        while idx:
            newName = f"{inputName}_{idx}"
            if newName not in existingNodeNames:
                return newName
            idx += 1

    def node(self, nodeName) -> Optional[Node]:
        return self._nodes.get(nodeName)

    def upgradeNode(self, nodeName) -> Node:
        """
        Upgrade the CompatibilityNode identified as 'nodeName'
        Args:
            nodeName (str): the name of the CompatibilityNode to upgrade

        Returns:
            - the upgraded (newly created) node
            - a dictionary containing the incoming edges removed by this operation:
                {dstAttr.getFullNameToNode(), srcAttr.getFullNameToNode()}
            - a dictionary containing the outgoing edges removed by this operation:
                {dstAttr.getFullNameToNode(), srcAttr.getFullNameToNode()}
            - a dictionary containing the values, indices and keys of attributes that were connected to a ListAttribute
                prior to the removal of all edges:
                {dstAttr.getFullNameToNode(), (dstAttr.root.getFullNameToNode(), dstAttr.index, dstAttr.value)}
        """
        node = self.node(nodeName)
        if not isinstance(node, CompatibilityNode):
            raise ValueError("Upgrade is only available on CompatibilityNode instances.")
        upgradedNode = node.upgrade()
        self.replaceNode(nodeName, upgradedNode)
        return upgradedNode

    @changeTopology
    def replaceNode(self, nodeName: str, newNode: BaseNode):
        """Replace the node idenfitied by `nodeName` with `newNode`, while restoring compatible edges.

        Args:
            nodeName: The name of the Node to replace.
            newNode: The Node instance to replace it with.
        """
        with GraphModification(self):
            _, outEdges, outListAttributes = self.removeNode(nodeName)
            self.addNode(newNode, nodeName)
            self._restoreOutEdges(outEdges, outListAttributes)
    
    def _restoreOutEdges(self, outEdges: dict[str, str], outListAttributes):
        """Restore output edges that were removed during a call to "removeNode".
        
        Args:
            outEdges: a dictionary containing the outgoing edges removed by a call to "removeNode".
                {dstAttr.getFullNameToNode(), srcAttr.getFullNameToNode()}
            outListAttributes: a dictionary containing the values, indices and keys of attributes that were connected
                to a ListAttribute prior to the removal of all edges.
                {dstAttr.getFullNameToNode(), (dstAttr.root.getFullNameToNode(), dstAttr.index, dstAttr.value)}
        """
        def _recreateTargetListAttributeChildren(listAttrName: str, index: int, value: Any):
            listAttr = self.attribute(listAttrName)
            if not isinstance(listAttr, ListAttribute):
                return
            if isinstance(value, list):
                listAttr[index:index] = value
            else:
                listAttr.insert(index, value)

        for dstName, srcName in outEdges.items():
            # Re-create the entries in ListAttributes that were completely removed during the call to "removeNode"
            if dstName in outListAttributes:
                _recreateTargetListAttributeChildren(*outListAttributes[dstName])
            try:
                self.addEdge(self.attribute(srcName), self.attribute(dstName))
            except (KeyError, ValueError) as e:
                logging.warning(f"Failed to restore edge {srcName} -> {dstName}: {e}")

    def upgradeAllNodes(self):
        """ Upgrade all upgradable CompatibilityNode instances in the graph. """
        nodeNames = [name for name, n in self._compatibilityNodes.items() if n.canUpgrade]
        with GraphModification(self):
            for nodeName in nodeNames:
                self.upgradeNode(nodeName)

    @Slot(str, result=Attribute)
    def attribute(self, fullName):
        # type: (str) -> Attribute
        """
        Return the attribute identified by the unique name 'fullName'.
        If it does not exist, return None.
        """
        node, attribute = fullName.split('.', 1)
        if self.node(node).hasAttribute(attribute):
            return self.node(node).attribute(attribute)
        return None

    @Slot(str, result=Attribute)
    def internalAttribute(self, fullName):
        # type: (str) -> Attribute
        """
        Return the internal attribute identified by the unique name 'fullName'.
        If it does not exist, return None.
        """
        node, attribute = fullName.split('.', 1)
        if self.node(node).hasInternalAttribute(attribute):
            return self.node(node).internalAttribute(attribute)
        return None

    @staticmethod
    def getNodeIndexFromName(name):
        """ Nodes are created with a suffix index; returns this index by parsing node name.

        Args:
            name (str): the node name
        Returns:
             int: the index retrieved from node name (-1 if not found)
        """
        try:
            return int(name.split('_')[-1])
        except Exception:
            return -1

    @staticmethod
    def sortNodesByIndex(nodes):
        """
        Sort the given list of Nodes using the suffix index in their names.
        [NodeName_1, NodeName_0] => [NodeName_0, NodeName_1]

        Args:
            nodes (list[Node]): the list of Nodes to sort
        Returns:
            list[Node]: the sorted list of Nodes based on their index
        """
        return sorted(nodes, key=lambda x: Graph.getNodeIndexFromName(x.name))

    def nodesOfType(self, nodeType, sortedByIndex=True):
        """
        Returns all Nodes of the given nodeType.

        Args:
            nodeType (str): the node type name to consider.
            sortedByIndex (bool): whether to sort the nodes by their index (see Graph.sortNodesByIndex)
        Returns:
            list[Node]: the list of nodes matching the given nodeType.
        """
        nodes = [n for n in self._nodes.values() if n.nodeType == nodeType]
        return self.sortNodesByIndex(nodes) if sortedByIndex else nodes

    def findInitNodes(self):
        """
        Returns:
            list[Node]: the list of Init nodes (nodes inheriting from InitNode)
        """
        nodes = [n for n in self._nodes.values() if isinstance(n.nodeDesc, meshroom.core.desc.InitNode)]
        return nodes

    def findNodeCandidates(self, nodeNameExpr: str) -> list[Node]:
        pattern = re.compile(nodeNameExpr)
        return [v for k, v in self._nodes.objects.items() if pattern.match(k)]

    def findNode(self, nodeExpr: str) -> Node:
        candidates = self.findNodeCandidates('^' + nodeExpr)
        if not candidates:
            raise KeyError(f'No node candidate for "{nodeExpr}"')
        if len(candidates) > 1:
            for c in candidates:
                if c.name == nodeExpr:
                    return c
            raise KeyError(f'Multiple node candidates for "{nodeExpr}": {str([c.name for c in candidates])}')
        return candidates[0]

    def findNodes(self, nodesExpr):
        if isinstance(nodesExpr, list):
            return [self.findNode(nodeName) for nodeName in nodesExpr]
        return [self.findNode(nodesExpr)]

    def edge(self, dstAttributeName):
        return self._edges.get(dstAttributeName)

    def getLeafNodes(self, dependenciesOnly):
        nodesWithOutputLink = {edge.src.node for edge in self.getEdges(dependenciesOnly)}
        return set(self._nodes) - nodesWithOutputLink

    def getRootNodes(self, dependenciesOnly):
        nodesWithInputLink = {edge.dst.node for edge in self.getEdges(dependenciesOnly)}
        return set(self._nodes) - nodesWithInputLink

    @changeTopology
    def addEdge(self, srcAttr, dstAttr):
        assert isinstance(srcAttr, Attribute)
        assert isinstance(dstAttr, Attribute)
        if srcAttr.node.graph != self or dstAttr.node.graph != self:
            raise RuntimeError('The attributes of the edge should be part of a common graph.')
        if dstAttr in self.edges.keys():
            raise RuntimeError(f'Destination attribute "{dstAttr.getFullNameToNode()}" is already connected.')
        edge = Edge(srcAttr, dstAttr)
        self.edges.add(edge)
        self.markNodesDirty(dstAttr.node)
        dstAttr.valueChanged.emit()
        dstAttr.isLinkChanged.emit()
        srcAttr.hasOutputConnectionsChanged.emit()
        return edge

    def addEdges(self, *edges):
        with GraphModification(self):
            for edge in edges:
                self.addEdge(*edge)

    @changeTopology
    def removeEdge(self, dstAttr):
        if dstAttr not in self.edges.keys():
            raise RuntimeError(f'Attribute "{dstAttr.getFullNameToNode()}" is not connected')
        edge = self.edges.pop(dstAttr)
        self.markNodesDirty(dstAttr.node)
        dstAttr.valueChanged.emit()
        dstAttr.isLinkChanged.emit()
        edge.src.hasOutputConnectionsChanged.emit()

    def getDepth(self, node, minimal=False):
        """ Return node's depth in this Graph.
        By default, returns the maximal depth of the node unless minimal is set to True.

        Args:
            node (Node): the node to consider.
            minimal (bool): whether to return the minimal depth instead of the maximal one (default).
        Returns:
            int: the node's depth in this Graph.
        """
        assert node.graph == self
        assert not self.dirtyTopology
        minDepth, maxDepth = self._nodesMinMaxDepths[node]
        return minDepth if minimal else maxDepth

    def getInputEdges(self, node, dependenciesOnly):
        return {edge for edge in self.getEdges(dependenciesOnly=dependenciesOnly) if edge.dst.node is node}

    def _getInputEdgesPerNode(self, dependenciesOnly):
        nodeEdges = defaultdict(set)

        for edge in self.getEdges(dependenciesOnly=dependenciesOnly):
            nodeEdges[edge.dst.node].add(edge.src.node)

        return nodeEdges

    def _getOutputEdgesPerNode(self, dependenciesOnly):
        nodeEdges = defaultdict(set)

        for edge in self.getEdges(dependenciesOnly=dependenciesOnly):
            nodeEdges[edge.src.node].add(edge.dst.node)

        return nodeEdges

    def dfs(self, visitor, startNodes=None, longestPathFirst=False):
        # Default direction (visitor.reverse=False): from node to root
        # Reverse direction (visitor.reverse=True): from node to leaves
        nodeChildren = self._getOutputEdgesPerNode(visitor.dependenciesOnly) \
                       if visitor.reverse else self._getInputEdgesPerNode(visitor.dependenciesOnly)
        # Initialize color map
        colors = {}
        for u in self._nodes:
            colors[u] = WHITE

        if longestPathFirst and visitor.reverse:
            # Because we have no knowledge of the node's count between a node and its leaves,
            # it is not possible to handle this case at the moment
            raise NotImplementedError("Graph.dfs(): longestPathFirst=True and visitor.reverse=True are not "
                                      "compatible yet.")

        nodes = startNodes or (self.getRootNodes(visitor.dependenciesOnly)
                               if visitor.reverse else self.getLeafNodes(visitor.dependenciesOnly))

        if longestPathFirst:
            # Graph topology must be known and node depths up-to-date
            assert not self.dirtyTopology
            nodes = sorted(nodes, key=lambda item: item.depth)

        try:
            for node in nodes:
                self.dfsVisit(node, visitor, colors, nodeChildren, longestPathFirst)
        except StopGraphVisit:
            pass

    def dfsVisit(self, u, visitor, colors, nodeChildren, longestPathFirst):
        try:
            self._dfsVisit(u, visitor, colors, nodeChildren, longestPathFirst)
        except StopBranchVisit:
            pass

    def _dfsVisit(self, u, visitor, colors, nodeChildren, longestPathFirst):
        colors[u] = GRAY
        visitor.discoverVertex(u, self)
        # d_time[u] = time = time + 1
        children = nodeChildren[u]
        if longestPathFirst:
            assert not self.dirtyTopology
            children = sorted(children, reverse=True, key=lambda item: self._nodesMinMaxDepths[item][1])
        for v in children:
            visitor.examineEdge((u, v), self)
            if colors[v] == WHITE:
                visitor.treeEdge((u, v), self)
                # (u,v) is a tree edge
                self.dfsVisit(v, visitor, colors, nodeChildren, longestPathFirst)  # TODO: avoid recursion
            elif colors[v] == GRAY:
                # (u,v) is a back edge
                visitor.backEdge((u, v), self)
            elif colors[v] == BLACK:
                # (u,v) is a cross or forward edge
                visitor.forwardOrCrossEdge((u, v), self)
            visitor.finishEdge((u, v), self)
        colors[u] = BLACK
        visitor.finishVertex(u, self)

    def dfsOnFinish(self, startNodes=None, longestPathFirst=False, reverse=False, dependenciesOnly=False):
        """
        Return the node chain from startNodes to the graph roots/leaves.
        Order is defined by the visit and finishVertex event.

        Args:
            startNodes (Node list): the nodes to start the visit from.
            longestPathFirst (bool): (optional) if multiple paths, nodes belonging to
                            the longest one will be visited first.
            reverse (bool): (optional) direction of visit.
                            True is for getting nodes depending on the startNodes (to leaves).
                            False is for getting nodes required for the startNodes (to roots).
        Returns:
            The list of nodes and edges, from startNodes to the graph roots/leaves following edges.
        """
        nodes = []
        edges = []
        visitor = Visitor(reverse=reverse, dependenciesOnly=dependenciesOnly)
        visitor.finishVertex = lambda vertex, graph: nodes.append(vertex)
        visitor.finishEdge = lambda edge, graph: edges.append(edge)
        self.dfs(visitor=visitor, startNodes=startNodes, longestPathFirst=longestPathFirst)
        return nodes, edges

    def dfsOnDiscover(self, startNodes=None, filterTypes=None, longestPathFirst=False, reverse=False, dependenciesOnly=False):
        """
        Return the node chain from startNodes to the graph roots/leaves.
        Order is defined by the visit and discoverVertex event.

        Args:
            startNodes (Node list): the nodes to start the visit from.
            filterTypes (str list): (optional) only return the nodes of the given types
                              (does not stop the visit, this is a post-process only)
            longestPathFirst (bool): (optional) if multiple paths, nodes belonging to
                            the longest one will be visited first.
            reverse (bool): (optional) direction of visit.
                            True is for getting nodes depending on the startNodes (to leaves).
                            False is for getting nodes required for the startNodes (to roots).
        Returns:
            The list of nodes and edges, from startNodes to the graph roots/leaves following edges.
        """
        nodes = []
        edges = []
        visitor = Visitor(reverse=reverse, dependenciesOnly=dependenciesOnly)

        def discoverVertex(vertex, graph):
            if not filterTypes or vertex.nodeType in filterTypes:
                nodes.append(vertex)

        visitor.discoverVertex = discoverVertex
        visitor.examineEdge = lambda edge, graph: edges.append(edge)
        self.dfs(visitor=visitor, startNodes=startNodes, longestPathFirst=longestPathFirst)
        return nodes, edges

    def dfsToProcess(self, startNodes=None):
        """
        Return the full list of predecessor nodes to process in order to compute the given nodes.

        Args:
            startNodes: list of starting nodes. Use all leaves if empty.

        Returns:
             visited nodes and edges that are not already computed (node.status != SUCCESS).
             The order is defined by the visit and finishVertex event.
        """
        nodes = []
        edges = []
        visitor = Visitor(reverse=False, dependenciesOnly=True)

        def discoverVertex(vertex, graph):
            if vertex.hasStatus(Status.SUCCESS):
                # stop branch visit if discovering a node already computed
                raise StopBranchVisit()

        def finishVertex(vertex, graph):
            chunksToProcess = []
            for chunk in vertex.chunks:
                if chunk.status.status is not Status.SUCCESS:
                    chunksToProcess.append(chunk)
            if chunksToProcess:
                nodes.append(vertex)  # We could collect specific chunks

        def finishEdge(edge, graph):
            if edge[0].isComputed or edge[1].isComputed:
                return
            edges.append(edge)

        visitor.finishVertex = finishVertex
        visitor.finishEdge = finishEdge
        visitor.discoverVertex = discoverVertex
        self.dfs(visitor=visitor, startNodes=startNodes)
        return nodes, edges

    @Slot(Node, result=bool)
    def canComputeTopologically(self, node):
        """
        Return the computability of a node based on itself and its dependency chain.
        It is a static result as it depends on the graph topology.
        Computation can't happen for:
         - CompatibilityNodes
         - nodes having a non-computed CompatibilityNode in its dependency chain

        Args:
            node (Node): the node to evaluate

        Returns:
            bool: whether the node can be computed
        """
        if isinstance(node, CompatibilityNode):
            return False
        return not self._computationBlocked[node]

    def updateNodesTopologicalData(self):
        """
        Compute and cache nodes topological data:
            - min and max depth
            - computability
        """

        self._nodesMinMaxDepths.clear()
        self._computationBlocked.clear()

        compatNodes = []
        visitor = Visitor(reverse=False, dependenciesOnly=False)

        def discoverVertex(vertex, graph):
            # initialize depths
            self._nodesMinMaxDepths[vertex] = (0, 0)
            # initialize computability
            self._computationBlocked[vertex] = False
            if isinstance(vertex, CompatibilityNode):
                compatNodes.append(vertex)
                # a not computed CompatibilityNode blocks computation
                if not vertex.hasStatus(Status.SUCCESS):
                    self._computationBlocked[vertex] = True

        def finishEdge(edge, graph):
            currentVertex, inputVertex = edge

            # update depths
            currentDepths = self._nodesMinMaxDepths[currentVertex]
            inputDepths = self._nodesMinMaxDepths[inputVertex]
            if currentDepths[0] == 0:
                # if not initialized, set the depth of the first child
                depthMin = inputDepths[0] + 1
            else:
                depthMin = min(currentDepths[0], inputDepths[0] + 1)
            self._nodesMinMaxDepths[currentVertex] = (depthMin, max(currentDepths[1], inputDepths[1] + 1))

            # update computability
            if currentVertex.hasStatus(Status.SUCCESS):
                # output is already computed and available,
                # does not depend on input connections computability
                return
            # propagate inputVertex computability
            self._computationBlocked[currentVertex] |= self._computationBlocked[inputVertex]

        leaves = self.getLeafNodes(visitor.dependenciesOnly)
        visitor.finishEdge = finishEdge
        visitor.discoverVertex = discoverVertex
        self.dfs(visitor=visitor, startNodes=leaves)

        # update graph computability status
        canComputeLeaves = all([self.canComputeTopologically(node) for node in leaves])
        if self._canComputeLeaves != canComputeLeaves:
            self._canComputeLeaves = canComputeLeaves
            self.canComputeLeavesChanged.emit()

        # update compatibilityNodes model
        if len(self._compatibilityNodes) != len(compatNodes):
            self._compatibilityNodes.reset(compatNodes)

    compatibilityNodes = Property(BaseObject, lambda self: self._compatibilityNodes, constant=True)

    def dfsMaxEdgeLength(self, startNodes=None, dependenciesOnly=True):
        """
        :param startNodes: list of starting nodes. Use all leaves if empty.
        :return:
        """
        nodesStack = []
        edgesScore = defaultdict(int)
        visitor = Visitor(reverse=False, dependenciesOnly=dependenciesOnly)

        def finishEdge(edge, graph):
            u, v = edge
            for i, n in enumerate(reversed(nodesStack)):
                index = i + 1
                if index > edgesScore[(n, v)]:
                    edgesScore[(n, v)] = index

        def finishVertex(vertex, graph):
            v = nodesStack.pop()
            assert v == vertex

        visitor.discoverVertex = lambda vertex, graph: nodesStack.append(vertex)
        visitor.finishVertex = finishVertex
        visitor.finishEdge = finishEdge
        self.dfs(visitor=visitor, startNodes=startNodes, longestPathFirst=True)
        return edgesScore

    def flowEdges(self, startNodes=None, dependenciesOnly=True):
        """
        Return as few edges as possible, such that if there is a directed path from one vertex to another in the
        original graph, there is also such a path in the reduction.

        :param startNodes:
        :return: the remaining edges after a transitive reduction of the graph.
        """
        flowEdges = []
        edgesScore = self.dfsMaxEdgeLength(startNodes, dependenciesOnly)

        for link, score in edgesScore.items():
            assert score != 0
            if score == 1:
                flowEdges.append(link)
        return flowEdges

    def getEdges(self, dependenciesOnly=False):
        if not dependenciesOnly:
            return self.edges

        outEdges = []
        for e in self.edges:
            attr = e.src
            if dependenciesOnly:
                if attr.isLink:
                    attr = attr.getLinkParam(recursive=True)
                if not attr.isOutput:
                    continue
            newE = Edge(attr, e.dst)
            outEdges.append(newE)
        return outEdges

    def getInputNodes(self, node, recursive, dependenciesOnly):
        """ Return either the first level input nodes of a node or the whole chain. """
        if not recursive:
            return {edge.src.node for edge in self.getEdges(dependenciesOnly) if edge.dst.node is node}

        inputNodes, edges = self.dfsOnDiscover(startNodes=[node], filterTypes=None, reverse=False)
        return inputNodes[1:]  # exclude current node

    def getOutputNodes(self, node, recursive, dependenciesOnly):
        """ Return either the first level output nodes of a node or the whole chain. """
        if not recursive:
            return {edge.dst.node for edge in self.getEdges(dependenciesOnly) if edge.src.node is node}

        outputNodes, edges = self.dfsOnDiscover(startNodes=[node], filterTypes=None, reverse=True)
        return outputNodes[1:]  # exclude current node

    @Slot(Node, result=int)
    def canSubmitOrCompute(self, startNode):
        """
        Check if a node can be submitted/computed.
        It does not depend on the topology of the graph and is based on the node status and its dependencies.

        Returns:
            int: 0 = cannot be submitted or computed /
                1 = can be computed /
                2 = can be submitted /
                3 = can be submitted and computed
        """
        if startNode.isAlreadySubmittedOrFinished():
            return 0

        class SCVisitor(Visitor):
            def __init__(self, reverse, dependenciesOnly):
                super().__init__(reverse, dependenciesOnly)

            canCompute = True
            canSubmit = True

            def discoverVertex(self, vertex, graph):
                if vertex.isAlreadySubmitted():
                    self.canSubmit = False
                    if vertex.isExtern():
                        self.canCompute = False

        visitor = SCVisitor(reverse=False, dependenciesOnly=True)
        self.dfs(visitor=visitor, startNodes=[startNode])
        return visitor.canCompute + (2 * visitor.canSubmit)

    def _applyExpr(self):
        with GraphModification(self):
            for node in self._nodes:
                node._applyExpr()

    def toDict(self):
        nodes = {k: node.toDict() for k, node in self._nodes.objects.items()}
        nodes = dict(sorted(nodes.items()))
        return nodes

    @Slot(result=str)
    def asString(self):
        return str(self.toDict())

    def copy(self) -> "Graph":
        """Create a copy of this Graph instance."""
        graph = Graph("")
        graph._deserialize(self.serialize())
        return graph

    def serialize(self, asTemplate: bool = False) -> dict:
        """Serialize this Graph instance.
        
        Args:
            asTemplate: Whether to use the template serialization.

        Returns:
            The serialized graph data.
        """
        SerializerClass = TemplateGraphSerializer if asTemplate else GraphSerializer
        return SerializerClass(self).serialize()

    def serializePartial(self, nodes: list[Node]) -> dict:
        """Partially serialize this graph considering only the given list of `nodes`.

        Args:
            nodes: The list of nodes to serialize.

        Returns:
            The serialized graph data.
        """
        return PartialGraphSerializer(self, nodes=nodes).serialize()

    def save(self, filepath=None, setupProjectFile=True, template=False):
        """
        Save the current Meshroom graph as a serialized ".mg" file.

        Args:
            filepath: project filepath to save as.
            setupProjectFile: Store the reference to the project file and setup the cache directory.
                              If false, it only saves the graph of the project file as a template.
            template: If true, saves the current graph as a template.
        """
        # Update the saving flag indicating that the current graph is being saved
        self._saving = True
        try:
            self._save(filepath=filepath, setupProjectFile=setupProjectFile, template=template)
        finally:
            self._saving = False

    def _save(self, filepath=None, setupProjectFile=True, template=False):
        path = filepath or self._filepath
        if not path:
            path = generateTempProjectFilepath()

        data = self.serialize(template)

        with open(path, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)

        if path != self._filepath and setupProjectFile:
            self._setFilepath(path)

        # update the file date version
        self._fileDateVersion = os.path.getmtime(path)

    def saveAsTemp(self, tmpFolder=None):
        """
        Save the current Meshroom graph as a temporary project file.
        """
        # Update the saving flag indicating that the current graph is being saved
        self._saving = True
        try:
            self._saveAsTemp(tmpFolder)
        finally:
            self._saving = False

    def _saveAsTemp(self, tmpFolder=None):
        projectPath = generateTempProjectFilepath(tmpFolder)
        self._save(projectPath)

    def _setFilepath(self, filepath):
        """
        Set the internal filepath of this Graph.
        This method should not be used directly from outside, use save/load instead.
        Args:
            filepath: the graph file path
        """
        if not os.path.isfile(filepath):
            self._unsetFilepath()
            return

        if self._filepath == filepath:
            return
        self._filepath = filepath
        # For now:
        #  * cache folder is located next to the graph file
        #  * graph name if the basename of the graph file
        self.name = os.path.splitext(os.path.basename(filepath))[0]
        self.cacheDir = os.path.join(os.path.abspath(os.path.dirname(filepath)), meshroom.core.cacheFolderName)
        self.filepathChanged.emit()

    def _unsetFilepath(self):
        self._filepath = ""
        self.name = ""
        self.cacheDir = ""
        self.filepathChanged.emit()

    def updateInternals(self, startNodes=None, force=False):
        nodes, edges = self.dfsOnFinish(startNodes=startNodes)
        for node in nodes:
            if node.dirty or force:
                node.updateInternals()

    def updateStatusFromCache(self, force=False):
        for node in self._nodes:
            if node.dirty or force:
                node.updateStatusFromCache()

    def updateStatisticsFromCache(self):
        for node in self._nodes:
            node.updateStatisticsFromCache()

    def updateNodesPerUid(self):
        """ Update the duplicate nodes (sharing same UID) list of each node. """
        # First step is to construct a map UID/nodes
        nodesPerUid = {}
        for node in self.nodes:
            uid = node._uid

            # We try to add the node to the list corresponding to this UID
            try:
                nodesPerUid.get(uid).append(node)
            # If it fails because the uid is not in the map, we add it
            except AttributeError:
                nodesPerUid.update({uid: [node]})

        # Now, update each individual node
        for node in self.nodes:
            node.updateDuplicates(nodesPerUid)

    def update(self):
        if not self._updateEnabled:
            # To do the update once for multiple changes
            self._updateRequested = True
            return

        self.updateInternals()
        if os.path.exists(self._cacheDir):
            self.updateStatusFromCache()
        for node in self.nodes:
            node.dirty = False

        self.updateNodesPerUid()

        # Graph topology has changed
        if self.dirtyTopology:
            # update nodes topological data cache
            self.updateNodesTopologicalData()
            self.dirtyTopology = False

        self.updated.emit()

    def markNodesDirty(self, fromNode):
        """
        Mark all nodes following 'fromNode' as dirty.
        All nodes marked as dirty will get their outputs to be re-evaluated
        during the next graph update.

        Args:
            fromNode (Node): the node to start the invalidation from

        See Also:
            Graph.update, Graph.updateInternals, Graph.updateStatusFromCache
        """
        nodes, edges = self.dfsOnDiscover(startNodes=[fromNode], reverse=True)
        for node in nodes:
            node.dirty = True

    def stopExecution(self):
        """ Request graph execution to be stopped by terminating running chunks"""
        for chunk in self.iterChunksByStatus(Status.RUNNING):
            if not chunk.isExtern():
                chunk.stopProcess()

    @Slot()
    def forceUnlockNodes(self):
        """ Force to unlock all the nodes. """
        for node in self.nodes:
            node.setLocked(False)

    @Slot()
    def clearSubmittedNodes(self):
        """ Reset the status of already submitted nodes to Status.NONE """
        for node in self.nodes:
            node.clearSubmittedChunks()

    def clearLocallySubmittedNodes(self):
        """ Reset the status of already locally submitted nodes to Status.NONE """
        for node in self.nodes:
            node.clearLocallySubmittedChunks()

    def iterChunksByStatus(self, status):
        """ Iterate over NodeChunks with the given status """
        for node in self.nodes:
            for chunk in node.chunks:
                if chunk.status.status == status:
                    yield chunk

    def getChunksByStatus(self, status):
        """ Return the list of NodeChunks with the given status """
        chunks = []
        for node in self.nodes:
            chunks += [chunk for chunk in node.chunks if chunk.status.status == status]
        return chunks

    def getChunks(self, nodes=None):
        """ Returns the list of NodeChunks for the given list of nodes (for all nodes if nodes is None) """
        chunks = []
        for node in nodes or self.nodes:
            chunks += [chunk for chunk in node.chunks]
        return chunks

    def getOrderedChunks(self):
        """ Get chunks as visited by dfsOnFinish.

        Returns:
            list of NodeChunks: the ordered list of NodeChunks
        """
        return self.getChunks(self.dfsOnFinish()[0])

    @property
    def nodes(self):
        return self._nodes

    @property
    def edges(self):
        return self._edges

    @property
    def cacheDir(self):
        return self._cacheDir

    @cacheDir.setter
    def cacheDir(self, value):
        if self._cacheDir == value:
            return
        # use unix-style paths for cache directory
        self._cacheDir = value.replace(os.path.sep, "/")
        self.updateInternals(force=True)
        self.updateStatusFromCache(force=True)
        self.cacheDirChanged.emit()

    @property
    def fileDateVersion(self):
        return self._fileDateVersion

    @fileDateVersion.setter
    def fileDateVersion(self, value):
        self._fileDateVersion = value

    @Slot(str, result=float)
    def getFileDateVersionFromPath(self, value):
        return os.path.getmtime(value)

    def setVerbose(self, v):
        with GraphModification(self):
            for node in self._nodes:
                if node.hasAttribute('verbose'):
                    try:
                        node.verbose.value = v
                    except Exception:
                        pass

    nodes = Property(BaseObject, nodes.fget, constant=True)
    edges = Property(BaseObject, edges.fget, constant=True)
    filepathChanged = Signal()
    filepath = Property(str, lambda self: self._filepath, notify=filepathChanged)
    isSaving = Property(bool, isSaving.fget, constant=True)
    fileReleaseVersion = Property(str, lambda self: self.header.get(GraphIO.Keys.ReleaseVersion, "0.0"),
                                  notify=filepathChanged)
    fileDateVersion = Property(float, fileDateVersion.fget, fileDateVersion.fset, notify=filepathChanged)
    cacheDirChanged = Signal()
    cacheDir = Property(str, cacheDir.fget, cacheDir.fset, notify=cacheDirChanged)
    updated = Signal()
    canComputeLeavesChanged = Signal()
    canComputeLeaves = Property(bool, lambda self: self._canComputeLeaves, notify=canComputeLeavesChanged)


def loadGraph(filepath, strictCompatibility: bool = False) -> Graph:
    """
    Load a Graph from a Meshroom Graph (.mg) file.

    Args:
        filepath: The path to the Meshroom Graph file.
        strictCompatibility: If True, raise a GraphCompatibilityError if the loaded Graph has node compatibility issues.

    Returns:
        Graph: The loaded Graph instance.

    Raises:
        GraphCompatibilityError: If the Graph has node compatibility issues and `strictCompatibility` is True.
    """
    graph = Graph("")
    graph.load(filepath)

    compatibilityIssues = len(graph.compatibilityNodes) > 0
    if compatibilityIssues and strictCompatibility:
        raise GraphCompatibilityError(filepath, {n.name: str(n.issue) for n in graph.compatibilityNodes})

    graph.update()
    return graph


def getAlreadySubmittedChunks(nodes):
    out = []
    for node in nodes:
        for chunk in node.chunks:
            if chunk.isAlreadySubmitted():
                out.append(chunk)
    return out


def executeGraph(graph, toNodes=None, forceCompute=False, forceStatus=False):
    """
    """
    if forceCompute:
        nodes, edges = graph.dfsOnFinish(startNodes=toNodes)
    else:
        nodes, edges = graph.dfsToProcess(startNodes=toNodes)
        chunksInConflict = getAlreadySubmittedChunks(nodes)

        if chunksInConflict:
            chunksStatus = {chunk.status.status.name for chunk in chunksInConflict}
            chunksName = [node.name for node in chunksInConflict]
            msg = 'WARNING: Some nodes are already submitted with status: {}\nNodes: {}'.format(
                  ', '.join(chunksStatus),
                  ', '.join(chunksName)
                  )
            if forceStatus:
                print(msg)
            else:
                raise RuntimeError(msg)

    print('Nodes to execute: ', str([n.name for n in nodes]))

    graph.save()

    for node in nodes:
        node.beginSequence(forceCompute)

    for n, node in enumerate(nodes):
        try:
            node.preprocess()
            multiChunks = len(node.chunks) > 1
            for c, chunk in enumerate(node.chunks):
                if multiChunks:
                    print('\n[{node}/{nbNodes}]({chunk}/{nbChunks}) {nodeName}'.format(
                        node=n+1, nbNodes=len(nodes),
                        chunk=c+1, nbChunks=len(node.chunks), nodeName=node.nodeType))
                else:
                    print(f'\n[{n + 1}/{len(nodes)}] {node.nodeType}')
                chunk.process(forceCompute)
            node.postprocess()
        except Exception as e:
            logging.error(f"Error on node computation: {e}")
            graph.clearSubmittedNodes()
            raise

    for node in nodes:
        node.endSequence()


def submitGraph(graph, submitter, toNodes=None, submitLabel="{projectName}"):
    nodesToProcess, edgesToProcess = graph.dfsToProcess(startNodes=toNodes)
    flowEdges = graph.flowEdges(startNodes=toNodes)
    edgesToProcess = set(edgesToProcess).intersection(flowEdges)

    if not nodesToProcess:
        logging.warning('Nothing to compute')
        return

    logging.info(f"Nodes to process: {edgesToProcess}")
    logging.info(f"Edges to process: {edgesToProcess}")

    sub = None
    if submitter:
        sub = meshroom.core.submitters.get(submitter, None)
    elif len(meshroom.core.submitters) == 1:
        # if only one submitter available use it
        sub = meshroom.core.submitters.values()[0]
    if sub is None:
        raise RuntimeError("Unknown Submitter: '{submitter}'. Available submitters are: '{allSubmitters}'.".format(
            submitter=submitter, allSubmitters=str(meshroom.core.submitters.keys())))

    try:
        res = sub.submit(nodesToProcess, edgesToProcess, graph.filepath, submitLabel=submitLabel)
        if res:
            for node in nodesToProcess:
                node.submit()  # update node status
    except Exception as e:
        logging.error(f"Error on submit : {e}")


def submit(graphFile, submitter, toNode=None, submitLabel="{projectName}"):
    """
    Submit the given graph via the given submitter.
    """
    graph = loadGraph(graphFile)
    toNodes = graph.findNodes(toNode) if toNode else None
    submitGraph(graph, submitter, toNodes, submitLabel=submitLabel)
