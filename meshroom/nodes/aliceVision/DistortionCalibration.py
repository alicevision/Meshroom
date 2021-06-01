__version__ = '2.0'

from meshroom.core import desc


class DistortionCalibration(desc.CommandLineNode):
    commandLine = 'aliceVision_distortionCalibration {allParams}'
    size = desc.DynamicNodeSize('input')

    documentation = '''
    Calibration of a camera/lens couple distortion using a full screen checkerboard
'''

    inputs = [
        desc.File(
            name='input',
            label='SfmData',
            description='SfmData File',
            value='',
            uid=[0],
        ),
        desc.ListAttribute(
            elementDesc=desc.File(
                name='lensGridImage',
                label='Lens Grid Image',
                description='',
                value='',
                uid=[0],
            ),
            name='lensGrid',
            label='Lens Grid Images',
            description='Lens grid images to estimate the optical distortions.',
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
            name='outSfMData',
            label='Output SfmData File',
            description='Path to the output sfmData file',
            value=desc.Node.internalFolder + 'sfmData.sfm',
            uid=[],
        )
    ]
