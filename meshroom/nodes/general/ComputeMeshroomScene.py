# -*- coding: utf-8 -*-

__version__ = "1.0"

from pathlib import Path

import meshroom
from meshroom import _MESHROOM_ROOT
from meshroom.core import desc


_MESHROOM_BATCH = Path(_MESHROOM_ROOT) / "bin" / "meshroom_batch"


class ComputeMeshroomScene(desc.CommandLineNode):
    """
    Compute or Submits a meshroom scene on the farm.
    """

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
    ]
