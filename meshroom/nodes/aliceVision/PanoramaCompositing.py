__version__ = "1.0"

import json
import os

from meshroom.core import desc


class PanoramaCompositing(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaCompositing {allParams}'
    size = desc.DynamicNodeSize('input')

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
            description='Which compositer should be used to blend images:\n'
                        ' * multiband: high quality transition by fusing images by frequency bands\n'
                        ' * replace: debug option with straight transitions\n'
                        ' * alpha: debug option with linear transitions\n',
            value='multiband',
            values=['replace', 'alpha', 'multiband'],
            exclusive=True,
            uid=[0]
        ),
        desc.BoolParam(
            name='useGraphCut',
            label='Use smart seams',
            description='Use a graphcut algorithm to select the seams for better compositing',
            value=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='overlayType',
            label='Overlay Type',
            description='Overlay on top of panorama to analyze transitions:\n'
                        ' * none: no overlay\n'
                        ' * borders: display image borders\n'
                        ' * seams: display transitions between images\n'
                        ' * all: display borders and seams\n',
            value='none',
            values=['none', 'borders', 'seams', 'all'],
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
