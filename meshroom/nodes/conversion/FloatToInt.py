__version__ = "1.0"

import math

from meshroom.core import desc


class FloatToInt(desc.ConversionNode):
    """
    Convert a floating-point value into an integer.

    It is automatically inserted when connecting a Float attribute to an Integer attribute.
    """

    inputs = [
        desc.FloatParam(
            name="input",
            label="Input",
            description="Floating-point value to convert.",
            value=0.0,
        ),
        desc.ChoiceParam(
            name="mode",
            label="Mode",
            description="Method used to convert the value:\n"
                        " - round: Nearest integer (halfway values are rounded away from zero).\n"
                        " - floor: Largest integer less than or equal to the value.\n"
                        " - ceil: Smallest integer greater than or equal to the value.\n"
                        " - trunc: Integer part of the value (rounded towards zero).",
            values=["round", "floor", "ceil", "trunc"],
            value="round",
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
        mode = node.mode.value
        if mode == "floor":
            return math.floor(value)
        if mode == "ceil":
            return math.ceil(value)
        if mode == "trunc":
            return math.trunc(value)
        # Python's round() uses banker's rounding: round halfway values away from zero instead
        return int(math.copysign(math.floor(abs(value) + 0.5), value))
