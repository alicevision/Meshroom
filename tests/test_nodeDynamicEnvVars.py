# coding:utf-8

from inspect import getfile
import os
from pathlib import Path
import pytest
from tempfile import gettempdir

from meshroom.core.exception import GraphCompatibilityError
from meshroom.core.graph import Graph, loadGraph
from meshroom.core import desc, loadAllNodes, registerNodeType, unregisterNodeType
from meshroom.core.node import Node
import meshroom.core


class RelativePaths(desc.Node):
    """
    Local "RelativePaths" node, with a different source code folder as the one in nodes/test.
    """
    documentation = "Test node with filepaths that are set relatively to some variables."
    inputs = [
        desc.File(
            name="relativePathInput",
            label="Relative Input File",
            description="Relative path to the input file.",
            value="${NODE_SOURCECODE_FOLDER}" + "/input.txt",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Path to the output file.",
            value="${NODE_CACHE_FOLDER}" + "file.out",
        ),
    ]

    def processChunk(self, chunk):
        pass


class RelativePathsV2(desc.Node):
    """
    Local "RelativePaths" node, with a different source code folder as the one in nodes/test.
    """
    documentation = "Test node with filepaths that are set relatively to some variables."
    inputs = [
        desc.File(
            name="relativePathInput2",
            label="Relative Input File",
            description="Relative path to the input file.",
            value="${NODE_SOURCECODE_FOLDER}" + "/input.txt",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Path to the output file.",
            value="${NODE_CACHE_FOLDER}" + "file.out",
        ),
    ]

    def processChunk(self, chunk):
        pass


class FakeRelativePaths(desc.Node):
    documentation = """
    Test node with filepaths that are set relatively to some variables that do not exist.
    """
    inputs = [
        desc.File(
            name="relativePathInput",
            label="Relative Input File",
            description="Relative path to the input file.",
            value="${NODE_UNEXISTING_FOLDER}" + "/input.txt",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="Path to the output file.",
            value="${NODE_RANDOM_FOLDER}" + "file.out",
        )
    ]

    def processChunk(self, chunk):
        pass


def test_registerSameNodeWithDifferentLocations():
    """
    Check that the nodes with the same description but registered at different locations
    have different evaluations for the NODE_SOURCECODE_FOLDER value.
    """
    loadAllNodes(os.path.join(os.path.dirname(__file__), "nodes"))
    assert "RelativePaths" in meshroom.core.nodesDesc

    # Node loaded from "nodes/test"
    n1 = Node("RelativePaths")
    sourceFolderNode1 = n1.attribute("relativePathInput").getEvalValue()
    assert sourceFolderNode1 == \
        Path(getfile(meshroom.core.nodesDesc["RelativePaths"])).parent.resolve().as_posix() + \
        "/input.txt"
    assert sourceFolderNode1 == n1.sourceCodeFolder + "/input.txt"
    assert Path(sourceFolderNode1).parent.resolve().as_posix() == \
        n1.dynamicEnvVars["NODE_SOURCECODE_FOLDER"]

    # Unregister that node and replace it with the one from this file
    unregisterNodeType(RelativePaths)
    assert "RelativePaths" not in meshroom.core.nodesDesc

    registerNodeType(RelativePaths)
    assert "RelativePaths" in meshroom.core.nodesDesc

    n2 = Node("RelativePaths")
    sourceFolderNode2 = n2.attribute("relativePathInput").getEvalValue()
    assert sourceFolderNode2 == \
        Path(getfile(meshroom.core.nodesDesc["RelativePaths"])).parent.resolve().as_posix() + \
        "/input.txt"
    assert sourceFolderNode2 == n2.sourceCodeFolder + "/input.txt"
    assert Path(sourceFolderNode2).parent.resolve().as_posix() == \
        n2.dynamicEnvVars["NODE_SOURCECODE_FOLDER"]

    assert sourceFolderNode1 is not sourceFolderNode2
    unregisterNodeType(RelativePaths)


def test_reloadGraphWithDifferentNodeLocations(graphSavedOnDisk):
    """
    Save a Graph with a node description registered at a specific location, unregister that node
    type, and register the same description from a different location.
    """
    loadAllNodes(os.path.join(os.path.dirname(__file__), "nodes"))
    assert "RelativePaths" in meshroom.core.nodesDesc

    graph: Graph = graphSavedOnDisk
    node = graph.addNewNode("RelativePaths")
    name = node.name
    filename = graph.filepath

    # Save graph in a file
    graph.save()

    sourceCodeFolderNode = node.attribute("relativePathInput").getEvalValue()
    assert sourceCodeFolderNode == node.dynamicEnvVars["NODE_SOURCECODE_FOLDER"] + "/input.txt"

    # Output attribute, already evaluated upon the node's creation
    cacheFolderNode = node.attribute("output").value

    node._buildCmdVars()
    assert desc.Node.internalFolder == node.dynamicEnvVars["NODE_CACHE_FOLDER"]
    assert cacheFolderNode == desc.Node.internalFolder.format(**node._cmdVars) + "file.out"

    # Delete the current graph
    del graph

    # Unregister that node and replace it with the one from this file
    unregisterNodeType(meshroom.core.nodesDesc["RelativePaths"])
    assert "RelativePaths" not in meshroom.core.nodesDesc

    registerNodeType(RelativePaths)
    assert "RelativePaths" in meshroom.core.nodesDesc

    # Reload the graph
    graph = loadGraph(filename)
    assert graph
    node = graph.node(name)
    assert node.nodeType == "RelativePaths"

    # Check that the relative path is different for the input
    assert node.attribute("relativePathInput").getEvalValue() != sourceCodeFolderNode

    # Check that it is the same for the cache
    assert node.attribute("output").value == cacheFolderNode

    os.remove(filename)
    unregisterNodeType(RelativePaths)


