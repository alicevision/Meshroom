__version__ = "1.0"

from meshroom.core import desc


class IntToFloat(desc.ConversionNode):
    """
    Convert an integer into a floating-point value.

    It is automatically inserted when connecting an Integer attribute to a Float attribute.
    """

    inputs = [
        desc.IntParam(
            name="input",
            label="Input",
            description="Integer value to convert.",
            value=0,
        ),
    ]

    outputs = [
        desc.FloatParam(
            name="output",
            label="Output",
            description="Converted floating-point value.",
            value=None,
        ),
    ]

    def convert(self, node, value):
        return float(value)
