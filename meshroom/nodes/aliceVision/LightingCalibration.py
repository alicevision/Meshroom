__version__ = "3.0"

from meshroom.core import desc


class LightingCalibration(desc.CommandLineNode):
    commandLine = 'aliceVision_lightingCalibration {allParams}'
    category = 'Photometry'
    documentation = '''
TODO.
'''

    inputs = [
        desc.File(
            name='inputJSON',
            label='Sphere detection file',
            description='Input file containing spheres centers and radius.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='inputPath',
            label='SfmData',
            description='Input file. Could be SfMData file or folder.',
            value='',
            uid=[0],
        ),
        desc.BoolParam(
            name='saveAsModel',
            label='Save as model',
            description='Check if this calibration file will be used with other datasets',
            value=False,
            uid=[0],
        ),
        desc.ChoiceParam(
            name='method',
            label='Calibration method',
            description='Method used for light calibration. Use brightestPoint for shiny sphere and whiteSphere for white matte sphere',
            values=['brightestPoint', 'whiteSphere'],
            value='brightestPoint',
            exclusive=True,
            uid=[0],
        )
    ]

    outputs = [
        desc.File(
            name='outputFile',
            label='Output light file',
            description='Light information will be written here.',
            value=desc.Node.internalFolder +'/lights.json' ,
            uid=[],
        )
    ]
