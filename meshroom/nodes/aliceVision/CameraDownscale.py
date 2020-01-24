__version__ = "1.0"

import json
import os

from meshroom.core import desc


class CameraDownscale(desc.CommandLineNode):
    commandLine = 'aliceVision_cameraDownscale {allParams}'
    size = desc.DynamicNodeSize('input')

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description="SfM Data File",
            value='',
            uid=[0],
        ),
        desc.FloatParam(
            name='rescalefactor',
            label='RescaleFactor',
            description='Newsize = rescalefactor * oldsize',
            value=0.5,
            range=(0.0, 1.0, 0.1),
            uid=[0],
            advanced=True,
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='Verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name='outSfMDataFilename',
            label='Output SfMData File',
            description='Path to the output sfmdata file',
            value=desc.Node.internalFolder + 'sfmData.abc',
            uid=[],
        )
    ]
