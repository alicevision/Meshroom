#!/usr/bin/env python
# coding:utf-8

import os
import shutil
import json
from pathlib import Path
import tempfile

from meshroom.core import desc, pluginManager, loadClassesNodes, initNodes
from meshroom.core.node import Position
from meshroom.core.graph import Graph, loadGraph
from meshroom.core.plugins import Plugin

from .utils import registerNodeDesc, unregisterNodeDesc, registeredNodeTypes


TEST_RESOURCES = Path(__file__).parent / "resources"


class TestNodeInfo:
    plugin = None

    @classmethod
    def setup_class(cls):
        cls.folder = os.path.join(os.path.dirname(__file__), "plugins", "meshroom")
        package = "pluginC"
        cls.plugin = Plugin(package, cls.folder)
        nodes = loadClassesNodes(cls.folder, package)
        for node in nodes:
            cls.plugin.addNodePlugin(node)
        pluginManager.addPlugin(cls.plugin)

    @classmethod
    def teardown_class(cls):
        for node in cls.plugin.nodes.values():
            pluginManager.unregisterNode(node)
        pluginManager.removePlugin(cls.plugin)
        cls.plugin = None

    def test_loadedPlugin(self):
        assert len(pluginManager.getPlugins()) >= 1
        plugin = pluginManager.getPlugin("pluginC")
        assert plugin == self.plugin
        node = plugin.nodes["PluginCNodeA"]
        nodeType = node.nodeDescriptor

        g = Graph("")
        registerNodeDesc(nodeType)
        node = g.addNewNode(nodeType.__name__)

        nodeDocumentation = node.getDocumentation()
        assert nodeDocumentation == "PluginCNodeA"
        nodeInfo = {item["key"]: item["value"] for item in node.getNodeInfo()}
        assert nodeInfo["module"] == "pluginC.PluginCNodeA"
        pluginPath = os.path.join(self.folder, "pluginC", "PluginCNodeA.py")
        assert nodeInfo["modulePath"] == Path(pluginPath).as_posix()  # modulePath seems to follow Linux convention
        assert nodeInfo["author"] == "testAuthor"
        assert nodeInfo["license"] == "no-license"
        assert nodeInfo["version"] == "1.0"
        unregisterNodeDesc(nodeType)


class TestNodeVariables:
    plugin = None

    @classmethod
    def setup_class(cls):
        folder = os.path.join(os.path.dirname(__file__), "plugins", "meshroom")
        package = "pluginA"
        cls.plugin = Plugin(package, folder)
        nodes = loadClassesNodes(folder, package)
        for node in nodes:
            cls.plugin.addNodePlugin(node)
        pluginManager.addPlugin(cls.plugin)

    @classmethod
    def teardown_class(cls):
        for node in cls.plugin.nodes.values():
            pluginManager.unregisterNode(node)
        pluginManager.removePlugin(cls.plugin)
        cls.plugin = None

    def test_staticVariables(self):
        g = Graph("")

        for nodeName in self.plugin.nodes.keys():
            n = g.addNewNode(nodeName)
            assert nodeName == n._staticExpVars["nodeType"]
            assert n.sourceCodeFolder
            assert n.sourceCodeFolder == n._staticExpVars["nodeSourceCodeFolder"]

            self.plugin.nodes[nodeName].reload()

            assert nodeName == n._staticExpVars["nodeType"]
            assert n.sourceCodeFolder
            assert n.sourceCodeFolder == n._staticExpVars["nodeSourceCodeFolder"]

    def test_expVariables(self):
        g = Graph("")

        for nodeName in self.plugin.nodes.keys():
            n = g.addNewNode(nodeName)
            assert n._expVars["uid"] == n._uid
            assert n.internalFolder
            assert n.internalFolder == n._expVars["nodeCacheFolder"]
            assert "node" in n._expVars
            assert n._expVars["node"] is n

            self.plugin.nodes[nodeName].reload()

            assert n._expVars["uid"] == n._uid
            assert n.internalFolder
            assert n.internalFolder == n._expVars["nodeCacheFolder"]
            assert "node" in n._expVars
            assert n._expVars["node"] is n


