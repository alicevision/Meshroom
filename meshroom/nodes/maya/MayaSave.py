__version__ = "1.0"

from meshroom.core.subgraph.sceneNodes import SaveNode, saveNodeInputs, saveNodeOutputs


class MayaSave(SaveNode):
    __doc__ = SaveNode.__doc__
    category = "Maya"
    context = "maya"

    inputs = saveNodeInputs("Maya")
    outputs = saveNodeOutputs()
