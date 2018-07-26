__version__ = "1.0"

from meshroom.core import desc


class SfMAlignment(desc.CommandLineNode):
    commandLine = 'aliceVision_utils_sfmAlignment {allParams}'
    size = desc.DynamicNodeSize('input')

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''SfMData file .''',
            value='',
            uid=[0],
        ),
        desc.File(
            name='reference',
            label='Reference',
            description='''Path to the scene used as the reference coordinate system.''',
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
            name='output',
            label='Output',
            description='''Aligned SfMData file .''',
            value=desc.Node.internalFolder + 'alignedSfM.abc',
            uid=[],
        ),
    ]
