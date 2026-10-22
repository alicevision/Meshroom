# -*- coding: utf-8 -*-

__version__ = "1.0"

from pathlib import Path
from typing import Callable, List, Tuple

from meshroom.core.attribute import AnySet
from meshroom.core.desc.attribute import Attribute
from meshroom.core.desc.validators import success
from meshroom.core.desc.validators import error
from meshroom.core.graph import loadGraph
from meshroom.core import desc, node

from meshroom import _MESHROOM_ROOT

import logging


logger = logging.getLogger(__name__)


_MESHROOM_BATCH = Path(_MESHROOM_ROOT) / "bin" / "meshroom_batch"


def isValidSceneFileValidator(node, _) -> Tuple[bool, List[str]]:
    filePath = Path(node.scene.value)
    errorMessages = []
    if not filePath.exists():
        errorMessages.append(f"{filePath} does not exist")
    if filePath.suffix not in ('.mg', '.mgt'):
        errorMessages.append(f"{filePath} should be a .mg or .mgt file")

    if len(errorMessages) > 0:
        return error(*errorMessages)
    
    return success()

def flattenAttributes(attributes: list[Attribute], filter: Callable = None) -> list[Attribute]:

    attrs = []
    for attr in attributes:
        if filter and filter(attr):
            continue
        
        if isinstance(attr, AnySet):
            attrs += flattenAttributes(attr.flatStaticChildren)
        else:
            attrs.append(attr)

    return attrs


class ComputeMeshroomScene(desc.CommandLineNode, desc.InputNode):
    """
    Compute or Submits a meshroom scene on the farm.
    """

    pythonExecutable = "python"
    category = "Utils"
    commandLine = "{node.nodeDesc.pythonExecutable} " + str(_MESHROOM_BATCH) + " -p {node.scene.value} --save {node.scene.value}"

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

        sceneInputs = " ".join([f"{attr.name.replace('__','.')}={attr.value}" for attr in flattenAttributes(node.inputs.value)])

        if sceneInputs:
            cmd += f" --paramOverrides {sceneInputs}"

        # Compute or Submit
        if node.submit.value:
            cmd += " --submit"
            if node.submitter.value:
                cmd += f" --submitter {node.submitter.value}"
            if node.submitLabel.value:
                cmd += f" --submitLabel \"{node.submitLabel.value}\""
        else:
            cmd += " --compute yes"

        print(cmd)
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
        desc.BoolParam(
            name="useOnlyGraphIONodes",
            label="Use only GraphIO nodes",
            description="When checked, only the attributes of GraphInput and GraphOutput nodes will be exposed"
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
    def _convertAttributeName(node: node.Node, attribute: Attribute) -> str:
        return f"{node.name}__{attribute.fullName.replace('.', '__')}"

    def initialize(self, node, inputs, recursiveInputs):
        
        if inputs is None or len(inputs) == 0:
            return
        
        givenFile = Path(inputs[0])

        if len(inputs) == 1 and givenFile.exists() and givenFile.suffix in ('.mg', '.mgt'):
            giveFilePath = str(givenFile)

            if node.scene.value == giveFilePath:
                return
            
            node.scene.value = giveFilePath

    def onSceneChanged(self, node):

        self._clearAnySet(node.inputs)
        self._clearAnySet(node.outputs)

        if not node.scene.value:
            return
        
        try:
            gaph = loadGraph(node.scene.value)
        except:
            logger.error('The given scene is not readable by Meshroom')
            return

        for inputNode in gaph.findInputNodes():

            if node.useOnlyGraphIONodes.value is True and inputNode.nodeType != 'GraphInput':
                continue

            for i, attr in enumerate(flattenAttributes(inputNode.getAttributes(), lambda attr: not attr.isInput)):
                attrDesc = attr.asDict()
                attrDesc['name'] = self._convertAttributeName(inputNode, attr)
                node.inputs.insertAttribute(attrDesc, i)

        for outputNode in gaph.findOutputNodes():

            if node.useOnlyGraphIONodes.value is True and outputNode.nodeType != 'GraphOutput':
                continue

            for i, attr in enumerate(flattenAttributes(outputNode.getAttributes())):
                attrDesc = attr.asDict()
                attrDesc['name'] = self._convertAttributeName(outputNode, attr)
                node.outputs.insertAttribute(attrDesc, i)

    def onUseOnlyGraphIONodesChanged(self, node):
        self.onSceneChanged(node)
        

