# -*- coding: utf-8 -*-

__version__ = "1.0"

from pathlib import Path
from meshroom.core import desc


SCRIPT = Path(__file__).parent / "scripts" / "extractMeshroomSceneParams.py"


class GetMeshroomSceneParams(desc.CommandLineNode):
    """Extract parameters from nodes of another scene.
    The output is a JSON file containing a list of items with the following keys:
    - node: node instance name
    - parameter: parameter path
    - value: extracted parameter value

    For the parameter you can put parameters inside groups and lists too:
    - simple parameter: "paramName"
    - parameter inside a group: "groupParamName.paramName"
    - parameter inside a list: "listParamName[index]"
    """

    category = "Utils"

    pythonExecutable = "python"
    commandLine = ""

    def buildCommandLine(self, chunk):
        node = chunk.node

        # Get request
        requestedParams = []
        for item in node.parameters.value:
            nodeName = item.nodeInstance.value.strip()
            paramPath = item.paramName.value.strip()
            if nodeName and paramPath:
                requestedParams.append(f"{nodeName}:{paramPath}")
        request = ";".join(requestedParams)

        # Build command line
        cmdLine = f"{node.nodeDesc.pythonExecutable} {SCRIPT}"
        cmdLine += f" --scene '{node.scene.value}'"
        cmdLine += f" --request '{request}'"
        cmdLine += f" --output '{node.paramValuesDict.value}'"

        node.nodeDesc.commandLine = cmdLine
        return super().buildCommandLine(chunk)

    inputs = [
        desc.File(
            name="scene",
            description="Meshroom scene.",
            value="",
            exposed=True,
        ),
        desc.ListAttribute(
            name="parameters",
            description="List of node/parameter pairs to extract from the source scene.",
            exposed=True,
            commandLineGroup="",
            elementDesc=desc.GroupAttribute(
                name="parameter",
                exposed=True,
                items=[
                    desc.StringParam(
                        name="nodeInstance",
                        label="Node Instance",
                        description="Node instance name.",
                        value="",
                        exposed=True,
                    ),
                    desc.StringParam(
                        name="paramName",
                        label="Parameter",
                        description="Attribute path to extract (e.g. 'groupName.subParam').",
                        value="",
                        exposed=True,
                    )
                ]
            )
        )
    ]

    outputs = [
        desc.File(
            name="paramValuesDict",
            label="Values JSON",
            description="Path to the JSON file containing the extracted override strings.",
            value="{nodeCacheFolder}/values.json",
        )
    ]
