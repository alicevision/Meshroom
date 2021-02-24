__version__ = "2.0"

import json
import os

from meshroom.core import desc


class PanoramaSeams(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaSeams {allParams}'
    size = desc.DynamicNodeSize('input')
    cpu = desc.Level.INTENSIVE
    ram = desc.Level.INTENSIVE

    category = 'Panorama HDR'
    documentation = '''
Estimate the seams lines between the inputs to provide an optimal compositing in a further node
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
        desc.IntParam(
            name='maxWidth',
            label='Max Resolution',
            description='Maximal resolution for the panorama seams estimation.',
            value=5000,
            range=(0, 100000, 1),
            uid=[0],
        ),
        desc.BoolParam(
            name='useGraphCut',
            label='Use Smart Seams',
            description='Use a graphcut algorithm to optmize seams for better transitions between images.',
            value=True,
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
        )
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output Labels',
            description='',
            value=desc.Node.internalFolder + 'labels.exr',
            uid=[],
        )
    ]
