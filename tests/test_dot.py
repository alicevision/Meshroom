# coding:utf-8

"""
Tests for the Dot node: a purely organizational pass-through node with a single
input and a single output, performing no computation. It is used to re-route and
tidy connections in the graph editor.
"""

import json
import os

import pytest

import meshroom.core
from meshroom.core import desc, pluginManager
from meshroom.core.exception import InvalidEdgeError
from meshroom.core.graph import Graph, loadGraph, executeGraph
from meshroom.core.node import Status

from .utils import registerNodeDesc, unregisterNodeDesc


class DotIntSource(desc.CommandLineNode):
    """ Test node with an IntParam output. """
    __test__ = False
    commandLine = "echo {valueValue}"
    inputs = [desc.IntParam(name="value", label="Value", description="", value=0)]
    outputs = [desc.IntParam(name="out", label="Out", description="", value=0)]


class DotIntSink(desc.CommandLineNode):
    """ Test node with an IntParam input. """
    __test__ = False
    commandLine = "echo {valueValue}"
    inputs = [desc.IntParam(name="value", label="Value", description="", value=0)]
    outputs = [desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out.txt")]


class DotStrSource(desc.CommandLineNode):
    """ Test node with a StringParam output. """
    __test__ = False
    commandLine = "echo {valueValue}"
    inputs = [desc.StringParam(name="value", label="Value", description="", value="")]
    outputs = [desc.StringParam(name="out", label="Out", description="", value="")]


class DotStrSink(desc.CommandLineNode):
    """ Test node with a StringParam input. """
    __test__ = False
    commandLine = "echo {valueValue}"
    inputs = [desc.StringParam(name="value", label="Value", description="", value="")]
    outputs = [desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out.txt")]


class DotListSource(desc.CommandLineNode):
    """ Test node with a ListAttribute output. """
    __test__ = False
    commandLine = "echo {filesValue}"
    inputs = [desc.File(name="input", label="Input", description="", value="")]
    outputs = [
        desc.ListAttribute(
            name="files", label="Files", description="",
            elementDesc=desc.File(name="file", label="File", description=""),
        )
    ]


class DotListSink(desc.CommandLineNode):
    """ Test node with a ListAttribute input. """
    __test__ = False
    commandLine = "cat {filesValue}"
    inputs = [
        desc.ListAttribute(
            name="files", label="Files", description="",
            elementDesc=desc.File(name="file", label="File", description=""),
        )
    ]
    outputs = [desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out.txt")]


class DotWriteFile(desc.BaseNode):
    """ Test node writing its input value and marker to its output file (in-process, no shell needed). """
    __test__ = False
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
        desc.StringParam(name="marker", label="Marker", description="", value=""),
    ]
    outputs = [desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out.txt")]

    def processChunk(self, chunk):
        with open(chunk.node.output.value, "w") as f:
            f.write(f"{chunk.node.input.value}|{chunk.node.marker.value}")


TEST_NODE_DESCS = [DotIntSource, DotIntSink, DotStrSource, DotStrSink, DotListSource, DotListSink, DotWriteFile]


class TestDotNode:
    """ Tests for the Dot node (organizational pass-through node). """

    loadedPlugins = pluginManager.getPlugins()

    @classmethod
    def setup_class(cls):
        meshroom.core.initNodes()
        for nodeDesc in TEST_NODE_DESCS:
            registerNodeDesc(nodeDesc)

    @classmethod
    def teardown_class(cls):
        for nodeDesc in TEST_NODE_DESCS:
            unregisterNodeDesc(nodeDesc)
        for plugin in pluginManager.getPlugins():
            if plugin not in cls.loadedPlugins:
                pluginManager.removePlugin(plugin)

    def test_dotNodeCreation(self):
        """ A Dot can be created from the node types and is registered in the 'Utils' category. """
        assert pluginManager.isNodeDescRegistered("Dot")
        assert pluginManager.getNodeDescProviders()["Dot"].nodeDescClass.category == "Utils"

        graph = Graph("Dot creation")
        dot = graph.addNewNode("Dot")

        assert dot.isDotNode
        assert not dot.isBackdropNode
        assert not dot.isInitNode
        assert not dot.isComputableType
        assert dot.hasAttribute("input")
        assert dot.hasAttribute("output")
        assert dot.attribute("input").isInput
        assert dot.attribute("output").isOutput

    def test_dotHasNoComputation(self):
        """ A Dot never creates chunks, a cache folder or a status file. """
        graph = Graph("Dot computation")
        ls = graph.addNewNode("Ls", input="/tmp")
        dot = graph.addNewNode("Dot")
        append = graph.addNewNode("AppendText", inputText="hello")
        ls.output.connectTo(dot.input)
        dot.output.connectTo(append.input)
        graph.update()

        # The Dot is skipped by the chunk/status pipeline
        assert dot._chunksCreated
        assert len(dot.chunks) == 0
        assert dot.getGlobalStatus() == Status.NONE
        # No cache folder or status file is created for the Dot
        assert not os.path.exists(dot.internalFolder)
        assert not os.path.exists(dot.nodeStatusFile)
        assert not os.path.exists(os.path.join(graph.cacheDir, "Dot"))

    def test_filePassThrough(self):
        """ A File attribute passes through the Dot unchanged, down to the downstream command line. """
        graph = Graph("Dot pass-through")
        ls = graph.addNewNode("Ls", input="/tmp")
        dot = graph.addNewNode("Dot")
        append = graph.addNewNode("AppendText", inputText="hello")
        ls.output.connectTo(dot.input)
        dot.output.connectTo(append.input)
        graph.update()

        # The Dot output takes the type of the connected upstream attribute
        assert dot.output.type == "File"
        assert dot.output.baseType == "File"
        # The value read downstream through the Dot is the real upstream value
        assert dot.output.value == ls.output.value
        assert append.input.value == ls.output.value
        assert "Dot" not in append.input.value
        # The downstream command line receives the actual upstream file path
        commandLine = append.nodeDesc.buildCommandLine(append.chunks[0])
        assert ls.output.value in commandLine

    def test_dynamicTypesFollowConnection(self):
        """ The Dot output type adapts to the connected upstream attribute (int, string, File, ListAttribute). """
        graph = Graph("Dot types")
        intSource = graph.addNewNode("DotIntSource", value=42)
        strSource = graph.addNewNode("DotStrSource", value="hello")
        ls = graph.addNewNode("Ls", input="/tmp")
        listSource = graph.addNewNode("DotListSource", input="/tmp")
        dotInt = graph.addNewNode("Dot")
        dotStr = graph.addNewNode("Dot")
        dotFile = graph.addNewNode("Dot")
        dotList = graph.addNewNode("Dot")
        intSink = graph.addNewNode("DotIntSink")
        strSink = graph.addNewNode("DotStrSink")
        listSink = graph.addNewNode("DotListSink")

        intSource.out.connectTo(dotInt.input)
        dotInt.output.connectTo(intSink.value)
        strSource.out.connectTo(dotStr.input)
        dotStr.output.connectTo(strSink.value)
        ls.output.connectTo(dotFile.input)
        listSource.files.connectTo(dotList.input)
        dotList.output.connectTo(listSink.files)
        graph.update()

        assert dotInt.output.type == "IntParam"
        assert dotInt.output.baseType == "IntParam"
        assert dotInt.output.value == intSource.out.value
        assert intSink.value.value == intSource.out.value

        assert dotStr.output.type == "StringParam"
        assert dotStr.output.baseType == "StringParam"
        assert dotStr.output.value == strSource.out.value
        assert strSink.value.value == strSource.out.value

        assert dotFile.output.type == "File"
        assert dotFile.output.value == ls.output.value

        assert dotList.output.type == "ListAttribute"
        assert dotList.output.baseType == "File"
        assert list(dotList.output.value) == list(listSource.files.value)
        assert list(listSink.files.value) == list(listSource.files.value)

    def test_disconnectResetsType(self):
        """ Disconnecting the Dot input resets the Dot output to its generic unconnected state. """
        graph = Graph("Dot disconnect")
        ls = graph.addNewNode("Ls", input="/tmp")
        dot = graph.addNewNode("Dot")
        ls.output.connectTo(dot.input)
        graph.update()
        assert dot.output.type == "File"

        dot.input.disconnectEdge()
        graph.update()
        assert dot.output.type == "DotAttribute"
        assert dot.output.baseType == "DotAttribute"

        # Reconnecting updates the type again
        ls.output.connectTo(dot.input)
        graph.update()
        assert dot.output.type == "File"

    def test_dotInputAcceptsAnyType(self):
        """ The Dot input accepts connections of any attribute type. """
        graph = Graph("Dot accepts any type")
        ls = graph.addNewNode("Ls", input="/tmp")
        intSource = graph.addNewNode("DotIntSource", value=42)
        strSource = graph.addNewNode("DotStrSource", value="hello")
        listSource = graph.addNewNode("DotListSource", input="/tmp")
        dot = graph.addNewNode("Dot")

        assert dot.input.validateIncomingConnection(ls.output)
        assert dot.input.validateIncomingConnection(intSource.out)
        assert dot.input.validateIncomingConnection(strSource.out)
        assert dot.input.validateIncomingConnection(listSource.files)

    def test_incompatibleConnectionRejected(self):
        """ Incompatible connections are rejected, with the same behavior as normal nodes. """
        graph = Graph("Dot incompatible")
        ls = graph.addNewNode("Ls", input="/tmp")
        dot = graph.addNewNode("Dot")
        intSink = graph.addNewNode("DotIntSink")
        strSink = graph.addNewNode("DotStrSink")
        intSource = graph.addNewNode("DotIntSource", value=42)
        strSource = graph.addNewNode("DotStrSource", value="hello")
        ls.output.connectTo(dot.input)

        # A File output cannot feed an IntParam input, even through a Dot
        with pytest.raises(InvalidEdgeError):
            dot.output.connectTo(intSink.value)

        # An IntParam output cannot feed a StringParam input, even through a Dot
        intSource.out.connectTo(dot.input)
        graph.update()
        with pytest.raises(InvalidEdgeError):
            dot.output.connectTo(strSink.value)

        # Compatible connections still work
        intSource.out.connectTo(intSink.value)
        strSource.out.connectTo(strSink.value)
        graph.update()
        assert intSink.value.value == intSource.out.value
        assert strSink.value.value == strSource.out.value

    def test_chainedDots(self):
        """ Chained Dots (A -> Dot -> Dot -> B) behave like a direct connection. """
        graph = Graph("Dot chained")
        ls = graph.addNewNode("Ls", input="/tmp")
        dot1 = graph.addNewNode("Dot")
        dot2 = graph.addNewNode("Dot")
        append = graph.addNewNode("AppendText", inputText="x")
        ls.output.connectTo(dot1.input)
        dot1.output.connectTo(dot2.input)
        dot2.output.connectTo(append.input)
        graph.update()

        assert dot2.output.type == "File"
        assert append.input.value == ls.output.value

        # The downstream UID is identical to the one of a direct connection
        directGraph = Graph("Direct")
        lsDirect = directGraph.addNewNode("Ls", input="/tmp")
        appendDirect = directGraph.addNewNode("AppendText", inputText="x")
        lsDirect.output.connectTo(appendDirect.input)
        directGraph.update()
        assert append.input.uid() == appendDirect.input.uid()

    def test_fanOut(self):
        """ A single Dot output can feed multiple downstream attributes. """
        graph = Graph("Dot fan-out")
        ls = graph.addNewNode("Ls", input="/tmp")
        dot = graph.addNewNode("Dot")
        appendB = graph.addNewNode("AppendText", inputText="x")
        appendC = graph.addNewNode("AppendText", inputText="y")
        ls.output.connectTo(dot.input)
        dot.output.connectTo(appendB.input)
        dot.output.connectTo(appendC.input)
        graph.update()

        assert appendB.input.value == ls.output.value
        assert appendC.input.value == ls.output.value
        assert len(dot.output.outputLinks) == 2

    def test_uidTransparencyAndInvalidation(self):
        """ Downstream UIDs are identical with and without a Dot, and upstream changes invalidate through the Dot. """
        graph = Graph("Dot uid")
        ls = graph.addNewNode("Ls", input="/tmp")
        dot = graph.addNewNode("Dot")
        append = graph.addNewNode("AppendText", inputText="hello")
        ls.output.connectTo(dot.input)
        dot.output.connectTo(append.input)
        graph.update()

        directGraph = Graph("Direct uid")
        lsDirect = directGraph.addNewNode("Ls", input="/tmp")
        appendDirect = directGraph.addNewNode("AppendText", inputText="hello")
        lsDirect.output.connectTo(appendDirect.input)
        directGraph.update()

        assert append.input.uid() == appendDirect.input.uid()

        # Changing the upstream input invalidates the downstream node through the Dot
        uidBefore = append.input.uid()
        ls.attribute("input").value = "/usr"
        assert append.input.uid() != uidBefore

    def test_dependenciesAndComputeOrder(self):
        """ Graph traversal and computation order are correct with a Dot in the graph. """
        graph = Graph("Dot order")
        ls = graph.addNewNode("Ls", input="/tmp")
        dot = graph.addNewNode("Dot")
        append = graph.addNewNode("AppendText", inputText="hello")
        ls.output.connectTo(dot.input)
        dot.output.connectTo(append.input)
        graph.update()

        nodes, _ = graph.dfsToProcess(startNodes=[append])
        names = [n.name for n in nodes]
        assert names.index(ls.name) < names.index(dot.name) < names.index(append.name)

        # Upstream/downstream traversal goes through the Dot
        assert ls in append.getInputNodes(recursive=True, dependenciesOnly=True)
        assert dot in append.getInputNodes(recursive=True, dependenciesOnly=True)
        assert append in ls.getOutputNodes(recursive=True, dependenciesOnly=True)
        assert dot in ls.getOutputNodes(recursive=True, dependenciesOnly=True)

        # The full computation order is the same as without the Dot, with the Dot inserted in sequence
        directGraph = Graph("Direct order")
        lsDirect = directGraph.addNewNode("Ls", input="/tmp")
        appendDirect = directGraph.addNewNode("AppendText", inputText="hello")
        lsDirect.output.connectTo(appendDirect.input)
        directGraph.update()
        assert [n.nodeType for n in nodes] == ["Ls", "Dot", "AppendText"]
        assert [n.nodeType for n in directGraph.dfsToProcess()[0]] == ["Ls", "AppendText"]

    def test_removingDotKeepsNeighbours(self):
        """ Removing a Dot does not remove its neighbours. """
        graph = Graph("Dot removal")
        ls = graph.addNewNode("Ls", input="/tmp")
        dot = graph.addNewNode("Dot")
        append = graph.addNewNode("AppendText", inputText="hello")
        ls.output.connectTo(dot.input)
        dot.output.connectTo(append.input)
        graph.update()

        graph.removeNode(dot.name)
        graph.update()

        assert graph.node(ls.name) is not None
        assert graph.node(append.name) is not None
        assert graph.node(dot.name) is None
        assert len(graph.edges) == 0

    def test_saveLoadRoundtrip(self, tmp_path):
        """ Dot nodes are saved and loaded in .mg files without any compatibility issue. """
        graph = Graph("Dot save/load")
        ls = graph.addNewNode("Ls", input="/tmp")
        dot = graph.addNewNode("Dot")
        append = graph.addNewNode("AppendText", inputText="hello")
        ls.output.connectTo(dot.input)
        dot.output.connectTo(append.input)
        graph.update()

        filepath = os.path.join(str(tmp_path), "dotGraph.mg")
        graph.save(filepath)

        # The Dot is serialized as a regular node, with its input as a link expression
        with open(filepath) as f:
            data = json.load(f)
        dotData = data["graph"][dot.name]
        assert dotData["nodeType"] == "Dot"
        assert dotData["inputs"]["input"] == f"{{{ls.name}.output}}"

        loadedGraph = loadGraph(filepath)
        loadedDot = loadedGraph.node(dot.name)
        assert loadedDot is not None
        assert loadedDot.isDotNode
        assert not loadedDot.isCompatibilityNode
        assert all(not node.isCompatibilityNode for node in loadedGraph.nodes)

        # Edges are restored and the value passes through the loaded Dot
        loadedLs = loadedGraph.node(ls.name)
        loadedAppend = loadedGraph.node(append.name)
        assert loadedDot.attribute("input").isLink
        assert loadedDot.attribute("input").inputLink is loadedLs.attribute("output")
        assert loadedAppend.attribute("input").isLink
        assert loadedAppend.attribute("input").inputLink is loadedDot.attribute("output")
        assert loadedAppend.attribute("input").value == loadedLs.attribute("output").value
        assert loadedDot.attribute("output").type == "File"

    def test_copyPaste(self):
        """ Copy/paste of a sub-graph containing a Dot preserves the links. """
        graph = Graph("Dot copy/paste")
        ls = graph.addNewNode("Ls", input="/tmp")
        dot = graph.addNewNode("Dot")
        append = graph.addNewNode("AppendText", inputText="hello")
        ls.output.connectTo(dot.input)
        dot.output.connectTo(append.input)
        graph.update()

        data = graph.serializePartial([ls, dot, append])
        pastedGraph = Graph("Dot pasted")
        pastedGraph._deserialize(data)
        pastedDots = [node for node in pastedGraph.nodes if node.isDotNode]
        assert len(pastedDots) == 1
        pastedDot = pastedDots[0]
        assert pastedDot.attribute("input").isLink
        assert pastedDot.attribute("output").value == pastedDot.attribute("input").value
        assert pastedDot.attribute("output").type == "File"

    def test_duplicate(self):
        """ Duplicating a Dot keeps its input link and its value passes through. """
        graph = Graph("Dot duplicate")
        ls = graph.addNewNode("Ls", input="/tmp")
        dot = graph.addNewNode("Dot")
        append = graph.addNewNode("AppendText", inputText="hello")
        ls.output.connectTo(dot.input)
        dot.output.connectTo(append.input)
        graph.update()

        duplicates = graph.duplicateNodes([dot])
        assert len(duplicates) == 1
        duplicatedDot = list(duplicates.values())[0][0]
        assert duplicatedDot.isDotNode
        assert duplicatedDot is not dot
        # The duplicate keeps the link to the original upstream attribute
        assert duplicatedDot.attribute("input").isLink
        assert duplicatedDot.attribute("input").inputLink is ls.attribute("output")
        assert duplicatedDot.attribute("output").value == ls.output.value
        # The original Dot keeps its output edges
        assert dot.attribute("output").hasAnyOutputLinks
        assert not duplicatedDot.attribute("output").hasAnyOutputLinks

    def test_executeGraphThroughDot(self, tmp_path):
        """ Computing a downstream node computes the upstream nodes through the Dot, with the result
        identical to a graph without Dot, and the Dot is never computed. """
        # Graph with a Dot: WriteFile -> Dot -> WriteFile
        graphWithDot = Graph("Dot execute")
        withDotFolder = tmp_path / "withDot"
        withDotFolder.mkdir()
        graphWithDot.saveAsTemp(str(withDotFolder))
        nodeA = graphWithDot.addNewNode("DotWriteFile", marker="first")
        dot = graphWithDot.addNewNode("Dot")
        nodeB = graphWithDot.addNewNode("DotWriteFile", marker="second")
        nodeA.output.connectTo(dot.input)
        dot.output.connectTo(nodeB.input)

        executeGraph(graphWithDot, toNodes=[nodeB])

        assert nodeA.hasStatus(Status.SUCCESS)
        assert nodeB.hasStatus(Status.SUCCESS)
        # The Dot is never computed: no chunk, no cache folder, no status file
        assert len(dot.chunks) == 0
        assert not os.path.exists(dot.internalFolder)
        assert not os.path.exists(dot.nodeStatusFile)
        assert not os.path.exists(os.path.join(graphWithDot.cacheDir, "Dot"))
        # Real nodes do create their cache folder
        assert os.path.exists(os.path.join(graphWithDot.cacheDir, "DotWriteFile"))
        # The downstream node received the real upstream output path and chained the values
        assert nodeB.attribute("input").value == nodeA.attribute("output").value
        with open(nodeB.attribute("output").value) as f:
            assert f.read() == f"{nodeA.attribute('output').value}|second"

        # Graph without Dot: WriteFile -> WriteFile
        graphDirect = Graph("Direct execute")
        directFolder = tmp_path / "direct"
        directFolder.mkdir()
        graphDirect.saveAsTemp(str(directFolder))
        nodeA2 = graphDirect.addNewNode("DotWriteFile", marker="first")
        nodeB2 = graphDirect.addNewNode("DotWriteFile", marker="second")
        nodeA2.output.connectTo(nodeB2.input)

        executeGraph(graphDirect, toNodes=[nodeB2])

        assert nodeA2.hasStatus(Status.SUCCESS)
        assert nodeB2.hasStatus(Status.SUCCESS)
        assert nodeB2.attribute("input").value == nodeA2.attribute("output").value
        with open(nodeB2.attribute("output").value) as f:
            assert f.read() == f"{nodeA2.attribute('output').value}|second"

    def test_existingGraphFileUnaffected(self):
        """ Loading an existing .mg file (without any Dot) is unaffected by the change. """
        filepath = os.path.join(os.path.dirname(os.path.realpath(__file__)), "appendTextAndFiles.mg")
        graph = loadGraph(filepath)

        # All nodes load without compatibility issue
        assert all(not node.isCompatibilityNode for node in graph.nodes)
        assert sorted(node.name for node in graph.nodes) == ["AppendFiles_1", "AppendText_1", "AppendText_2"]

        # Links and values resolve as before
        appendText1 = graph.node("AppendText_1")
        appendText2 = graph.node("AppendText_2")
        appendFiles = graph.node("AppendFiles_1")
        assert appendFiles.attribute("input").value == appendText1.attribute("output").value
        assert appendFiles.attribute("input2").value == appendText2.attribute("output").value
        assert appendFiles.attribute("input3").value == appendText1.attribute("input").value
        assert appendFiles.attribute("input4").value == appendText2.attribute("input").value
