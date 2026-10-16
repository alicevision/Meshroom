__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.subgraph.nodes import portSpecParam, syncSpecPorts
from meshroom.core.subgraph.ports import anySetValues, parsePortSpec


class GraphOutput(desc.LiveNode):
    """
    Exit of a subgraph: the values connected to its ports are the outputs of the subgraph (the outputs
    of the SubGraph node, or the result of meshroom.subgraph.run). A subgraph has at most one GraphOutput node.
    """
    category = "SubGraph"
    subGraphRole = "output"

    inputs = [
        portSpecParam(),
        desc.AnySet(
            name="ports",
            label="Ports",
            description="The values returned by the subgraph.",
            exposed=True,
        ),
    ]

    outputs = []

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

    def collectOutputs(self, values: dict) -> dict:
        """ {port name: value} of the ports, from the resolved input values of the node. """
        connected = anySetValues(values.get("ports"))
        return {name: connected.get(name) for name in self.portNames(values)}

    def execute(self, ctx, inputs: dict) -> dict:
        return {}
