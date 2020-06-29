__version__ = "2.0"

from meshroom.core import desc


class LdrToHdrCalibration(desc.CommandLineNode):
    commandLine = 'aliceVision_LdrToHdrCalibration {allParams}'
    size = desc.DynamicNodeSize('input')
    #parallelization = desc.Parallelization(blockSize=40)
    #commandLineRange = '--rangeStart {rangeStart} --rangeSize {rangeBlockSize}'

    documentation = '''
    Calibrate LDR to HDR response curve from samples
'''

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='samples',
            label='Samples folder',
            description='Samples folder',
            value=desc.Node.internalFolder,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='calibrationMethod',
            label='Calibration Method',
            description="Method used for camera calibration \n"
                        " * Linear: Disable the calibration and assumes a linear Camera Response Function. If images are encoded in a known colorspace (like sRGB for JPEG), the images will be automatically converted to linear. \n"
                        " * Debevec: This is the standard method for HDR calibration. \n"
                        " * Grossberg: Based on learned database of cameras, it allows to reduce the CRF to few parameters while keeping all the precision. \n"
                        " * Laguerre: Simple but robust method estimating the minimal number of parameters. \n"
                        " * Robertson: First method for HDR calibration in the literature. \n",
            values=['linear', 'debevec', 'grossberg', 'laguerre'],
            value='debevec',
            exclusive=True,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='calibrationWeight',
            label='Calibration Weight',
            description="Weight function used to calibrate camera response \n"
                        " * default (automatically selected according to the calibrationMethod) \n"
                        " * gaussian \n"
                        " * triangle \n"
                        " * plateau",
            value='default',
            values=['default', 'gaussian', 'triangle', 'plateau'],
            exclusive=True,
            uid=[0],
        ),
        desc.IntParam(
            name='userNbBrackets',
            label='Number of Brackets',
            description='Number of exposure brackets per HDR image (0 for automatic detection).',
            value=0,
            range=(0, 15, 1),
            uid=[0],
            group='user',  # not used directly on the command line
        ),
        desc.IntParam(
            name='nbBrackets',
            label='Automatic Nb Brackets',
            description='Number of exposure brackets used per HDR image. It is detected automatically from input Viewpoints metadata if "userNbBrackets" is 0, else it is equal to "userNbBrackets".',
            value=0,
            range=(0, 10, 1),
            uid=[],
        ),
        desc.BoolParam(
            name='byPass',
            label='bypass convert',
            description="Bypass HDR creation and use the medium bracket as the source for the next steps",
            value=False,
            uid=[0],
            advanced=True,
        ),
        desc.IntParam(
            name='channelQuantizationPower',
            label='Channel Quantization Power',
            description='Quantization level like 8 bits or 10 bits.',
            value=10,
            range=(8, 14, 1),
            uid=[0],
            advanced=True,
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
            name='response',
            label='Output response  File',
            description='Path to the output response file',
            value=desc.Node.internalFolder + 'response.csv',
            uid=[],
        )
    ]