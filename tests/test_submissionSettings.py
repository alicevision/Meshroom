# coding:utf-8

"""
Test the settings a node exposes to the submitters, and the tasks the submitters create from the graph.
Unlike test_submit.py, nothing here requires a local farm so these tests run on all platforms.
"""

import logging

import pytest

from meshroom.core import desc
from meshroom.core.graph import Graph
from meshroom.core.submitter import OrderedTask, OrderedTasks, OrderedTaskType

from .utils import registeredNodeTypes


class DefaultSettingsNode(desc.Node):
    pass


class ResourcesNode(desc.Node):
    cpu = desc.Level.INTENSIVE
    ram = desc.Level.EXTREME
    gpu = desc.Level.NORMAL
    _licenses = ["licenseA"]


class DynamicResourcesNode(desc.Node):
    def cpu(node):
        return desc.Level.EXTREME


class DeprecatedTagsNode(desc.Node):
    _cuda_tag = "cudaTag"
    _service_key = "serviceKey"


class CustomSettingsNode(desc.Node):
    cpu = desc.Level.INTENSIVE

    def getSubmissionSettings(self, node):
        settings = super().getSubmissionSettings(node)
        settings.preprocess.cpu = desc.Level.EXTREME
        settings.process.target_os = "windows"
        return settings


class PrePostNode(desc.Node):
    size = desc.StaticNodeSize(2)
    parallelization = desc.Parallelization(blockSize=1)

    def preprocess(self, node):
        pass

    def postprocess(self, node):
        pass


NODE_TYPES = [DefaultSettingsNode, ResourcesNode, DynamicResourcesNode, DeprecatedTagsNode, CustomSettingsNode, PrePostNode]


@pytest.fixture
def graph():
    with registeredNodeTypes(NODE_TYPES):
        yield Graph("")


def getSettings(graph, nodeDesc):
    node = graph.addNewNode(nodeDesc.__name__)
    return node.nodeDesc.getSubmissionSettings(node)


class TestStageSettings:
    def test_defaultValues(self):
        stage = desc.StageSettings()
        assert (stage.cpu, stage.ram, stage.gpu) == (desc.Level.NORMAL, desc.Level.NORMAL, desc.Level.NONE)

    def test_levelsAreKept(self):
        stage = desc.StageSettings(cpu=desc.Level.EXTREME, ram=desc.Level.INTENSIVE, gpu=desc.Level.NORMAL)
        assert stage.cpu is desc.Level.EXTREME
        assert stage.ram is desc.Level.INTENSIVE
        assert stage.gpu is desc.Level.NORMAL

    def test_levelValuesAreConverted(self):
        stage = desc.StageSettings(ram=2)
        assert stage.ram is desc.Level.INTENSIVE
        stage.gpu = 3
        assert stage.gpu is desc.Level.EXTREME

    @pytest.mark.parametrize("resource", desc.StageSettings.RESOURCES)
    @pytest.mark.parametrize("value", ["high", 42, None])
    def test_invalidResourcesAreRejected(self, resource, value):
        with pytest.raises(ValueError):
            desc.StageSettings(**{resource: value})
        stage = desc.StageSettings()
        with pytest.raises(ValueError):
            setattr(stage, resource, value)

    def test_customSettings(self):
        stage = desc.StageSettings(target_os="windows")
        stage.setup_command = "mount"
        assert stage.target_os == "windows"
        assert "target_os" in stage
        assert "setup_command" in stage
        assert "cpu" in stage
        assert "unknown" not in stage


