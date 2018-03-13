import sys
from meshroom.core import desc


class PrepareDenseScene(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_prepareDenseScene {allParams}'
    size = desc.DynamicNodeSize('input')

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''SfMData file.''',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        ),
    ]

    outputs = [
        desc.File(
            name='ini',
            label='MVS Configuration file',
            description='',
            value='{cache}/{nodeType}/{uid0}/mvs.ini',
            uid=[],
            group='',  # not a command line arg
        ),

        desc.File(
            name='output',
            label='Output',
            description='''Output folder.''',
            value='{cache}/{nodeType}/{uid0}/',
            uid=[],
        )
    ]
