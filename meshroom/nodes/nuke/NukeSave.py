__version__ = "1.0"

from meshroom.core.subgraph.sceneNodes import SaveNode, saveNodeInputs, saveNodeOutputs


class NukeSave(SaveNode):
    __doc__ = SaveNode.__doc__
    category = "Nuke"
    context = "nuke"

    inputs = saveNodeInputs("Nuke")
    outputs = saveNodeOutputs()
