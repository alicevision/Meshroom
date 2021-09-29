__version__ = "1.0"

from meshroom.core import desc

import os.path


class ColorCheckerCorrection(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_colorCheckerCorrection {allParams}'
    size = desc.DynamicNodeSize('input')
    # parallelization = desc.Parallelization(blockSize=40)
    # commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    documentation = '''
(BETA) \\
Performs color calibration from Macbeth color checker chart.

The node assumes all the images to process are sharing the same colorimetric properties.
All the input images will get the same correction.

If multiple color charts are submitted, only the first one will be taken in account.
'''

    inputs = [
        desc.File(
            name='inputData',
            label='Color checker data',
            description='Position and colorimetric data of the color checker',
            value='',
            uid=[0],
        ),
        desc.File(
            name='input',
            label='Input',
            description='SfMData file input, image filenames or regex(es) on the image file path.\nsupported regex: \'#\' matches a single digit, \'@\' one or more digits, \'?\' one character and \'*\' zero or more.',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='extension',
            label='Output File Extension',
            description='Output Image File Extension.',
            value='exr',
            values=['exr', ''],
            exclusive=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='storageDataType',
            label='Storage Data Type for EXR output',
            description='Storage image data type:\n'
                        ' * float: Use full floating point (32 bits per channel)\n'
                        ' * half: Use half float (16 bits per channel)\n'
                        ' * halfFinite: Use half float, but clamp values to avoid non-finite values\n'
                        ' * auto: Use half float if all values can fit, else use full float\n',
            value='float',
            values=['float', 'half', 'halfFinite', 'auto'],
            exclusive=True,
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
