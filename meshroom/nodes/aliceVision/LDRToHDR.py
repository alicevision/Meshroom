__version__ = "1.0"

import json
import os

from meshroom.core import desc


class DividedInputNodeSize(desc.DynamicNodeSize):
    """
    The LDR2HDR will reduce the amount of views in the SfMData.
    This class converts the number of LDR input views into the number of HDR output views.
    """
    def __init__(self, param, divParam):
        super(DividedInputNodeSize, self).__init__(param)
        self._divParam = divParam
    def computeSize(self, node):
        s = super(DividedInputNodeSize, self).computeSize(node)
        divParam = node.attribute(self._divParam)
        return s / divParam.value


class LDRToHDR(desc.CommandLineNode):
    commandLine = 'aliceVision_convertLDRToHDR {allParams}'
    size = DividedInputNodeSize('input', 'groupSize')

    inputs = [
        desc.File(
            name='input',
            label='Input',
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
        desc.IntParam(
            name='groupSize',
            label='Exposure bracket count',
            description='Number of exposure brackets used per HDR image',
            value=3,
            range=(0, 10, 1),
            uid=[0]
        ),
        desc.FloatParam(
            name='expandDynamicRange',
            label='Expand Dynamic Range',
            description='float value between 0 and 1 to correct clamped high values in dynamic range: use 0 for no correction, 0.5 for interior lighting and 1 for outdoor lighting.',
            value=1.0,
            range=(0.0, 1.0, 0.01),
            uid=[0],
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
