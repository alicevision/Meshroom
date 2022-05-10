__version__ = "1.0"

import json
import os

from meshroom.core import desc


class CheckerboardDetection(desc.CommandLineNode):
    commandLine = 'aliceVision_checkerboardDetection {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=5)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Other'
    documentation = '''
Compute the image warping for each input image in the panorama coordinate system.
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description="SfM Data File",
            value='',
            uid=[0],
        ),
        desc.BoolParam(
            name='exportDebugImages',
            label='Export Debug Images',
            description='Export Debug Images.',
            value=False,
            uid=[0],
        ),
        desc.BoolParam(
            name='doubleSize',
            label='Double Size',
            description='Double the image size prior to processing.',
            value=False,
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
            label='Output Directory',
            description='',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
