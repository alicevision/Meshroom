from __future__ import print_function

import json
import logging
import os
import re
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
from meshroom.core.node import nodeFactory, Status, Node, CompatibilityNode

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
        super(Edge, self).__init__(parent)
        self._src = weakref.ref(src)
        self._dst = weakref.ref(dst)
        self._repr = "<Edge> {} -> {}".format(self._src(), self._dst())

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


class Visitor(object):
    """
    Base class for Graph Visitors that does nothing.
    Sub-classes can override any method to implement specific algorithms.
    """
    def __init__(self, reverse, dependenciesOnly):
        super(Visitor, self).__init__()
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
    _cacheDir = ""

    class IO(object):
        """ Centralize Graph file keys and IO version. """
        __version__ = "2.0"

        class Keys(object):
            """ File Keys. """
            # Doesn't inherit enum to simplify usage (Graph.IO.Keys.XX, without .value)
            Header = "header"
            NodesVersions = "nodesVersions"
            ReleaseVersion = "releaseVersion"
            FileVersion = "fileVersion"
            Graph = "graph"

        class Features(Enum):
            """ File Features. """
            Graph = "graph"
            Header = "header"
            NodesVersions = "nodesVersions"
            PrecomputedOutputs = "precomputedOutputs"
            NodesPositions = "nodesPositions"

        @staticmethod
        def getFeaturesForVersion(fileVersion):
            """ Return the list of supported features based on a file version.

            Args:
                fileVersion (str, Version): the file version

            Returns:
                tuple of Graph.IO.Features: the list of supported features
            """
            if isinstance(fileVersion, str):
                fileVersion = Version(fileVersion)

            features = [Graph.IO.Features.Graph]
            if fileVersion >= Version("1.0"):
                features += [Graph.IO.Features.Header,
                             Graph.IO.Features.NodesVersions,
                             Graph.IO.Features.PrecomputedOutputs,
                             ]

            if fileVersion >= Version("1.1"):
                features += [Graph.IO.Features.NodesPositions]

            return tuple(features)

    def __init__(self, name, parent=None):
        super(Graph, self).__init__(parent)
        self.name = name
        self._loading = False
        self._saving = False
        self._updateEnabled = True
        self._updateRequested = False
        self.dirtyTopology = False
        self._nodesMinMaxDepths = {}
        self._computationBlocked = {}
        self._canComputeLeaves = True
        self._nodes = DictModel(keyAttrName='name', parent=self)
        # Edges: use dst attribute as unique key since it can only have one input connection
        self._edges = DictModel(keyAttrName='dst', parent=self)
        self._importedNodes = DictModel(keyAttrName='name', parent=self)
        self._compatibilityNodes = DictModel(keyAttrName='name', parent=self)
        self.cacheDir = meshroom.core.defaultCacheFolder
        self._filepath = ''
        self._fileDateVersion = 0
        self.header = {}

    def clear(self):
        self.header.clear()
        self._compatibilityNodes.clear()
        self._edges.clear()
        # Tell QML nodes are going to be deleted
        for node in self._nodes:
            node.alive = False
        self._importedNodes.clear()
        self._nodes.clear()
        self._unsetFilepath()

    @property
    def fileFeatures(self):
        """ Get loaded file supported features based on its version. """
        return Graph.IO.getFeaturesForVersion(self.header.get(Graph.IO.Keys.FileVersion, "0.0"))

    @property
    def isLoading(self):
        """ Return True if the graph is currently being loaded. """
        return self._loading
    
    @property
    def isSaving(self):
        """ Return True if the graph is currently being saved. """
        return self._saving

    @Slot(str)
    def load(self, filepath, setupProjectFile=True, importProject=False, publishOutputs=False):
        """
        Load a Meshroom graph ".mg" file.

        Args:
            filepath: project filepath to load
            setupProjectFile: Store the reference to the project file and setup the cache directory.
                              If false, it only loads the graph of the project file as a template.
            importProject: True if the project that is loaded will be imported in the current graph, instead
                           of opened.
            publishOutputs: True if "Publish" nodes from templates should not be ignored.
        """
        self._loading = True
        try:
            return self._load(filepath, setupProjectFile, importProject, publishOutputs)
        finally:
            self._loading = False

    def _load(self, filepath, setupProjectFile, importProject, publishOutputs):
        if not importProject:
            self.clear()
        with open(filepath) as jsonFile:
            fileData = json.load(jsonFile)

        self.header = fileData.get(Graph.IO.Keys.Header, {})

        fileVersion = self.header.get(Graph.IO.Keys.FileVersion, "0.0")
        # Retro-compatibility for all project files with the previous UID format
        if Version(fileVersion) < Version("2.0"):
            # For internal folders, all "{uid0}" keys should be replaced with "{uid}"
            updatedFileData = json.dumps(fileData).replace("{uid0}", "{uid}")

            # For fileVersion < 2.0, the nodes' UID is stored as:
            # "uids": {"0": "hashvalue"}
            # These should be identified and replaced with:
            # "uid": "hashvalue"
            uidPattern = re.compile(r'"uids": \{"0":.*?\}')
            uidOccurrences = uidPattern.findall(updatedFileData)
            for occ in uidOccurrences:
                uid = occ.split("\"")[-2]  # UID is second to last element
                newUidStr = r'"uid": "{}"'.format(uid)
                updatedFileData = updatedFileData.replace(occ, newUidStr)
            fileData = json.loads(updatedFileData)

        # Older versions of Meshroom files only contained the serialized nodes
        graphData = fileData.get(Graph.IO.Keys.Graph, fileData)

        if importProject:
            self._importedNodes.clear()
            graphData = self.updateImportedProject(graphData)

        if not isinstance(graphData, dict):
            raise RuntimeError('loadGraph error: Graph is not a dict. File: {}'.format(filepath))

        nodesVersions = self.header.get(Graph.IO.Keys.NodesVersions, {})

        self._fileDateVersion = os.path.getmtime(filepath)

        # Check whether the file was saved as a template in minimal mode
        isTemplate = self.header.get("template", False)

        with GraphModification(self):
            # iterate over nodes sorted by suffix index in their names
            for nodeName, nodeData in sorted(graphData.items(), key=lambda x: self.getNodeIndexFromName(x[0])):
                if not isinstance(nodeData, dict):
                    raise RuntimeError('loadGraph error: Node is not a dict. File: {}'.format(filepath))

                # retrieve version from
                #   1. nodeData: node saved from a CompatibilityNode
                #   2. nodesVersion in file header: node saved from a Node
                #   3. fallback to no version "0.0": retro-compatibility
                if "version" not in nodeData:
                    nodeData["version"] = nodesVersions.get(nodeData["nodeType"], "0.0")

                # if the node is a "Publish" node and comes from a template file, it should be ignored
                # unless publishOutputs is True
                if isTemplate and not publishOutputs and nodeData["nodeType"] == "Publish":
                    continue

                n = nodeFactory(nodeData, nodeName, template=isTemplate)

                # Add node to the graph with raw attributes values
                self._addNode(n, nodeName)

                if importProject:
                    self._importedNodes.add(n)

            # Create graph edges by resolving attributes expressions
            self._applyExpr()

            if setupProjectFile:
                # Update filepath related members
                # Note: needs to be done at the end as it will trigger an updateInternals.
                self._setFilepath(filepath)
            elif not isTemplate:
                # If no filepath is being set but the graph is not a template, trigger an updateInternals either way.
                self.updateInternals()

            # By this point, the graph has been fully loaded and an updateInternals has been triggered, so all the
            # nodes' links have been resolved and their UID computations are all complete.
            # It is now possible to check whether the UIDs stored in the graph file for each node correspond to the ones
            # that were computed.
            if not isTemplate:  # UIDs are not stored in templates
                self._evaluateUidConflicts(graphData)
                try:
                    self._applyExpr()
                except Exception as e:
                    logging.warning(e)

        return True

    def _evaluateUidConflicts(self, data):
        """
        Compare the UIDs of all the nodes in the graph with the UID that is expected in the graph file. If there
        are mismatches, the nodes with the unexpected UID are replaced with "UidConflict" compatibility nodes.
        Already existing nodes are removed and re-added to the graph identically to preserve all the edges,
        which may otherwise be invalidated when a node with output edges but a UID conflict is re-generated as a
        compatibility node.

        Args:
            data (dict): the dictionary containing all the nodes to import and their data
        """
        for nodeName, nodeData in sorted(data.items(), key=lambda x: self.getNodeIndexFromName(x[0])):
            node = self.node(nodeName)

            savedUid = nodeData.get("uid", None)
            graphUid = node._uid  # Node's UID from the graph itself

            if savedUid != graphUid and graphUid is not None:
                # Different UIDs, remove the existing node from the graph and replace it with a CompatibilityNode
                logging.debug("UID conflict detected for {}".format(nodeName))
                self.removeNode(nodeName)
                n = nodeFactory(nodeData, nodeName, template=False, uidConflict=True)
                self._addNode(n, nodeName)
            else:
                # f connecting nodes have UID conflicts and are removed/re-added to the graph, some edges may be lost:
                # the links will be erroneously updated, and any further resolution will fail.
                # Recreating the entire graph as it was ensures that all edges will be correctly preserved.
                self.removeNode(nodeName)
                n = nodeFactory(nodeData, nodeName, template=False, uidConflict=False)
                self._addNode(n, nodeName)

    def updateImportedProject(self, data):
        """
        Update the names and links of the project to import so that it can fit
        correctly in the existing graph.

        Parse all the nodes from the project that is going to be imported.
        If their name already exists in the graph, replace them with new names,
        then parse all the nodes' inputs/outputs to replace the old names with
        the new ones in the links.

        Args:
            data (dict): the dictionary containing all the nodes to import and their data

        Returns:
            updatedData (dict): the dictionary containing all the nodes to import with their updated names and data
        """
        nameCorrespondences = {}  # maps the old node name to its updated one
        updatedData = {}  # input data with updated node names and links

        def createUniqueNodeName(nodeNames, inputName):
            """
            Create a unique name that does not already exist in the current graph or in the list
            of nodes that will be imported.
            """
            i = 1
            while i:
                newName = "{name}_{index}".format(name=inputName, index=i)
                if newName not in nodeNames and newName not in updatedData.keys():
                    return newName
                i += 1

        # First pass to get all the names that already exist in the graph, update them, and keep track of the changes
        for nodeName, nodeData in sorted(data.items(), key=lambda x: self.getNodeIndexFromName(x[0])):
            if not isinstance(nodeData, dict):
                raise RuntimeError('updateImportedProject error: Node is not a dict.')

            if nodeName in self._nodes.keys() or nodeName in updatedData.keys():
                newName = createUniqueNodeName(self._nodes.keys(), nodeData["nodeType"])
                updatedData[newName] = nodeData
                nameCorrespondences[nodeName] = newName

            else:
                updatedData[nodeName] = nodeData

        newNames = [nodeName for nodeName in updatedData]  # names of all the nodes that will be added

        # Second pass to update all the links in the input/output attributes for every node with the new names
        for nodeName, nodeData in updatedData.items():
            nodeType = nodeData.get("nodeType", None)
            nodeDesc = meshroom.core.nodesDesc[nodeType]

            inputs = nodeData.get("inputs", {})
            outputs = nodeData.get("outputs", {})

            if inputs:
                inputs = self.updateLinks(inputs, nameCorrespondences)
                inputs = self.resetExternalLinks(inputs, nodeDesc.inputs, newNames)
                updatedData[nodeName]["inputs"] = inputs
            if outputs:
                outputs = self.updateLinks(outputs, nameCorrespondences)
                outputs = self.resetExternalLinks(outputs, nodeDesc.outputs, newNames)
                updatedData[nodeName]["outputs"] = outputs

        return updatedData

    @staticmethod
    def updateLinks(attributes, nameCorrespondences):
        """
        Update all the links that refer to nodes that are going to be imported and whose
        names have to be updated.

        Args:
            attributes (dict): attributes whose links need to be updated
            nameCorrespondences (dict): node names to replace in the links with the name to replace them with

        Returns:
            attributes (dict): the attributes with all the updated links
        """
        for key, val in attributes.items():
            for corr in nameCorrespondences.keys():
                if isinstance(val, str) and corr in val:
                    attributes[key] = val.replace(corr, nameCorrespondences[corr])
                elif isinstance(val, list):
                    for v in val:
                        if isinstance(v, str):
                            if corr in v:
                                val[val.index(v)] = v.replace(corr, nameCorrespondences[corr])
                        else:  # the list does not contain strings, so there cannot be links to update
                            break
                    attributes[key] = val

        return attributes

    @staticmethod
    def resetExternalLinks(attributes, nodeDesc, newNames):
        """
        Reset all links to nodes that are not part of the nodes which are going to be imported:
        if there are links to nodes that are not in the list, then it means that the references
        are made to external nodes, and we want to get rid of those.

        Args:
            attributes (dict): attributes whose links might need to be reset
            nodeDesc (list): list with all the attributes' description (including their default value)
            newNames (list): names of the nodes that are going to be imported; no node name should be referenced
                             in the links except those contained in this list

        Returns:
            attributes (dict): the attributes with all the links referencing nodes outside those which will be imported
                               reset to their default values
        """
        for key, val in attributes.items():
            defaultValue = None
            for desc in nodeDesc:
                if desc.name == key:
                    defaultValue = desc.value
                    break

            if isinstance(val, str):
                if Attribute.isLinkExpression(val) and not any(name in val for name in newNames):
                    if defaultValue is not None:  # prevents from not entering condition if defaultValue = ''
                        attributes[key] = defaultValue

            elif isinstance(val, list):
                removedCnt = len(val)  # counter to know whether all the list entries will be deemed invalid
                tmpVal = list(val)  # deep copy to ensure we iterate over the entire list (even if elements are removed)
                for v in tmpVal:
                    if isinstance(v, str) and Attribute.isLinkExpression(v) and not any(name in v for name in newNames):
                        val.remove(v)
                        removedCnt -= 1
                if removedCnt == 0 and defaultValue is not None:  # if all links were wrong, reset the attribute
                    attributes[key] = defaultValue

        return attributes

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

    def pasteNodes(self, data, position):
        """
        Paste node(s) in the graph with their connections. The connections can only be between
        the pasted nodes and not with the rest of the graph.

        Args:
            data (dict): the dictionary containing the information about the nodes to paste, with their names and
                         links already updated to be added to the graph
            position (list): the list of positions for each node to paste

        Returns:
            list: the list of Node objects that were pasted and added to the graph
        """
        nodes = []
        with GraphModification(self):
            positionCnt = 0  # always valid because we know the data is sorted the same way as the position list
            for key in sorted(data):
                nodeType = data[key].get("nodeType", None)
                if not nodeType:  # this case should never occur, as the data should have been prefiltered first
                    pass

                attributes = {}
                attributes.update(data[key].get("inputs", {}))
                attributes.update(data[key].get("outputs", {}))
                attributes.update(data[key].get("internalInputs", {}))

                node = Node(nodeType, position=position[positionCnt], **attributes)
                self._addNode(node, key)

                nodes.append(node)
                positionCnt += 1

            self._applyExpr()
        return nodes

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
            if node in self._importedNodes:
                self._importedNodes.remove(node)
            self.update()

        return inEdges, outEdges, outListAttributes

    def addNewNode(self, nodeType, name=None, position=None, **kwargs):
        """
        Create and add a new node to the graph.

        Args:
            nodeType (str): the node type name.
            name (str): if specified, the desired name for this node. If not unique, will be prefixed (_N).
            position (Position): (optional) the position of the node
            **kwargs: keyword arguments to initialize node's attributes

        Returns:
             The newly created node.
        """
        if name and name in self._nodes.keys():
            name = self._createUniqueNodeName(name)

        n = self.addNode(Node(nodeType, position=position, **kwargs), uniqueName=name)
        n.updateInternals()
        return n

    def _createUniqueNodeName(self, inputName):
        i = 1
        while i:
            newName = "{name}_{index}".format(name=inputName, index=i)
            if newName not in self._nodes.objects:
                return newName
            i += 1

    def node(self, nodeName):
        return self._nodes.get(nodeName)

    def upgradeNode(self, nodeName):
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
        with GraphModification(self):
            inEdges, outEdges, outListAttributes = self.removeNode(nodeName)
            self.addNode(upgradedNode, nodeName)
            for dst, src in outEdges.items():
                # Re-create the entries in ListAttributes that were completely removed during the call to "removeNode"
                # If they are not re-created first, adding their edges will lead to errors
                # 0 = attribute name, 1 = attribute index, 2 = attribute value
                if dst in outListAttributes.keys():
                    listAttr = self.attribute(outListAttributes[dst][0])
                    if isinstance(outListAttributes[dst][2], list):
                        listAttr[outListAttributes[dst][1]:outListAttributes[dst][1]] = outListAttributes[dst][2]
                    else:
                        listAttr.insert(outListAttributes[dst][1], outListAttributes[dst][2])
                try:
                    self.addEdge(self.attribute(src), self.attribute(dst))
                except (KeyError, ValueError) as e:
                    logging.warning("Failed to restore edge {} -> {}: {}".format(src, dst, str(e)))

        return upgradedNode, inEdges, outEdges, outListAttributes

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

    def findNodeCandidates(self, nodeNameExpr):
        pattern = re.compile(nodeNameExpr)
        return [v for k, v in self._nodes.objects.items() if pattern.match(k)]

    def findNode(self, nodeExpr):
        candidates = self.findNodeCandidates('^' + nodeExpr)
        if not candidates:
            raise KeyError('No node candidate for "{}"'.format(nodeExpr))
        if len(candidates) > 1:
            for c in candidates:
                if c.name == nodeExpr:
                    return c
            raise KeyError('Multiple node candidates for "{}": {}'.format(nodeExpr, str([c.name for c in candidates])))
        return candidates[0]

    def findNodes(self, nodesExpr):
        if isinstance(nodesExpr, list):
            return [self.findNode(nodeName) for nodeName in nodesExpr]
        return [self.findNode(nodesExpr)]

    def edge(self, dstAttributeName):
        return self._edges.get(dstAttributeName)

    def getLeafNodes(self, dependenciesOnly):
        nodesWithOutputLink = set([edge.src.node for edge in self.getEdges(dependenciesOnly)])
        return set(self._nodes) - nodesWithOutputLink

    def getRootNodes(self, dependenciesOnly):
        nodesWithInputLink = set([edge.dst.node for edge in self.getEdges(dependenciesOnly)])
        return set(self._nodes) - nodesWithInputLink

    @changeTopology
    def addEdge(self, srcAttr, dstAttr):
        assert isinstance(srcAttr, Attribute)
        assert isinstance(dstAttr, Attribute)
        if srcAttr.node.graph != self or dstAttr.node.graph != self:
            raise RuntimeError('The attributes of the edge should be part of a common graph.')
        if dstAttr in self.edges.keys():
            raise RuntimeError('Destination attribute "{}" is already connected.'.format(dstAttr.getFullNameToNode()))
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
            raise RuntimeError('Attribute "{}" is not connected'.format(dstAttr.getFullNameToNode()))
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
        return set([edge for edge in self.getEdges(dependenciesOnly=dependenciesOnly) if edge.dst.node is node])

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
        edgesScore = defaultdict(lambda: 0)
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
            return set([edge.src.node for edge in self.getEdges(dependenciesOnly) if edge.dst.node is node])

        inputNodes, edges = self.dfsOnDiscover(startNodes=[node], filterTypes=None, reverse=False)
        return inputNodes[1:]  # exclude current node

    def getOutputNodes(self, node, recursive, dependenciesOnly):
        """ Return either the first level output nodes of a node or the whole chain. """
        if not recursive:
            return set([edge.dst.node for edge in self.getEdges(dependenciesOnly) if edge.src.node is node])

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
                super(SCVisitor, self).__init__(reverse, dependenciesOnly)

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
            raise ValueError("filepath must be specified for unsaved files.")

        self.header[Graph.IO.Keys.ReleaseVersion] = meshroom.__version__
        self.header[Graph.IO.Keys.FileVersion] = Graph.IO.__version__

        # Store versions of node types present in the graph (excluding CompatibilityNode instances)
        # and remove duplicates
        usedNodeTypes = set([n.nodeDesc.__class__ for n in self._nodes if isinstance(n, Node)])
        # Convert to node types to "name: version"
        nodesVersions = {
            "{}".format(p.__name__): meshroom.core.nodeVersion(p, "0.0")
            for p in usedNodeTypes
        }
        # Sort them by name (to avoid random order changing from one save to another)
        nodesVersions = dict(sorted(nodesVersions.items()))
        # Add it the header
        self.header[Graph.IO.Keys.NodesVersions] = nodesVersions
        self.header["template"] = template

        data = {}
        if template:
            data = {
                Graph.IO.Keys.Header: self.header,
                Graph.IO.Keys.Graph: self.getNonDefaultInputAttributes()
            }
        else:
            data = {
                Graph.IO.Keys.Header: self.header,
                Graph.IO.Keys.Graph: self.toDict()
            }

        with open(path, 'w') as jsonFile:
            json.dump(data, jsonFile, indent=4)

        if path != self._filepath and setupProjectFile:
            self._setFilepath(path)

        # update the file date version
        self._fileDateVersion = os.path.getmtime(path)

    def getNonDefaultInputAttributes(self):
        """
        Instead of getting all the inputs and internal attribute keys, only get the keys of
        the attributes whose value is not the default one.
        The output attributes, UIDs, parallelization parameters and internal folder are
        not relevant for templates, so they are explicitly removed from the returned dictionary.

        Returns:
            dict: self.toDict() with the output attributes, UIDs, parallelization parameters, internal folder
            and input/internal attributes with default values removed
        """
        graph = self.toDict()
        for nodeName in graph.keys():
            node = self.node(nodeName)

            inputKeys = list(graph[nodeName]["inputs"].keys())

            internalInputKeys = []
            internalInputs = graph[nodeName].get("internalInputs", None)
            if internalInputs:
                internalInputKeys = list(internalInputs.keys())

            for attrName in inputKeys:
                attribute = node.attribute(attrName)
                # check that attribute is not a link for choice attributes
                if attribute.isDefault and not attribute.isLink:
                    del graph[nodeName]["inputs"][attrName]

            for attrName in internalInputKeys:
                attribute = node.internalAttribute(attrName)
                # check that internal attribute is not a link for choice attributes
                if attribute.isDefault and not attribute.isLink:
                    del graph[nodeName]["internalInputs"][attrName]

            # If all the internal attributes are set to their default values, remove the entry
            if len(graph[nodeName]["internalInputs"]) == 0:
                del graph[nodeName]["internalInputs"]

            del graph[nodeName]["outputs"]
            del graph[nodeName]["uid"]
            del graph[nodeName]["internalFolder"]
            del graph[nodeName]["parallelization"]

        return graph

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
        self.cacheDir = meshroom.core.defaultCacheFolder
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
    def importedNodes(self):
        """" Return the list of nodes that were added to the graph with the latest 'Import Project' action. """
        return self._importedNodes

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
    fileReleaseVersion = Property(str, lambda self: self.header.get(Graph.IO.Keys.ReleaseVersion, "0.0"),
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
            chunksStatus = set([chunk.status.status.name for chunk in chunksInConflict])
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
                    print('\n[{node}/{nbNodes}] {nodeName}'.format(
                        node=n + 1, nbNodes=len(nodes), nodeName=node.nodeType))
                chunk.process(forceCompute)
            node.postprocess()
        except Exception as e:
            logging.error("Error on node computation: {}".format(e))
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

    logging.info("Nodes to process: {}".format(edgesToProcess))
    logging.info("Edges to process: {}".format(edgesToProcess))

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
        logging.error("Error on submit : {}".format(e))


def submit(graphFile, submitter, toNode=None, submitLabel="{projectName}"):
    """
    Submit the given graph via the given submitter.
    """
    graph = loadGraph(graphFile)
    toNodes = graph.findNodes(toNode) if toNode else None
    submitGraph(graph, submitter, toNodes, submitLabel=submitLabel)
