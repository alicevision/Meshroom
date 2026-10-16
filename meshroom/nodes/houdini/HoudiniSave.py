__version__ = "1.0"

from meshroom.core.subgraph.sceneNodes import SaveNode, saveNodeInputs, saveNodeOutputs


class HoudiniSave(SaveNode):
    __doc__ = SaveNode.__doc__
    category = "Houdini"
    context = "houdini"

    inputs = saveNodeInputs("Houdini")
    outputs = saveNodeOutputs()
