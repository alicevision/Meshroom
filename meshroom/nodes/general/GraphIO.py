__version__ = "1.0"

from meshroom.core import desc



class GraphInput(desc.InitNode, desc.InputNode):
    """
    """

    inputs = [
        desc.AnySet(
            name="exposeds",
            label="Exposed attributes",
            description="Those attributes are in the scene node",
            exposed=True
        )
    ]


class GraphOutput(desc.Node, desc.OutputNode):
    """
    """

    inputs = [
        desc.AnySet(
            name="exposeds",
            label="Exposed attributes",
            description="Those attributes are in the scene node",
            exposed=True
        )
    ]
