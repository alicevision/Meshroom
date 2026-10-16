__version__ = "1.0"

from meshroom.core import desc

from meshroom.core.subgraph.houdini import samePath, sceneOutput


class HoudiniOpenScene(desc.LiveNode):
    """
    Opens a Houdini scene (.hip), unless it is already the current scene (from a Houdini session, the
    subgraph then works on the open scene and its unsaved changes).
    """
    category = "Houdini"
    context = "houdini"

    inputs = [
        desc.File(
            name="hipFile",
            label="Scene File",
            description="The .hip file to open.",
            value="",
        ),
        desc.BoolParam(
            name="reload",
            label="Reload",
            description="Open the file even if it is the current scene (unsaved changes are lost).",
            value=False,
        ),
    ]

    outputs = [
        sceneOutput(),
    ]

    def execute(self, ctx, inputs):
        hou = ctx.context.session
        hipFile = inputs["hipFile"]
        if hipFile and (inputs["reload"] or not samePath(hou.hipFile.path(), hipFile)):
            ctx.logger.info(f"[Houdini] Open {hipFile}")
            hou.hipFile.load(hipFile, suppress_save_prompt=True, ignore_load_warnings=True)
        return {"sceneOut": hou.hipFile.path()}
