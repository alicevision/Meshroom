import sys
from meshroom.core import desc


class PrepareDenseScene(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_prepareDenseScene {allParams}'

    input = desc.File(
            label='Input',
            description='''SfMData file.''',
            value='',
            uid=[0],
            isOutput=False,
            )
    mvsConfig = desc.File(
            label='MVS Configuration file',
            description='',
            value='{cache}/{nodeType}/{uid0}/_tmp_scale{scaleValue}/mvs.ini',
            uid=[0],
            isOutput=True,
            group='',  # not a command line arg
            )

    output = desc.File(
            label='Output',
            description='''Output directory.''',
            value='{cache}/{nodeType}/{uid0}/',
            uid=[],
            isOutput=True,
            )
    scale = desc.IntParam(
            label='Scale',
            description='''Image downscale factor.''',
            value=2,
            range=(-sys.maxsize, sys.maxsize, 1),
            uid=[0],
            )
    verboseLevel = desc.ChoiceParam(
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[0],
            )