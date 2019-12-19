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
        desc.ChoiceParam(
            name='compositerType',
            label='Compositer Type',
            description='Which compositer should be used to blend images',
            value='multiband',
            values=['replace', 'alpha', 'multiband'],
            exclusive=True,
            uid=[0]
        ),
        desc.ChoiceParam(
            name='overlayType',
            label='Overlay Type',
            description='Which overlay to display on top of panorama for debug',
            value='none',
            values=['none', 'borders', 'seams'],
            exclusive=True,
            advanced=True,
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
