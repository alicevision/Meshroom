__version__ = "1.0"

from meshroom.core import desc


class InputString(desc.InputNode, desc.InitNode):
    """
    This node is an input node that receives a String.
    """

    size = desc.StaticNodeSize(0)
    category = "Other"

    inputs = [
        desc.StringParam(
            name="string",
            label="Input String",
            description="A string.",
            value="",
            exposed=True
        )
    ]
