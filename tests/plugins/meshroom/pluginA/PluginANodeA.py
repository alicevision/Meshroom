__version__ = "1.0"

import time

from meshroom.core import desc


class PluginANodeA(desc.Node):
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
            value=None,
        ),
    ]

    def process(self, node):
        time.sleep(3)  # Simulates a long process
        node.output.value = node.input.value + "_value"