from contextlib import contextmanager
from unittest.mock import patch

import meshroom
from meshroom.core import desc, pluginManager, loadPluginFolder
from meshroom.core.plugins.manager import NodeProvider

import os


@contextmanager
def registeredNodeTypes(nodeTypes: list[desc.Node]):
    nodeProvidersList = {}
    for nodeType in nodeTypes:
        nodeProvider = NodeProvider(nodeType)
        pluginManager.loadNodeProvider(nodeProvider)
        nodeProvidersList[nodeType] = nodeProvider

    yield

    for nodeType in nodeTypes:
        pluginManager.unloadNodeProvider(nodeProvidersList[nodeType])


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
    if not pluginManager.isLoaded(name):
        pluginManager._nodeProviders[name] = NodeProvider(nodeDesc)


def unregisterNodeDesc(nodeDesc: desc.Node):
    name = nodeDesc.__name__
    if pluginManager.isLoaded(name):
        del pluginManager._nodeProviders[name]


@contextmanager
def loadedPlugins(folder: str):
    plugins = loadPluginFolder(folder)

    yield

    for plugin in plugins:
        pluginManager.removePlugin(plugin)

@contextmanager
def loadedUserPlugins(folder: str):
    plugins = loadPluginFolder(folder, userPlugin=True)

    yield

    for plugin in plugins:
        pluginManager.removePlugin(plugin)


@contextmanager
def overrideOsEnvironmentVariables(envVariables: dict):
    with patch.dict(os.environ, envVariables, clear=False):
        yield
