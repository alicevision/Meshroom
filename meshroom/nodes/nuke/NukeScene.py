__version__ = "1.0"

from meshroom.core.subgraph.sceneNodes import SceneNode, sceneNodeInputs, sceneNodeOutputs


class NukeScene(SceneNode):
    __doc__ = SceneNode.__doc__
    category = "Nuke"
    context = "nuke"

    inputs = sceneNodeInputs("Nuke")
    outputs = sceneNodeOutputs()