class TestInitNode:
    plugin = None

    @classmethod
    def setup_class(cls):
        folder = os.path.join(os.path.dirname(__file__), "plugins", "meshroom")
        package = "pluginA"
        cls.plugin = Plugin(package, folder)
        nodes = loadClassesNodes(folder, package)
        for node in nodes:
            cls.plugin.addNodePlugin(node)
        pluginManager.addPlugin(cls.plugin)

    @classmethod
    def teardown_class(cls):
        for node in cls.plugin.nodes.values():
            pluginManager.unregisterNode(node)
        pluginManager.removePlugin(cls.plugin)
        cls.plugin = None

    def test_initNode(self):
        g = Graph("")

        node = g.addNewNode("PluginAInputInitNode")

        # Check that the init node is correctly detected
        initNodes = g.findInitNodes()
        assert len(initNodes) == 1 and node in initNodes

        # Check that the init node's initialize method has been set
        inputs = ["/path/to/file", "/path/to/file/2"]
        node.nodeDesc.initialize(node, inputs, None)
        assert node.input.value == inputs[0]


class TestBackdropNode:
    loadedPlugins = pluginManager.getPlugins()

    @classmethod
    def setup_class(cls):
        initNodes()

    @classmethod
    def teardown_class(cls):
        for plugin in pluginManager.getPlugins():
            if plugin not in cls.loadedPlugins:
                for node in plugin.nodes.values():
                    pluginManager.unregisterNode(node)
                pluginManager.removePlugin(plugin)

    def test_backdropNode(self):
        """ Test that a backdrop node can be added to a graph with its expected default values. """
        g = Graph("Default Backdrop node")
        backdrop = g.addNewNode("Backdrop")

        # Check that the default values for backdrop are as expected
        assert backdrop is not None
        assert backdrop.nodeWidth == 600
        assert backdrop.nodeHeight == 400
        assert backdrop.fontSize == 12
        assert backdrop.fontColor == ""
        assert backdrop.color == ""
        assert backdrop.comment == ""

        # Add a non-backdrop node and check that its default values are not backdrop's ones
        node = g.addNewNode("CopyFiles")
        assert node is not None
        assert node.nodeWidth == 0
        assert node.nodeHeight == 0
        assert node.fontSize == 0
        assert node.fontColor == ""
        assert node.color == ""
        assert node.comment == ""

    def test_backdropNode_customAttributes(self):
        """ Test that a backdrop node's attributes can be correctly updated. """
        g = Graph("Backdrop node with custom values")
        backdrop = g.addNewNode("Backdrop")

        # Set custom values for backdrop and assert the properties are correctly updated
        width = backdrop.internalAttribute("nodeWidth")
        width.value = 400
        assert backdrop.nodeWidth == 400

        height = backdrop.internalAttribute("nodeHeight")
        height.value = 200
        assert backdrop.nodeHeight == 200

        fontSize = backdrop.internalAttribute("fontSize")
        fontSize.value = 10
        assert backdrop.fontSize == 10

        fontColor = backdrop.internalAttribute("fontColor")
        fontColor.value = "#00FF00"
        assert backdrop.fontColor == "#00FF00"

        color = backdrop.internalAttribute("color")
        color.value = "#FF0000"
        assert backdrop.color == "#FF0000"

        comment = backdrop.internalAttribute("comment")
        comment.value = "hello world"
        assert backdrop.comment == "hello world"

    def test_backdropNode_defaultSerialization(self):
        """ Test that a backdrop node with default values is correctly serialized and deserialized. """
        g = Graph("Backdrop node default serialization")
        backdrop = g.addNewNode("Backdrop")

        # Save the graph in a file
        graphFile = os.path.join(tempfile.mkdtemp(), "test_backdrop_serialization.mg")
        g.save(graphFile)

        # Reload the graph and check the values for the backdrop node are the default ones
        g = loadGraph(graphFile)
        backdrop = g.node("Backdrop_1")
        assert backdrop is not None
        assert backdrop.nodeWidth == 600
        assert backdrop.nodeHeight == 400
        assert backdrop.fontSize == 12
        assert backdrop.fontColor == ""
        assert backdrop.color == ""
        assert backdrop.comment == ""

    def test_backdropNode_customSerialization(self):
        """ Test that a backdrop node with custom values is correctly serialized and deserialized. """
        g = Graph("Backdrop node custom serialization")
        backdrop = g.addNewNode("Backdrop")

        # Set custom values for backdrop
        width = backdrop.internalAttribute("nodeWidth")
        width.value = 400
        height = backdrop.internalAttribute("nodeHeight")
        height.value = 200
        fontSize = backdrop.internalAttribute("fontSize")
        fontSize.value = 10
        fontColor = backdrop.internalAttribute("fontColor")
        fontColor.value = "#00FF00"
        color = backdrop.internalAttribute("color")
        color.value = "#FF0000"
        comment = backdrop.internalAttribute("comment")
        comment.value = "hello world"

        # Save the graph in a file
        graphFile = os.path.join(tempfile.mkdtemp(), "test_backdrop_serialization.mg")
        g.save(graphFile)

        # Reload the graph and check the values for the backdrop node are the default ones
        g = loadGraph(graphFile)
        backdrop = g.node("Backdrop_1")
        assert backdrop is not None
        assert backdrop.nodeWidth == 400
        assert backdrop.nodeHeight == 200
        assert backdrop.fontSize == 10
        assert backdrop.fontColor == "#00FF00"
        assert backdrop.color == "#FF0000"
        assert backdrop.comment == "hello world"

    def test_backdropNode_templateSerialization(self):
        """ Test that a graph with a backdrop node can be saved as a template. """
        g = Graph("Backdrop node template serialization")
        backdrop = g.addNewNode("Backdrop")

        # Save the graph as a template
        templateFile = os.path.join(tempfile.mkdtemp(), "test_backdrop_template.mg")
        g.save(templateFile, template=True)

        # Reload the graph and check both nodes are present
        g = loadGraph(templateFile)
        assert g.node("Backdrop_1") is not None

    def test_backdropNode_templateSerialization_customAttributes(self):
        """ Test that a backdrop node with custom values is correctly saved as a template. """
        g = Graph("Backdrop node template custom serialization")
        backdrop = g.addNewNode("Backdrop")

        # Set custom values
        backdrop.internalAttribute("nodeWidth").value = 400
        backdrop.internalAttribute("comment").value = "Template backdrop"

        templateFile = os.path.join(tempfile.mkdtemp(), "test_backdrop_template_custom.mg")
        g.save(templateFile, template=True)

        # Reload and verify custom values are preserved
        g = loadGraph(templateFile)
        backdrop = g.node("Backdrop_1")
        assert backdrop is not None
        assert backdrop.nodeWidth == 400
        assert backdrop.comment == "Template backdrop"


