__version__ = "1.0"

import json
import os

from meshroom.core import desc


class PanoramaCompositing(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaCompositing {allParams}'
    size = desc.DynamicNodeSize('input')

    parallelization = desc.Parallelization(blockSize=5)
    commandLineRange = '--rangeIteration {rangeIteration} --rangeSize {rangeBlockSize}'
    
    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    documentation = '''
Once the images have been transformed geometrically (in PanoramaWarping),
they have to be fused together in a single panorama image which looks like a single photography.
The Multi-band Blending method provides the best quality. It averages the pixel values using multiple bands in the frequency domain.
Multiple cameras are contributing to the low frequencies and only the best one contributes to the high frequencies.
'''

    inputs = [
        desc.File(
            name='input',
            label='Input SfMData',
            description="Input SfMData.",
            value='',
            uid=[0],
        ),
        desc.File(
            name='warpingFolder',
            label='Warping Folder',
            description="Panorama Warping results",
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='compositerType',
            label='Compositer Type',
            description='Which compositer should be used to blend images:\n'
                        ' * multiband: high quality transition by fusing images by frequency bands\n'
                        ' * replace: debug option with straight transitions\n'
                        ' * alpha: debug option with linear transitions\n',
            value='multiband',
            values=['replace', 'alpha', 'multiband'],
            exclusive=True,
            uid=[0]
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
        desc.File(
            name='customCacheFolder',
            label='Cache Folder',
            description="Temporary cache directory",
            value='',
            uid=[0],
            group='',
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
            name='output',
            label='Output Folder',
            description='',
            value=desc.Node.internalFolder,
            uid=[],
        ),
        desc.File(
            name='cacheFolder',
            label='Cache Folder',
            description='Temporary cache directory',
            value=lambda attr: attr.node.customCacheFolder.value if attr.node.customCacheFolder.value else (desc.Node.internalFolder + 'cache/'),
            uid=[],
        ),
    ]
