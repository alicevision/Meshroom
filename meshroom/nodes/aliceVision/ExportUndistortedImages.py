from meshroom.core import desc

class ExportUndistortedImages(desc.CommandLineNode):
    commandLine = 'aliceVision_exportUndistortedImages {allParams}'

    inputs = [
        desc.File(
            name='input',
            label='Input SfMData',
            description='SfMData file containing a complete SfM.',
            value='',
            uid=[0],
        ),
        desc.ChoiceParam(
            name='outputFileType',
            label='Output File Type',
            description='Output file type for the undistorted images.',
            value='exr',
            values=['jpg', 'png', 'tif', 'exr'],
            exclusive=True,
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
            label='Output Folder',
            description='Output folder for the undistorted images.',
            value=desc.Node.internalFolder,
            uid=[],
        ),
    ]
