__version__ = "1.0"

import os
from meshroom.core import desc


class ReadEnvVar(desc.InputNode):
    """
    Read a variable from an env
    """

    category = "Other"

    inputs = [
        desc.StringParam(
            name="varname",
            label="Name",
            description="Environment variable name.",
            value="",
        )
    ]

    outputs = [
        desc.StringParam(
            name="varvalue",
            label="Value",
            description="Environment variable value.",
            value="",
        )
    ]

    def update(self, node):
        self.updateOutputs(node)

    def updateOutputs(self, node):
        if node.varname.value:
            node.varvalue.value = os.getenv(node.varname.value, "")
        else:
            node.varvalue.value = ""
