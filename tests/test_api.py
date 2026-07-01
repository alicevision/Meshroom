import os
import tempfile
import pytest
from collections import defaultdict

from meshroom.core.graph import Graph
from meshroom.core import desc, cacheFolderName
from meshroom.core.graph import Graph, loadGraph
from meshroom.core.node import CompatibilityIssue, CompatibilityNode
from meshroom.core.exception import GraphCompatibilityError, NodeUpgradeError
from .utils import registerNodeDesc, registeredNodeTypes, overrideNodeTypeVersion

from meshroom import api as meshroomApi


@pytest.fixture
def sceneFilepath():
    """ Scene with :
    - 1 Backdrop node (Backdrop_1) containing :
      - 2 InputString nodes (A_1, InputString_1)
      - 1 InputInt node (Int_1)
      - 1 InputFile node (InsideBackdrop_1)
    - 1 InputFile node (OutsideBackdrop_1)
    """
    folder = os.path.join(os.path.dirname(__file__), "resources")
    scene = "templateGraphWithBackdrops.mg"
    path = os.path.join(folder, scene)
    return path


def loadGraph(path, failedOnCompatbility=False):
    g = meshroomApi.loadGraph(path, strictCompatibility=failedOnCompatbility)
    return g


def getGeneralPlugin():
    plugins = meshroomApi.listPlugins()
    assert "general" in plugins.keys()
    p = plugins["general"]
    return p


def getInputFileNodePlugin():
    nodes = meshroomApi.listNodes()
    assert "InputFile" in nodes.keys()
    n = nodes["InputFile"]
    return n


class TestMeshroomApi:
    @classmethod
    def setup_class(cls):
        # meshroomApi.setLoglevel("info")
        meshroomApi.initialize(nodes=True)

    @classmethod
    def teardown_class(cls):
        meshroomApi.setLoglevel("warning")

    def test_api_registerPlugin(self):
        """ Test unregisterPlugin, unregisterPlugin, listPlugins """
        plugin = getGeneralPlugin()
        meshroomApi.unregisterPlugin("general")
        meshroomApi.registerPlugin(plugin)
        plugins = meshroomApi.listPlugins()
        assert "general" in plugins.keys()

    def test_api_registerNode(self):
        """ Test unregisterNode, registerNode, listNodes """
        node = getInputFileNodePlugin()
        meshroomApi.unregisterNode("InputFile")
        meshroomApi.registerNode(node)
        nodes = meshroomApi.listNodes()
        assert "InputFile" in nodes

    def test_api_loadGraph(self, sceneFilepath):
        g = loadGraph(sceneFilepath, failedOnCompatbility=True)
        assert g.filepath == sceneFilepath
        assert os.path.dirname(g.cacheDir) == os.path.dirname(sceneFilepath)

    def test_api_loadGraphRaiseOnCompatibility(self, sceneFilepath):
        node = getInputFileNodePlugin()
        try:
            meshroomApi.unregisterNode("InputFile")
            _ = loadGraph(sceneFilepath, failedOnCompatbility=True)
        except (NodeUpgradeError, GraphCompatibilityError):
            pass
        else:
            raise RuntimeError("Test was expected to fail because of missing nodes.")
        finally:
            # Restore InputFile for other tests
            meshroomApi.registerNode(node)

    def test_api_getNodes(self, sceneFilepath):
        g = loadGraph(sceneFilepath)
        nodes = meshroomApi.getNodes(g)
        nodeByType = defaultdict(list)
        for node in nodes:
            nodeByType[node.nodeType].append(node)
        nodeTypes = nodeByType.keys()
        assert set(nodeTypes) == {"InputString", "InputFile", "InputInt", "Backdrop"}
        assert len(nodeByType["InputString"]) == 2
        assert len(nodeByType["InputFile"]) == 2
        assert len(nodeByType["InputInt"]) == 1
        assert len(nodeByType["Backdrop"]) == 1

    def test_api_getBackdropNodes(self, sceneFilepath):
        g = loadGraph(sceneFilepath)
        backdropNodes = meshroomApi.getBackdropNodes(g)
        assert len(backdropNodes) == 1
        backdrop = backdropNodes[0]
        assert backdrop.name == "Backdrop_1"

    def test_api_getNode(self, sceneFilepath):
        g = loadGraph(sceneFilepath)
        def checkNode(name, checkType):
            node = meshroomApi.getNode(g, instanceName=name)
            assert node is not None
            assert node.nodeType == checkType
        checkNode("Backdrop_1", "Backdrop")
        checkNode("A_1", "InputString")
        checkNode("InputString_1", "InputString")
        checkNode("Int_1", "InputInt")
        checkNode("InsideBackdrop_1", "InputFile")
        checkNode("OutsideBackdrop_1", "InputFile")

    def test_api_getNodesInsideBackdrop(self, sceneFilepath):
        g = loadGraph(sceneFilepath)
        backdropNode = meshroomApi.getBackdropNodes(g)[0]
        nodesInside = meshroomApi.getNodesInsideBackdrop(g, backdropNode)
        nodeNames = set([n.name for n in nodesInside])
        for n in ["A_1", "InputString_1", "Int_1", "InsideBackdrop_1"]:
            assert n in nodeNames
        assert "OutsideBackdrop_1" not in nodeNames

    def test_api_getNodeAttributes(self, sceneFilepath):
        g = loadGraph(sceneFilepath)
        nodeInt_1 = meshroomApi.getNode(g, instanceName="Int_1")
        attrs = meshroomApi.getNodeAttributes(nodeInt_1)
        assert len(attrs) == 1
        assert attrs[0].name == "integer"
