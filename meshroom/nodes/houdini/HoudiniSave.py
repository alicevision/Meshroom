__version__ = "1.0"

from meshroom.core import desc


class HoudiniSave(desc.LiveNode):
    """
    Saves the Houdini scene once, with the changes of the previous nodes (the saves of the task nodes of
    the subgraph are grouped in this one). In a Houdini session (meshroom.subgraph.run from the Python
    shell), the scene is only saved if "Save In Houdini Session" is on.
    """
    category = "Houdini"
    context = "houdini"

    inputs = [
        desc.File(
            name="scene",
            label="Scene",
            description="Connect the previous Houdini node to run after it.",
            value="",
        ),
        desc.File(
            name="hipFile",
            label="Save As",
            description="Where to save the scene (empty: its current file).",
            value="",
        ),
        desc.BoolParam(
            name="saveInSession",
            label="Save In Houdini Session",
            description="Also save when the subgraph runs in an open Houdini session (from its Python shell).",
            value=False,
        ),
    ]

    outputs = [
        desc.File(
            name="sceneOut",
            label="Scene",
            description="Path of the saved scene.",
            value=None,
        ),
    ]

    def execute(self, ctx, inputs):
        session = ctx.context
        if session.ownsSession or inputs.get("saveInSession"):
            session.saveScene(inputs.get("hipFile") or None)
            ctx.logger.info(f"[{ctx.nodeName}] Saved: {session.session.hipFile.path()}")
        else:
            session.discardPendingSave()
            ctx.logger.info(f"[{ctx.nodeName}] Houdini session: the scene is not saved.")
        return {"sceneOut": session.session.hipFile.path()}
