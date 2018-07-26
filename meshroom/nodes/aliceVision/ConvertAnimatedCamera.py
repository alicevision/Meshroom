__version__ = "1.0"

from meshroom.core import desc


class ConvertAnimatedCamera(desc.CommandLineNode):
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
            description='Path to the output Alembic file.',
            value=desc.Node.internalFolder + 'animatedCamera.abc',
            uid=[],
            ),
    ]
