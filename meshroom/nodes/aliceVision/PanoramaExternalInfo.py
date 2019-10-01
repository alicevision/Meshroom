__version__ = "1.0"

import json
import os

from meshroom.core import desc


class PanoramaExternalInfo(desc.CommandLineNode):
    commandLine = 'aliceVision_panoramaExternalInfo {allParams}'
    size = desc.DynamicNodeSize('input')

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description="SfM Data File",
            value='',
            uid=[0],
        ),
        desc.File(
            name='config',
            label='Xml Config',
            description="XML Data File",
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
            name='outSfMDataFilename',
            label='Output SfMData File',
            description='Path to the output sfmdata file',
            value=desc.Node.internalFolder + 'sfmData.abc',
            uid=[],
        )
    ]
