__version__ = "1.0"

from meshroom.core import desc


class PluginBNodeB(desc.Node):
    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="",
            value="",
        ),
        desc.IntParam(
            name="int",
            label="Integer",
            description="",
            value="not an integer",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="",
            value="",
        ),
    ]
