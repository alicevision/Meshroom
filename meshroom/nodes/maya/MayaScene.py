__version__ = "1.0"

from meshroom.core.subgraph.sceneNodes import SceneNode, sceneNodeInputs, sceneNodeOutputs


class MayaScene(SceneNode):
    __doc__ = SceneNode.__doc__
    category = "Maya"
    context = "maya"

    inputs = sceneNodeInputs("Maya")
    outputs = sceneNodeOutputs()
