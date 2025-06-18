__version__ = "1.0"

from meshroom.core import desc


class PluginANodeA(desc.Node):
    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="",
            value="",
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
