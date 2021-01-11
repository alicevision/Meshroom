__version__ = "1.0"

from meshroom.core import desc

import os.path


class ColorCheckerDetection(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_colorCheckerDetection {allParams}'
    size = desc.DynamicNodeSize('input')
    # parallelization = desc.Parallelization(blockSize=40)
    # commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    documentation = '''
TODO
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file input, image filenames or regex(es) on the image file path.\nsupported regex: \'#\' matches a single digit, \'@\' one or more digits, \'?\' one character and \'*\' zero or more.',
            value='',
            uid=[0],
        ),
        desc.BoolParam(
            name='debug',
            label='Debug',
            description='If checked, debug data will be generated',
            value=True,
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output Color Checker Data',
            description='Output colorimetric data extracted from a detected color checker in the images',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
