__version__ = "1.0"

from meshroom.core import desc


class FileToString(desc.ConversionNode):
    """
    Convert a file path into a string.

    It is automatically inserted when connecting a File attribute to a String attribute.
    """

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="File path to convert.",
            value="",
        ),
    ]

    outputs = [
        desc.StringParam(
            name="output",
            label="Output",
            description="File path as a string.",
            value=None,
        ),
    ]

    def convert(self, node, value):
        return str(value)
