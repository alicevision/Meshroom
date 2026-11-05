__version__ = "1.0"

from meshroom.core import desc


class GraphInput(desc.InitNode, desc.InputNode):
    """
    Expose attributes as the inputs of the scene.
    When the scene is computed by another graph (e.g. with ComputeMeshroomScene), these attributes can be set from it.

    Connect the "Exposed attributes" pin to the input attributes of other nodes to create one graph input per connection.
    Its attributes are the entry points of the graph: they cannot be connected as destination.
    """

    def __init_subclass__(cls, **kwargs):
        # Standard node identifying the inputs of a graph by its node type
        raise TypeError(f"'{cls.__name__}': GraphInput is a standard Meshroom node and cannot be subclassed.")

    size = desc.StaticNodeSize(0)
    category = "Utils"

    inputs = [
        desc.AnySet(
            name="exposeds",
            label="Exposed attributes",
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

    def __init_subclass__(cls, **kwargs):
        # Standard node identifying the outputs of a graph by its node type
        raise TypeError(f"'{cls.__name__}': GraphOutput is a standard Meshroom node and cannot be subclassed.")

    size = desc.StaticNodeSize(0)
    category = "Utils"

    inputs = [
        desc.AnySet(
            name="exposeds",
            label="Exposed attributes",
            description="Attributes exposed as the outputs of the scene.",
            exposed=True
        )
    ]
