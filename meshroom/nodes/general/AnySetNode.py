__version__ = "1.0"

from meshroom.core import desc


class AnySetNode(desc.InitNode):
    """
    Hold a set of attributes, which can be connected on both sides: to drive the attributes of other nodes,
    or to gather their values.
    GraphInput and GraphOutput nodes added to a graph that already has one become AnySetNode nodes.
    """

    size = desc.StaticNodeSize(0)
    category = "Utils"

    inputs = [
        desc.AnySet(
            name="attributes",
            label="Attributes",
            description="Attributes held by the node.",
            exposed=True
        )
    ]
