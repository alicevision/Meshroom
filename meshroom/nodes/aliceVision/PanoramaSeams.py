__version__ = "2.0"

import json
import os

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL


class PanoramaSeams(desc.AVCommandLineNode):
    commandLine = 'aliceVision_panoramaSeams {allParams}'
    size = desc.DynamicNodeSize('input')
    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    category = 'Panorama HDR'
    documentation = '''
Estimate the seams lines between the inputs to provide an optimal compositing in a further node
'''

    inputs = [
        desc.File(
            name="input",
            label="Input SfMData",
            description="Input SfMData file.",
            value="",
        ),
        desc.File(
            name="warpingFolder",
            label="Warping Folder",
            description="Panorama warping results.",
            value="",
        ),
        desc.IntParam(
            name="maxWidth",
            label="Max Resolution",
            description="Maximal resolution for the panorama seams estimation.",
            value=5000,
            range=(0, 100000, 1),
        ),
        desc.BoolParam(
            name="useGraphCut",
            label="Use Smart Seams",
            description="Use a graphcut algorithm to optimize seams for better transitions between images.",
            value=True,
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
            label="Labels",
            description="",
            semantic="image",
            value=desc.Node.internalFolder + "labels.exr",
        ),
        desc.File(
            name="outputSfm",
            label="Output SfMData File",
            description="Path to the output SfMData file.",
            value=desc.Node.internalFolder + "panorama.sfm",
        ),
    ]
