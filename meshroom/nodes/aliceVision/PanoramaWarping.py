__version__ = "1.0"

import json
import os

from meshroom.core import desc


class PanoramaWarping(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaWarping {allParams}'
    size = desc.DynamicNodeSize('input')
    parallelization = desc.Parallelization(blockSize=5)
    commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    category = 'Panorama HDR'
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
            name='estimateResolution',
            label='Estimate Resolution',
            description='Estimate output panorama resolution automatically based on the input images resolution.',
            value=True,
            uid=[0],
            group=None, # skip group from command line
        ),
        desc.IntParam(
            name='panoramaWidth',
            label='Panorama Width',
            description='Choose the output panorama width (in pixels).',
            value=10000,
            range=(0, 50000, 1000),
            uid=[0],
            enabled=lambda node: (not node.estimateResolution.value),
        ),
        desc.IntParam(
            name='percentUpscale',
            label='Upscale Ratio',
            description='Percentage of upscaled pixels.\n'
                        '\n'
                        'How many percent of the pixels will be upscaled (compared to its original resolution):\n'
                        ' * 0: all pixels will be downscaled\n'
                        ' * 50: on average the input resolution is kept (optimal to reduce over/under-sampling)\n'
                        ' * 100: all pixels will be upscaled\n',
            value=50,
            range=(0, 100, 1),
            enabled=lambda node: (node.estimateResolution.value),
            uid=[0]
        ),
        desc.IntParam(
            name='maxPanoramaWidth',
            label='Max Panorama Width',
            description='Choose the maximal output panorama width (in pixels). Zero means no limit.',
            value=70000,
            range=(0, 100000, 1000),
            uid=[0],
            enabled=lambda node: (node.estimateResolution.value),
        ),
        desc.ChoiceParam(
            name='storageDataType',
            label='Storage Data Type',
            description='Storage image data type:\n'
                        ' * float: Use full floating point (32 bits per channel)\n'
                        ' * half: Use half float (16 bits per channel)\n'
                        ' * halfFinite: Use half float, but clamp values to avoid non-finite values\n'
                        ' * auto: Use half float if all values can fit, else use full float\n',
            value='float',
            values=['float', 'half', 'halfFinite', 'auto'],
            exclusive=True,
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
            label='Output directory',
            description='',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
