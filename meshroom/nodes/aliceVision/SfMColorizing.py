__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

import json

class SfMColorizing(desc.AVCommandLineNode):

    commandLine = "aliceVision_sfmColorizing {allParams}"
    size = desc.DynamicNodeSize("input")
    
    category = "Utils"
    documentation = """
    Colorize the pointcloud of a sfmData
    """

    inputs = [
        desc.File(
            name="input",
            label="SfMData",
            description="Input SfMData file.",
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
            value=desc.Node.internalFolder + "sfmData.abc",
        ),
    ]