class TestResourceLevels:
    """ Test that cpu, gpu, and ram descriptor attributes support both static Level values and callables. """

    def test_staticResourceLevels(self):
        """ Test that static Level values are returned as-is. """

        class StaticLevelNode(desc.Node):
            cpu = desc.Level.INTENSIVE
            gpu = desc.Level.NONE
            ram = desc.Level.EXTREME

            inputs = []
            outputs = []

        with registeredNodeTypes([StaticLevelNode]):
            g = Graph("")
            node = g.addNewNode("StaticLevelNode")

            assert node.cpu == desc.Level.INTENSIVE
            assert node.gpu == desc.Level.NONE
            assert node.ram == desc.Level.EXTREME

    def test_callableResourceLevels(self):
        """ Test that callable cpu/gpu/ram values are called with the node instance. """

        class CallableLevelNode(desc.Node):
            cpu = lambda node: desc.Level.INTENSIVE if node.attribute("useMoreCpu").value else desc.Level.NORMAL
            gpu = lambda node: desc.Level.NORMAL if node.attribute("useGpu").value else desc.Level.NONE
            ram = lambda node: desc.Level.EXTREME if node.attribute("useMuchRam").value else desc.Level.NORMAL

            inputs = [
                desc.BoolParam(name="useMoreCpu", label="", description="", value=False, invalidate=False),
                desc.BoolParam(name="useGpu", label="", description="", value=False, invalidate=False),
                desc.BoolParam(name="useMuchRam", label="", description="", value=False, invalidate=False),
            ]
            outputs = []

        with registeredNodeTypes([CallableLevelNode]):
            g = Graph("")
            node = g.addNewNode("CallableLevelNode")

            # Default values: all False
            assert node.cpu == desc.Level.NORMAL
            assert node.gpu == desc.Level.NONE
            assert node.ram == desc.Level.NORMAL

            # Change attribute values
            node.attribute("useMoreCpu").value = True
            assert node.cpu == desc.Level.INTENSIVE

            node.attribute("useGpu").value = True
            assert node.gpu == desc.Level.NORMAL

            node.attribute("useMuchRam").value = True
            assert node.ram == desc.Level.EXTREME

    def test_mixedResourceLevels(self):
        """ Test a node mixing static and callable resource level attributes. """

        class MixedLevelNode(desc.Node):
            cpu = desc.Level.NORMAL  # static
            gpu = lambda node: desc.Level.INTENSIVE if node.attribute("useGpu").value else desc.Level.NONE  # callable
            ram = desc.Level.EXTREME  # static

            inputs = [
                desc.BoolParam(name="useGpu", label="", description="", value=False, invalidate=False),
            ]
            outputs = []

        with registeredNodeTypes([MixedLevelNode]):
            g = Graph("")
            node = g.addNewNode("MixedLevelNode")

            assert node.cpu == desc.Level.NORMAL
            assert node.gpu == desc.Level.NONE
            assert node.ram == desc.Level.EXTREME

            node.attribute("useGpu").value = True
            assert node.gpu == desc.Level.INTENSIVE


