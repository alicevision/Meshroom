__version__ = "1.0"

import json
import os

from meshroom.core import desc


class PanoramaWarping(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaWarping {allParams}'
    size = desc.DynamicNodeSize('input')

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description="SfM Data File",
            value='',
            uid=[0],
        ),
        desc.IntParam(
            name='panoramaWidth',
            label='Panorama Width',
            description='Panorama width (pixels). 0 For automatic size',
            value=10000,
            range=(0, 50000, 1000),
            uid=[0]
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
            name='output',
            label='Output directory',
            description='',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
