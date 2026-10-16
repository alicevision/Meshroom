__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.subgraph.nodes import isFrameLoop, portSpecParam, syncSpecPorts, watchSpecPorts
from meshroom.core.subgraph.ports import parsePortSpec


class GraphInput(desc.LiveNode):
    """
    Entry of a subgraph: its ports output the values given to the subgraph (the inputs of the SubGraph
    node, or of meshroom.subgraph.run). Add a port by connecting its "Ports" to an input, rename it or
    change its label like any AnySet child; the inputs of the SubGraph node follow.
    It also outputs the loop state: the iteration (count loop), the frame and the frame range (frame range loop).
    A subgraph has at most one GraphInput node.
    """
    category = "SubGraph"
    subGraphRole = "input"

    inputs = [
        portSpecParam(),
        desc.StringParam(
            name="loopMode",
            label="Loop Mode",
            description="Loop of the node running the subgraph (set when entering it): shows the matching outputs.",
            value="none",
            invalidate=False,
            advanced=True,
            visible=False,
        ),
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
            description="Iteration of the count loop (0 for the first one).",
            enabled=lambda node: node.loopMode.value == "count",
        ),
        desc.LiveValue(
            name="frame",
            label="Frame",
            description="Current frame of the frame range loop.",
            enabled=lambda node: isFrameLoop(node.loopMode.value),
        ),
        desc.LiveValue(
            name="frameStart",
            label="Frame Start",
            description="First frame of the frame range.",
            enabled=lambda node: isFrameLoop(node.loopMode.value),
        ),
        desc.LiveValue(
            name="frameEnd",
            label="Frame End",
            description="Last frame of the frame range.",
            enabled=lambda node: isFrameLoop(node.loopMode.value),
        ),
    ]

    @classmethod
    def ports(cls, inputs: dict):
        """ The (name, type, label) of the ports, from the serialized or resolved input values. """
        return parsePortSpec(inputs.get("portSpec", ""))

    @classmethod
    def portNames(cls, inputs: dict):
        return [port[0] for port in cls.ports(inputs)]

    @classmethod
    def initDynamicAttributes(cls, node):
        watchSpecPorts(node, "portSpec", "ports")

    @classmethod
    def onPortSpecChanged(cls, node):
        syncSpecPorts(node, "portSpec", "ports")

    def executeInput(self, ctx, values: dict, inputs: dict) -> dict:
        """ The outputs of the node in a run: the values given to the subgraph for its ports, and the loop state. """
        ports = {}
        for name in self.portNames(values):
            if name not in inputs:
                ctx.logger.debug(f"[SubGraph] No value given for the input port '{name}'.")
            ports[name] = inputs.get(name)
        isFrames = ctx.loop.mode == "frames"
        return {
            "ports": ports,
            "iteration": ctx.iteration,
            "frame": ctx.frame,
            "frameStart": ctx.loop.first if isFrames else None,
            "frameEnd": ctx.loop.last if isFrames else None,
        }

    def execute(self, ctx, inputs: dict) -> dict:
        return self.executeInput(ctx, inputs, {})
