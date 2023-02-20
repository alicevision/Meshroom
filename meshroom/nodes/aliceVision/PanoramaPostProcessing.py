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
    Post process the panorama
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
            label='Output Folder',
            description='',
            semantic='image',
            value=desc.Node.internalFolder + 'panorama.exr',
            uid=[],
        ),
    ]
