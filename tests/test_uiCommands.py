from meshroom.core import desc, pluginManager
from meshroom.core.graph import loadGraph
from meshroom.core.plugins.base import NodeDescProvider
from meshroom.ui.commands import UpgradeNodeCommand

from .utils import registeredNodeTypes


class UpgradeSource(desc.Node):
    inputs = [desc.File(name="input", label="Input", description="", value="")]
    outputs = [
        desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out"),
        desc.File(name="extra", label="Extra", description="", value="{nodeCacheFolder}/extra"),
    ]


class UpgradeSourceV2(desc.Node):
    """ 'extra' has been removed. """
    inputs = [desc.File(name="input", label="Input", description="", value="")]
    outputs = [desc.File(name="output", label="Output", description="", value="{nodeCacheFolder}/out")]


class UpgradeTarget(desc.Node):
    inputs = [
        desc.File(name="input", label="Input", description="", value=""),
        desc.File(name="other", label="Other", description="", value=""),
        desc.ListAttribute(name="files", label="Files", description="",
                           elementDesc=desc.File(name="file", label="File", description="", value="")),
    ]
    outputs = []


def edges(graph):
    return sorted((edge.src.fullName, edge.dst.fullName) for edge in graph.edges)


def test_upgradeNodeUndoRestoresLostEdges(graphSavedOnDisk):
    with registeredNodeTypes([UpgradeSource, UpgradeTarget]):
        graph = graphSavedOnDisk
        source, target = graph.addNewNode("UpgradeSource"), graph.addNewNode("UpgradeTarget")
        target.files.extend(["", ""])
        graph.addEdge(source.output, target.input)
        graph.addEdge(source.extra, target.other)
        graph.addEdge(source.extra, target.files.at(1))
        graph.save()

        pluginManager.getNodeDescProviders()["UpgradeSource"] = NodeDescProvider(UpgradeSourceV2)
        graph = loadGraph(graph.filepath)
        before = edges(graph)
        command = UpgradeNodeCommand(graph, graph.node(source.name))

        assert command.redoImpl()
        assert edges(graph) == [("UpgradeSource_1.output", "UpgradeTarget_1.input")]

        command.undoImpl()
        assert graph.node(source.name).isCompatibilityNode
        assert edges(graph) == before
        assert len(graph.node(target.name).files) == 2

        # Redo after undo loses the same edges again
        assert command.redoImpl()
        assert edges(graph) == [("UpgradeSource_1.output", "UpgradeTarget_1.input")]
