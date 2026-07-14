from contextlib import contextmanager
from unittest.mock import patch

import meshroom
from meshroom.core import desc, pluginManager, loadPluginFolder
from meshroom.core.plugins.base import NodeDescProvider

import os


@contextmanager
def registeredNodeTypes(nodeTypes: list[desc.Node]):
    nodeDescProvidersList = {}
    for nodeType in nodeTypes:
        nodeDescProvider = NodeDescProvider(nodeType)
        pluginManager.registerNode(nodeDescProvider)
        nodeDescProvidersList[nodeType] = nodeDescProvider

    yield

    for nodeType in nodeTypes:
        pluginManager.unregisterNode(nodeDescProvidersList[nodeType])


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


def registerNodeDesc(nodeDesc: desc.Node):
    name = nodeDesc.__name__
    if not pluginManager.isNodeDescRegistered(name):
        pluginManager._nodeDescProviders[name] = NodeDescProvider(nodeDesc)


def unregisterNodeDesc(nodeDesc: desc.Node):
    name = nodeDesc.__name__
    if pluginManager.isNodeDescRegistered(name):
        del pluginManager._nodeDescProviders[name]


@contextmanager
def registeredPlugins(folder: str):
    plugins = loadPluginFolder(folder)

    yield

    for plugin in plugins:
        pluginManager.removePlugin(plugin)

@contextmanager
def registeredUserPlugins(folder: str):
    plugins = loadPluginFolder(folder, userPlugin=True)

    yield

    for plugin in plugins:
        pluginManager.removePlugin(plugin)


@contextmanager
def overrideOsEnvironmentVariables(envVariables: dict):
    with patch.dict(os.environ, envVariables, clear=False):
        yield
