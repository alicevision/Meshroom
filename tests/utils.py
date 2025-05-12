from contextlib import contextmanager
from unittest.mock import patch
from typing import Type

import meshroom
from meshroom.core import registerNodeType, unregisterNodeType
from meshroom.core import desc

@contextmanager
def registeredNodeTypes(nodeTypes: list[Type[desc.Node]]):
    for nodeType in nodeTypes:
        registerNodeType(nodeType)

    yield

    for nodeType in nodeTypes:
        unregisterNodeType(nodeType)

@contextmanager
def overrideNodeTypeVersion(nodeType: Type[desc.Node], version: str):
    """ Helper context manager to override the version of a given node type. """
    unpatchedFunc = meshroom.core.nodeVersion
    with patch.object(
        meshroom.core,
        "nodeVersion",
        side_effect=lambda type: version if type is nodeType else unpatchedFunc(type),
    ):
        yield
