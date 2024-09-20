__version__ = "1.1"

from meshroom.core import desc
from meshroom.core.utils import VERBOSE_LEVEL

import os.path


class PanoramaPrepareImages(desc.AVCommandLineNode):
    commandLine = 'aliceVision_panoramaPrepareImages {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Panorama HDR'
    documentation = '''
Prepare images for Panorama pipeline: ensures that images orientations are coherent.
'''

    inputs = [
        desc.File(
            name="input",
            label="Input",
            description="SfMData file.",
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
            description="Output SfMData file.",
            value=lambda attr: desc.Node.internalFolder + os.path.basename(attr.node.input.value),
        ),
    ]
