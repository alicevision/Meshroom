__version__ = "1.0"

from meshroom.core import desc


class PluginAInputInitNode(desc.InputNode, desc.InitNode):
    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="",
            value="",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="Output",
            description="",
            value="",
        ),
    ]

    def initialize(self, node, inputs, recursiveInputs):
        if len(inputs) >= 1:
            self.setAttributes(node, {"input": inputs[0]})
