__version__ = "1.0"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

import os.path

class SfMToRig(desc.AVCommandLineNode):
    commandLine = 'aliceVision_sfmToRig {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
Assumes the input SfMData describes a set of cameras capturing a scene at a common time. Transformd the set of cameras into a rig of cameras.
'''

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
            description="Path to the output SfM file (in SfMData format).",
            value=lambda attr: desc.Node.internalFolder + "sfmData.sfm",
        ),
    ]
