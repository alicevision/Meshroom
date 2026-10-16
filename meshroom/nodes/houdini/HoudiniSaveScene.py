__version__ = "1.0"

from meshroom.core import desc

from meshroom.core.subgraph.houdini import sceneInput, sceneOutput


class HoudiniSaveScene(desc.LiveNode):
    """ Saves the Houdini scene, to its current file or to another one. """
    category = "Houdini"
    context = "houdini"

    inputs = [
        sceneInput(),
        desc.File(
            name="hipFile",
            label="Scene File",
            description="Where to save the scene (empty: its current file).",
            value="",
        ),
    ]

    outputs = [
        sceneOutput(),
    ]

    def execute(self, ctx, inputs):
        hou = ctx.context.session
        hou.hipFile.save(inputs["hipFile"] or None)
        return {"sceneOut": hou.hipFile.path()}
