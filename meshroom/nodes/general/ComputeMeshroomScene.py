# -*- coding: utf-8 -*-

__version__ = "1.0"

from pathlib import Path
from typing import List, Tuple
import json

from meshroom.core.desc.validators import success
from meshroom.core.desc.validators import error
from meshroom import _MESHROOM_ROOT
from meshroom.core import desc, node

import logging
logger = logging.getLogger(__name__)


_MESHROOM_BATCH = Path(_MESHROOM_ROOT) / "bin" / "meshroom_batch"


def isValidSceneFileValidator(node, _) -> Tuple[bool, List[str]]:
    filePath = Path(node.scene.value)
    errorMessages = []
    if not filePath.exists():
        errorMessages.append(f"{filePath} doesn't exists")
    if filePath.suffix not in ('.mg', '.mgt'):
        errorMessages.append(f"{filePath} should be a .mg or .mgt file")

    if len(errorMessages) > 0:
        return error(errorMessages)
    
    return success()

class ComputeMeshroomScene(desc.CommandLineNode, desc.InputNode):
    """
    Compute or Submits a meshroom scene on the farm.
    """

    pythonExecutable = "python"
    category = "Utils"

    def __getSubmitters():
        from meshroom.core import submitters
        submitterNames = []
        for subName, _ in submitters.items():
            submitterNames.append(subName)
        return submitterNames
    
    SUBMITTERS = __getSubmitters()
    
    def buildCommandLine(self, chunk) -> str:
        cmd = super().buildCommandLine(chunk)
        node = chunk.node
        # ForceCompute
        if node.forceCompute.value == True:
            cmd += " --forceCompute"
        # Compute or Submit
        if node.submit.value:
            cmd += " --submit"
            if node.submitter.value:
                cmd += f" --submitter {node.submitter.value}"
            if node.submitLabel.value:
                cmd += f" --submitLabel \"{node.submitLabel.value}\""
        else:
            cmd += " --compute yes"
        return cmd

    inputs = [
        desc.File(
            name="scene",
            label="Scene",
            description="Meshroom scene.",
            value="",
            validators=[
                isValidSceneFileValidator
            ]
        ),
        desc.BoolParam(
            name="forceCompute",
            label="Force Compute",
            description=(
                "Set True to force compute. If nodes are already computed, the status will"
                "be reset to None and the cache will be deleted."
            ),
            value=True,
        ),
        desc.BoolParam(
            name="submit",
            label="Submit",
            description="Set True to submit, False to compute locally.",
            value=False,
            enabled=len(SUBMITTERS)>0
        ),
        desc.ChoiceParam(
            name="submitter",
            label="Submitter",
            description="Select submitter. An empty string will select the default one.",
            value="",
            values=[""] + SUBMITTERS,
            enabled=lambda node: node.submit.value is True
        ),
        desc.StringParam(
            name="submitLabel",
            label="Submit Label",
            description=(
                "The label that will be set for the submitted job name.\n"
                "An empty string will set a default string: '[Meshroom] {projectName}'.\n"
                "The following strings between brackets can be used as they will be automatically replaced:\n"
                "- projectName: the name of the scene file"
            ),
            value="",
            enabled=len(SUBMITTERS)>0
        ),
        desc.AnySet(
            name="inputs",
            label="Inputs",
            description="All the parameters exposed in the GraphInput of the given Scene file",
            exposed=True
        )        
    ]

    outputs = [
        desc.AnySet(
            name="outputs",
            label="Outputs",
            description="All the parameters exposed in the GraphOutput of the given Scene file",
            exposed=True
        )
    ]


    @staticmethod
    def _clearAnySet(anySet: desc.AnySet):
        inputAttributes = [input for input in anySet.value]
        for input in inputAttributes:
            anySet.removeAttribute(input)

    @staticmethod
    def _updateInputAttributes(node: node.Node, sceneFile: Path, sceneFileNode: dict):

        if sceneFileNode.get('nodeType', None) != 'GraphInput':
            logger.warning('The given scene file should contain a GraphInput')
            return

        exposedAttribute = sceneFileNode.get('inputs', {}).get('exposeds', None)
        if not exposedAttribute:
            logger.warning(f"{sceneFile} should have a GraphInputNode with a exposeds attribute")
            return
        
        for i, attr in enumerate(exposedAttribute.get('children', [])):
            node.inputs.insertAttribute(attr, i)
    
    @staticmethod
    def _updateOutputAttributes(node: node.Node, sceneFile: Path, sceneFileNode: dict):

        if sceneFileNode.get('nodeType', None) != 'GraphOutput':
            logger.warning('The given scene file should contain a GraphOutput')
            return

        exposedAttribute = sceneFileNode.get('inputs', {}).get('exposeds', None)
        if not exposedAttribute:
            logger.warning(f"{sceneFile} should have a GraphOutputNode with a exposeds attribute")
            return
        
        for i, attr in enumerate(exposedAttribute.get('children', [])):

            if attr.get('value', None):
                print(f"Removing {attr.get('value', None)}")
                del attr['value']

            node.outputs.insertAttribute(attr, i)    

    @staticmethod
    def _updateAttributesFromSceneFile(node, sceneFile):
        
        if not sceneFile.exists():
            logger.warning(f"{sceneFile} doesn't exists")
            return
        
        with open(sceneFile, 'r', encoding="utf8") as sceneFileStream:
            sceneFileData = json.load(sceneFileStream)
        
        if not sceneFileData:
            return
        
        for _, sceneFileNode in sceneFileData.get('graph', {}).items():
            ComputeMeshroomScene._updateInputAttributes(node, sceneFile, sceneFileNode)
            ComputeMeshroomScene._updateOutputAttributes(node, sceneFile, sceneFileNode)

    def initialize(self, node, inputs, recursiveInputs):
        
        givenFile = Path(inputs[0])

        if len(inputs) == 1 and givenFile.exists() and givenFile.suffix in ('.mg', '.mgt'):
            giveFilePath = str(givenFile)

            if node.scene.value == giveFilePath:
                return
            
            node.scene.value = giveFilePath

    def onSceneChanged(self, node):

        self._clearAnySet(node.inputs)
        self._updateAttributesFromSceneFile(node=node, 
                                            sceneFile=Path(node.scene.value))

    def buildCommandLine(self, chunk):
        node = chunk.node

        sceneInputs = " ".join([f"GraphInput:exposeds.{inputAttr.name}={inputAttr.value}" for inputAttr in node.inputs.value])
        
        return  f"{node.nodeDesc.pythonExecutable} " + str(_MESHROOM_BATCH) + f" -p {node.scene.value} --save {node.scene.value} --paramOverrides {sceneInputs}"

