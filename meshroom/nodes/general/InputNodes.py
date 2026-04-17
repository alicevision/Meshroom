__version__ = "1.0"

from pathlib import Path
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


class InputString(desc.InputNode, desc.InitNode):
    """
    This node is an input node that receives a String.
    """

    size = desc.StaticNodeSize(0)
    category = "Other"

    inputs = [
        desc.StringParam(
            name="string",
            label="Input String",
            description="A string.",
            value="",
            exposed=True
        )
    ]


class InputInt(desc.InputNode, desc.InitNode):
    """
    This node is an input node that receives a String.
    """

    category = "Other"

    inputs = [
        desc.IntParam(
            name="integer",
            label="Input Integer",
            description="An integer.",
            value=0,
            exposed=True
        )
    ]


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


class GetParentFolder(desc.Node):
    """ Get the parent folder """
    
    category = "Other"

    inputs = [
        desc.File(
            name="file",
            label="File",
            description="File or Folder.",
            exposed=True,
            value=""
        ),
    ]

    outputs = [
        desc.File(
            name="folder",
            label="Folder",
            description="Parent folder.",
            value=None,
        )
    ]

    def process(self, node):
        path = node.file.value
        if path:
            path = Path(path)
            if path.exists():
                node.folder.value = str(Path(path).parent)
                return
        node.folder.value = ""
