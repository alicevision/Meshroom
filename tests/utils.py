from contextlib import contextmanager
from typing import Type
from meshroom.core import registerNodeType, unregisterNodeType

from meshroom.core import desc

@contextmanager
def registeredNodeTypes(nodeTypes: list[Type[desc.Node]]):
    for nodeType in nodeTypes:
        registerNodeType(nodeType)

    yield

    for nodeType in nodeTypes:
        unregisterNodeType(nodeType)
