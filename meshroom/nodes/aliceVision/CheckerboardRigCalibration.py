__version__ = "1.0"

import json
import os

from meshroom.core import desc


class CheckerboardRigCalibration(desc.CommandLineNode):
    commandLine = 'aliceVision_checkerboardRigCalibration {allParams}'
    category = 'Other'
    documentation = '''
Calibrate relative pose of camera in the rig using previously detected checkerboards
'''

    inputs = [
        desc.File(
            name='inputSfmData',
            label='First input',
            description="SfM Data File",
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
