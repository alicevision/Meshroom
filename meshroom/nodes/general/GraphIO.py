__version__ = "1.0"

from meshroom.core import desc


class GraphInput(desc.InitNode, desc.InputNode):
    """
    Expose attributes as the inputs of the scene.
    When the scene is computed by another graph (e.g. with ComputeMeshroomScene), these attributes can be set from it.
    """

    size = desc.StaticNodeSize(0)
    category = "Utils"

    inputs = [
        desc.AnySet(
            name="in",
            label="Incoming attributes",
            description="Attributes exposed as the inputs of the scene.",
            exposed=True
        )
    ]


class GraphOutput(desc.InitNode):
    """
    Expose attributes as the outputs of the scene.
    When the scene is computed by another graph (e.g. with ComputeMeshroomScene), these attributes can be read from it.

    An InitNode, as it has nothing to compute. Not an OutputNode, as output nodes are removed from the graphs
    created from a template.
    """

    size = desc.StaticNodeSize(0)
    category = "Utils"

    inputs = [
        desc.AnySet(
            name="out",
            label="Outcoming attributes",
            description="Attributes exposed as the outputs of the scene.",
            exposed=True
        )
    ]
