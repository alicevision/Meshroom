import sys
from meshroom.core import desc


class ConvertAnimatedCamera(desc.CommandLineNode):
    internalFolder = '{cache}/{nodeType}/{uid0}/'
    commandLine = 'aliceVision_convertAnimatedCamera {allParams}'

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='''SfMData file.''',
            value='',
            uid=[0],
            ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Output',
            description='''Path to the output Alembic file.''',
            value='{cache}/{nodeType}/{uid0}/animatedCamera.abc',
            uid=[],
            ),
    ]
