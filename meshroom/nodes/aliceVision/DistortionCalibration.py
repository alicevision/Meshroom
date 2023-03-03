__version__ = '3.0'

from meshroom.core import desc


class DistortionCalibration(desc.AVCommandLineNode):
    commandLine = 'aliceVision_distortionCalibration {allParams}'
    size = desc.DynamicNodeSize('input')

    category = 'Other'
    documentation = '''
Calibration of a camera/lens couple distortion using a full screen checkerboard.
'''

    inputs = [
        desc.File(
            name='input',
            label='SfmData',
            description='SfmData File',
            value='',
            uid=[0],
        ),
        desc.File(
            name='checkerboards',
            label='Checkerboards folder',
            description='Folder containing checkerboard JSON files',
            value='',
            uid=[0]
        ),
    ]

    outputs = [
        desc.File(
            name='outSfMData',
            label='SfmData File',
            description='Path to the output sfmData file',
            value=desc.Node.internalFolder + 'sfmData.sfm',
            uid=[],
        )
    ]
