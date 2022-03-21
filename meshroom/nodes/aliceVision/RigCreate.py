__version__ = "1.0"

import json
import os

from meshroom.core import desc


class RigCreate(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_rigCreate {allParams}'
    category = 'Other'
    documentation = '''
Create a rig from multiple input sfm files.
No modification is done on the data. Rig calibration is not performed here.
'''

    inputs = [
        desc.File(
            name='inputSfmData1',
            label='First input',
            description="First SfM Data File",
            value='',
            uid=[0],
        ),
        desc.File(
            name='inputSfmData2',
            label='Second input',
            description="Second SfM Data File",
            value='',
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
            label='Output SfMData File',
            description='SfMData file.',
            value=desc.Node.internalFolder + 'rig.sfm',
            uid=[],
        ),
    ]
