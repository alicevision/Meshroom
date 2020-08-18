__version__ = "1.0"

import json
import os

from meshroom.core import desc


class PanoramaWarping(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaWarping {allParams}'
    size = desc.DynamicNodeSize('input')

    parallelization = desc.Parallelization(blockSize=5)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

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
        desc.IntParam(
            name='panoramaWidth',
            label='Panorama Width',
            description='Panorama Width (in pixels).\n'
                        'Set 0 to let the software choose the size automatically, so that on average the input resolution is kept (to limit over/under sampling).',
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
