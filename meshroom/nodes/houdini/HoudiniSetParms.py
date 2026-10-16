__version__ = "1.0"

from meshroom.core import desc

from meshroom.core.subgraph.houdini import parseParmLines, sceneInput, sceneOutput, setParm


class HoudiniSetParms(desc.LiveNode):
    """
    Sets parameters of the Houdini scene:
    - one per line in Parameters: "/obj/geo1/xform1/t = (0, 1, 0)", "/out/mantra1/vm_picture = $HIP/render/$F4.exr"
      (a Python literal or a text), "/obj/geo1/xform1/ry := $F * 2" (an HScript expression);
    - and/or one parameter from a connected value: Parameter Path and Value.
    """
    category = "Houdini"
    context = "houdini"

    inputs = [
        sceneInput(),
        desc.StringParam(
            name="parms",
            label="Parameters",
            description="One per line: 'path/parm = value' or 'path/parm := expression'.",
            value="",
            semantic="multiline",
        ),
        desc.StringParam(
            name="parmPath",
            label="Parameter Path",
            description="Full path of a parameter set to Value (e.g. /obj/geo1/xform1/scale).",
            value="",
        ),
        desc.LiveValue(
            name="value",
            label="Value",
            description="Value of the parameter Parameter Path (a list / tuple sets a parameter tuple).",
        ),
    ]

    outputs = [
        sceneOutput(),
    ]

    def execute(self, ctx, inputs):
        hou = ctx.context.session
        for path, value, isExpression in parseParmLines(inputs["parms"]):
            setParm(hou, path, value, isExpression)
        if inputs["parmPath"]:
            setParm(hou, inputs["parmPath"], inputs["value"])
        return {"sceneOut": hou.hipFile.path()}
