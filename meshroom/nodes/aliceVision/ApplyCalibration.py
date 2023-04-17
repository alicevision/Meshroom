__version__ = "1.0"

from meshroom.core import desc

class ApplyCalibration(desc.AVCommandLineNode):
    commandLine = 'aliceVision_applyCalibration {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Utils'
    documentation = '''
Overwrite intrinsics with a calibrated intrinsic.
'''

    inputs = [
        desc.File(
            name='input',
            label='Input SfMData',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='calibration',
            label='Calibration',
            description='Calibration SfMData file.',
            value='',
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='SfMData File.',
            description='Path to the output sfmData file.',
            value=desc.Node.internalFolder + 'sfmData.sfm',
            uid=[],
        ),
    ]
