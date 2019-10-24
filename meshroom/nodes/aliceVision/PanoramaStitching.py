__version__ = "1.0"

import json
import os

from meshroom.core import desc


class PanoramaStitching(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaStitching {allParams}'
    size = desc.DynamicNodeSize('input')

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description="SfM Data File",
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
        desc.IntParam(
            name='panoramaWidth',
            label='Panorama Width',
            description='Panorama width (pixels). 0 For automatic size',
            value=1000,
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
            label='Output Panorama',
            description='',
            value=desc.Node.internalFolder + 'panorama.{outputFileTypeValue}',
            uid=[],
        ),
    ]
