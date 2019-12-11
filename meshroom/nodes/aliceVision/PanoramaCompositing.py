__version__ = "1.0"

import json
import os

from meshroom.core import desc


class PanoramaCompositing(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaCompositing {allParams}'
    size = desc.DynamicNodeSize('input')

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description="Panorama Warping result",
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='outputFileType',
            label='Output File Type',
            description='Output file type for the undistorted images.',
            value='exr',
            values=['jpg', 'png', 'tif', 'exr'],
            exclusive=True,
            uid=[0],
            group='', # not part of allParams, as this is not a parameter for the command line
        ),
        desc.BoolParam(
            name='multiband',
            label='Use Multiband',
            description='Use multi band algorithm for compositing',
            value=True,
            uid=[0],
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
            label='Output Panorama',
            description='',
            value=desc.Node.internalFolder + 'panorama.{outputFileTypeValue}',
            uid=[],
        ),
    ]
