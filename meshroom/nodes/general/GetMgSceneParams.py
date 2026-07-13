# -*- coding: utf-8 -*-

__version__ = "1.0"

import shlex
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
        cmdLine = f"{node.nodeDesc.pythonExecutable} {SCRIPT.as_posix()}"
        cmdLine += f" --scene {shlex.quote(node.scene.value)}"
        cmdLine += f" --request {shlex.quote(request)}"
        cmdLine += f" --output {shlex.quote(node.paramValuesDict.value)}"
        
        if node.advanced.failOnMissingScene.value == True:
            cmdLine += " --failOnMissingScene"
        if node.advanced.failOnMissingParams.value == True:
            cmdLine += " --failOnMissingParams"

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
        ),
        desc.GroupAttribute(
            name="advanced",
            items=[
                desc.BoolParam(
                    name="failOnMissingScene",
                    description="Fail if the scene doesn't exist.",
                    value=True,
                    invalidate=False
                ),
                desc.BoolParam(
                    name="failOnMissingParams",
                    description="Fail if we don't find one or several params inside the scene.",
                    value=True,
                    invalidate=False
                ),
            ],
            advanced=True,
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