def test_reloadGraphWithCompatibilityIssue(graphSavedOnDisk):
    registerNodeType(RelativePaths)

    graph: Graph = graphSavedOnDisk
    node = graph.addNewNode(RelativePaths.__name__)
    graph.save()

    # Replace saved node description by V2
    meshroom.core.nodesDesc[RelativePaths.__name__] = RelativePathsV2

    # Check that the compatibility issue is raised
    with pytest.raises(GraphCompatibilityError):
        loadGraph(graph.filepath, strictCompatibility=True)

    compatibilityGraph = loadGraph(graph.filepath)
    compatibilityNode = compatibilityGraph.node(node.name)
    assert compatibilityNode.isCompatibilityNode

    # Check that the dynamicEnvVars content for CompatibilityNodes checks out:
    # dynamicEnvVars for CompatibilityNodes only contains a set "NODE_CACHE_FOLDER" and
    # a "NODE_SOURCECODE_FOLDER" that is set to "UndefinedPath"
    assert len(compatibilityNode.dynamicEnvVars) == len(node.dynamicEnvVars)
    assert "NODE_CACHE_FOLDER" in compatibilityNode.dynamicEnvVars
    assert "NODE_SOURCECODE_FOLDER" in compatibilityNode.dynamicEnvVars
    assert compatibilityNode.dynamicEnvVars["NODE_SOURCECODE_FOLDER"] == "UndefinedPath"

    # Input values should be the same, but the evaluation should differ as dynamicEnvVars
    # for CompatibilityNodes do not include the same value for "NODE_SOURCECODE_FOLDER"
    assert compatibilityNode.attribute("relativePathInput").value == \
        node.attribute("relativePathInput").value
    assert compatibilityNode.attribute("relativePathInput").getEvalValue() != \
        node.attribute("relativePathInput").getEvalValue()

    # Output values are evaluated straight away: they should be the same since "NODE_CACHE_FOLDER"
    # is always available
    assert compatibilityNode.attribute("output").value == \
        compatibilityNode.attribute("output").getEvalValue() == \
        node.attribute("output").value

    unregisterNodeType(RelativePaths)


class TestDynamicEnvVarsContent():
    """ Class to test changes on the dynamic environment variables' values. """
    @classmethod
    def setup_class(cls):
        """ Register nodes upon class' creation. """
        registerNodeType(RelativePaths)
        registerNodeType(FakeRelativePaths)

    @classmethod
    def teardown_class(cls):
        """ Unregister nodes upon class' destruction. """
        unregisterNodeType(RelativePaths)
        unregisterNodeType(FakeRelativePaths)

    def test_updateDynamicEnvVars(self):
        """
        Check that dynamic environment variables can be added and removed.
        """
        assert "RelativePaths" in meshroom.core.nodesDesc

        node = Node("RelativePaths")
        assert len(node.dynamicEnvVars) == 2

        # Add a new element in the list of dynamic environment variables
        node.dynamicEnvVars.update({"NODE_TEST_FOLDER": gettempdir()})
        assert len(node.dynamicEnvVars) == 3

        attr = node.attribute("relativePathInput")

        sourceCodeFolder = attr.getEvalValue()
        attr.value = "${NODE_TEST_FOLDER}" + "/input.txt"
        assert attr.getEvalValue() == gettempdir() + "/input.txt"
        assert attr.getEvalValue() != sourceCodeFolder

        # Remove the extra element in the list of dynamic environment variables
        node.dynamicEnvVars.pop("NODE_TEST_FOLDER", None)
        assert len(node.dynamicEnvVars) == 2

        assert attr.getEvalValue() != gettempdir() + "/input.txt"
        # Unevaluated value as the variable does not exist
        assert attr.getEvalValue() == attr.value

        attr.value = attr.defaultValue()
        assert attr.getEvalValue() == sourceCodeFolder


    def test_nonExistingDynamicEnvVars(self):
        """
        Check that a variable that does not correspond to any dynamic environment variable
        is not evaluated.
        """
        node = Node("FakeRelativePaths")

        # The dynamic environment variable cannot be evaluated as it does not exist: it is not substituted
        assert node.attribute("relativePathInput").getEvalValue() == \
            node.attribute("relativePathInput").value
        assert node.attribute("output").getEvalValue() == \
            node.attribute("output").value == "${NODE_RANDOM_FOLDER}file.out"
