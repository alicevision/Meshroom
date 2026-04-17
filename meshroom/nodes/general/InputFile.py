__version__ = "1.0"

import logging
import os

from meshroom.core import desc

class InputFile(desc.InputNode, desc.InitNode):
    """
This node is an input node that receives a File.
"""
    category = "Other"

    inputs = [
        desc.File(
            name="inputFile",
            label="Input File",
            description="A file or folder to use as the input.",
            value="",
        )
    ]

    def initialize(self, node, inputs, recursiveInputs):
        self.resetAttributes(node, ["inputFile"])

        if len(inputs) >= 1:
            if os.path.isfile(inputs[0]) or os.path.isdir(inputs[0]):
                self.setAttributes(node, {"inputFile": inputs[0]})

                if len(inputs) > 1:
                    logging.warning(f"Several inputs were provided ({inputs}).")
                    logging.warning(f"Only the first one ({inputs[0]}) will be used.")
            else:
                raise RuntimeError(f"{inputs[0]} is not a valid file or directory.")

        elif len(recursiveInputs) >= 1:
            if os.path.isfile(recursiveInputs[0]) or os.path.isdir(recursiveInputs[0]):
                self.setAttributes(node, {"inputFile": recursiveInputs[0]})

                if len(recursiveInputs) > 1:
                    logging.warning(f"Several recursive inputs were provided ({recursiveInputs}).")
                    logging.warning(f"Only the first valid one ({recursiveInputs[0]}) will be used.")

            else:
                raise RuntimeError(f"{recursiveInputs[0]} is not a valid file or directory.")

        else:
            raise RuntimeError("No file or directory has been set for 'inputFile'.")
