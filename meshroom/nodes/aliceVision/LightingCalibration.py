__version__ = "1.0"

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
            label='SfMData',
            description='Input file. Could be SfMData file or folder.',
            value='',
            uid=[0]
        ),
        desc.File(
            name='inputJSON',
            label='Sphere Detection File',
            description='Input JSON file containing spheres centers and radius.',
            value='',
            uid=[0]
        ),
        desc.BoolParam(
            name='saveAsModel',
            label='Save As Model',
            description='Check if this calibration file will be used with other datasets.',
            value=False,
            uid=[0]
        ),
        desc.ChoiceParam(
            name='method',
            label='Calibration Method',
            description='Method used for light calibration. Use "brightestPoint" for shiny spheres and "whiteSphere" for white matte spheres.',
            values=['brightestPoint', 'whiteSphere'],
            value='brightestPoint',
            exclusive=True,
            uid=[0]
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='Verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[]
        )
    ]

    outputs = [
        desc.File(
            name='outputFile',
            label='Light File',
            description='Light information will be written here.',
            value=desc.Node.internalFolder +'/lights.json' ,
            uid=[]
        )
    ]
