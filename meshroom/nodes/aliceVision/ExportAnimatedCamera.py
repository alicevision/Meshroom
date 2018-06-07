from meshroom.core import desc


class ExportAnimatedCamera(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_exportAnimatedCamera {allParams}'

    inputs = [
        desc.File(
            name='input',
            label='Input SfMData',
            description='SfMData file containing a complete SfM.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='filter',
            label='SfMData Filter',
            description='A SfMData file use as filter.',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='Verbosity level (fatal, error, warning, info, debug, trace).',
            value='info',
            values=['fatal', 'error', 'warning', 'info', 'debug', 'trace'],
            exclusive=True,
            uid=[],
        )
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output filename',
            description='Output filename for the alembic animated camera.',
            value='{cache}/{nodeType}/{uid0}/camera.abc',
            uid=[],
        ),
    ]
