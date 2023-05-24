__version__ = "1.0"

from meshroom.core import desc

class ExportDistortion(desc.AVCommandLineNode):
    commandLine = 'aliceVision_exportDistortion {allParams}'

    category = 'Export'
    documentation = '''
Export the distortion model and parameters of cameras in a SfM scene.
'''

    inputs = [
        desc.File(
            name='input',
            label='Input SfMData',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
    ]

    outputs = [
        desc.File(
            name='output',
            label='Folder',
            description='Output folder.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
