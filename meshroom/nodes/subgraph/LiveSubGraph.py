__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.subgraph import SubGraphError, SubGraphPlan, runPlan
from meshroom.core.subgraph.nodes import (contextParam, graphSource, loopFromValues, loopParams, makeLocal,
                                          subGraphSourceParams, syncSubGraphPorts)
from meshroom.core.subgraph.ports import anySetValues


class LiveSubGraph(desc.LiveNode):
    """
    A subgraph inside a subgraph: runs in the context of its parent (the same session), with its own loop
    (e.g. N iterations of an effect feeding itself, for a fractal). Its GraphInput ports are its inputs
    (`ins`), its GraphOutput ports its outputs (`outs`).
    """
    category = "SubGraph"

    inputs = subGraphSourceParams() + [contextParam()] + loopParams() + [
        desc.AnySet(
            name="ins",
            label="Inputs",
            description="Values given to the GraphInput ports of the subgraph.",
            exposed=True,
        ),
    ]

    outputs = [
        desc.AnySet(
            name="outs",
            label="Outputs",
            description="Values of the GraphOutput ports of the subgraph.",
            exposed=True,
        ),
    ]

    @classmethod
    def initDynamicAttributes(cls, node):
        syncSubGraphPorts(node)

    @classmethod
    def onSubGraphChanged(cls, node):
        syncSubGraphPorts(node)

    @classmethod
    def onTemplateChanged(cls, node):
        syncSubGraphPorts(node)

    @classmethod
    def onMakeLocalClicked(cls, node):
        makeLocal(node)

    def execute(self, ctx, inputs: dict) -> dict:
        source = graphSource(inputs.get("subGraph"), inputs.get("template"))
        if source is None:
            raise SubGraphError("The node has no subgraph (no embedded subgraph nor template).", ctx.nodeName)
        plan = SubGraphPlan.cached(source)
        context = inputs.get("context") or "auto"
        if context != "auto" and context != ctx.context.name:
            raise SubGraphError(f"It needs the '{context}' context, it runs in '{ctx.context.name}'.", ctx.nodeName)
        plan.checkContext(ctx.context.name)
        parentNode = ctx.nodeName
        outputs = runPlan(plan, ctx.child(loopFromValues(inputs)), anySetValues(inputs.get("ins")))
        ctx.nodeName = parentNode
        return {"outs": outputs}
