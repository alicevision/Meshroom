__version__ = "1.0"

from meshroom.core import desc

import os.path


class ColorCheckerCorrection(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_colorCheckerCorrection {allParams}'
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
        desc.File(
            name='inputColorData',
            label='Input Color Data',
            description='Input colorimetric data extracted from a detected color checker in the images',
            value='',
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name='outSfMData',
            label='Output sfmData',
            description='Output sfmData.',
            value=lambda attr: (desc.Node.internalFolder + os.path.basename(attr.node.input.value)) if (os.path.splitext(attr.node.input.value)[1] in ['.abc', '.sfm']) else '',
            uid=[],
            group='',  # do not export on the command line
        ),
        desc.File(
            name='output',
            label='Output Folder',
            description='Output Images Folder.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
