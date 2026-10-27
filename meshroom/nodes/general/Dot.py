__version__ = "1.0"

from meshroom.core import desc


class Dot(desc.DotNode):
    """ Dot node: a pass-through node that forwards the value of its input to its output,
    without any computation. It is only used to organize and re-route connections in the
    graph (re-route long links, avoid crossings, or fan a single output out to many inputs
    through a single anchor point). """

    category = "Utils"
    documentation = """\
A Dot node is a purely organizational, pass-through node: it has exactly one input and one
output, performs no processing, and the data passes through unchanged.

It is drawn as a tiny dot instead of a full node rectangle. Its purpose is to route and tidy
connections: re-route long links, avoid crossings, and fan a single output out to many inputs
through a single anchor point.

The type of the Dot output follows the type of the attribute connected to its input. Any type
of attribute can be connected to the input, and the output can be connected to multiple
downstream attributes of compatible type. The Dot is never computed: it creates no chunk, no
cache folder and no status file, and downstream nodes resolve their values and dependencies
through it exactly as if the upstream attribute was connected directly.
"""

    inputs = [
        desc.DotAttribute(
            name="input",
            label="Input",
            description="The attribute to forward to the output. Connections of any type are accepted.",
        ),
    ]

    outputs = [
        desc.DotAttribute(
            name="output",
            label="Output",
            description="Forwards the value of the input. Its type follows the type of the connected input.",
        ),
    ]
