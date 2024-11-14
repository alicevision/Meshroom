__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

import json

class SfMPoseInjecting(desc.AVCommandLineNode):

    commandLine = "aliceVision_sfmPoseInjecting {allParams}"
    size = desc.DynamicNodeSize("input")
    
    category = "Utils"
    documentation = """
Use a JSON file to inject poses inside the SfMData.
"""

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="posesFilename",
            label="Poses",
            description="Input JSON file containing the poses.",
            value="",
        ),
        desc.ChoiceParam(
            name="rotationFormat",
            label="Rotation Format",
            description="Defines the rotation format for the input poses:\n"
                        " - EulerZXY: Euler rotation in degrees (Y*X*Z)",
            values=["EulerZXY"],
            value="EulerZXY",
        ),
        desc.ChoiceParam(
            name="verboseLevel",
            label="Verbose Level",
            description="Verbosity level (fatal, error, warning, info, debug, trace).",
            values=VERBOSE_LEVEL,
            value="info",
        ),
    ]

    outputs = [
        desc.File(
            name="output",
            label="SfMData",
            description="Path to the output SfM file.",
            value=desc.Node.internalFolder + "sfmData.sfm",
        ),
    ]
