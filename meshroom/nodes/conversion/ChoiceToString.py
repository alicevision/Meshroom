__version__ = "1.0"

from meshroom.core import desc


class ChoiceToString(desc.ConversionNode):
    """
    Convert the selected value(s) of a choice into a string.

    It is automatically inserted when connecting a Choice attribute to a String attribute.
    """

    inputs = [
        desc.ChoiceParam(
            name="input",
            label="Input",
            description="Choice to convert.",
            value="",
            values=[],
        ),
    ]

    outputs = [
        desc.StringParam(
            name="output",
            label="Output",
            description="Selected value, or comma-separated selected values for a non-exclusive choice.",
            value=None,
        ),
    ]

    def convert(self, node, value):
        return ",".join(str(v) for v in value) if isinstance(value, (list, tuple)) else str(value)
