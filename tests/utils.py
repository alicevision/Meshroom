from contextlib import contextmanager
from unittest.mock import patch

import meshroom
from meshroom.core import desc, pluginManager
from meshroom.core.plugins import NodePlugin, NodePluginStatus

@contextmanager
def registeredNodeTypes(nodeTypes: list[desc.Node]):
    nodePluginsList = {}
    for nodeType in nodeTypes:
        nodePlugin = NodePlugin(nodeType)
        pluginManager.registerNode(nodePlugin)
        nodePluginsList[nodeType] = nodePlugin

    yield

    for nodeType in nodeTypes:
        pluginManager.unregisterNode(nodePluginsList[nodeType])

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
    if not pluginManager.isRegistered(name):
        pluginManager._nodePlugins[name] = NodePlugin(nodeDesc)
        pluginManager._nodePlugins[name].status = NodePluginStatus.LOADED

def unregisterNodeDesc(nodeDesc: desc.Node):
    name = nodeDesc.__name__
    if pluginManager.isRegistered(name):
        plugin = pluginManager.getRegisteredNodePlugin(name)
        plugin.status = NodePluginStatus.NOT_LOADED
        del pluginManager._nodePlugins[name]
