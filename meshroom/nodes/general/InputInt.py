__version__ = "1.0"

from meshroom.core import desc


class InputInt(desc.InputNode, desc.InitNode):
    """
    This node is an input node that receives a String.
    """

    category = "Other"

    inputs = [
        desc.IntParam(
            name="integer",
            label="Input Integer",
            description="An integer.",
            value=0,
            exposed=True
        )
    ]