class TestSubmissionSettings:
    def test_defaultSettingsPerStage(self, graph):
        """ The resources of the node description only apply to the process stage. """
        settings = getSettings(graph, ResourcesNode)
        process = settings.process
        assert process.cpu == desc.Level.INTENSIVE
        assert process.ram == desc.Level.EXTREME
        assert process.gpu == desc.Level.NORMAL
        assert process.licenses == ["licenseA"]
        for stage in (settings.preprocess, settings.postprocess):
            assert stage == desc.StageSettings()
            assert "licenses" not in stage

    def test_defaultNodeHasNoOptionalSettings(self, graph, caplog):
        with caplog.at_level(logging.WARNING):
            settings = getSettings(graph, DefaultSettingsNode)
        assert settings.process.licenses == []
        assert "cuda_tag" not in settings.process
        assert "service_key" not in settings.process
        assert "DeprecationWarning" not in caplog.text

    def test_licensesAreNotShared(self, graph):
        """ Editing the licenses of a node's settings does not impact its node type or the other node types. """
        settings = getSettings(graph, ResourcesNode)
        settings.process.licenses.append("licenseB")
        assert ResourcesNode._licenses == ["licenseA"]
        assert getSettings(graph, ResourcesNode).process.licenses == ["licenseA"]

        settings = getSettings(graph, DefaultSettingsNode)
        settings.process.licenses.append("licenseB")
        assert desc.BaseNode._licenses == []
        assert getSettings(graph, DefaultSettingsNode).process.licenses == []

    def test_callableResourcesAreResolved(self, graph):
        settings = getSettings(graph, DynamicResourcesNode)
        assert settings.process.cpu == desc.Level.EXTREME

    def test_deprecatedTags(self, graph, caplog):
        """ Node types still declaring '_cuda_tag' or '_service_key' keep working, with a warning. """
        with caplog.at_level(logging.WARNING):
            settings = getSettings(graph, DeprecatedTagsNode)
        assert settings.process.cuda_tag == "cudaTag"
        assert settings.process.service_key == "serviceKey"
        assert "'_cuda_tag'" in caplog.text
        assert "'_service_key'" in caplog.text

    def test_nodeTypeOverride(self, graph):
        settings = getSettings(graph, CustomSettingsNode)
        assert settings.preprocess.cpu == desc.Level.EXTREME
        assert settings.process.cpu == desc.Level.INTENSIVE
        assert settings.process.target_os == "windows"
        assert "target_os" not in settings.postprocess

    def test_getStageSettings(self, graph):
        settings = getSettings(graph, DefaultSettingsNode)
        assert settings.getStageSettings() is settings.process
        for stageName in desc.SubmissionSettings.STAGES:
            assert settings.getStageSettings(stageName) is getattr(settings, stageName)

    @pytest.mark.parametrize("stageName", ["unknown", "STAGES"])
    def test_getStageSettingsInvalidName(self, graph, stageName):
        """ Only the stages can be retrieved, not any attribute of the settings. """
        settings = getSettings(graph, DefaultSettingsNode)
        with pytest.raises(ValueError, match=stageName):
            settings.getStageSettings(stageName)


class TestOrderedTask:
    def test_uidsAreUniqueAndIncreasing(self):
        uids = [OrderedTask(OrderedTaskType.PLACEHOLDER).uid for _ in range(3)]
        assert uids == sorted(set(uids))

    def test_nameWithoutNode(self):
        task = OrderedTask(OrderedTaskType.PLACEHOLDER)
        assert task.nodeName == "NONE"
        assert task.name == f"{task.uid:03d} NONE_PLACEHOLDER"

    def test_namePerTaskType(self, graph):
        node = graph.addNewNode("PrePostNode")
        names = {
            (OrderedTaskType.PREPROCESS, -1): "PREPROCESS",
            (OrderedTaskType.EXPANDING, -1): "EXPANDING",
            (OrderedTaskType.CHUNK, -1): "process",
            (OrderedTaskType.CHUNK, 2): "2",
            (OrderedTaskType.POSTPROCESS, -1): "POSTPROCESS",
        }
        for (taskType, iteration), suffix in names.items():
            task = OrderedTask(taskType, node, iteration=iteration)
            assert task.name == f"{task.uid:03d} {node.name}_{suffix}"

    def test_addDependency(self):
        task = OrderedTask(OrderedTaskType.PLACEHOLDER)
        dependency = OrderedTask(OrderedTaskType.PLACEHOLDER)
        task.addDependency(dependency)
        assert task.dependencies == [dependency]

    def test_displayOrderedTasks(self, graph, caplog):
        """ The display gives the tasks of the node and their dependencies, from their names. """
        node = graph.addNewNode("PrePostNode")
        nodes, edges = graph.dfsOnFinish(startNodes=[node])
        orderedTasks = OrderedTasks(nodes, edges)
        with caplog.at_level(logging.DEBUG):
            orderedTasks.display()
        for task in orderedTasks:
            assert f"[{task.name}]" in caplog.text
        postprocess = orderedTasks.rootTask.dependencies[0]
        assert postprocess.taskType == OrderedTaskType.POSTPROCESS
        expectedDependencies = [t.name for t in postprocess.dependencies]
        assert len(expectedDependencies) == 2
        assert f"[{postprocess.name}] {postprocess} -> depends on {expectedDependencies}" in caplog.text
