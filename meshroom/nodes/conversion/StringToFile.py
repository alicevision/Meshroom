__version__ = "1.0"

from meshroom.core import desc


class StringToFile(desc.ConversionNode):
    """
    Convert a string into a file path.

    It is automatically inserted when connecting a String attribute to a File attribute.
    """

    inputs = [
        desc.StringParam(
            name="input",
            label="Input",
            description="String to convert.",
            value="",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="String as a file path.",
            value=None,
        ),
    ]

    def convert(self, node, value):
        return str(value)