class TestNodeColor:
    """ Test that the color descriptor attribute can be defined on a node class and overridden. """

    def test_defaultColor(self):
        """ Test that the default color for a node with no color defined is empty string. """

        class NoColorNode(desc.Node):
            inputs = []
            outputs = []

        with registeredNodeTypes([NoColorNode]):
            g = Graph("")
            node = g.addNewNode("NoColorNode")

            assert node.color == ""

    def test_descriptorColor(self):
        """ Test that a node class with a color defined returns that color when no instance color is set. """

        class ColoredNode(desc.Node):
            color = "#FF0000"
            inputs = []
            outputs = []

        with registeredNodeTypes([ColoredNode]):
            g = Graph("")
            node = g.addNewNode("ColoredNode")

            # The node has no instance-specific color, so it should return the descriptor color
            assert node.color == "#FF0000"

    def test_instanceColorOverridesDescriptorColor(self):
        """ Test that an instance-specific color overrides the descriptor color. """

        class ColoredNode2(desc.Node):
            color = "#FF0000"
            inputs = []
            outputs = []

        with registeredNodeTypes([ColoredNode2]):
            g = Graph("")
            node = g.addNewNode("ColoredNode2")

            # Override with instance color
            node.internalAttribute("color").value = "#00FF00"
            assert node.color == "#00FF00"

    def test_resetToDefaultRestoresDescriptorColor(self):
        """ Test that resetting the color attribute to its default restores the descriptor color. """

        class ColoredNode3(desc.Node):
            color = "#FF0000"
            inputs = []
            outputs = []

        with registeredNodeTypes([ColoredNode3]):
            g = Graph("")
            node = g.addNewNode("ColoredNode3")

            # Set an instance color
            node.internalAttribute("color").value = "#00FF00"
            assert node.color == "#00FF00"

            # Resetting to default should restore the descriptor color
            node.internalAttribute("color").resetToDefaultValue()
            assert node.color == "#FF0000"


