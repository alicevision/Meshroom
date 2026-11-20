__version__ = "1.0"

from meshroom.core import desc


class BoolToInt(desc.ConversionNode):
    """
    Convert a boolean into an integer (1 if True, 0 otherwise).

    It is automatically inserted when connecting a Boolean attribute to an Integer attribute.
    """

    inputs = [
        desc.BoolParam(
            name="input",
            label="Input",
            description="Boolean value to convert.",
            value=False,
        ),
    ]

    outputs = [
        desc.IntParam(
            name="output",
            label="Output",
            description="Converted integer value.",
            value=None,
        ),
    ]

    def convert(self, node, value):
        return int(value)
