__version__ = "1.0"

import json
import os

from meshroom.core import desc


class FisheyeCircle(desc.CommandLineNode):
    commandLine = 'aliceVision_fisheyeCircle {allParams}'
    size = desc.DynamicNodeSize('input')

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description="SfM Data File",
            value='',
            uid=[0],
        ),
        desc.FloatParam(
            name='offsetx',
            label='Center X offset',
            description='Fisheye visibillity circle offset in X (pixels).',
            value=0.0,
            range=(-1000.0, 1000.0, 0.01),
            uid=[0],
        ),
        desc.FloatParam(
            name='offsety',
            label='Center Y offset',
            description='Fisheye visibillity circle offset in Y (pixels).',
            value=0.0,
            range=(-1000.0, 1000.0, 0.01),
            uid=[0],
        ),
        desc.FloatParam(
            name='radius',
            label='Radius',
            description='Fisheye visibillity circle radius (pixels).',
            value=100.0,
            range=(0.0, 100000.0, 0.01),
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
