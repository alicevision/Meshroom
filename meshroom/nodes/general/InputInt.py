__version__ = "1.0"

from meshroom.core import desc


class InputInt(desc.InitNode, desc.InputNode):
    """
    This node is an init node that receives an Integer.
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


class Input_Int2(desc.InitNode, desc.InputNode):
    """
    This node is an init node that receives an Integer.
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

class Input_Int_3(desc.InitNode, desc.InputNode):
    """
    This node is an init node that receives an Integer.
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
