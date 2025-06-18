__version__ = "1.0"

from meshroom.core import desc


class PluginANodeB(desc.Node):
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
            value=1,
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
