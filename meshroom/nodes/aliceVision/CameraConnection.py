from meshroom.core import desc


class CameraConnection(desc.CommandLineNode):
    internalFolder = desc.Node.internalFolder
    commandLine = 'aliceVision_cameraConnection {allParams}'
    size = desc.DynamicNodeSize('ini')

    inputs = [
        desc.File(
            name="ini",
            label='MVS Configuration file',
            description='',
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

