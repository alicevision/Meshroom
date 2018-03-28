import sys
from meshroom.core import desc


class ConvertSfMFormat(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_convertSfMFormat {allParams}'

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''SfMData file.''',
            value='',
            uid=[0],
            ),
        desc.ChoiceParam(
            name='fileExt',
            label='SfM File Format',
            description='''SfM File Format''',
            value='abc',
            values=['abc', 'sfm', 'ply', 'bin', 'json','colmap-txt'],
            exclusive=True,
            uid=[0],
            group='',  # exclude from command line
            ),
        desc.BoolParam(
            name='views',
            label='Views',
            description='''Export views.''',
            value=True,
            uid=[0],
            ),
        desc.BoolParam(
            name='intrinsics',
            label='Intrinsics',
            description='''Export intrinsics.''',
            value=True,
            uid=[0],
            ),
        desc.BoolParam(
            name='extrinsics',
            label='Extrinsics',
            description='''Export extrinsics.''',
            value=True,
            uid=[0],
            ),
        desc.BoolParam(
            name='structure',
            label='Structure',
            description='''Export structure.''',
            value=True,
            uid=[0],
            ),
        desc.BoolParam(
            name='observations',
            label='Observations',
            description='''Export observations.''',
            value=True,
            uid=[0],
            ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='''verbosity level (fatal, error, warning, info, debug, trace).''',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[0],
            ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='''Path to the output SfM Data file.''',
            value='{cache}/{nodeType}/{uid0}/sfm.{fileExtValue}',
            uid=[],
            ),
    ]

