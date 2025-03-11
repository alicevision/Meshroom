__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

import json

class SfMSurveyInjecting(desc.AVCommandLineNode):

    commandLine = "aliceVision_sfmSurveyInjecting {allParams}"
    size = desc.DynamicNodeSize("input")
    
    category = "Utils"
    documentation = """
Use a JSON file to inject survey measurements inside the SfMData.
"""

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="surveyFilename",
            label="Survey",
            description="Input JSON file containing the survey.",
            value="",
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
            value="{nodeCacheFolder}/sfmData.abc",
        ),
    ]
