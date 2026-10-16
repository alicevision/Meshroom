__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.subgraph.nodes import portSpecParam, syncSpecPorts, watchSpecPorts
from meshroom.core.subgraph.ports import anySetValues


class LiveScript(desc.LiveNode):
    """
    Runs Python code in the context of the subgraph (e.g. the hou module in Houdini).
    The code reads `ins` (dict of the input values), `ctx` (the run context: ctx.frame, ctx.iteration,
    ctx.variables, ctx.context.session...) and fills `outs` (dict of the output values).
    """
    category = "SubGraph"

    inputs = [
        desc.StringParam(
            name="code",
            label="Code",
            description="Python code: reads ins, ctx; fills outs.",
            value="outs.update(ins)",
            semantic="multiline",
        ),
        portSpecParam("inSpec", "Input Ports"),
        portSpecParam("outSpec", "Output Ports"),
        desc.AnySet(
            name="ins",
            label="Inputs",
            description="Input values of the code.",
            exposed=True,
        ),
    ]

    outputs = [
        desc.AnySet(
            name="outs",
            label="Outputs",
            description="Values set by the code.",
            exposed=True,
        ),
    ]

    @classmethod
    def initDynamicAttributes(cls, node):
        watchSpecPorts(node, "inSpec", "ins")
        watchSpecPorts(node, "outSpec", "outs")

    @classmethod
    def onInSpecChanged(cls, node):
        syncSpecPorts(node, "inSpec", "ins")

    @classmethod
    def onOutSpecChanged(cls, node):
        syncSpecPorts(node, "outSpec", "outs")

    def execute(self, ctx, inputs: dict) -> dict:
        outs = {}
        namespace = {"ins": anySetValues(inputs.get("ins")), "outs": outs, "ctx": ctx,
                     "session": ctx.context.session}
        exec(compile(inputs.get("code") or "", f"<{ctx.nodeName}>", "exec"), namespace)
        return {"outs": outs}
