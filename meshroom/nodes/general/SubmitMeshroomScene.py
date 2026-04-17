# -*- coding: utf-8 -*-

__version__ = "1.0"

from pathlib import Path

import shutil
import shlex
import logging
import subprocess

import meshroom
from meshroom.core import desc


_MESHROOM_ROOT = Path(meshroom.__file__).parent.parent.as_posix()
_MESHROOM_BATCH = (Path(_MESHROOM_ROOT) / "bin" / "meshroom_batch").as_posix()
PYTHON_EXE = "python"


class SubmitMeshroomScene(desc.CommandLineNode):
    """
    Submits a meshroom scene on the farm.
    """

    category = "Utils"
    commandLine = f"{PYTHON_EXE} {_MESHROOM_BATCH}" + " -p {node.scene.value} --save {node.scene.value}"
    
    def buildCommandLine(self, chunk) -> str:
        cmd = super().buildCommandLine(chunk)
        # Submit
        if chunk.node.submit.value:
            cmd += " --submit"
        else:
            cmd += " --compute yes"
        # ForceCompute
        if chunk.node.forceCompute.value == True:
            cmd += " --forceCompute"
        return cmd

    inputs = [
        desc.File(
            name="scene",
            label="Scene",
            description="Meshroom scene",
            value="",
        ),
        desc.BoolParam(
            name="submit",
            label="Submit",
            description="Set True to submit, False to compute locally",
            value=True,
        ),
        desc.BoolParam(
            name="forceCompute",
            label="Force Compute",
            description=(
                "Set True to force compute. If nodes are already computed, the status will"
                "be reset to None and the cache will be deleted."
            ),
            value=True,
        )
    ]
