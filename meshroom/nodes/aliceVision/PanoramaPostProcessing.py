__version__ = "1.0"

import json
import os

from meshroom.core import desc


class PanoramaPostProcessing(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaPostProcessing {allParams}'
    cpu = desc.Level.NORMAL
    ram = desc.Level.INTENSIVE

    category = 'Panorama HDR'
    documentation = '''
Post process the panorama.
'''

    inputs = [
        desc.File(
            name='inputPanorama',
            label='Input Panorama',
            description="Input Panorama.",
            value='',
            uid=[0],
        ),
        desc.BoolParam(
            name='fillHoles',
            label='Use fill holes algorithm',
            description='Fill the non attributed pixels with push pull algorithm.',
            value=False,
            uid=[0],
        ),
        desc.IntParam(
            name='previewSize',
            label='Panorama Preview Width',
            description='The width (in pixels) of the output panorama preview.',
            value=1000,
            range=(0, 5000, 100),
            uid=[0]
        ),
        desc.ChoiceParam(
            name='outputColorSpace',
            label='Output Color Space',
            description='Allows you to choose the color space of the output image.',
            value='Linear',
            values=['sRGB', 'rec709', 'Linear', 'ACES2065-1', 'ACEScg'],
            exclusive=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='compressionMethod',
            label='Compression Method',
            description='Compression method for output EXR image.',
            value='auto',
            values=['none', 'auto', 'rle', 'zip', 'zips', 'piz', 'pxr24', 'b44', 'b44a', 'dwaa', 'dwab'],
            exclusive=True,
            uid=[0],
        ),
        desc.IntParam(
            name='compressionLevel',
            label='Compression Level',
            description='Level of compression for output EXR image, range depends on method used.\n'
                        'For zip/zips methods, values must be between 1 and 9.\n'
                        'A value of 0 will be ignored, default value for the selected method will be used.',
            value=0,
            range=(0, 500, 1),
            uid=[0],
            enabled=lambda node: node.compressionMethod.value in ['dwaa', 'dwab', 'zip', 'zips']
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
            name='outputPanorama',
            label='Output Panorama',
            description='Generated panorama in EXR format.',
            semantic='image',
            value=desc.Node.internalFolder + 'panorama.exr',
            uid=[],
        ),
        desc.File(
            name='outputPanoramaPreview',
            label='Output Panorama Preview',
            description='Preview of the generated panorama in JPG format.',
            semantic='image',
            value=desc.Node.internalFolder + 'panoramaPreview.jpg',
            uid=[],
        ),
    ]