class TestNodeSizeLambda:
    """Tests for the node size evaluation with single-argument lambda (`lambda node: ...`)."""

    def test_size_lambda_single_arg(self):
        """size defined as `lambda node: ...` should be evaluated with the node instance."""

        class NodeWithLambdaSize(desc.Node):
            inputs = [
                desc.IntParam(
                    name="sizeInput",
                    label="Size Input",
                    description="Defines the node size.",
                    value=5,
                    range=(0, 100, 1),
                ),
            ]
            outputs = []
            size = lambda node: node.sizeInput.value

        with registeredNodeTypes([NodeWithLambdaSize]):
            g = Graph("")
            node = g.addNewNode("NodeWithLambdaSize")

            assert node.evaluateSize() == 5

            node.sizeInput.value = 10
            assert node.evaluateSize() == 10

    def test_size_static_node_size(self):
        """size defined as StaticNodeSize should still be evaluated correctly."""

        class NodeWithStaticSize(desc.Node):
            inputs = []
            outputs = []
            size = desc.StaticNodeSize(7)

        with registeredNodeTypes([NodeWithStaticSize]):
            g = Graph("")
            node = g.addNewNode("NodeWithStaticSize")

            assert node.evaluateSize() == 7

    def test_size_dynamic_node_size(self):
        """size defined as DynamicNodeSize should return the value of the referenced IntParam."""

        class NodeWithDynamicSize(desc.Node):
            inputs = [
                desc.IntParam(
                    name="count",
                    label="Count",
                    description="Number of items.",
                    value=4,
                    range=(0, 100, 1),
                ),
            ]
            outputs = []
            size = desc.DynamicNodeSize("count")

        with registeredNodeTypes([NodeWithDynamicSize]):
            g = Graph("")
            node = g.addNewNode("NodeWithDynamicSize")

            assert node.evaluateSize() == 4

            node.count.value = 12
            assert node.evaluateSize() == 12

    def test_size_custom_function(self):
        """size defined as a named function should be called with the node instance."""

        def customSizeFunction(node):
            return node.itemCount.value * 2

        class NodeWithCustomFunctionSize(desc.Node):
            inputs = [
                desc.IntParam(
                    name="itemCount",
                    label="Item Count",
                    description="Number of items.",
                    value=3,
                    range=(0, 100, 1),
                ),
            ]
            outputs = []
            size = customSizeFunction

        with registeredNodeTypes([NodeWithCustomFunctionSize]):
            g = Graph("")
            node = g.addNewNode("NodeWithCustomFunctionSize")

            assert node.evaluateSize() == 6

            node.itemCount.value = 5
            assert node.evaluateSize() == 10

    def test_size_custom_callable_class(self):
        """size defined as an instance of a class with __call__ should be called with the node instance."""

        class CustomSizeComputer:
            def __call__(self, node):
                return node.itemCount.value + 1

        class NodeWithCustomCallableSize(desc.Node):
            inputs = [
                desc.IntParam(
                    name="itemCount",
                    label="Item Count",
                    description="Number of items.",
                    value=7,
                    range=(0, 100, 1),
                ),
            ]
            outputs = []
            size = CustomSizeComputer()

        with registeredNodeTypes([NodeWithCustomCallableSize]):
            g = Graph("")
            node = g.addNewNode("NodeWithCustomCallableSize")

            assert node.evaluateSize() == 8

            node.itemCount.value = 9
            assert node.evaluateSize() == 10


