__version__ = "1.0"

from meshroom.core import desc


class InputString(desc.InitNode, desc.InputNode):
    """
    This node is an init node that receives a String.
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
