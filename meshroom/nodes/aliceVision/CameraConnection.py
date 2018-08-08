__version__ = "1.0"

from meshroom.core import desc


class CameraConnection(desc.CommandLineNode):
    internalFolder = desc.Node.internalFolder
    commandLine = 'aliceVision_cameraConnection {allParams}'
    size = desc.DynamicNodeSize('input')

    inputs = [
        desc.File(
            name='input',
            label='Input',
            description='SfMData file.',
            value='',
            uid=[0],
        ),
        desc.File(
            name='imagesFolder',
            label='Images Folder',
            description='Use images from a specific folder instead of those specify in the SfMData file.\nFilename should be the image uid.',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='verboseLevel',
            label='Verbose Level',
            description='verbosity level (fatal, error, warning, info, debug, trace).',
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
        description='Output folder for the camera pairs matrix file.',
        value=desc.Node.internalFolder,
        uid=[],
    )
]

