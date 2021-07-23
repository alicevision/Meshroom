__version__ = "1.1"

from meshroom.core import desc

import os.path


class PanoramaPrepareImages(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaPrepareImages {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Panorama HDR'
    documentation = '''
Prepare images for Panorama pipeline: ensures that images orientations are coherent.
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output sfmData',
            description='Output sfmData.',
            value=lambda attr: desc.Node.internalFolder + os.path.basename(attr.node.input.value),
            uid=[],
        ),
    ]
