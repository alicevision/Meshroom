__version__ = "3.0"

from meshroom.core import desc

class NormalIntegration(desc.CommandLineNode):
    commandLine = 'aliceVision_normalIntegration {allParams}'
    category = 'Photometry'
    documentation = '''
TODO.
'''

    inputs = [
        desc.File(
            name='sfmDataFile',
            label='sfmDataFile',
            description='''SfMData file.''',
            value='',
            uid=[0],
        ),
        desc.File(
            name='inputPath',
            label='inputPath',
            description='Normal maps folder',
            value='',
            uid=[0]
         )
    ]

    outputs = [
        desc.File(
            name='outputPath',
            label='Output path',
            description='Path to the output folder',
            value=desc.Node.internalFolder,
            uid=[],
        )
    ]
