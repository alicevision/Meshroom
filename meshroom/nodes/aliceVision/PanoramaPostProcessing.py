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
            description='Compression method for output image.',
            value='Auto',
            values=['None', 'Auto', 'RLE', 'ZIP', 'ZIPS', 'PIZ', 'PXR24', 'B44', 'B44A', 'DWAA', 'DWAB'],
            exclusive=True,
            uid=[0],
        ),
        desc.IntParam(
            name='compressionLevel',
            label='Compression Level',
            description='Level of compression relying on the selected compression method.',
            value=0,
            range=(0, 200, 1),
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
