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
            name='inputPath',
            label='SfmData',
            description='Input file. Coulb be SfMData file or folder.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='inputJSON',
            label='inputJSON',
            description='Input file. Coulb be SfMData file or folder.',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='method',
            label='method',
            description='Method used for light calibration.',
            values=['brightestPoint', 'whiteSphere'],
            value='brightestPoint',
            exclusive=True,
            uid=[0],
        )
    ]

    outputs = [
        desc.File(
            name='outputFile',
            label='Output json file',
            description='Light information will be written here.',
            value=desc.Node.internalFolder +'/lights.json' ,
            uid=[],
        )
    ]
