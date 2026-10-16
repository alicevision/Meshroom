__version__ = "1.0"

from meshroom.core import desc

from meshroom.core.subgraph.houdini import ropOutputFile, sceneInput, sceneOutput


class HoudiniRender(desc.LiveNode):
    """
    Renders / exports with a ROP (Mantra, Karma, ROP Geometry Output, File Cache...): the current frame
    in a frame loop, else the frame range of the ROP.
    """
    category = "Houdini"
    context = "houdini"

    inputs = [
        sceneInput(),
        desc.StringParam(
            name="rop",
            label="ROP",
            description="Path of the ROP node (e.g. /out/mantra1, /obj/geo1/filecache1/render).",
            value="/out/mantra1",
        ),
        desc.BoolParam(
            name="loopFrame",
            label="Frame Of The Loop",
            description="In a frame loop, render the current frame only (else the frame range of the ROP).",
            value=True,
        ),
        desc.BoolParam(
            name="ignoreInputs",
            label="Ignore Inputs",
            description="Do not render the ROPs connected to the inputs of this one.",
            value=False,
        ),
    ]

    outputs = [
        sceneOutput(),
        desc.LiveValue(
            name="outputFile",
            label="Output File",
            description="The file written (for the current frame).",
        ),
    ]

    def execute(self, ctx, inputs):
        hou = ctx.context.session
        rop = hou.node(inputs["rop"])
        if rop is None:
            raise ValueError(f"No node '{inputs['rop']}'.")
        frame = ctx.frame if inputs["loopFrame"] else None
        kwargs = {"ignore_inputs": inputs["ignoreInputs"], "verbose": False}
        if frame is not None:
            kwargs["frame_range"] = (frame, frame)
        ctx.logger.info(f"[Houdini] Render {rop.path()}" + (f" frame {frame}" if frame is not None else ""))
        rop.render(**kwargs)
        errors = rop.errors()
        if errors:
            raise RuntimeError("; ".join(errors))
        return {"sceneOut": hou.hipFile.path(), "outputFile": ropOutputFile(rop, frame)}