class TestGenerateMgScene:
    loadedPlugins = pluginManager.getPlugins()

    @classmethod
    def setup_class(cls):
        initNodes()

    @classmethod
    def teardown_class(cls):
        for plugin in pluginManager.getPlugins():
            if plugin not in cls.loadedPlugins:
                for node in plugin.nodes.values():
                    pluginManager.unregisterNode(node)
                pluginManager.removePlugin(plugin)

    @staticmethod
    def generate_img_folder(tmpdir: Path, nbImages: int):
        """ Create an image folder from an empty image """
        img_ref = str(TEST_RESOURCES / "empty.jpg")
        img_folder = tmpdir / "images"
        img_folder.mkdir()
        for i in range(nbImages):
            shutil.copy(img_ref, img_folder / f"{i:03d}.jpg")
        return img_folder

    @staticmethod
    def create_template(tmpdir: Path):
        """ Create the template scene for the test """
        graph = Graph("Test template")
        graph.addNewNode("InputString", "A_1", position=Position(0, 0))
        graph.addNewNode("InputInt", "B_1", Position(200, 0))
        graph.addNewNode("InputInt", "C_1", Position(400, 0))
        graph.addNewNode("InputFile", "InputImages_1", Position(600, 0))
        graphFile = tmpdir / "test_template_generatemgscene.mg"
        graph.save(graphFile)
        return graphFile
    
    @staticmethod
    def processNode(node):
        """ Process a non-parallelized node and check that it succeed """
        cache = Path(node.internalFolder)
        cache.mkdir(parents=True)
        # Process
        logFile = cache / f"0.log"
        logFile.touch()
        node.prepareLogger(-1)
        node.preprocess()
        node.process(True, True)
        node.postprocess()
        node.restoreLogger()
        # Check output
        nodeStatusFile = cache / "nodeStatus"
        assert(nodeStatusFile.exists())
        with open(str(nodeStatusFile), "r") as f:
            c = json.load(f)
        assert(c.get("status") == "SUCCESS")
        return True

    @staticmethod
    def comparePaths(pathA, pathB):
        assert(Path(pathA) == Path(pathB))

    def test_generatemgscene(self):
        """ Test the GenerateMeshroomScene & MeshroomSceneParameter nodes

        We test as much features as possible :
        - MeshroomSceneParameter :
            - node_instance(default) and node_type modes
            - with and without attrName
            - empty attrValue
        - GenerateMeshroomScene :
            - override inputs (CameraInit)
            - override other node parameters
            - an empty override item for both
            - override parameter with node instance and node type modes
        """
        nbImages = 2
        tmpdir = Path(tempfile.mkdtemp())
        images = self.generate_img_folder(tmpdir, nbImages)
        template = self.create_template(tmpdir)
        # Create graph
        graph = Graph("Test GenerateMeshroomScene")
        # - Inputs Overrides
        nodeA = graph.addNewNode("MeshroomSceneParameter", position=Position(0, 0))
        nodeA.nodeName.value = "InputImages_1"
        nodeA.attrValue.value = str(images)
        nodeB = graph.addNewNode("MeshroomSceneParameter", position=Position(0, 100))
        nodeB.nodeName.value = "InputFile_1"
        # - Param Overrides
        nodeC = graph.addNewNode("MeshroomSceneParameter", position=Position(0, 200))
        nodeC.nodeName.value = "A_1"
        nodeC.attrName.value = "string"
        nodeC.attrValue.value = "test"
        nodeD = graph.addNewNode("MeshroomSceneParameter", position=Position(0, 300))
        nodeD.nodeName.value = "A_2"
        nodeD.attrName.value = "string"
        nodeD.attrValue.value = ""
        nodeE = graph.addNewNode("MeshroomSceneParameter", position=Position(0, 400))
        nodeE.nodeName.value = "InputInt"
        nodeE.attrName.value = "integer"
        nodeE.attrValue.value = "42"
        nodeE.mode.value = "node_type"
        # - GenerateMeshroomScene Node
        testNode = graph.addNewNode("GenerateMeshroomScene", position=Position(200, 150))
        testNode.templatePath.value = str(template)
        # - Connections
        testNode.inputOverrides.extend(["0", "1"])
        for i, upstreamNode in enumerate([nodeA, nodeB]):
            upstreamNode.output.connectTo(testNode.inputOverrides.at(i))
        testNode.paramOverrides.extend(["0", "1", "2"])
        for i, upstreamNode in enumerate([nodeC, nodeD, nodeE]):
            upstreamNode.output.connectTo(testNode.paramOverrides.at(i))
        # Save graph
        graphFile = tmpdir / "test_scene_generatemgscene.mg"
        graph.save(graphFile)
        # Execute graph
        for node in [nodeA, nodeB, nodeC, nodeD, nodeE]:
            self.processNode(node)
        self.processNode(testNode)
        # Check output scene
        scene = Path(testNode.internalFolder) / "scene.mg"
        assert(scene.exists())
        with open(str(scene), "r") as f:
            c = json.load(f)
        generatedSceneGraph = c["graph"]
        assert(generatedSceneGraph["A_1"]["inputs"]["string"] == "test")
        assert(generatedSceneGraph["B_1"]["inputs"]["integer"] == 42)
        assert(generatedSceneGraph["C_1"]["inputs"]["integer"] == 42)
        self.comparePaths(generatedSceneGraph["InputImages_1"]["inputs"]["inputFile"], images)
