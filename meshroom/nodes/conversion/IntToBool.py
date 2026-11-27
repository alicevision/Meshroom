__version__ = "1.0"

from meshroom.core import desc


class IntToBool(desc.ConversionNode):
    """
    Convert an integer into a boolean (False if 0, True otherwise).

    It is automatically inserted when connecting an Integer attribute to a Boolean attribute.
    """

    lossy = True

    inputs = [
        desc.IntParam(
            name="input",
            label="Input",
            description="Integer value to convert.",
            value=0,
        ),
    ]

    outputs = [
        desc.BoolParam(
            name="output",
            label="Output",
            description="Converted boolean value.",
            value=None,
        ),
    ]

    def convert(self, node, value):
        return bool(value)
