from contextlib import contextmanager
from unittest.mock import patch

import meshroom
from meshroom.core import desc, pluginManager
from meshroom.core.plugins import NodePlugin

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
