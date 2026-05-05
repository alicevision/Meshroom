from meshroom.core import desc


class DynamicInputsNode(desc.Node):
    """Test node exposing a DynamicAttribute for unit testing."""

    inputs = [
        desc.File(
            name="staticInput",
            label="Static Input",
            description="A regular static file input",
            value="",
        ),
        desc.DynamicAttribute(
            name="dynInputs",
            description="Dynamic inputs of any type",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="",
            value="{nodeCacheFolder}/out.txt",
        ),
    ]
