__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.subgraph.nodes import portSpecParam, syncSpecPorts
from meshroom.core.subgraph.ports import parsePortSpec


class GraphInput(desc.LiveNode):
    """
    Entry of a subgraph: its ports output the values given to the subgraph (the inputs of the SubGraph
    node, or of meshroom.subgraph.run). It also outputs the loop state: the iteration and the frame.
    A subgraph has at most one GraphInput node.
    """
    category = "SubGraph"
    subGraphRole = "input"

    inputs = [
        portSpecParam(),
    ]

    outputs = [
        desc.AnySet(
            name="ports",
            label="Ports",
            description="The values given to the subgraph.",
            exposed=True,
        ),
        desc.LiveValue(
            name="iteration",
            label="Iteration",
            description="Iteration of the loop of the subgraph (0 for the first one).",
        ),
        desc.LiveValue(
            name="frame",
            label="Frame",
            description="Frame of a frame loop (None outside of a frame loop).",
        ),
    ]

    @classmethod
    def ports(cls, inputs: dict):
        """ The (name, type) of the ports, from the serialized or resolved input values. """
        return parsePortSpec(inputs.get("portSpec", ""))

    @classmethod
    def portNames(cls, inputs: dict):
        return [name for name, _ in cls.ports(inputs)]

    @classmethod
    def initDynamicAttributes(cls, node):
        syncSpecPorts(node, "portSpec", "ports")

    @classmethod
    def onPortSpecChanged(cls, node):
        syncSpecPorts(node, "portSpec", "ports")

    def executeInput(self, ctx, values: dict, inputs: dict) -> dict:
        """ The outputs of the node in a run: the values given to the subgraph for its ports. """
        ports = {}
        for name in self.portNames(values):
            if name not in inputs:
                ctx.logger.debug(f"[SubGraph] No value given for the input port '{name}'.")
            ports[name] = inputs.get(name)
        return {"ports": ports, "iteration": ctx.iteration, "frame": ctx.frame}

    def execute(self, ctx, inputs: dict) -> dict:
        return self.executeInput(ctx, inputs, {})
