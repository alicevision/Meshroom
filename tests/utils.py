from contextlib import contextmanager
from unittest.mock import patch
from pathlib import Path

import meshroom
from meshroom.core import desc, pluginManager
from meshroom.core.plugins.base import NodeDescProvider

import os


def writeFile(filePath: Path, content: str = "") -> Path:
    filePath.parent.mkdir(parents=True, exist_ok=True)
    filePath.write_text(content)
    return filePath


@contextmanager
def overrideNodeTypeVersion(nodeType: desc.Node, version: str):
    """ Helper context manager to override the version of a given node type. """
    unpatchedFunc = meshroom.core.nodeVersion
    with patch.object(
        meshroom.core,
        "nodeVersion",
        side_effect=lambda type: version if type is nodeType else unpatchedFunc(type),
    ):
        yield


@contextmanager
def registeredNodeTypes(nodeDescs: list[desc.Node]):
    for nodeDesc in nodeDescs:
        nodeType = nodeDesc.__name__
        if not pluginManager.isNodeDescRegistered(nodeType):
            nodeDescProvider = NodeDescProvider(nodeDesc)
            pluginManager._nodeDescProviders[nodeType] = nodeDescProvider

    yield

    for nodeDesc in nodeDescs:
        nodeType = nodeDesc.__name__
        if pluginManager.isNodeDescRegistered(nodeType):
            del pluginManager._nodeDescProviders[nodeType]


@contextmanager
def registeredPlugin(pluginName: str, pluginFolder: str, isUserPlugin: bool = False):
    pluginManager.addPluginFromPath(pluginName, pluginFolder, isUserPlugin=isUserPlugin)

    yield

    plugin = pluginManager.getPlugin(pluginName)
    if plugin:
        pluginManager.removePlugin(plugin)


def registerNodeDesc(nodeDesc: desc.Node):
    nodeType = nodeDesc.__name__
    if not pluginManager.isNodeDescRegistered(nodeType):
        pluginManager._nodeDescProviders[nodeType] = NodeDescProvider(nodeDesc)


def unregisterNodeDesc(nodeDesc: desc.Node):
    nodeType = nodeDesc.__name__
    if pluginManager.isNodeDescRegistered(nodeType):
        del pluginManager._nodeDescProviders[nodeType]


@contextmanager
def overrideOsEnvironmentVariables(envVariables: dict):
    with patch.dict(os.environ, envVariables, clear=False):
        yield
