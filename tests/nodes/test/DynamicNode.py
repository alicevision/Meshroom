from meshroom.core import desc


class DynamicNode(desc.Node):
    inputs = [
        desc.StringParam(
            name="code",
            label="Python Code",
            value="Python Code",
            exposed=True,
            semantic="multiline"
        ),
        desc.AnySet(
            name="ins",
            label="Custom Inputs",
            description="Custom Inputs",
            exposed=True
        )
    ]

    outputs = [
        desc.AnySet(
            name="outs",
            label="Custom Outputs",
            description="Custom Outputs",
            exposed=True
        )
    ]

    def process(self, node):
        exec(node.code.value)
